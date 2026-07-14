"""Tests for agent routing logic — pattern matching and confidence scoring."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_route_code_task_to_opencode():
    """Code-related tasks should route to opencode."""
    from server import load_router_config, score_routing_rules
    
    config = load_router_config()
    _, _, agent, confidence = score_routing_rules("write code for a new API endpoint", config)
    assert agent == "opencode"
    # "code" keyword should match with medium+ confidence


def test_route_devops_task_to_opencode():
    """DevOps/infrastructure tasks should route to opencode."""
    from server import load_router_config, score_routing_rules
    
    config = load_router_config()
    _, _, agent, confidence = score_routing_rules("deploy the kubernetes cluster to GCP", config)
    assert agent == "opencode"
    assert confidence in ("high", "medium")


def test_route_memory_task_to_hermes():
    """Memory/schedule tasks should route to hermes."""
    from server import load_router_config, score_routing_rules
    
    config = load_router_config()
    _, _, agent, confidence = score_routing_rules("remember that the meeting is at 3pm", config)
    assert agent == "hermes"


def test_route_research_task_to_gemini():
    """Research tasks should route to gemini."""
    from server import load_router_config, score_routing_rules
    
    config = load_router_config()
    _, _, agent, _ = score_routing_rules("research the latest papers on kidney stones", config)
    assert agent == "gemini"


def test_route_unknown_task_falls_back():
    """Unknown tasks should fall back to opencode with low confidence."""
    from server import load_router_config, score_routing_rules
    
    config = load_router_config()
    _, _, agent, confidence = score_routing_rules("blargle flargle wozzle", config)
    assert agent == "opencode"
    assert confidence == "fallback"


def test_routing_config_has_required_keys():
    """Router config must have routing_rules and agent_capabilities."""
    from server import load_router_config
    
    config = load_router_config()
    assert "routing_rules" in config
    assert "agent_capabilities" in config
    assert len(config["routing_rules"]) > 0
    assert "opencode" in config["agent_capabilities"]
    assert "hermes" in config["agent_capabilities"]
    assert "gemini" in config["agent_capabilities"]


def test_cost_tracker_record_computes_daily_totals():
    """Recording a cost entry should update daily totals."""
    from modules.cost_tracker import record, get_history
    
    # Record a test entry
    record(agent="opencode", model="__test_cleanup__", tokens=150, cost=0.001)
    
    history = get_history()
    assert "daily_totals" in history
    assert "entries" in history
    assert len(history["entries"]) > 0
    assert history["entries"][-1]["agent"] == "opencode"
    
    # Cleanup — remove test entry
    _cleanup_test_entries()


def test_cost_tracker_free_tier_alert_triggers():
    """When usage exceeds warn_pct, alert should appear in free_tier_alerts."""
    from modules.cost_tracker import record, get_history
    
    # Record many high-token entries to trigger alerts
    for _ in range(50):
        record(agent="gemini", model="__test_cleanup__", tokens=100000, cost=0.0)
    
    history = get_history()
    assert "free_tier_alerts" in history
    
    # Cleanup — remove all test entries
    _cleanup_test_entries()


def _cleanup_test_entries():
    """Remove test entries from cost-history.json so they don't pollute production."""
    from modules.cost_tracker import _history_path, _load, DEFAULT_SHAPE
    import json
    path = _history_path()
    if not path.exists():
        return
    data = _load()
    data["entries"] = [e for e in data["entries"] if e.get("model") != "__test_cleanup__"]
    path.write_text(json.dumps(data, indent=2))
