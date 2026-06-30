"""Identity module — wraps CRM contacts and auth credentials for session-based login.

Provides user lookup by email/id, credential management, and identity mapping.
"""
import json
import threading
import time
from pathlib import Path
from typing import Optional

from modules.config import get_settings

settings = get_settings()
DATA_DIR = settings.DATA_DIR
CRM_PATH = settings.CRM_PATH
AUTH_CREDENTIALS_PATH = DATA_DIR / "auth_credentials.json"
IDENTITY_MAP_PATH = DATA_DIR / "identity_map.json"

# Simple file cache (mirrors vapi_bridge.py pattern)
_cache: dict[Path, dict] = {}
_cache_lock = threading.Lock()


def _load_json_cached(path: Path):
    """Load a JSON file with caching."""
    if not path.exists():
        return None
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
            data = None
        _cache[path] = {"data": data, "mtime": path.stat().st_mtime if path.exists() else 0, "ts": now}
        return data


def _invalidate_cache(path: Path | None = None):
    with _cache_lock:
        if path is None:
            _cache.clear()
        elif path in _cache:
            del _cache[path]


def _load_crm() -> list:
    """Load CRM contacts list."""
    contacts = _load_json_cached(CRM_PATH)
    if contacts is None:
        return []
    return contacts if isinstance(contacts, list) else []


def _load_credentials() -> dict:
    """Load auth credentials dict keyed by crm_id."""
    creds = _load_json_cached(AUTH_CREDENTIALS_PATH)
    if creds is None:
        return {}
    return creds if isinstance(creds, dict) else {}


def _save_credentials(creds: dict):
    """Atomically save auth credentials to disk."""
    AUTH_CREDENTIALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUTH_CREDENTIALS_PATH.write_text(json.dumps(creds, indent=2))
    _invalidate_cache(AUTH_CREDENTIALS_PATH)


def _load_identity_map() -> dict:
    """Load identity map dict keyed by crm_id."""
    imap = _load_json_cached(IDENTITY_MAP_PATH)
    if imap is None:
        return {}
    return imap if isinstance(imap, dict) else {}


# ─── Public API ──────────────────────────────────────────────────────────────

def get_user_by_email(email: str) -> Optional[dict]:
    """Find a CRM contact by email address."""
    if not email:
        return None
    email_lower = email.lower().strip()
    contacts = _load_crm()
    for contact in contacts:
        if contact.get("email", "").lower().strip() == email_lower:
            return contact
    return None


def get_user_by_id(crm_id: str) -> Optional[dict]:
    """Find a CRM contact by id."""
    if not crm_id:
        return None
    contacts = _load_crm()
    for contact in contacts:
        if contact.get("id") == crm_id:
            return contact
    return None


def get_credential(crm_id: str) -> Optional[dict]:
    """Get auth credential for a user by crm_id."""
    if not crm_id:
        return None
    credentials = _load_credentials()
    return credentials.get(crm_id)


def save_credential(crm_id: str, data: dict):
    """Save or update an auth credential for a user."""
    credentials = _load_credentials()
    credentials[crm_id] = data
    _save_credentials(credentials)


def get_identity_map_entry(crm_id: str) -> Optional[dict]:
    """Get identity map entry (links CRM id to app-specific IDs)."""
    if not crm_id:
        return None
    imap = _load_identity_map()
    return imap.get(crm_id)


def save_identity_map_entry(crm_id: str, data: dict):
    """Save or update an identity map entry."""
    imap = _load_identity_map()
    imap[crm_id] = data
    IDENTITY_MAP_PATH.parent.mkdir(parents=True, exist_ok=True)
    IDENTITY_MAP_PATH.write_text(json.dumps(imap, indent=2))
    _invalidate_cache(IDENTITY_MAP_PATH)
