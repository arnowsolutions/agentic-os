"""
CRM Database Module — reads contacts from Supabase Postgres.
Falls back to legacy JSON file if the direct PG connection isn't available.

Usage:
    from modules.crm_db import get_contacts
    contacts = get_contacts()  # Returns list of dicts (same format as JSON)
"""
import json, os, logging
from functools import lru_cache
from pathlib import Path
from typing import Any

logger = logging.getLogger("agentic_os.crm_db")

# Legacy fallback path
FALLBACK_PATH = Path(__file__).resolve().parent.parent / "data" / "crm_contacts.fallback.json"

# PG connection — lazy-loaded
_PG_CONN = None


def _get_pg_connection():
    """Get or create Postgres connection to Supabase on VPS."""
    global _PG_CONN
    if _PG_CONN is not None:
        try:
            # Quick health check
            _PG_CONN.cursor().execute("SELECT 1")
            return _PG_CONN
        except Exception:
            _PG_CONN = None

    try:
        import psycopg2
        pw = os.environ.get("POSTGRES_PASSWORD", "")
        if not pw:
            # Try to read from unified env file
            env_path = Path("/workspace/projects/unified/app/.env")
            if env_path.exists():
                for line in env_path.read_text().splitlines():
                    if line.startswith("POSTGRES_PASSWORD="):
                        pw = line.split("=", 1)[1].strip()
                        break

        if not pw:
            logger.warning("No POSTGRES_PASSWORD available for direct PG connection")
            return None

        _PG_CONN = psycopg2.connect(
            host="127.0.0.1", port=5432,
            dbname="postgres", user="postgres", password=pw,
            connect_timeout=3,
        )
        logger.info("Connected to Supabase Postgres")
        return _PG_CONN
    except Exception as e:
        logger.warning(f"Cannot connect to Supabase PG: {e}")
        return None


def get_contacts() -> list[dict[str, Any]]:
    """Return contacts list. Reads from Supabase PG, falls back to JSON."""
    conn = _get_pg_connection()
    if conn is not None:
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, ez_id, first_name, last_name, email, category,
                       mobile, title, role, location, primary_location,
                       pgy, block, shift, hours_per_shift, work_days_per_week,
                       rotation_start, rotation_end, banner_id, course,
                       notes, gme_visible, data_gaps
                FROM public.contacts
                ORDER BY category, last_name, first_name
            """)
            cols = [desc[0] for desc in cur.description]
            contacts = []
            for row in cur.fetchall():
                c = dict(zip(cols, row))
                # Convert to the format expected by downstream code
                contact = {
                    "id": c.get("id", ""),
                    "ezId": c.get("ez_id", "") or "",
                    "firstName": c.get("first_name", "") or "",
                    "lastName": c.get("last_name", "") or "",
                    "email": c.get("email", "") or "",
                    "category": c.get("category", "") or "",
                    "mobile": c.get("mobile", "") or "",
                    "title": c.get("title", "") or "",
                    "role": c.get("role", "") or "",
                    "location": c.get("location", "") or "",
                    "pgy": c.get("pgy", "") or "",
                    "block": c.get("block", "") or "",
                    "shift": c.get("shift", "") or "",
                    "notes": c.get("notes", "") or "",
                    # These fields may not exist in all downstream consumers
                    "bannerId": c.get("banner_id", "") or "",
                    "primaryLocation": c.get("primary_location", "") or "",
                }
                contacts.append(contact)
            cur.close()
            logger.info(f"Loaded {len(contacts)} contacts from Supabase PG")
            return contacts
        except Exception as e:
            logger.warning(f"Supabase PG read failed, falling back: {e}")

    # Fallback to JSON
    if FALLBACK_PATH.exists():
        try:
            contacts = json.loads(FALLBACK_PATH.read_text())
            logger.info(f"Loaded {len(contacts)} contacts from JSON fallback")
            return contacts
        except Exception as e:
            logger.error(f"Failed to read fallback JSON: {e}")
            return []

    logger.warning("No contacts source available")
    return []


def get_contact_by_ezid(ez_id: str) -> dict[str, Any] | None:
    """Look up a single contact by EZ ID."""
    for c in get_contacts():
        if c.get("ezId", "").lower() == ez_id.lower():
            return c
    return None


def get_contact_by_email(email: str) -> dict[str, Any] | None:
    """Look up a single contact by email."""
    for c in get_contacts():
        if c.get("email", "").lower() == email.lower():
            return c
    return None
