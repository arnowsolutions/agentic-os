"""Centralized configuration for the Agentic OS voice/backend stack.

Values are loaded from environment variables and/or a `.env` file in the
project root. Secrets are never hard-coded here.
"""
import json
import os
from functools import lru_cache
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.resolve()
ENV_FILE = BASE_DIR / ".env"
DATA_DIR = BASE_DIR / "data"


def _load_env_file(path: Path):
    """Load KEY=VALUE pairs from a .env file into os.environ."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k:
            os.environ.setdefault(k, v)


# Load root .env once at import time
_load_env_file(ENV_FILE)


class Settings:
    """Runtime configuration. Access via `get_settings()`."""

    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent.resolve()
    DATA_DIR: Path = BASE_DIR / "data"

    # Server
    HOST: str = os.environ.get("HOST", "0.0.0.0")
    PORT: int = int(os.environ.get("PORT", "8090"))
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")

    # Vapi
    VAPI_API_KEY: str = os.environ.get("VAPI_API_KEY", "")
    VAPI_ASSISTANT_ID: str = os.environ.get(
        "VAPI_ASSISTANT_ID", "9b00342e-1951-4bd0-b4a5-5ca4c9827bd0"
    )
    VAPI_ENDPOINT_PATH: str = os.environ.get("VAPI_ENDPOINT_PATH", "/vapi")

    # Supabase (prefer env; fall back to legacy JSON for migration period)
    SUPABASE_URL: str = os.environ.get("SUPABASE_URL", "")
    SUPABASE_SERVICE_KEY: str = os.environ.get("SUPABASE_SERVICE_KEY", "")
    SUPABASE_PROJECT_ID: str = os.environ.get("SUPABASE_PROJECT_ID", "")

    # Google OAuth token path
    GOOGLE_TOKEN_PATH: Path = Path(
        os.environ.get("GOOGLE_TOKEN_PATH", DATA_DIR / "google_token.json")
    )

    # Security
    WEBHOOK_IP_ALLOWLIST: list[str] = [
        s.strip()
        for s in os.environ.get("WEBHOOK_IP_ALLOWLIST", "").split(",")
        if s.strip()
    ]
    WEBHOOK_SECRET: str = os.environ.get("WEBHOOK_SECRET", "")
    AUTH_MAX_ATTEMPTS: int = int(os.environ.get("AUTH_MAX_ATTEMPTS", "5"))
    AUTH_LOCKOUT_SECONDS: int = int(os.environ.get("AUTH_LOCKOUT_SECONDS", "300"))

    # Central Auth (SSO IdP) — web session management
    SESSION_COOKIE_NAME: str = "aos_session"
    SESSION_SECRET: str = os.environ.get("SESSION_SECRET", "")
    SESSION_TTL_HOURS: int = int(os.environ.get("SESSION_TTL_HOURS", "8"))
    SESSIONS_PATH: Path = Path(
        os.environ.get("SESSIONS_PATH", DATA_DIR / "sessions.json")
    )
    WEB_AUTH_LOCKOUTS_PATH: Path = Path(
        os.environ.get("WEB_AUTH_LOCKOUTS_PATH", DATA_DIR / "auth_lockouts_web.json")
    )

    # Cache
    CACHE_TTL_SECONDS: int = int(os.environ.get("CACHE_TTL_SECONDS", "60"))

    # Logging
    LOG_DIR: Path = Path(os.environ.get("LOG_DIR", BASE_DIR / "logs"))
    AUDIT_LOG_FILE: Path = Path(
        os.environ.get("AUDIT_LOG_FILE", LOG_DIR / "vapi_audit.log")
    )
    APP_LOG_FILE: Path = Path(
        os.environ.get("APP_LOG_FILE", LOG_DIR / "vapi_app.log")
    )

    # Data
    CRM_PATH: Path = Path(os.environ.get(
        "CRM_PATH", str(DATA_DIR / "crm_contacts.fallback.json")
    ))  # CRM JSON file path
    PIN_DB_PATH: Path = Path(os.environ.get("PIN_DB_PATH", DATA_DIR / "user_pins.json"))
    KNOWLEDGE_DIR: Path = Path(
        os.environ.get("KNOWLEDGE_DIR", BASE_DIR / "knowledge-base")
    )

    # LLM
    OPENROUTER_API_KEY: str = os.environ.get("OPENROUTER_API_KEY", "")
    OPENROUTER_MODEL: str = os.environ.get(
        "OPENROUTER_MODEL", "openai/gpt-4o-mini"
    )

    # Notifications
    ADMIN_EMAIL: str = os.environ.get("ADMIN_EMAIL", "")
    SCHEDULE_EMAIL_RECIPIENT: str = os.environ.get("SCHEDULE_EMAIL_RECIPIENT", "")

    @classmethod
    def load_legacy_supabase_key(cls):
        """Backwards-compatible loader for data/supabase_key.json."""
        legacy = DATA_DIR / "supabase_key.json"
        if not legacy.exists():
            return None
        try:
            data = json.loads(legacy.read_text())
            return {
                "supabase_url": data.get("supabase_url", ""),
                "service_key": data.get("service_key", ""),
                "project_id": data.get("project_id", ""),
            }
        except Exception:
            return None

    def supabase_config(self):
        """Return Supabase URL + service key, falling back to legacy JSON."""
        url = self.SUPABASE_URL
        key = self.SUPABASE_SERVICE_KEY
        if url and key:
            return {"supabase_url": url, "service_key": key}
        legacy = self.load_legacy_supabase_key()
        return legacy


@lru_cache()
def get_settings() -> Settings:
    return Settings()
