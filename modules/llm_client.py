"""Minimal LLM client for summaries and classification."""
import json
import logging
from typing import List

import httpx

from modules.config import get_settings

logger = logging.getLogger("agentic_os.llm_client")


def _messages_for_summary(transcript: str) -> List[dict]:
    return [
        {
            "role": "system",
            "content": (
                "You are a concise assistant that summarizes phone calls for an admin. "
                "Return ONLY a JSON object with these keys: caller_name, reason, urgency "
                "(low/medium/high), action_items (list of strings), and sentiment. "
                "No markdown, no explanation."
            ),
        },
        {
            "role": "user",
            "content": f"Summarize this call transcript:\n\n{transcript}",
        },
    ]


def summarize_transcript(transcript: str) -> dict:
    """Generate a structured summary from a call transcript."""
    settings = get_settings()
    key = settings.OPENROUTER_API_KEY
    if not key:
        logger.warning("OPENROUTER_API_KEY not set; using heuristic summary")
        return _heuristic_summary(transcript)
    try:
        r = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://agentic-os.local",
                "X-Title": "Agentic OS Vapi Summary",
            },
            json={
                "model": settings.OPENROUTER_MODEL,
                "messages": _messages_for_summary(transcript),
                "temperature": 0.2,
            },
            timeout=30,
        )
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"]
        # Strip markdown fences
        content = content.strip()
        if content.startswith("```"):
            content = "\n".join(content.split("\n")[1:])
            if content.endswith("```"):
                content = content[:-3].strip()
        return json.loads(content)
    except Exception as e:
        logger.warning("LLM summary failed, falling back to heuristic", extra={"error": str(e)})
        return _heuristic_summary(transcript)


def _heuristic_summary(transcript: str) -> dict:
    t = transcript.lower()
    urgency = "low"
    if any(w in t for w in ["urgent", "emergency", "asap", "right away", "critical"]):
        urgency = "high"
    elif any(w in t for w in ["today", "tomorrow", "soon", "need to know"]):
        urgency = "medium"
    action_items = []
    if "message" in t or "tell shareef" in t:
        action_items.append("Deliver message to Shareef")
    if "schedule" in t or "on call" in t:
        action_items.append("Check schedule and follow up")
    if "swap" in t:
        action_items.append("Process swap request")
    return {
        "caller_name": "Unknown",
        "reason": "Voice call",
        "urgency": urgency,
        "action_items": action_items or ["Review call transcript"],
        "sentiment": "neutral",
    }
