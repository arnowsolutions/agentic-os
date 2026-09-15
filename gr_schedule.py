#!/usr/bin/env python3
"""
gr_schedule.py — SINGLE SOURCE OF TRUTH reader/writer for the Grand Rounds &
Monday conference schedule used by the Agentic OS invite stack.

CANONICAL STORE (the ONLY place the schedule lives):
    database: postgres (Supabase), schema: unified, table: unified.grand_rounds
    - 2026-09-09 consolidation: urology_qgenda.grand_rounds_schedule + embedded
      GR_DATA arrays in dashboard JS were retired. Everything reads THIS table.

Rows: one per academic week (Monday conference + Friday Grand Rounds) plus
optional Friday-only events (mon_date NULL, e.g. Residency Interview Days).

Consumers:
    outlook_deeplink_generator.py, send_grand_rounds_email.py,
    send_monday_sasp_email.py, server.py (conference endpoints), dashboard pages.

Send-tracking lives HERE TOO (per-event columns, added migration 027):
    mon_invite_sent_at / mon_reminder_sent_at / fri_invite_sent_at / fri_reminder_sent_at
"""
from __future__ import annotations

import os
from datetime import datetime

try:
    import psycopg2
    _HAS_PSYCOPG2 = True
except Exception:  # pragma: no cover
    _HAS_PSYCOPG2 = False

_Hosts = ("172.16.3.1", "127.0.0.1")   # docker bridge gateway first, then localhost
# NOTE: container-localhost 5432 has no listener; only the docker bridge gateway
# (172.16.3.1) answers. Keep the gateway FIRST so the 2x3s connect_timeout on the
# dead fallbacks is never paid (cron jobs inherit a short effective window).

_last_error: str | None = None


def get_pw() -> str:
    """POSTGRES_PASSWORD from env or the app .env (never logs the value)."""
    pw = os.environ.get("POSTGRES_PASSWORD", "")
    if pw:
        return pw
    for env_path in ("/workspace/agentic-os/.env",
                     "/workspace/projects/unified/app/.env"):
        if os.path.exists(env_path):
            try:
                with open(env_path) as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("POSTGRES_PASSWORD") and "=" in line:
                            return line.split("=", 1)[1].strip().strip('"').strip("'")
            except Exception:
                continue
    return ""


def _connect():
    """psycopg2 connection to the canonical postgres DB (unified schema)."""
    global _last_error
    if not _HAS_PSYCOPG2:
        _last_error = "psycopg2 not installed"
        return None
    pw = get_pw()
    last_exc = None
    for host in _Hosts:
        try:
            kwargs = dict(host=host, port=5432, dbname="postgres",
                          user="postgres", connect_timeout=3)
            if pw:
                kwargs["password"] = pw
            return psycopg2.connect(**kwargs)
        except Exception as e:
            last_exc = e
            continue
    _last_error = f"cannot reach canonical DB: {last_exc}"
    return None


# Legacy 11-column row layout (kept for the old JS GR_DATA parsers):
# 0=month 1=mon_date 2=mon_topic 3=mon_resident 4=mon_attending 5=cme7 6=cme8
# 7=fri_date 8=fri_gr7 9=fri_gr8 10=notes   (+11=tb, informational)
_LEGACY_COLS = ("month", "mon_date", "mon_topic", "mon_resident", "mon_attending",
                "mon_cme7", "mon_cme8", "fri_date", "fri_gr7", "fri_gr8", "notes")

_SELECT = """
    SELECT month, to_char(mon_date, 'YYYY-MM-DD') mon_date, mon_topic,
           mon_resident, mon_attending, mon_cme7, mon_cme8,
           to_char(fri_date, 'YYYY-MM-DD') fri_date, fri_gr7, fri_gr8, notes, tb
    FROM unified.grand_rounds
    ORDER BY COALESCE(mon_date, fri_date) ASC, id ASC
"""


def fetch_rows(include_tb: bool = True) -> list[list[str]]:
    """Return schedule rows in the legacy 11-col layout (+ optional tb col 11).

    RAISES RuntimeError when the canonical DB is unreachable — callers must
    fail loudly rather than silently fall back to any stale copy.
    """
    global _last_error
    conn = _connect()
    if not conn:
        raise RuntimeError(_last_error or "no DB connection")
    try:
        cur = conn.cursor()
        cur.execute(_SELECT)
        rows = []
        for r in cur.fetchall():
            row = [(x or "") for x in r[:11]]
            if include_tb:
                row.append(r[11] or "")
            rows.append(row)
        cur.close()
        conn.close()
        _last_error = None
        return rows
    except Exception as e:
        _last_error = f"canonical DB query failed: {e}"
        try:
            conn.close()
        except Exception:
            pass
        raise RuntimeError(_last_error) from e


def fetch_dicts() -> list[dict]:
    """Schedule rows as dicts incl. send-tracking timestamps."""
    conn = _connect()
    if not conn:
        raise RuntimeError(_last_error or "no DB connection")
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, month, to_char(mon_date,'YYYY-MM-DD') mon_date, mon_topic,
                   mon_resident, mon_attending, tb,
                   to_char(fri_date,'YYYY-MM-DD') fri_date, fri_gr7, fri_gr8, notes,
                   mon_invite_sent_at, mon_reminder_sent_at,
                   fri_invite_sent_at, fri_reminder_sent_at
            FROM unified.grand_rounds
            ORDER BY COALESCE(mon_date, fri_date) ASC, id ASC
        """)
        cols = [d[0] for d in cur.description]
        out = [dict(zip(cols, r)) for r in cur.fetchall()]
        cur.close()
        conn.close()
        return out
    except Exception as e:
        try:
            conn.close()
        except Exception:
            pass
        raise RuntimeError(f"canonical DB query failed: {e}") from e


# ── Send tracker (Phase E) ────────────────────────────────────────────────
# kind -> (date column to match, timestamp column to set)
_KIND_MAP = {
    "mon_invite":    ("mon_date",  "mon_invite_sent_at"),
    "mon_reminder":  ("mon_date",  "mon_reminder_sent_at"),
    "fri_invite":    ("fri_date",  "fri_invite_sent_at"),
    "fri_reminder":  ("fri_date",  "fri_reminder_sent_at"),
}

SEND_KINDS = tuple(_KIND_MAP.keys())


def mark_sent(date_iso: str, kind: str, clear: bool = False) -> int:
    """Stamp (or clear) a send timestamp for every row matching that date+side.

    kind: mon_invite | mon_reminder | fri_invite | fri_reminder
    Returns number of rows updated (0 if no event matches the date).
    """
    if kind not in _KIND_MAP:
        raise ValueError(f"kind must be one of {SEND_KINDS}")
    date_col, stamp_col = _KIND_MAP[kind]
    conn = _connect()
    if not conn:
        raise RuntimeError(_last_error or "no DB connection")
    try:
        cur = conn.cursor()
        if clear:
            sql = (f"UPDATE unified.grand_rounds SET {stamp_col} = NULL, updated_at = now() "
                   f"WHERE {date_col} = %s::date")
        else:
            sql = (f"UPDATE unified.grand_rounds SET {stamp_col} = now(), updated_at = now() "
                   f"WHERE {date_col} = %s::date")
        cur.execute(sql, (date_iso,))
        conn.commit()
        n = cur.rowcount
        cur.close()
        conn.close()
        return n
    except Exception as e:
        try:
            conn.rollback()
            conn.close()
        except Exception:
            pass
        raise RuntimeError(f"mark_sent failed: {e}") from e


def last_error() -> str | None:
    return _last_error


# ── Resident name display — invites must read "Dr. LastName" ───────────────
# The schedule stores residents as FIRST names (Excel convention). This curated
# map (verified against CRM public.contacts category=Resident, 2026-09-09) is
# the ONLY resident-name map in the invite stack — do not add copies elsewhere.
_RESIDENT_DR = {
    # schedule first names / nicknames
    "joe": "Dr. Kim", "joseph": "Dr. Kim",
    "nate": "Dr. Iskhakov", "nathaniel": "Dr. Iskhakov", "nathan": "Dr. Iskhakov",
    "jasmin": "Dr. Capellan",
    "dinora": "Dr. Murota",
    "val": "Dr. V. Patel", "valmic": "Dr. V. Patel",
    "sam": "Dr. Yim", "samuel": "Dr. Yim",
    "jake": "Dr. Drobner",
    "kelli": "Dr. Aibel",
    "rutul": "Dr. R. Patel",
    "jen": "Dr. Pak", "jennifer": "Dr. Pak", "so yeon": "Dr. Pak", "soyeon": "Dr. Pak",
    "hill": "Dr. Hill", "hordines": "Dr. Hordines",
    # last-name keys (already-correct inputs)
    "iskhakov": "Dr. Iskhakov", "capellan": "Dr. Capellan", "murota": "Dr. Murota",
    "drobner": "Dr. Drobner", "aibel": "Dr. Aibel", "kim": "Dr. Kim",
    "pak": "Dr. Pak", "yim": "Dr. Yim", "patel": "Dr. Patel",
}


def dr_resident(raw):
    """Resident display name -> 'Dr. LastName'.

    Blank / N/A / ':' / '?' -> '' (caller may substitute 'TBD').
    Unknown input -> 'Dr. <name>' (assumed already a last name).
    """
    if raw is None:
        return ""
    s = str(raw).strip()
    if not s or s.lower() in ("n/a", "tbd", "none", "?", ":("):
        return ""
    key = s.lower()
    if key in _RESIDENT_DR:
        return _RESIDENT_DR[key]
    return f"Dr. {s}"


if __name__ == "__main__":
    # quick CLI sanity check: python3 gr_schedule.py [--status]
    rows = fetch_rows()
    print(f"canonical rows: {len(rows)}")
    for r in rows[:3]:
        print(r)
    if "--status" in os.sys.argv:
        for d in fetch_dicts():
            if d.get("mon_invite_sent_at") or d.get("fri_invite_sent_at"):
                print("sent:", d.get("mon_date"), d.get("fri_date"))
