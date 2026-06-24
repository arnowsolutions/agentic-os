"""Integration tests for the Vapi voice webhook pipeline."""
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure project root on path
sys.path.insert(0, str(Path(__file__).parent.parent))

from server import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def _function_call(name: str, arguments: dict) -> dict:
    return {
        "message": {
            "type": "function-call",
            "function": {"name": name, "arguments": arguments},
        }
    }


def test_status_endpoint(client):
    r = client.get("/vapi/status")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "pin_db" in data


def _tool_call(tool_call_id: str, name: str, arguments: dict) -> dict:
    return {
        "message": {
            "type": "tool-calls",
            "toolCalls": [
                {
                    "id": tool_call_id,
                    "type": "function",
                    "function": {"name": name, "arguments": arguments},
                }
            ],
        }
    }


def test_verify_caller_success(client):
    payload = _function_call("verifyCaller", {"caller_name": "Shareef Frasier", "caller_pin": "1279"})
    r = client.post("/vapi", json=payload)
    assert r.status_code == 200
    result = json.loads(r.json()["result"])
    assert result["verified"] is True
    assert result["next_step"] == "proceed"
    assert "greeting" in result


def test_verify_caller_tool_calls_format(client):
    payload = _tool_call("call_test_abc", "verifyCaller", {"caller_name": "Shareef Frasier", "caller_pin": "1279"})
    r = client.post("/vapi", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "results" in data
    assert len(data["results"]) == 1
    assert data["results"][0]["toolCallId"] == "call_test_abc"
    result = json.loads(data["results"][0]["result"])
    assert result["verified"] is True
    assert result["next_step"] == "proceed"


def test_verify_caller_wrong_pin(client):
    payload = _function_call("verifyCaller", {"caller_name": "Shareef Frasier", "caller_pin": "9999"})
    r = client.post("/vapi", json=payload)
    assert r.status_code == 200
    result = json.loads(r.json()["result"])
    assert result["verified"] is False
    assert result["next_step"] == "retry_pin"


def test_verify_caller_incomplete_pin(client):
    payload = _function_call("verifyCaller", {"caller_name": "Shareef Frasier", "caller_pin": "12"})
    r = client.post("/vapi", json=payload)
    assert r.status_code == 200
    result = json.loads(r.json()["result"])
    assert result["verified"] is False
    assert result["next_step"] == "retry_pin"
    assert "2 digit" in result["message"]


def test_verify_caller_name_normalization(client):
    payload = _function_call("verifyCaller", {"caller_name": "Sharif Frazier", "caller_pin": "1279"})
    r = client.post("/vapi", json=payload)
    assert r.status_code == 200
    result = json.loads(r.json()["result"])
    assert result["verified"] is True


def test_knowledge_search_returns_results(client):
    payload = _function_call("knowledgeSearch", {"q": "Grand Rounds schedule"})
    r = client.post("/vapi", json=payload)
    assert r.status_code == 200
    result = json.loads(r.json()["result"])
    assert isinstance(result, list)
    assert len(result) > 0
    assert "snippet" in result[0]


def test_take_message(client):
    payload = _function_call("takeMessage", {
        "caller_name": "Test Caller",
        "message": "Please call me back about the schedule.",
        "phone": "555-1234",
        "callback_requested": True,
    })
    r = client.post("/vapi", json=payload)
    assert r.status_code == 200
    result = json.loads(r.json()["result"])
    assert "message_id" in result
    assert "confirmation" in result


def test_unknown_function(client):
    payload = _function_call("nonexistentTool", {})
    r = client.post("/vapi", json=payload)
    assert r.status_code == 200
    result = json.loads(r.json()["result"])
    assert "error" in result


def test_end_of_call_report(client):
    payload = {
        "message": {
            "type": "end-of-call-report",
            "call": {"id": "test-call-123", "durationSeconds": 45, "cost": 0.12, "recordingUrl": ""},
            "transcript": "Hi this is Dr. Smith. I need to swap my Friday call because of a family event.",
        }
    }
    r = client.post("/vapi", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["result"] == "logged"


def test_rate_limit_locks_after_repeated_failures(client):
    # Reset limiter state is not exposed, but running max attempts in a row should lock.
    for _ in range(6):
        payload = _function_call("verifyCaller", {"caller_name": "Shareef Frasier", "caller_pin": "0000"})
        r = client.post("/vapi", json=payload)
        assert r.status_code == 200
    result = json.loads(r.json()["result"])
    # After AUTH_MAX_ATTEMPTS failures we should be locked out
    assert result["verified"] is False
    assert "minute" in result["message"].lower() or "try again" in result["message"].lower()


def test_swap_call_returns_candidates(client):
    payload = _function_call("swapCall", {
        "caller_name": "Shareef Frasier",
        "date": "2026-07-01",
        "reason": "Family event",
    })
    r = client.post("/vapi", json=payload)
    assert r.status_code == 200
    result = json.loads(r.json()["result"])
    assert result.get("status") in ("candidates_found", "no_candidates")


def test_get_deadlines(client):
    payload = _function_call("getDeadlines", {"role": "resident"})
    r = client.post("/vapi", json=payload)
    assert r.status_code == 200
    result = json.loads(r.json()["result"])
    assert "deadlines" in result


def test_admin_dashboard(client):
    r = client.get("/vapi/admin")
    assert r.status_code == 200
    assert b"Vapi Voice Admin" in r.content


def test_admin_audit_api(client):
    r = client.get("/vapi/admin/api/audit")
    assert r.status_code == 200
    data = r.json()
    assert "records" in data


def test_webhook_secret_blocks_unsigned_request(client, monkeypatch):
    from server import _settings
    monkeypatch.setattr(_settings, "WEBHOOK_SECRET", "test-secret")

    payload = _function_call("verifyCaller", {"caller_name": "Webhook Test Caller", "caller_pin": "0000"})
    r = client.post("/vapi", json=payload)
    assert r.status_code == 403
    assert "invalid signature" in r.json()["error"]


def test_webhook_secret_allows_signed_request(client, monkeypatch):
    import hmac, hashlib, json as _json
    from server import _settings
    monkeypatch.setattr(_settings, "WEBHOOK_SECRET", "test-secret")

    payload = _function_call("verifyCaller", {"caller_name": "Webhook Test Caller", "caller_pin": "0000"})
    body = _json.dumps(payload).encode()
    sig = hmac.new(b"test-secret", body, hashlib.sha256).hexdigest()
    r = client.post("/vapi", content=body, headers={"x-signature-sha256": sig, "Content-Type": "application/json"})
    assert r.status_code == 200
    result = _json.loads(r.json()["result"])
    assert result["verified"] is False
    assert result["next_step"] in ("retry_pin", "take_message")


def test_metrics_endpoint(client):
    r = client.get("/metrics")
    assert r.status_code == 200
    text = r.text
    assert "agentic_os_requests_total" in text
    assert "agentic_os_vapi_webhooks_total" in text
    assert "agentic_os_auth_attempts_total" in text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
