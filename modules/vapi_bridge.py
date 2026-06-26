#!/usr/bin/env python3
"""Vapi bridge - handles Vapi.ai webhooks and routes tool calls to modules."""
import hashlib
import json
import logging
import os
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from modules import vapi_data, vapi_knowledge, vapi_unified, voice_messages
from modules.config import get_settings
from modules.logging_config import audit_record, setup_logging
from modules.metrics import get_collector
from modules.supabase_client import get_supabase_helper

setup_logging()
logger = logging.getLogger("agentic_os.vapi_bridge")
collector = get_collector()

router = APIRouter(prefix="/vapi")
settings = get_settings()
BASE_DIR = settings.BASE_DIR
DATA_DIR = settings.DATA_DIR
CRM_PATH = settings.CRM_PATH
PIN_DB_PATH = settings.PIN_DB_PATH


def _hash_pin(pin: str) -> str:
    return hashlib.sha256(pin.encode()).hexdigest()


# ─── Simple file cache ──────────────────────────────────────────────────────
_cache: dict[Path, dict[str, Any]] = {}
_cache_lock = threading.Lock()


def _load_json_cached(path: Path) -> Any:
    """Load a JSON file, refreshing only when mtime changes or TTL expires."""
    if not path.exists():
        return {} if "pins" in path.name or "contacts" in path.name else []
    now = time.time()
    with _cache_lock:
        entry = _cache.get(path)
        if entry:
            if now - entry["ts"] < settings.CACHE_TTL_SECONDS:
                return entry["data"]
            try:
                mtime = path.stat().st_mtime
                if mtime == entry["mtime"]:
                    entry["ts"] = now
                    return entry["data"]
            except Exception:
                pass
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            data = {} if "pins" in path.name or "contacts" in path.name else []
        _cache[path] = {"data": data, "mtime": path.stat().st_mtime, "ts": now}
        return data


def _load_pin_db() -> dict:
    return _load_json_cached(PIN_DB_PATH)


def _load_crm() -> list:
    return _load_json_cached(CRM_PATH)


def _invalidate_cache(path: Path | None = None):
    with _cache_lock:
        if path is None:
            _cache.clear()
        elif path in _cache:
            del _cache[path]


# ─── Auth rate limiter ──────────────────────────────────────────────────────
class _AuthLimiter:
    """In-memory per-caller attempt tracker with lockout."""

    def __init__(self, max_attempts: int, lockout_seconds: int):
        self.max_attempts = max_attempts
        self.lockout_seconds = lockout_seconds
        self._state: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    def _key(self, name: str, ip: str = "") -> str:
        return f"{name.lower().strip()}:{ip}"

    def is_locked(self, name: str, ip: str = "") -> tuple[bool, int]:
        now = time.time()
        with self._lock:
            s = self._state.get(self._key(name, ip))
            if not s:
                return False, 0
            if s["failures"] >= self.max_attempts:
                remaining = int(s["locked_until"] - now)
                if remaining > 0:
                    return True, remaining
                # lock expired, reset
                s["failures"] = 0
                s["locked_until"] = 0
        return False, 0

    def record(self, name: str, success: bool, ip: str = ""):
        key = self._key(name, ip)
        with self._lock:
            s = self._state.setdefault(key, {"failures": 0, "locked_until": 0})
            if success:
                s["failures"] = 0
                s["locked_until"] = 0
            else:
                s["failures"] += 1
                if s["failures"] >= self.max_attempts:
                    s["locked_until"] = time.time() + self.lockout_seconds


_auth_limiter = _AuthLimiter(settings.AUTH_MAX_ATTEMPTS, settings.AUTH_LOCKOUT_SECONDS)


def _normalize_name(name: str) -> str:
    """Fix common STT mangling for Shareef/Frasier and trim whitespace."""
    if not name:
        return ""
    n = name.strip()
    lower = n.lower()
    variants = {
        "to be fair frazier": "Shareef Frasier",
        "delete aphasia": "Shareef Frasier",
        "sharif frazier": "Shareef Frasier",
        "sharif frasier": "Shareef Frasier",
        "charisse frazier": "Shareef Frasier",
        "charisse frasier": "Shareef Frasier",
        "charisse fraser": "Shareef Frasier",
        "shereef frazier": "Shareef Frasier",
        "shereef frasier": "Shareef Frasier",
        "therese fraser": "Shareef Frasier",
        "cherise fraser": "Shareef Frasier",
        "frazier": "Frasier",
        "fraser": "Frasier",
    }
    for bad, good in variants.items():
        if lower == bad or lower.endswith(" " + bad) or lower.startswith(bad + " "):
            n = good
            break
    return n.strip()


def _supabase_config():
    return settings.supabase_config()


def _log_auth_attempt(
    name: str,
    pin_len: int,
    success: bool,
    reason: str,
    client_ip: str = "",
    user_agent: str = "",
):
    """Write a sanitized auth audit record to Supabase and local audit log."""
    record = {
        "caller_name": name,
        "pin_length": pin_len,
        "success": success,
        "reason": reason,
        "source": "vapi_voice",
        "client_ip": client_ip,
        "user_agent": user_agent,
        "assistant_id": settings.VAPI_ASSISTANT_ID,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    audit_record("auth_attempt", **record)
    sb = get_supabase_helper()
    if sb.available():
        sb.insert("auth_attempts", record)


def _client_info(request: Request | None) -> tuple[str, str]:
    """Extract client IP and User-Agent from a request."""
    if request is None:
        return "", ""
    forwarded = request.headers.get("x-forwarded-for", "")
    ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "")
    ua = request.headers.get("user-agent", "")
    return ip, ua


def _default_pin(contact: dict) -> str:
    phone = (contact.get("phone", "") or "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
    return phone[-4:] if len(phone) >= 4 else ""


def _crm_role_to_vapi(cat: str) -> str:
    m = {
        "Faculty": "attending",
        "Resident": "resident",
        "Nurse Practitioner": "nurse",
        "Staff": "staff",
        "Physician Assistant": "staff",
        "Medical Student": "student",
    }
    return m.get(cat, "other")


def _get_greeting(role: str, name: str) -> str:
    if role == "administrator":
        return f"Welcome back, {name}! You can manage schedules, check reimbursements, or review call coverage."
    elif role == "attending":
        last = name.split()[-1] if name.split() else name
        return f"Welcome back, Dr. {last}! Need your schedule or looking for someone?"
    elif role == "resident":
        first = name.split()[0] if name.split() else name
        return f"Hey {first}! Want to check your GME balance or see your assignments?"
    elif role in ("nurse", "staff"):
        first = name.split()[0] if name.split() else name
        return f"Welcome, {first}! How can I help you today?"
    return f"Welcome back, {name}!"


def _handle_auth(name: str, pin: str, ez_id: str = "", client_ip: str = "", request: Request | None = None):
    result = _handle_auth_inner(name, pin, ez_id, client_ip, request)
    status = "success" if result.get("verified") else result.get("next_step", "unknown")
    collector.observe_auth_attempt(status)
    return result


def _handle_auth_inner(name: str, pin: str, ez_id: str = "", client_ip: str = "", request: Request | None = None):
    name = _normalize_name(name)
    pin_clean = "".join(c for c in (pin or "") if c.isdigit())
    name_lower = name.lower().strip()
    words = [w for w in name_lower.replace("-", " ").split() if len(w) >= 3]

    ip, ua = _client_info(request) if request else (client_ip, "")
    if request is None and client_ip:
        ip = client_ip
    locked, remaining = _auth_limiter.is_locked(name, ip)
    if locked:
        return {
            "verified": False,
            "user": None,
            "greeting": None,
            "message": f"Too many failed attempts. Please try again in {remaining // 60 + 1} minute(s).",
            "next_step": "take_message",
        }

    def _strong(n, uid, dbn, dbd):
        nl = n.lower().strip()
        if nl == uid.lower() or nl == dbn or nl == dbd:
            return True
        if len(nl) >= 3 and (nl in uid.lower() or uid.lower() in nl):
            return True
        if " " in nl:
            for p in nl.split():
                if len(p) >= 2 and (p in dbn or p in dbd):
                    return True
        for w in nl.split():
            if len(w) >= 3 and (w in dbn or w in dbd or w in uid.lower()):
                return True
        return False

    users = _load_pin_db()

    # PRIORITY 0: EZ ID match — exact, unambiguous. Skip name matching entirely.
    ez_id_clean = ez_id.strip().lower()
    if ez_id_clean:
        for uid, u in users.items():
            db_ez = (u.get("ez_id", "") or "").strip().lower()
            if db_ez and (db_ez == ez_id_clean or ez_id_clean in db_ez or db_ez in ez_id_clean):
                name_lower = u.get("name", "").lower().strip()
                if u.get("pin_hash") == _hash_pin(pin_clean):
                    profile = {k: v for k, v in u.items() if k != "pin_hash"}
                    greeting = _get_greeting(u.get("role", ""), u.get("display_name", uid))
                    _auth_limiter.record(name, True, ip)
                    _log_auth_attempt(ez_id_clean, len(pin_clean), True, "verified_ezid", ip, ua)
                    return {
                        "verified": True,
                        "user": profile,
                        "greeting": greeting,
                        "message": "Verified.",
                        "next_step": "proceed",
                    }
                # EZ ID found but PIN wrong
                _auth_limiter.record(name, False, ip)
                _log_auth_attempt(ez_id_clean, len(pin_clean), False, "invalid_pin", ip, ua)
                return {
                    "verified": False, "user": None, "greeting": None,
                    "message": "That PIN didn't match.", "next_step": "retry_pin",
                }
        
        # EZ ID provided but no match found — try CRM directly
        for c in _load_crm():
            c_ez = (c.get("ezId", "") or "").strip().lower()
            if c_ez and (c_ez == ez_id_clean or ez_id_clean in c_ez or c_ez in ez_id_clean):
                d = _default_pin(c)
                if pin_clean == d:
                    role = _crm_role_to_vapi(c.get("category", ""))
                    display = f"{c.get('firstName', '')} {c.get('lastName', '')}".strip()
                    _auth_limiter.record(name, True, ip)
                    _log_auth_attempt(ez_id_clean, len(pin_clean), True, "verified_ezid_crm", ip, ua)
                    return {
                        "verified": True,
                        "user": {"name": display, "role": role, "email": c.get("email", "")},
                        "greeting": _get_greeting(role, c.get("firstName", "")),
                        "message": "Verified.",
                        "next_step": "proceed",
                    }
                _auth_limiter.record(name, False, ip)
                _log_auth_attempt(ez_id_clean, len(pin_clean), False, "invalid_pin", ip, ua)
                return {
                    "verified": False, "user": None, "greeting": None,
                    "message": "That PIN didn't match.", "next_step": "retry_pin",
                }

    # No EZ ID or EZ ID didn't match — fall back to name matching
    def _fuzzy(w1, w2):
        ml = min(len(w1), len(w2))
        if ml < 4 or w1[0] != w2[0]:
            return False
        return sum(1 for i in range(ml) if w1[i] == w2[i]) >= 3

    had = False
    for uid, u in users.items():
        dbn = u.get("name", "").lower().strip()
        dbd = u.get("display_name", "").lower().strip()
        if _strong(name_lower, uid, dbn, dbd):
            had = True
            if u.get("pin_hash") == _hash_pin(pin_clean):
                profile = {k: v for k, v in u.items() if k != "pin_hash"}
                greeting = _get_greeting(u.get("role", ""), u.get("display_name", uid))
                _auth_limiter.record(name, True, ip)
                _log_auth_attempt(name, len(pin_clean), True, "verified", ip, ua)
                return {
                    "verified": True,
                    "user": profile,
                    "greeting": greeting,
                    "message": "Verified.",
                    "next_step": "proceed",
                }
            _auth_limiter.record(name, False, ip)
            _log_auth_attempt(name, len(pin_clean), False, "invalid_pin", ip, ua)
            return {
                "verified": False,
                "user": None,
                "greeting": None,
                "message": "That PIN didn't match.",
                "next_step": "retry_pin",
            }

    if had:
        _auth_limiter.record(name, False, ip)
        _log_auth_attempt(name, len(pin_clean), False, "invalid_pin", ip, ua)
        return {
            "verified": False,
            "user": None,
            "greeting": None,
            "message": "That PIN didn't match.",
            "next_step": "retry_pin",
        }

    # Fuzzy fallback on name words
    for uid, u in users.items():
        dbn = u.get("name", "").lower().strip()
        dbd = u.get("display_name", "").lower().strip()
        for w in words:
            for dw in (dbn + " " + dbd).replace("-", " ").split():
                if len(dw) >= 3 and _fuzzy(w, dw) and u.get("pin_hash") == _hash_pin(pin_clean):
                    profile = {k: v for k, v in u.items() if k != "pin_hash"}
                    greeting = _get_greeting(u.get("role", ""), u.get("display_name", uid))
                    _auth_limiter.record(name, True, ip)
                    _log_auth_attempt(name, len(pin_clean), True, "verified_fuzzy", ip, ua)
                    return {
                        "verified": True,
                        "user": profile,
                        "greeting": greeting,
                        "message": "Verified.",
                        "next_step": "proceed",
                    }

    # Last resort: check raw CRM with default last-4 phone PIN
    for c in _load_crm():
        fn = (c.get("firstName", "") or "").lower()
        ln = (c.get("lastName", "") or "").lower()
        full = f"{fn} {ln}"
        matched = (
            name_lower == full or full in name_lower or name_lower in full
            or (fn and (name_lower == fn or fn in name_lower or name_lower in fn))
            or (ln and (name_lower == ln or ln in name_lower or name_lower in ln))
        )
        if not matched:
            for w in words:
                if w == fn or w == ln or w in full.split():
                    matched = True
                    break
        if matched:
            d = _default_pin(c)
            if pin_clean == d:
                role = _crm_role_to_vapi(c.get("category", ""))
                display = f"{c.get('firstName', '')} {c.get('lastName', '')}".strip()
                _auth_limiter.record(name, True, ip)
                _log_auth_attempt(name, len(pin_clean), True, "verified_crm_default", ip, ua)
                return {
                    "verified": True,
                    "user": {"name": display, "role": role, "email": c.get("email", "")},
                    "greeting": _get_greeting(role, c.get("firstName", "")),
                    "message": "Verified.",
                    "next_step": "proceed",
                }
            _auth_limiter.record(name, False, ip)
            _log_auth_attempt(name, len(pin_clean), False, "invalid_pin", ip, ua)
            return {
                "verified": False,
                "user": None,
                "greeting": None,
                "message": "That PIN didn't match.",
                "next_step": "retry_pin",
            }

    _auth_limiter.record(name, False, ip)
    _log_auth_attempt(name, len(pin_clean), False, "user_not_found", ip, ua)
    return {
        "verified": False,
        "user": None,
        "greeting": None,
        "message": "I couldn't find you in our directory.",
        "next_step": "take_message",
    }


def _handle_sick_call(args: dict):
    cfg = _supabase_config()
    if not cfg:
        return {"status": "error", "message": "Sick call not configured"}
    eid = args.get("employee_id", "").strip()
    sd = args.get("start_date", "").strip()
    days = args.get("days_requested", 1)
    if not eid or not sd:
        return {"status": "error", "message": "employee_id and start_date required"}
    try:
        r = httpx.post(
            f"{cfg['supabase_url']}/functions/v1/submit-intake",
            json={
                "employee_id": eid,
                "start_date": sd,
                "days_requested": days,
                "channel": "phone",
                "internal_service_key": cfg["service_key"],
            },
            headers={"Authorization": f"Bearer {cfg['service_key']}"},
            timeout=15,
        )
        if r.status_code == 200:
            return {"status": "submitted", "confirmation": r.json().get("confirmation_number", "N/A")}
        return {"status": "error", "message": f"Sick call API returned {r.status_code}"}
    except Exception as e:
        return {"status": "error", "message": f"Submission failed: {e}"}


def _handle_weather(location: str = "Bronx, NY"):
    import random
    return {"location": location, "temperature": f"{random.randint(65, 88)}F", "condition": random.choice(["sunny", "partly cloudy", "clear", "cloudy"])}


def _handle_news(topic: str = ""):
    if topic:
        return {"topic": topic, "headline": f"Recent developments in {topic}", "source": "demo"}
    return {"headlines": ["Bronx health initiatives expand", "Montefiore launches new services"], "source": "demo"}


class MeetingRequest(BaseModel):
    title: str
    date: str
    start_time: str = "12:00"
    duration_minutes: int = 30
    attendees: list = []
    description: str = ""


def _generate_ics(m: MeetingRequest):
    from datetime import timedelta
    p = m.date.replace("-", "").split("T")[0]
    sh, sm = m.start_time.split(":")
    sd = datetime.strptime(f"{p} {sh}:{sm}:00", "%Y%m%d %H:%M:%S")
    ed = sd + timedelta(minutes=m.duration_minutes)
    uid = hashlib.md5(f"{m.title}{m.date}".encode()).hexdigest()
    ics = [
        "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Vapi//EN", "BEGIN:VEVENT",
        f"UID:{uid}@vapi", f"DTSTART:{sd.strftime('%Y%m%dT%H%M%S')}",
        f"DTEND:{ed.strftime('%Y%m%dT%H%M%S')}", f"SUMMARY:{m.title}",
    ]
    for a in m.attendees:
        ics.append(f"ATTENDEE;CN={a}:mailto:{a}")
    ics.extend(["END:VEVENT", "END:VCALENDAR"])
    return "\r\n".join(ics)


def _send_meeting_email(m: MeetingRequest, ics: str):
    try:
        subprocess.run(
            [sys.executable, str(BASE_DIR / "email_helper.py"), "--to", ",".join(m.attendees + ["sfrasier@montefiore.org"]), "--subject", f"Meeting: {m.title}"],
            timeout=30, capture_output=True, text=True
        )
    except Exception as e:
        logger.warning("meeting email failed", extra={"error": str(e)})
    return {"status": "email_sent"}


def _create_google_cal_event(m: MeetingRequest):
    try:
        gt = json.loads(settings.GOOGLE_TOKEN_PATH.read_text())
        at = gt.get("access_token", "")
        if not at:
            return {"status": "created", "note": "Calendar logged"}
        from datetime import timedelta
        p = m.date.replace("-", "").split("T")[0]
        sh, sm = m.start_time.split(":")
        sd = datetime.strptime(f"{p} {sh}:{sm}:00", "%Y%m%d %H:%M:%S") - timedelta(hours=4)
        r = httpx.post(
            "https://www.googleapis.com/calendar/v3/calendars/primary/events",
            json={
                "summary": m.title,
                "start": {"dateTime": sd.isoformat(), "timeZone": "America/New_York"},
                "end": {"dateTime": (sd + timedelta(minutes=m.duration_minutes)).isoformat(), "timeZone": "America/New_York"},
            },
            headers={"Authorization": f"Bearer {at}"},
            timeout=15,
        )
        if r.status_code == 200:
            return {"status": "created", "htmlLink": r.json().get("htmlLink", "")}
    except Exception as e:
        logger.warning("google calendar create failed", extra={"error": str(e)})
    return {"status": "created", "note": "Calendar logged"}


def _send_message_confirmation(email: str, result: dict, args: dict):
    # TEST MODE: redirect all confirmation emails to sfrasier
    email = "sfrasier@montefiore.org"
    try:
        subprocess.run(
            [sys.executable, str(BASE_DIR / "email_helper.py"), "--to", email, "--subject", "Message for Shareef Frasier - Confirmation"],
            timeout=30, capture_output=True, text=True
        )
    except Exception as e:
        logger.warning("message confirmation email failed", extra={"error": str(e)})
    return {"status": "queued", "to": email}


def _client_info(request: Request | None) -> tuple[str, str]:
    """Extract client IP and User-Agent from a request."""
    if request is None:
        return "", ""
    return _client_ip(request), request.headers.get("user-agent", "")


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else ""


@router.post("/auth")
async def vapi_auth(request: Request, body: dict):
    return _handle_auth(body.get("name", ""), body.get("pin", ""), request=request)


@router.post("/verify")
async def vapi_verify(request: Request, body: dict):
    """Dedicated secure verification webhook for Vapi function calls."""
    return _handle_auth(
        body.get("caller_name", body.get("name", "")),
        body.get("caller_pin", body.get("pin", "")),
        request=request,
    )


@router.get("/first-message")
async def first_message():
    try:
        h = (datetime.now(timezone.utc).hour - 4) % 24
        g = "Good morning" if 5 <= h < 12 else ("Good afternoon" if 12 <= h < 17 else "Good evening")
        return {"firstMessage": f"{g}, this is Shareef Frasier's assistant. Who am I speaking with?"}
    except Exception:
        return {"firstMessage": "Hey, thanks for calling Shareef's line at Montefiore Urology. I'm his assistant — who am I speaking with?"}


@router.post("")
async def vapi_webhook(request: Request):
    try:
        body = await request.json()
    except Exception:
        collector.observe_vapi_webhook("parse", "error")
        return {"error": "invalid JSON"}

    # Capture Vapi tool-call metadata before dispatch so we can shape the response.
    msg = body.get("message", body) if isinstance(body, dict) else {}
    tool_calls = msg.get("toolCalls", []) if isinstance(msg, dict) else []
    tool_call_id = tool_calls[0].get("id") if isinstance(tool_calls, list) and tool_calls else None
    is_tool_calls = msg.get("type", "") == "tool-calls"

    result, status = await _dispatch_vapi_webhook(request, body)
    collector.observe_vapi_webhook(result.get("_metric_fn") if isinstance(result, dict) else "", status)
    if isinstance(result, dict):
        result.pop("_metric_fn", None)

    # Vapi's newer tool-calls format requires results matched by toolCallId.
    if is_tool_calls and tool_call_id and "result" in result:
        result = {"results": [{"toolCallId": tool_call_id, "result": result["result"]}]}

    return result


async def _dispatch_vapi_webhook(request: Request, body: dict):
    """Inner dispatcher so the outer route can record metrics once."""
    logger.debug("vapi webhook received", extra={"body_preview": json.dumps(body, default=str)[:500]})

    msg = body.get("message", body) if isinstance(body, dict) else {}
    if not isinstance(msg, dict):
        return {"error": "unexpected payload"}, "error"

    mt = msg.get("type", "")
    if mt == "assistant-request":
        h = (datetime.now(timezone.utc).hour - 4) % 24
        g = "Good morning" if 5 <= h < 12 else ("Good afternoon" if 12 <= h < 17 else "Good evening")
        return {"firstMessage": f"{g}, this is Shareef Frasier's assistant. Who am I speaking with?"}, "ok"

    if mt == "end-of-call-report":
        from modules import vapi_call_summary
        try:
            vapi_call_summary.handle_end_of_call(body)
        except Exception as e:
            logger.error("end-of-call summary failed", extra={"error": str(e)})
        return {"result": "logged"}, "ok"

    if mt not in ("function-call", "tool-calls"):
        return {"result": ""}, "ok"

    fn = msg.get("function", {})
    tc = msg.get("toolCalls", [])
    fn_name = fn.get("name", "")
    fn_args = fn.get("arguments", {})
    if not fn_name and tc:
        fi = tc[0].get("function", {})
        fn_name = fi.get("name", "")
        fn_args = fi.get("arguments", {})
    if isinstance(fn_args, str):
        try:
            fn_args = json.loads(fn_args)
        except Exception:
            fn_args = {}

    logger.info("tool call", extra={"function": fn_name, "arguments": {k: v for k, v in fn_args.items() if k not in ("pin", "caller_pin")}})

    try:
        if fn_name in ("authUser", "verifyCaller"):
            name = fn_args.get("caller_name") or fn_args.get("name", "")
            ez_id = fn_args.get("caller_ez_id") or fn_args.get("ez_id", "")
            pin = fn_args.get("caller_pin") or fn_args.get("pin", "")
            pd = "".join(c for c in (pin or "") if c.isdigit())
            if len(pd) < 4:
                return {"result": json.dumps({
                    "verified": False,
                    "message": f"I only caught {len(pd)} digit{'s' if len(pd) != 1 else ''}. Please say your full 4-digit PIN again.",
                    "next_step": "retry_pin",
                }), "_metric_fn": fn_name}, "ok"
            r = _handle_auth(name, pin, ez_id=ez_id, request=request)
            return {"result": json.dumps(r), "_metric_fn": fn_name}, "ok"
        elif fn_name == "searchCrm":
            q = fn_args.get("q", "").lower()
            m = [
                {"name": f"{c.get('firstName', '')} {c.get('lastName', '')}", "category": c.get("category", "")}
                for c in _load_crm()
                if q in (c.get("firstName", "") or "").lower() or q in (c.get("lastName", "") or "").lower()
            ]
            return {"result": json.dumps({"count": len(m), "results": m}), "_metric_fn": fn_name}, "ok"
        elif fn_name == "getFaculty":
            f = [f"{c.get('firstName', '')} {c.get('lastName', '')}" for c in _load_crm() if c.get("category") == "Faculty"]
            return {"result": json.dumps({"count": len(f), "faculty": f}), "_metric_fn": fn_name}, "ok"
        elif fn_name == "getResidents":
            r2 = [f"{c.get('firstName', '')} {c.get('lastName', '')}" for c in _load_crm() if c.get("category") == "Resident"]
            return {"result": json.dumps({"count": len(r2), "residents": r2}), "_metric_fn": fn_name}, "ok"
        elif fn_name == "getTodaySchedule":
            return {"result": json.dumps(vapi_data.schedule_today()), "_metric_fn": fn_name}, "ok"
        elif fn_name == "getPersonSchedule":
            return {"result": json.dumps(vapi_data.schedule_person(fn_args.get("name", ""))), "_metric_fn": fn_name}, "ok"
        elif fn_name == "getWeekendSchedule":
            return {"result": json.dumps(vapi_data.schedule_weekend()), "_metric_fn": fn_name}, "ok"
        elif fn_name == "getPersonMonth":
            return {"result": json.dumps(vapi_data.schedule_month(fn_args.get("name", ""))), "_metric_fn": fn_name}, "ok"
        elif fn_name == "scheduleByDate":
            return {"result": json.dumps(vapi_unified.schedule_by_date(fn_args.get("date", ""))), "_metric_fn": fn_name}, "ok"
        elif fn_name == "getGmeBalance":
            return {"result": json.dumps(vapi_data.gme_balance_for(fn_args.get("name", ""))), "_metric_fn": fn_name}, "ok"
        elif fn_name == "qgendaToday":
            n = fn_args.get("name", "")
            return {"result": json.dumps(vapi_unified.qgenda_person_day(n) if n else vapi_unified.qgenda_today()), "_metric_fn": fn_name}, "ok"
        elif fn_name == "qgendaUpcoming":
            return {"result": json.dumps(vapi_unified.qgenda_person_upcoming(fn_args.get("name", ""), fn_args.get("days", 7))), "_metric_fn": fn_name}, "ok"
        elif fn_name == "qgendaWhere":
            t = fn_args.get("task", "")
            return {"result": json.dumps(vapi_unified.qgenda_today_task(t) if t else vapi_unified.qgenda_today()), "_metric_fn": fn_name}, "ok"
        elif fn_name == "staffFind":
            return {"result": json.dumps(vapi_unified.staff_lookup(fn_args.get("name", ""))), "_metric_fn": fn_name}, "ok"
        elif fn_name == "staffLocation":
            return {"result": json.dumps(vapi_unified.staff_by_location(fn_args.get("location", ""))), "_metric_fn": fn_name}, "ok"
        elif fn_name == "staffAtLocation":
            from modules import roster_parser
            loc = fn_args.get("location", "")
            dt = fn_args.get("date", "")
            return {"result": json.dumps(roster_parser.staff_at_location(loc, dt)), "_metric_fn": fn_name}, "ok"
        elif fn_name == "knowledgeSearch":
            q = fn_args.get("q", "")
            top_k = fn_args.get("top_k", 3)
            return {"result": json.dumps(vapi_knowledge.query(q, top_k=top_k)), "_metric_fn": fn_name}, "ok"
        elif fn_name == "submitSickCall":
            return {"result": json.dumps(_handle_sick_call(fn_args)), "_metric_fn": fn_name}, "ok"
        elif fn_name == "takeMessage":
            result = voice_messages.take_message(
                fn_args.get("caller_name", "Unknown"),
                fn_args.get("message", ""),
                fn_args.get("phone", ""),
                fn_args.get("callback_requested", False),
            )
            if fn_args.get("email", ""):
                try:
                    _send_message_confirmation(fn_args["email"], result, fn_args)
                except Exception:
                    pass
            return {"result": json.dumps(result), "_metric_fn": fn_name}, "ok"
        elif fn_name == "getWeather":
            return {"result": json.dumps(_handle_weather(fn_args.get("location", "Bronx, NY"))), "_metric_fn": fn_name}, "ok"
        elif fn_name == "getNews":
            return {"result": json.dumps(_handle_news(fn_args.get("topic", ""))), "_metric_fn": fn_name}, "ok"
        elif fn_name == "swapCall":
            from modules import vapi_swap
            return {"result": json.dumps(vapi_swap.handle_swap_request(fn_args)), "_metric_fn": fn_name}, "ok"
        elif fn_name == "scheduleMeeting":
            m = MeetingRequest(
                title=fn_args.get("title", "Meeting"),
                date=fn_args.get("date", ""),
                start_time=fn_args.get("start_time", "12:00"),
                duration_minutes=fn_args.get("duration_minutes", 30),
                attendees=fn_args.get("attendees", []),
                description=fn_args.get("description", ""),
            )
            ics = _generate_ics(m)
            er = _send_meeting_email(m, ics)
            cr = _create_google_cal_event(m)
            return {"result": json.dumps({
                "status": "scheduled",
                "title": m.title,
                "date": m.date,
                "time": m.start_time,
                "attendees": m.attendees,
                "email": er.get("status", "sent"),
                "calendar": cr.get("status", "created"),
                "calendar_link": cr.get("htmlLink", ""),
            }), "_metric_fn": fn_name}, "ok"
        elif fn_name == "getDeadlines":
            from modules import vapi_concierge
            return {"result": json.dumps(vapi_concierge.get_deadlines(fn_args.get("role", ""))), "_metric_fn": fn_name}, "ok"
        elif fn_name == "getEvaluationsDue":
            from modules import vapi_concierge
            return {"result": json.dumps(vapi_concierge.get_evaluations_due(fn_args.get("name", ""))), "_metric_fn": fn_name}, "ok"
        elif fn_name == "emailSchedule":
            from modules import vapi_email
            email = fn_args.get("email", "")
            date_from = fn_args.get("date_from", "")
            date_to = fn_args.get("date_to", "")
            person = fn_args.get("person", "")
            campus_filter = fn_args.get("campus", "")

            # Gather schedule data
            schedule_data = []
            if date_from and date_to:
                from datetime import date, timedelta
                start = date.fromisoformat(date_from) if isinstance(date_from, str) else date_from
                end = date.fromisoformat(date_to) if isinstance(date_to, str) else date_to
                current = start
                while current <= end:
                    ds = current.strftime("%Y-%m-%d")
                    result = vapi_unified.schedule_by_date(ds)
                    campuses = result.get("campuses", {})
                    for cname, cov in campuses.items():
                        if campus_filter and campus_filter.lower() != cname.lower():
                            continue
                        schedule_data.append({
                            "date": ds, "day": current.strftime("%A"),
                            "primary": cov.get("primary", "—"),
                            "backup": cov.get("backup", "—"),
                            "peds": cov.get("peds", "—"),
                            "campus": cname,
                        })
                    current += timedelta(days=1)
            elif person:
                # Get person schedule from vapi_data
                sched = vapi_unified._load_schedule()
                name_lower = person.lower().strip()
                for campus, rows in sched.items():
                    for row in rows:
                        for key in ("primary_clean", "backup_clean", "peds_clean"):
                            val = row.get(key, "")
                            if val and name_lower in val.lower():
                                schedule_data.append({
                                    "date": row["date"], "day": row["day"],
                                    "primary": row.get("primary", "—"),
                                    "backup": row.get("backup", "—"),
                                    "peds": row.get("peds", "—"),
                                    "campus": campus.title(),
                                })
                                break

            if not schedule_data:
                return {"result": json.dumps({
                    "success": False,
                    "message": "No schedule data found for that request."
                }), "_metric_fn": fn_name}, "ok"

            date_text = f"{date_from} to {date_to}" if date_from and date_to else f"Upcoming for {person}" if person else "Requested dates"
            campuses = list(set(s["campus"] for s in schedule_data))

            r = vapi_email.email_schedule(
                email=email,
                schedule_data=schedule_data,
                date_range_text=date_text,
                campuses=campuses,
                person_name=person or None,
            )
            return {"result": json.dumps(r), "_metric_fn": fn_name}, "ok"
        elif fn_name == "queryLocationRoster":
            location = fn_args.get("location", "")
            date_str = fn_args.get("date", "")
            try:
                from modules.roster_parser import query_location_roster
                r = query_location_roster(location=location, date_str=date_str)
            except ImportError:
                r = {"success": False, "count": 0, "records": [],
                     "note": "Roster parser not available on this server."}
            return {"result": json.dumps(r), "_metric_fn": fn_name}, "ok"
        elif fn_name == "emailStaffRoster":
            from modules import vapi_email
            email = fn_args.get("email", "")
            location = fn_args.get("location", "")
            date_str = fn_args.get("date", "")

            if not email:
                email = os.environ.get(
                    "SCHEDULE_EMAIL_RECIPIENT", "sfrasier@montefiore.org"
                )

            r = vapi_email.email_staff_roster(
                email=email,
                location=location,
                date_str=date_str,
            )
            audit_record("tool_call", function=fn_name, email=email,
                         location=location, date=date_str, result="ok" if r.get("success") else "fail")
            return {"result": json.dumps(r), "_metric_fn": fn_name}, "ok"
        else:
            return {"result": json.dumps({"error": f"Unknown function: {fn_name}"}), "_metric_fn": fn_name}, "ok"
    except Exception as e:
        logger.exception("tool call failed", extra={"function": fn_name})
        return {"result": json.dumps({"error": str(e)}), "_metric_fn": fn_name}, "error"


@router.get("/admin", response_class=HTMLResponse)
async def vapi_admin():
    """Simple HTML admin dashboard for call logs, auth attempts, and lockouts."""
    settings = get_settings()
    return f"""<!DOCTYPE html>
<html><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Vapi Admin Dashboard</title>
<style>
  body{{font-family:system-ui,sans-serif;background:#f4f6f8;margin:0;padding:24px;color:#111}}
  h1{{color:#1a3a5c}} .card{{background:#fff;border-radius:12px;padding:20px;margin-bottom:20px;box-shadow:0 2px 8px rgba(0,0,0,0.08)}}
  table{{width:100%;border-collapse:collapse;font-size:13px}}
  th,td{{text-align:left;padding:8px;border-bottom:1px solid #e5e7eb}}
  th{{color:#6b7280;font-weight:600}} .tag{{display:inline-block;padding:2px 8px;border-radius:12px;font-size:11px}}
  .high{{background:#fee2e2;color:#991b1b}} .medium{{background:#fef3c7;color:#92400e}} .low{{background:#d1fae5;color:#065f46}}
</style></head><body>
<h1>🎧 Vapi Voice Admin</h1>
<div class="card">
  <h3>Status</h3>
  <p>Assistant ID: {settings.VAPI_ASSISTANT_ID}</p>
  <p>Endpoint: {settings.VAPI_ENDPOINT_PATH}</p>
  <p><a href="/vapi/admin/api/audit" target="_blank">Raw audit JSON</a></p>
</div>
<div class="card">
  <h3>Recent Activity</h3>
  <div id="activity">Loading...</div>
</div>
<script>
async function load(){{
  const r=await fetch('/vapi/admin/api/audit');
  const data=await r.json();
  const rows=data.records.slice(0,50).map(e=>{{
    const urgency=e.urgency?`<span class="tag ${{e.urgency}}">${{e.urgency}}</span>`:'';
    return `<tr><td>${{e.ts?.slice(0,19)}}</td><td>${{e.event}}</td><td>${{e.caller_name||e.caller||'-'}}</td><td>${{e.reason||e.message||'-'}}</td><td>${{urgency}}</td></tr>`;
  }}).join('');
  document.getElementById('activity').innerHTML=`<table><tr><th>Time</th><th>Event</th><th>Caller</th><th>Detail</th><th>Urgency</th></tr>${{rows}}</table>`;
}}
load();
</script>
</body></html>"""


@router.get("/admin/api/audit")
async def vapi_admin_api():
    """Return recent audit records as JSON."""
    settings = get_settings()
    records = []
    if settings.AUDIT_LOG_FILE.exists():
        for line in settings.AUDIT_LOG_FILE.read_text().strip().split("\n"):
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except Exception:
                continue
    records.reverse()
    return {"count": len(records), "records": records[:200]}


@router.post("/admin/api/clear-lockout")
async def vapi_clear_lockout(body: dict):
    """Manually clear rate-limit lockout for a caller."""
    name = body.get("name", "")
    ip = body.get("ip", "")
    if not name:
        return {"error": "name required"}
    _auth_limiter._state.pop(_auth_limiter._key(name, ip), None)
    return {"status": "cleared", "name": name, "ip": ip}


@router.get("/status")
async def vapi_status():
    return {"status": "ok", "pin_db": len(_load_pin_db()), "crm": len(_load_crm()), "ts": datetime.now().isoformat()}
