"""Message-taking service for Vapi voice calls.
   When someone can't authenticate or wants to leave a message,
   this stores it and can email you later.
"""
import json, os, datetime

MESSAGES_PATH = "/workspace/agentic-os/data/voice_messages.json"

def _load_messages() -> list:
    if os.path.exists(MESSAGES_PATH):
        try:
            with open(MESSAGES_PATH) as f:
                return json.load(f)
        except:
            return []
    return []

def _save_messages(messages: list):
    os.makedirs(os.path.dirname(MESSAGES_PATH), exist_ok=True)
    with open(MESSAGES_PATH, "w") as f:
        json.dump(messages, f, indent=2)

def take_message(caller_name: str, message: str, phone: str = "", callback_requested: bool = False) -> dict:
    """Record a message from a caller who couldn't be verified.
    Returns the message ID and confirmation.
    """
    messages = _load_messages()
    msg_id = f"MSG-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}-{len(messages)+1}"
    
    entry = {
        "id": msg_id,
        "caller_name": caller_name,
        "phone": phone,
        "message": message,
        "callback_requested": callback_requested,
        "created_at": datetime.datetime.now().isoformat(),
        "delivered": False,
    }
    messages.append(entry)
    _save_messages(messages)
    
    return {
        "message_id": msg_id,
        "confirmation": f"Your message has been recorded as {msg_id}. Big Reef will review it.",
        "count": len(messages),
    }

def get_undelivered() -> list:
    """Get all messages that haven't been delivered yet."""
    return [m for m in _load_messages() if not m.get("delivered")]

def mark_delivered(msg_id: str):
    messages = _load_messages()
    for m in messages:
        if m["id"] == msg_id:
            m["delivered"] = True
    _save_messages(messages)

def format_for_email() -> str:
    """Format undelivered messages as an email body."""
    msgs = get_undelivered()
    if not msgs:
        return "No new messages."
    
    lines = ["<h2>Voice Messages — Pending Review</h2>", "<table border='1' cellpadding='8' style='border-collapse:collapse'>",
             "<tr><th>ID</th><th>Caller</th><th>Phone</th><th>Message</th><th>Callback?</th><th>Time</th></tr>"]
    for m in msgs:
        cb = "Yes" if m.get("callback_requested") else "No"
        lines.append(f"<tr><td>{m['id']}</td><td>{m.get('caller_name','?')}</td><td>{m.get('phone','')}</td>"
                     f"<td>{m.get('message','')}</td><td>{cb}</td><td>{m['created_at'][:16]}</td></tr>")
    lines.append("</table>")
    return "\n".join(lines)
