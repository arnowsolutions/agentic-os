"""Post-call summary pipeline.

Triggered by Vapi's end-of-call-report webhook. Generates a structured summary,
logs it, emails Shareef, and creates a kanban task draft.
"""
import json
import logging
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from modules import llm_client
from modules.config import get_settings
from modules.logging_config import audit_record

logger = logging.getLogger("agentic_os.vapi_call_summary")


def _kanban_dir():
    from modules import kanban
    return kanban.KANBAN_DIR or (get_settings().BASE_DIR / "data" / "kanban")


def _save_task(title: str, body: str, priority: str = "medium"):
    try:
        kd = _kanban_dir()
        kd.mkdir(parents=True, exist_ok=True)
        task = {
            "id": str(uuid.uuid4())[:8],
            "title": title,
            "body": body,
            "status": "triage",
            "priority": priority,
            "assignee": "Shareef Frasier",
            "comments": [],
            "links": [],
            "created": datetime.now(timezone.utc).isoformat(),
            "updated": datetime.now(timezone.utc).isoformat(),
        }
        (kd / f"{task['id']}.json").write_text(json.dumps(task, indent=2))
        return task["id"]
    except Exception as e:
        logger.warning("failed to create kanban task", extra={"error": str(e)})
        return None


def _email_summary(summary: Dict[str, Any], call_meta: Dict[str, Any]):
    settings = get_settings()
    subject = f"Call summary: {summary.get('caller_name', 'Unknown')} — {summary.get('urgency', 'low')} urgency"
    body_lines = [
        f"Caller: {summary.get('caller_name', 'Unknown')}",
        f"Reason: {summary.get('reason', 'N/A')}",
        f"Urgency: {summary.get('urgency', 'low')}",
        f"Sentiment: {summary.get('sentiment', 'neutral')}",
        "",
        "Action items:",
    ]
    for item in summary.get("action_items", []):
        body_lines.append(f"  - {item}")
    body_lines.extend([
        "",
        f"Duration: {call_meta.get('duration_seconds', 'unknown')}s",
        f"Cost: {call_meta.get('cost', 'unknown')}",
        f"Recording: {call_meta.get('recording_url', 'N/A')}",
    ])
    body = "\n".join(body_lines)
    try:
        helper = settings.BASE_DIR / "email_helper.py"
        if helper.exists():
            subprocess.run(
                [sys.executable, str(helper), "--to", "sfrasier@montefiore.org", "--subject", subject],
                input=body, text=True, timeout=30, capture_output=True
            )
        else:
            logger.warning("email_helper.py not found; skipping email")
    except Exception as e:
        logger.warning("failed to send summary email", extra={"error": str(e)})


def handle_end_of_call(payload: Dict[str, Any]):
    """Process Vapi end-of-call-report payload."""
    call = payload.get("call", {}) if isinstance(payload.get("call"), dict) else {}
    transcript = payload.get("transcript", "") or call.get("transcript", "")
    if not transcript and "messages" in payload:
        transcript = "\n".join(str(m.get("content", "")) for m in payload["messages"])

    summary = llm_client.summarize_transcript(transcript or "No transcript available")

    call_meta = {
        "call_id": payload.get("call", {}).get("id") if isinstance(payload.get("call"), dict) else None,
        "duration_seconds": payload.get("call", {}).get("durationSeconds") if isinstance(payload.get("call"), dict) else None,
        "cost": payload.get("call", {}).get("cost") if isinstance(payload.get("call"), dict) else None,
        "recording_url": payload.get("call", {}).get("recordingUrl") if isinstance(payload.get("call"), dict) else None,
    }

    audit_record(
        "call_summary",
        caller_name=summary.get("caller_name", "Unknown"),
        reason=summary.get("reason", ""),
        urgency=summary.get("urgency", "low"),
        sentiment=summary.get("sentiment", "neutral"),
        action_items=summary.get("action_items", []),
        call_meta=call_meta,
    )

    priority = summary.get("urgency", "medium")
    task_id = _save_task(
        title=f"Call follow-up: {summary.get('caller_name', 'Unknown')} — {summary.get('reason', 'N/A')}",
        body=json.dumps({"summary": summary, "call_meta": call_meta}, indent=2),
        priority=priority,
    )

    _email_summary(summary, call_meta)

    logger.info("call summary processed", extra={"caller": summary.get("caller_name"), "urgency": priority, "task_id": task_id})
    return {"status": "processed", "summary": summary, "task_id": task_id}
