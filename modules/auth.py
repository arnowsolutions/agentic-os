"""Session-based web authentication for the Agentic OS dashboard.

Owns sessions, rate-limiting, and audit. Wired into server.py as both
middleware and an included router.
"""
import hashlib
import json
import logging
import secrets
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from modules import identity as identity_module
from modules.config import get_settings
from modules.logging_config import audit_record
from modules.supabase_client import get_supabase_helper

settings = get_settings()

router = APIRouter(prefix="/api/auth", tags=["auth"])

logger = logging.getLogger("agentic_os.auth")

# ─── Path constants ──────────────────────────────────────────────────────────
SESSIONS_PATH = settings.SESSIONS_PATH
WEB_LOCKOUTS_PATH = settings.WEB_AUTH_LOCKOUTS_PATH


# ─── Session store helpers ───────────────────────────────────────────────────

def _load_sessions() -> dict:
    """Load sessions dict from disk. Returns {} if file missing or corrupt."""
    if not SESSIONS_PATH.exists():
        return {}
    try:
        return json.loads(SESSIONS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_sessions(data: dict):
    """Atomically write sessions dict to disk."""
    SESSIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SESSIONS_PATH.write_text(json.dumps(data, indent=2))


def purge_expired():
    """Remove all expired sessions and save."""
    sessions = _load_sessions()
    now = datetime.now(timezone.utc)
    expired = [
        token
        for token, s in sessions.items()
        if datetime.fromisoformat(s.get("expires_at", "1970-01-01T00:00:00+00:00")) < now
    ]
    if expired:
        for token in expired:
            del sessions[token]
        _save_sessions(sessions)
        logger.debug("purged %d expired sessions", len(expired))


def create_session(crm_id: str, email: str, role: str) -> str:
    """Create a new session, return opaque token."""
    from datetime import timedelta

    token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=settings.SESSION_TTL_HOURS)

    # Purge expired first
    purge_expired()

    sessions = _load_sessions()
    sessions[token] = {
        "crm_id": crm_id,
        "email": email,
        "role": role,
        "created_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
        "last_seen": now.isoformat(),
    }
    _save_sessions(sessions)
    return token


def get_session(token: str) -> Optional[dict]:
    """Get session dict if valid. Returns None if expired or missing."""
    if not token:
        return None
    sessions = _load_sessions()
    s = sessions.get(token)
    if not s:
        return None
    try:
        expires_at = datetime.fromisoformat(s["expires_at"])
        if expires_at < datetime.now(timezone.utc):
            return None
    except (ValueError, KeyError):
        return None
    return s


def touch_session(token: str):
    """Update last_seen and slide expiry forward."""
    from datetime import timedelta

    if not token:
        return
    sessions = _load_sessions()
    s = sessions.get(token)
    if not s:
        return
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=settings.SESSION_TTL_HOURS)
    s["last_seen"] = now.isoformat()
    s["expires_at"] = expires_at.isoformat()
    _save_sessions(sessions)


def revoke_session(token: str):
    """Remove a session token."""
    if not token:
        return
    sessions = _load_sessions()
    if token in sessions:
        del sessions[token]
        _save_sessions(sessions)


# ─── Web Auth Rate Limiter ───────────────────────────────────────────────────

class _WebAuthLimiter:
    """Per-email+IP rate limiter with disk persistence.

    Mirrors _AuthLimiter in vapi_bridge.py but:
    - Keys on email:ip (not name:ip)
    - Persists state to WEB_LOCKOUTS_PATH
    """

    def __init__(self, max_attempts: int, lockout_seconds: int):
        self.max_attempts = max_attempts
        self.lockout_seconds = lockout_seconds
        self._state: dict[str, dict] = {}
        self._lock = threading.Lock()
        self._loaded = False

    def _load_disk(self):
        """Load persisted lockout state from disk on first access."""
        if self._loaded:
            return
        if WEB_LOCKOUTS_PATH.exists():
            try:
                disk = json.loads(WEB_LOCKOUTS_PATH.read_text(encoding="utf-8"))
                with self._lock:
                    self._state.update(disk)
            except Exception:
                pass
        self._loaded = True

    def _persist(self):
        """Write current state to disk."""
        WEB_LOCKOUTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            WEB_LOCKOUTS_PATH.write_text(json.dumps(self._state, indent=2))

    def _key(self, email: str, ip: str = "") -> str:
        return f"{email.lower().strip()}:{ip}"

    def is_locked(self, email: str, ip: str = "") -> tuple[bool, int]:
        self._load_disk()
        now = time.time()
        with self._lock:
            s = self._state.get(self._key(email, ip))
            if not s:
                return False, 0
            if s.get("failures", 0) >= self.max_attempts:
                remaining = int(s.get("locked_until", 0) - now)
                if remaining > 0:
                    return True, remaining
                # Lock expired, reset
                s["failures"] = 0
                s["locked_until"] = 0
        return False, 0

    def record(self, email: str, success: bool, ip: str = ""):
        self._load_disk()
        key = self._key(email, ip)
        with self._lock:
            s = self._state.setdefault(key, {"failures": 0, "locked_until": 0})
            if success:
                s["failures"] = 0
                s["locked_until"] = 0
            else:
                s["failures"] += 1
                if s["failures"] >= self.max_attempts:
                    s["locked_until"] = time.time() + self.lockout_seconds
        self._persist()


_web_limiter = _WebAuthLimiter(settings.AUTH_MAX_ATTEMPTS, settings.AUTH_LOCKOUT_SECONDS)


# ─── Audit helper ────────────────────────────────────────────────────────────

def _log_web_auth(email: str, success: bool, reason: str, ip: str, ua: str):
    """Write a web login audit record."""
    record = {
        "caller_name": email,
        "pin_length": 0,  # not applicable for web login
        "success": success,
        "reason": reason,
        "source": "web_login",
        "client_ip": ip,
        "user_agent": ua,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    audit_record("auth_attempt", **record)
    sb = get_supabase_helper()
    if sb.available():
        sb.insert("auth_attempts", record)


# ─── Client info helper ──────────────────────────────────────────────────────

def _client_info(request: Request) -> tuple[str, str]:
    """Extract client IP and User-Agent from a request."""
    forwarded = request.headers.get("x-forwarded-for", "")
    ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "")
    ua = request.headers.get("user-agent", "")
    return ip, ua


# ─── Password helpers ────────────────────────────────────────────────────────

def _parse_pbkdf2_hash(hash_str: str) -> tuple[str, str, int, str, str] | None:
    """Parse pbkdf2:algorithm:iterations:salt:hash into components."""
    try:
        parts = hash_str.split(":")
        if len(parts) != 5 or parts[0] != "pbkdf2":
            return None
        algorithm, iterations, salt, h = parts[1], int(parts[2]), parts[3], parts[4]
        return algorithm, salt, iterations, h, None
    except (ValueError, IndexError):
        return None


def _verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against a stored PBKDF2 hash."""
    parsed = _parse_pbkdf2_hash(stored_hash)
    if not parsed:
        return False
    algorithm, salt, iterations, expected_hash, _ = parsed
    computed = hashlib.pbkdf2_hmac(algorithm, password.encode(), salt.encode(), iterations)
    return secrets.compare_digest(computed.hex(), expected_hash)


def _hash_password(password: str) -> str:
    """Generate a PBKDF2 hash for a password."""
    algorithm = "sha256"
    iterations = 600_000
    salt = secrets.token_hex(16)
    hash_bytes = hashlib.pbkdf2_hmac(algorithm, password.encode(), salt.encode(), iterations)
    return f"pbkdf2:{algorithm}:{iterations}:{salt}:{hash_bytes.hex()}"


# ─── Pydantic Models ─────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


# ─── Routes ──────────────────────────────────────────────────────────────────

@router.post("/login")
async def login(request: Request, body: LoginRequest):
    """Authenticate a user and create a session.

    Returns a session cookie on success.
    """
    email = body.email.strip().lower()
    ip, ua = _client_info(request)

    # 1. Rate limit check
    locked, remaining = _web_limiter.is_locked(email, ip)
    if locked:
        _log_web_auth(email, False, "rate_limited", ip, ua)
        return JSONResponse(
            {"detail": f"Account locked. Try again in {remaining}s."},
            status_code=429,
        )

    # 2. Find user by email
    user = identity_module.get_user_by_email(email)
    if not user:
        _web_limiter.record(email, False, ip)
        _log_web_auth(email, False, "user_not_found", ip, ua)
        return JSONResponse({"detail": "Invalid email or password."}, status_code=401)

    crm_id = user.get("id", "")

    # 3. Load credential and verify password
    credential = identity_module.get_credential(crm_id)
    if not credential:
        _web_limiter.record(email, False, ip)
        _log_web_auth(email, False, "no_credential", ip, ua)
        return JSONResponse({"detail": "Invalid email or password."}, status_code=401)

    stored_hash = credential.get("password_hash", "")
    if not _verify_password(body.password, stored_hash):
        _web_limiter.record(email, False, ip)
        _log_web_auth(email, False, "wrong_password", ip, ua)
        return JSONResponse({"detail": "Invalid email or password."}, status_code=401)

    # 4. Check credential status
    if credential.get("status") != "active":
        _log_web_auth(email, False, "inactive_credential", ip, ua)
        return JSONResponse(
            {"detail": "Account is not active. Contact an administrator."},
            status_code=403,
        )

    # 5. Record successful auth
    _web_limiter.record(email, True, ip)
    role = user.get("category", "user").lower()
    _log_web_auth(email, True, "success", ip, ua)

    # 6. Create session
    token = create_session(crm_id, email, role)

    # 7. Set cookie and return
    response = JSONResponse({
        "ok": True,
        "role": role,
        "must_reset": credential.get("must_reset", False),
    })
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=settings.SESSION_TTL_HOURS * 3600,
    )
    return response


@router.post("/logout")
async def logout(request: Request):
    """Revoke the session and clear the cookie."""
    token = request.cookies.get(settings.SESSION_COOKIE_NAME, "")
    revoke_session(token)
    response = JSONResponse({"ok": True})
    response.delete_cookie(settings.SESSION_COOKIE_NAME)
    return response


@router.get("/me")
async def me(request: Request):
    """Return the current authenticated user's profile."""
    token = request.cookies.get(settings.SESSION_COOKIE_NAME, "")
    session = get_session(token)
    if not session:
        return JSONResponse({"detail": "Unauthenticated"}, status_code=401)

    touch_session(token)
    crm_id = session["crm_id"]

    # Load CRM contact
    user = identity_module.get_user_by_id(crm_id)
    if not user:
        return JSONResponse({"detail": "User not found"}, status_code=400)

    # Load identity map entry
    imap = identity_module.get_identity_map_entry(crm_id) or {}

    # Return merged profile
    return {
        "crm_id": crm_id,
        "email": session["email"],
        "role": session["role"],
        "firstName": user.get("firstName", ""),
        "lastName": user.get("lastName", ""),
        "category": user.get("category", ""),
        "pgy": user.get("pgy", ""),
        "qgenda_user_id": imap.get("qgenda_user_id", ""),
        "reimbursement_user_id": imap.get("reimbursement_user_id", ""),
        "supabase_user_id": imap.get("supabase_user_id", ""),
    }


@router.post("/change-password")
async def change_password(request: Request, body: ChangePasswordRequest):
    """Change the authenticated user's password."""
    token = request.cookies.get(settings.SESSION_COOKIE_NAME, "")
    session = get_session(token)
    if not session:
        return JSONResponse({"detail": "Unauthenticated"}, status_code=401)

    crm_id = session["crm_id"]
    credential = identity_module.get_credential(crm_id)
    if not credential:
        return JSONResponse({"detail": "No credential found"}, status_code=400)

    # Verify current password
    stored_hash = credential.get("password_hash", "")
    if not _verify_password(body.current_password, stored_hash):
        return JSONResponse({"detail": "Current password is incorrect."}, status_code=400)

    # Validate new password strength
    new_pw = body.new_password
    if len(new_pw) < 8:
        return JSONResponse(
            {"detail": "Password must be at least 8 characters."},
            status_code=400,
        )

    # Hash and save new password
    new_hash = _hash_password(new_pw)
    updated = {**credential, "password_hash": new_hash, "must_reset": False}
    identity_module.save_credential(crm_id, updated)

    return JSONResponse({"ok": True})
