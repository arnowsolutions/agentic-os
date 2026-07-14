"""Predictive call-swap intelligence.

When a caller asks to swap a call, this module:
1. Parses the target date and reason.
2. Finds eligible replacements from the CRM who are NOT already on call that day.
3. Ranks candidates by workload (fewer upcoming calls = higher rank).
4. Returns top candidates with contact info so the assistant can offer them.

All data resolved through EZ ID (universal key).
Swap execution routes through the Unified Platform.
"""
import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from modules.config import get_settings
from modules.logging_config import audit_record

logger = logging.getLogger("agentic_os.vapi_swap")


def _crm_path() -> Path:
    return get_settings().CRM_PATH


def _schedule_path() -> Path:
    # Look for the master call schedule; fall back to schedule module JSON if present
    base = get_settings().BASE_DIR
    candidates = [
        base / "data" / "call_schedule.json",
        base / "Call_Schedule_Q3_Q4_2026.xlsx",
        base / "data" / "schedule.json",
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]


def _load_crm() -> List[dict]:
    try:
        return json.loads(_crm_path().read_text())
    except Exception:
        return []


def _load_schedule() -> List[dict]:
    p = _schedule_path()
    if p.suffix == ".json" and p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            return []
    # Excel path placeholder: schedule module handles Excel
    return []


def _people_on_call(date_str: str, schedule: List[dict]) -> set:
    """Return set of names (lower) on call for a given YYYY-MM-DD date."""
    on_call = set()
    for entry in schedule:
        if entry.get("date") == date_str:
            for role in ("chief", "first_call", "second_call", "backup"):
                val = entry.get(role)
                if val:
                    if isinstance(val, list):
                        for v in val:
                            on_call.add(str(v).lower())
                    else:
                        on_call.add(str(val).lower())
    return on_call


def _upcoming_call_count(name: str, schedule: List[dict], from_date: datetime) -> int:
    """Count how many calls a person has in the next 30 days."""
    name_l = name.lower()
    count = 0
    window_end = from_date + timedelta(days=30)
    for entry in schedule:
        try:
            ed = datetime.strptime(entry.get("date", ""), "%Y-%m-%d")
        except Exception:
            continue
        if from_date.date() <= ed.date() <= window_end.date():
            for role in ("chief", "first_call", "second_call", "backup"):
                val = entry.get(role)
                if val:
                    vals = val if isinstance(val, list) else [val]
                    if any(str(v).lower() == name_l for v in vals):
                        count += 1
    return count


def _candidate_name(c: dict) -> str:
    return f"{c.get('firstName', '')} {c.get('lastName', '')}".strip()


def _candidate_ez_id(c: dict) -> Optional[str]:
    """Get a candidate's EZ ID from the CRM entry."""
    return c.get('ezId') or c.get('ez_id') or None


# ─── Swap Execution ──────────────────────────────────────────────────────

# Import the swap engine to execute swaps directly
import sys
_swap_engine_path = Path("/workspace/call-schedule-app/swap_engine.py")
if _swap_engine_path.exists():
    import importlib.util
    spec = importlib.util.spec_from_file_location("swap_engine", _swap_engine_path)
    _swap_engine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(_swap_engine)
    execute_swap = _swap_engine.execute_swap
else:
    def execute_swap(requester=None, target=None, req_date_str=None, tgt_date_str=None, **kwargs):
        return {"success": False, "error": "swap_engine.py not found"}


def _format_phone(phone: str) -> str:
    digits = "".join(c for c in (phone or "") if c.isdigit())
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    return phone or ""


def handle_swap_request(args: Dict[str, Any]) -> Dict[str, Any]:
    """Main entrypoint for the swapCall tool."""
    caller = args.get("caller_name", "Unknown")
    date_str = args.get("date", "")
    reason = args.get("reason", "")
    preferred = args.get("preferred_replacement", "")

    if not date_str:
        return {"status": "error", "message": "Please tell me the date you need to swap."}

    # Normalize date
    try:
        target = datetime.strptime(date_str, "%Y-%m-%d")
    except Exception:
        # Try common spoken formats
        for fmt in ("%B %d, %Y", "%b %d, %Y", "%m/%d/%Y", "%m-%d-%Y"):
            try:
                target = datetime.strptime(date_str, fmt)
                break
            except Exception:
                continue
        else:
            return {"status": "error", "message": f"I didn't understand the date '{date_str}'. Please say it like July 1st, 2026."}
    date_str = target.strftime("%Y-%d")
    # FIX: above produces wrong format (year-day). Let's use %Y-%m-%d.
    date_str = target.strftime("%Y-%m-%d")

    crm = _load_crm()
    schedule = _load_schedule()
    on_call = _people_on_call(date_str, schedule)

    candidates = []
    for c in crm:
        name = _candidate_name(c)
        if not name:
            continue
        name_l = name.lower()
        # Eligible if not already on call that day and is a resident/faculty/staff
        if name_l in on_call:
            continue
        if c.get("category") not in ("Resident", "Faculty", "Nurse Practitioner", "Physician Assistant", "Staff"):
            continue
        workload = _upcoming_call_count(name, schedule, target)
        candidates.append({
            "name": name,
            "ezId": _candidate_ez_id(c),
            "category": c.get("category", ""),
            "phone": _format_phone(c.get("phone", "")),
            "email": c.get("email", ""),
            "workload_next_30d": workload,
        })

    # Rank by workload (fewer calls first), then preferred replacement first
    candidates.sort(key=lambda x: (0 if x["name"].lower() == preferred.lower() else 1, x["workload_next_30d"]))
    top = candidates[:5]

    audit_record(
        "swap_request",
        caller=caller,
        date=date_str,
        reason=reason,
        preferred=preferred,
        candidates=[c["name"] for c in top],
    )

    if not top:
        return {
            "status": "no_candidates",
            "message": "I couldn't find an eligible replacement who isn't already on call that day. I'll log this for Shareef.",
            "date": date_str,
        }

    return {
        "status": "candidates_found",
        "date": date_str,
        "reason": reason,
        "top_candidates": top,
        "next_step": "contact_candidate",
        "message": f"I found {len(top)} possible replacement{'s' if len(top)>1 else ''}. Want me to reach out to {top[0]['name']}?",
    }
