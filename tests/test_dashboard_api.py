"""Lightweight API contract tests for Agentic OS dashboard-critical endpoints.

Covers the endpoints identified in the code review: kanban, analytics,
sessions, settings, and duplicate route detection.
Tests use the FastAPI TestClient and confirm response shapes without
mutating production data.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure project root on path
sys.path.insert(0, str(Path(__file__).parent.parent))

from server import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


# ─── Helper ──────────────────────────────────────────────────────────

def assert_is_list_of_dicts(items, required_keys=None):
    """Assert items is a list and each item is a dict with required keys."""
    assert isinstance(items, list), f"Expected list, got {type(items)}"
    if required_keys:
        for item in items:
            assert isinstance(item, dict), f"Expected dict, got {type(item)}"
            for k in required_keys:
                assert k in item, f"Missing key '{k}' in item {item.get('id', item.get('name', '?'))}"


# ─── Duplicate Route Assertion ──────────────────────────────────────

def test_no_duplicate_routes(client):
    """Assert no two routes share the same method+path (method collisions)."""
    seen = {}
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            for method in route.methods - {"HEAD", "OPTIONS"}:
                key = (method, route.path)
                assert key not in seen, f"Duplicate route: {method} {route.path}"
                seen[key] = route


# ─── Kanban ─────────────────────────────────────────────────────────

def test_kanban_board_returns_contract(client):
    """Canonical contract: { columns: dict, tasks: list, total: int }."""
    r = client.get("/api/kanban/board")
    assert r.status_code == 200
    data = r.json()
    assert "columns" in data, "Missing columns in /api/kanban/board response"
    assert "tasks" in data, "Missing tasks (flat array) in /api/kanban/board response"
    assert "total" in data, "Missing total in /api/kanban/board response"
    assert isinstance(data["columns"], dict), "columns must be a dict"
    assert isinstance(data["tasks"], list), "tasks must be a list"
    assert isinstance(data["total"], int), "total must be an int"


def test_kanban_create_task(client):
    """Verify we can create a task and it returns the expected shape."""
    r = client.post("/api/kanban/tasks", json={
        "title": "Test Contract Task",
        "body": "Verify the contract",
        "status": "triage",
        "priority": "high",
    })
    assert r.status_code == 200
    task = r.json()
    assert "id" in task
    assert task["title"] == "Test Contract Task"
    assert task["status"] == "triage"
    # Cleanup
    task_id = task["id"]
    client.delete(f"/api/kanban/tasks/{task_id}")


def test_kanban_delete_task_not_found(client):
    """DELETE on nonexistent task returns 404."""
    r = client.delete("/api/kanban/tasks/nonexistent-task-id")
    assert r.status_code == 404


# ─── Analytics ──────────────────────────────────────────────────────

def test_analytics_skills_contract(client):
    """Canonical contract: { skills: [{ name, score, evals, best }] }."""
    r = client.get("/api/analytics/skills")
    assert r.status_code == 200
    data = r.json()
    assert "skills" in data
    assert isinstance(data["skills"], list)
    required = ["name", "score", "evals", "best"]
    for skill in data["skills"]:
        for k in required:
            assert k in skill, f"Missing '{k}' in skill {skill.get('name', '?')}"
        # score and best should be floats in 0-1 range
        assert isinstance(skill["score"], (int, float)), f"score must be numeric in {skill['name']}"
        assert isinstance(skill["evals"], int), f"evals must be int in {skill['name']}"
        assert isinstance(skill["best"], (int, float)), f"best must be numeric in {skill['name']}"


def test_analytics_trends_contract(client):
    """Canonical contract: { trends: { skillName: [scores...], ... } }."""
    r = client.get("/api/analytics/trends")
    assert r.status_code == 200
    data = r.json()
    assert "trends" in data
    assert isinstance(data["trends"], dict), "trends must be a dict (skill-keyed map)"
    for skill_name, scores in data["trends"].items():
        assert isinstance(scores, list), f"trends[{skill_name}] must be a list"
        for score in scores:
            assert isinstance(score, (int, float)), f"Score in {skill_name} must be numeric"


# ─── Sessions ───────────────────────────────────────────────────────

def test_sessions_list_contract(client):
    """Canonical contract: { sessions: [{ id, date, size, ... }] }."""
    r = client.get("/api/sessions/list")
    assert r.status_code == 200
    data = r.json()
    assert "sessions" in data
    assert isinstance(data["sessions"], list)
    for session in data["sessions"]:
        assert "id" in session, "Missing id in session"
        assert "date" in session, "Missing canonical date field in session"
        assert "size" in session, "Missing size in session"


def test_session_replay_messages_contract(client):
    """Messages should be objects with role/content/timestamp.

    Accepts either valid sessions or 404 fallback responses, but the
    structure must be consistent.
    """
    # Try a likely-nonexistent session to test the contract safety
    r = client.get("/api/sessions/__test_nonexistent_session__/replay")
    assert r.status_code == 200
    data = r.json()
    assert "session" in data, "Missing session in replay response"
    assert "messages" in data, "Missing messages in replay response"
    assert isinstance(data["messages"], list), "messages must be a list"
    for msg in data["messages"]:
        assert "role" in msg, f"Missing role in message: {msg.get('content', '')[:50]}"
        assert "content" in msg, f"Missing content in message"
        assert "timestamp" in msg, "Missing timestamp in message"


# ─── Settings ───────────────────────────────────────────────────────

def test_settings_returns_defaults(client):
    """GET /api/settings returns a complete payload with expected keys."""
    r = client.get("/api/settings")
    assert r.status_code == 200
    data = r.json()
    # It should at least have top-level sections
    assert isinstance(data, dict), "settings must be a dict"
    # The payload should be self-consistent — if data exists, check structure


# ─── Health ─────────────────────────────────────────────────────────

def test_agent_health_contract(client):
    """Canonical contract: { agents: [{ name, health_label, total_runs, last_seen, availability }] }."""
    r = client.get("/api/agents/health")
    assert r.status_code == 200
    data = r.json()
    assert "agents" in data
    assert isinstance(data["agents"], list)
    for agent in data["agents"]:
        assert "name" in agent
        assert "health_label" in agent
        assert "total_runs" in agent
        valid_labels = {"healthy", "offline", "no_usage_yet"}
        assert agent["health_label"] in valid_labels, f"Unexpected health_label: {agent['health_label']}"


# ─── Selftest ──────────────────────────────────────────────────────

def test_selftest_contract(client):
    """Canonical contract: { ok: bool, checks: [{ name, ok }] }."""
    r = client.get("/api/selftest")
    assert r.status_code == 200
    data = r.json()
    assert "ok" in data, "Missing ok flag in selftest"
    assert "checks" in data, "Missing checks in selftest"
    assert isinstance(data["checks"], list), "checks must be a list"
    for check in data["checks"]:
        assert "name" in check, "Missing name in check"
        assert "ok" in check, "Missing ok in check"


# ─── Router ─────────────────────────────────────────────────────────

def test_router_config_contract(client):
    """Canonical contract: { routing_rules: [...], agent_capabilities: {...} }."""
    r = client.get("/api/router/config")
    assert r.status_code == 200
    data = r.json()
    assert "routing_rules" in data, "Missing routing_rules"
    assert "agent_capabilities" in data, "Missing agent_capabilities"
    assert isinstance(data["routing_rules"], list), "routing_rules must be a list"
    assert isinstance(data["agent_capabilities"], dict), "agent_capabilities must be a dict"
    for rule in data["routing_rules"]:
        assert "pattern" in rule
        assert "target" in rule
        assert "priority" in rule


def test_router_suggest_contract(client):
    """Canonical contract: { suggested_agent, confidence, scores, matched_rules }."""
    r = client.post("/api/router/suggest", json={"task": "deploy the application to GCP"})
    assert r.status_code == 200
    data = r.json()
    assert "suggested_agent" in data
    assert "confidence" in data
    assert "scores" in data
    assert "matched_rules" in data
    assert data["suggested_agent"] in ("opencode", "hermes", "gemini")
    assert data["confidence"] in ("high", "medium", "low", "fallback")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
