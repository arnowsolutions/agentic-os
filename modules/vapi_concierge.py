"""Voice concierge utilities: deadlines, evaluations due, and reminders."""
import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List

from modules.config import get_settings

logger = logging.getLogger("agentic_os.vapi_concierge")


def _today() -> datetime:
    return datetime.now(timezone.utc).astimezone()


def _eval_forms_dir() -> Path:
    return get_settings().BASE_DIR / "data" / "eval_forms"


def _load_eval_forms(name: str = "") -> List[dict]:
    """Load evaluation forms if they exist; otherwise return synthetic deadlines."""
    d = _eval_forms_dir()
    forms = []
    if d.exists():
        for f in sorted(d.glob("*.json")):
            try:
                data = json.loads(f.read_text())
                if isinstance(data, list):
                    forms.extend(data)
                else:
                    forms.append(data)
            except Exception:
                continue
    if not forms:
        # Synthetic academic-year deadlines
        today = _today()
        forms = [
            {"title": "Faculty evaluation", "due": (today + timedelta(days=14)).strftime("%Y-%m-%d"), "type": "evaluation"},
            {"title": "Resident evaluation", "due": (today + timedelta(days=21)).strftime("%Y-%m-%d"), "type": "evaluation"},
        ]
    if name:
        name_l = name.lower()
        forms = [f for f in forms if name_l in (f.get("resident_name", "") + f.get("faculty_name", "") + f.get("title", "")).lower()]
    return forms


def get_deadlines(role: str = "") -> Dict[str, Any]:
    """Return upcoming program deadlines based on role."""
    today = _today()
    deadlines = []

    # Academic year cycle
    year = today.year
    if today.month >= 7:
        ay_start = datetime(year, 7, 1, tzinfo=today.tzinfo)
        ay_end = datetime(year + 1, 6, 30, tzinfo=today.tzinfo)
    else:
        ay_start = datetime(year - 1, 7, 1, tzinfo=today.tzinfo)
        ay_end = datetime(year, 6, 30, tzinfo=today.tzinfo)

    if not role or role.lower() in ("resident", "all"):
        deadlines.extend([
            {"item": "GME reimbursement request", "due": "Before funds run out", "note": "Up to $1,250 per academic year"},
            {"item": "Sick call notification", "due": "As soon as possible", "note": "Call the assistant to file"},
        ])
    if not role or role.lower() in ("faculty", "attending", "all"):
        deadlines.append({"item": "Faculty evaluations", "due": "End of rotation", "note": "Required for each resident"})

    return {
        "today": today.strftime("%Y-%m-%d"),
        "academic_year": f"{ay_start.strftime('%Y')}-{ay_end.strftime('%y')}",
        "deadlines": deadlines,
    }


def get_evaluations_due(name: str = "") -> Dict[str, Any]:
    """Return pending evaluations, optionally filtered by resident/faculty name."""
    forms = _load_eval_forms(name)
    today = _today().date()
    pending = []
    for f in forms:
        due = f.get("due", "")
        try:
            due_dt = datetime.strptime(due, "%Y-%m-%d").date()
            days_left = (due_dt - today).days
        except Exception:
            days_left = None
        pending.append({
            "title": f.get("title", "Evaluation"),
            "due": due,
            "days_left": days_left,
            "completed": f.get("completed", False),
        })
    pending.sort(key=lambda x: x["days_left"] if x["days_left"] is not None else 999)
    return {
        "count": len(pending),
        "pending": pending,
        "message": f"You have {len(pending)} evaluation{'s' if len(pending)!=1 else ''} pending." if not name else f"{name} has {len(pending)} pending evaluation{'s' if len(pending)!=1 else ''}.",
    }


def file_sick_call(args: Dict[str, Any]) -> Dict[str, Any]:
    """Thin wrapper around the sick-call intake."""
    from modules import vapi_bridge
    return vapi_bridge._handle_sick_call(args)
