#!/usr/bin/env python3
"""Point send_chief_meeting_email.py at the canonical chief-meeting store.

Run as root (the file is root-owned 600) inside the AOS container:
  docker exec hermes-webui-gsga-agentic-os-1 python3 /workspace/agentic-os/scripts/aos-audit/patch_chief_script.py
"""
import re
import shutil
import sys
from pathlib import Path

TARGET = Path("/workspace/agentic-os/send_chief_meeting_email.py")
src = TARGET.read_text()
orig = src

OLD = '''PROD_RECIPIENTS = [
    "sfrasier@montefiore.org",   # Admin
    "asankin@montefiore.org",    # Dr. Sankin
    "alesmall@montefiore.org",   # Dr. Small
    "mschoenb@montefiore.org",   # Dr. Schoenberg
    # Chief Residents:
    "johill@montefiore.org",     # John Hill
    "johordines@montefiore.org", # John Hordines
    "sopak@montefiore.org",      # So Yeon (Jen) Pak
]

# ── Meeting Dates ─────────────────────────────────────────
CHIEF_MEETINGS = [
    {"date": "2026-09-04", "label": "Kick Off"},
    {"date": "2026-10-16", "label": ""},
    {"date": "2026-12-04", "label": ""},
    {"date": "2027-01-14", "label": ""},
    {"date": "2027-02-26", "label": ""},
    {"date": "2027-04-09", "label": ""},
    {"date": "2027-06-04", "label": ""},
]'''

NEW = '''# ── Canonical store (single source of truth) ──────────────
# The schedule + attendee list used to be hardcoded here AND in two dashboard
# pages. They now live in unified.chief_meetings / unified.chief_meeting_attendees
# on the postgres DB, and everything reads from there (2026-09-13).
ADMIN_EMAIL = "sfrasier@montefiore.org"


def _db_conn():
    """psycopg2 connection to the canonical postgres DB (unified schema)."""
    import psycopg2
    pw = os.environ.get("POSTGRES_PASSWORD", "")
    if not pw:
        for env_path in ("/workspace/agentic-os/.env",
                         "/workspace/projects/unified/app/.env"):
            try:
                if os.path.exists(env_path):
                    with open(env_path) as ef:
                        for line in ef:
                            if line.strip().startswith("POSTGRES_PASSWORD="):
                                pw = line.strip().split("=", 1)[1].strip()
                                break
            except Exception:
                continue
            if pw:
                break
    for host in ("172.16.3.1", "127.0.0.1"):
        try:
            kwargs = dict(host=host, port=5432, dbname="postgres", user="postgres", connect_timeout=3)
            if pw:
                kwargs["password"] = pw
            return psycopg2.connect(**kwargs)
        except Exception:
            continue
    return None


def load_chief_meetings():
    """Meeting schedule from unified.chief_meetings."""
    conn = _db_conn()
    if not conn:
        print("WARNING: no DB connection — cannot read unified.chief_meetings", file=sys.stderr)
        return []
    try:
        cur = conn.cursor()
        cur.execute("SELECT meeting_date::text, label FROM unified.chief_meetings ORDER BY meeting_date")
        rows = [{"date": r[0], "label": r[1] or ""} for r in cur.fetchall()]
        cur.close()
        conn.close()
        return rows
    except Exception as e:
        print(f"WARNING: chief meetings read failed: {e}", file=sys.stderr)
        return []


def load_attendees():
    """Active attendees from unified.chief_meeting_attendees."""
    conn = _db_conn()
    if not conn:
        print("WARNING: no DB connection — cannot read chief_meeting_attendees", file=sys.stderr)
        return []
    try:
        cur = conn.cursor()
        cur.execute("""SELECT name, email, role FROM unified.chief_meeting_attendees
                       WHERE is_active ORDER BY sort_order, name""")
        rows = [{"name": r[0], "email": r[1], "role": r[2] or "attending"} for r in cur.fetchall()]
        cur.close()
        conn.close()
        return rows
    except Exception as e:
        print(f"WARNING: chief attendees read failed: {e}", file=sys.stderr)
        return []


ATTENDEES = load_attendees()
PROD_RECIPIENTS = [ADMIN_EMAIL] + [a["email"] for a in ATTENDEES]
CHIEF_MEETINGS = load_chief_meetings()
ATTENDEE_LINE = ", ".join([a["name"] for a in ATTENDEES if a["role"] == "attending"] +
                          [a["name"] for a in ATTENDEES if a["role"] == "chief"]) or "Attendees"'''

assert OLD in src, "recipient/meeting block not found — aborting"
src = src.replace(OLD, NEW)

# The email body names the attendees; derive it so a change in the DB flows through.
line_old = "Dr. Schoenberg, Dr. Sankin, Dr. Small, Chief Residents"
if line_old in src:
    fstr_ok = bool(re.search(r'f"""[\s\S]{0,4000}?' + re.escape(line_old), src))
    if fstr_ok:
        src = src.replace(line_old, "{ATTENDEE_LINE}")
        print("body attendee line -> {ATTENDEE_LINE} (inside an f-string)")
    else:
        print("WARN: attendee prose line is NOT inside an f-string — left unchanged")
else:
    print("note: attendee prose line not present")

desc_old = '"Chief Residents\' Meeting with Dr. Schoenberg, Dr. Sankin, Dr. Small"'
if desc_old in src:
    src = src.replace(desc_old, 'f"Chief Residents\' Meeting with {ATTENDEE_LINE}"')
    print("3 description strings -> f-string with ATTENDEE_LINE")

if src != orig:
    shutil.copy2(TARGET, str(TARGET) + ".bak-chiefdb")
    TARGET.write_text(src)
    print(f"written: {TARGET} (backup .bak-chiefdb)")
else:
    print("nothing changed")
