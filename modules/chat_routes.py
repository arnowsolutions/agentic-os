"""
Agentic OS — Chat Routes
Extracted from server.py Phase 9 module extraction.
"""
import json
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from modules.config import get_settings
from modules.agent_executor import execute_agent

router = APIRouter(prefix="/api/chat", tags=["chat"])

# ─── Models ──────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    agent: str
    message: str

# ─── Helpers ─────────────────────────────────────────────────────

def _get_base_dir() -> Path:
    settings = get_settings()
    return settings.BASE_DIR


def _get_chat_history_file() -> Path:
    return _get_base_dir() / "data" / "chat-history.json"


def _load_chat_history() -> dict:
    """Load chat history from disk, returning {"messages": []} if missing."""
    path = _get_chat_history_file()
    if path.exists():
        return json.loads(path.read_text())
    return {"messages": []}


def _save_chat_message(msg: dict):
    """Append a message to chat history, capping at 200 messages."""
    path = _get_chat_history_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    history = _load_chat_history()
    history["messages"].append(msg)
    if len(history["messages"]) > 200:
        history["messages"] = history["messages"][-200:]
    path.write_text(json.dumps(history, indent=2))


def _get_timestamp() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def _record_agent_run(action: str, source: str, agent: str, status: str = "success", metadata: dict | None = None):
    """Record a normalized agent run event to the audit log."""
    base = _get_base_dir()
    audit_file = base / "audit" / "audit.log"
    audit_file.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "action": action,
        "source": source,
        "agent": agent,
        "event_id": str(uuid.uuid4())[:12],
        "status": status,
        "metadata": metadata or {},
        "timestamp": _get_timestamp(),
        "id": str(uuid.uuid4())[:8],
    }
    with open(audit_file, "a") as f:
        f.write(json.dumps(entry) + "\n")


# ─── Routes ──────────────────────────────────────────────────────

@router.post("")
def chat(req: ChatRequest):
    agent = req.agent.lower().strip()
    if agent not in ["opencode", "hermes", "gemini"]:
        raise HTTPException(400, "Agent must be one of: opencode, hermes, gemini")

    user_msg = {
        "id": str(uuid.uuid4())[:8],
        "role": "user",
        "agent": agent,
        "content": req.message,
        "timestamp": _get_timestamp(),
    }
    _save_chat_message(user_msg)

    response_text = execute_agent(agent, req.message)

    agent_msg = {
        "id": str(uuid.uuid4())[:8],
        "role": "assistant",
        "agent": agent,
        "content": response_text,
        "timestamp": _get_timestamp(),
    }
    _save_chat_message(agent_msg)

    _record_agent_run(
        action="chat_message",
        source="chat",
        agent=agent,
        status="success",
        metadata={
            "msg_preview": req.message[:100],
            "response_preview": response_text[:100],
        },
    )

    return {"status": "ok", "response": agent_msg}


@router.get("/history")
def get_chat_history():
    return _load_chat_history()
