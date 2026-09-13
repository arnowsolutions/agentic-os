"""
ssot — Single Source Of Truth layer for the Agentic OS dashboard (2026-09-12).

Problem it solves: the dashboard accumulated frozen JSON snapshots
(data/*.json) that pages kept serving long after the sync cron moved on.
The freshest data (data/sync_cache.db, refreshed daily 09:01 by
daily_sync.py) only fed the Vapi voice bridge, not the hub.

Rule introduced here:
  - Data-backed endpoints read LIVE sources first (sync_cache.db, the
    unified Postgres via modules.crm, real files on disk), falling back to
    the old JSON snapshot ONLY when live is unavailable — and the response
    then says so via the stamp fields.
  - Every response carries an envelope:
        as_of   ISO timestamp of the underlying data (not of the request)
        source  human label, e.g. "sync_cache.db:call_schedule"
        freshness {age_minutes, level: fresh|warn|stale|unknown}
    so the frontend can render a "as of / source / FROZEN" badge and the
    staleness problem can never hide again.

No emoji (DESIGN.md). No class/token renames. Sync-friendly: every helper
returns plain JSON-serialisable structures.
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

BASE_DIR = Path(__file__).resolve().parent.parent          # /workspace/agentic-os
DATA_DIR = BASE_DIR / "data"
SYNC_DB = DATA_DIR / "sync_cache.db"
TZ_LABEL = "America/New_York"

# Freshness thresholds (minutes) for data produced by the 09:01 daily sync.
FRESH_MIN = 60 * 26      # <= ~26h: the sync has run since yesterday
WARN_MIN = 60 * 24 * 3   # <= 3d
STALE_MIN = 60 * 24 * 7  # <= 7d, beyond = stale

_SYNC_META_CACHE: dict = {"ts": 0.0, "meta": {}}


# ──────────────────────────────────────────────────────────────────────────
# Stamp envelope
# ──────────────────────────────────────────────────────────────────────────

def stamp(source: str, as_of: Optional[datetime]) -> dict:
    """Envelope dict to merge into any endpoint response."""
    if as_of is None:
        return {"as_of": None, "source": source,
                "freshness": {"age_minutes": None, "level": "unknown"}}
    if as_of.tzinfo is None:
        as_of = as_of.replace(tzinfo=timezone.utc)
    age = (datetime.now(timezone.utc) - as_of).total_seconds() / 60.0
    if age <= FRESH_MIN:
        level = "fresh"
    elif age <= WARN_MIN:
        level = "warn"
    else:
        level = "stale"
    return {"as_of": as_of.isoformat(timespec="seconds"),
            "source": source,
            "freshness": {"age_minutes": round(max(age, 0)), "level": level}}


def _file_mtime_dt(path: Path) -> Optional[datetime]:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    except OSError:
        return None


# ──────────────────────────────────────────────────────────────────────────
# sync_cache.db access
# ──────────────────────────────────────────────────────────────────────────

def _db() -> Optional[sqlite3.Connection]:
    if not SYNC_DB.exists():
        return None
    conn = sqlite3.connect(f"file:{SYNC_DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def sync_meta() -> dict:
    """{table: {row_count, synced_at(datetime)}} — 30s memo so page loads
    that call several helpers don't re-hit the disk each time."""
    now = time.time()
    if now - _SYNC_META_CACHE["ts"] < 30:
        return _SYNC_META_CACHE["meta"]
    meta: dict = {}
    conn = _db()
    if conn:
        try:
            for row in conn.execute("SELECT table_name, row_count, synced_at FROM sync_meta"):
                try:
                    dt = datetime.fromisoformat(row["synced_at"])
                except (ValueError, TypeError):
                    dt = None
                meta[row["table_name"]] = {"row_count": row["row_count"], "synced_at": dt}
        finally:
            conn.close()
    _SYNC_META_CACHE["ts"] = now
    _SYNC_META_CACHE["meta"] = meta
    return meta


def sync_overall() -> dict:
    """Envelope stamp for the sync cache as a whole (newest synced_at)."""
    meta = sync_meta()
    times = [m["synced_at"] for m in meta.values() if m.get("synced_at")]
    newest = max(times) if times else None
    out = stamp("sync_cache.db (daily_sync 09:01)", newest)
    out["tables"] = {t: {"rows": m["row_count"],
                         "synced_at": m["synced_at"].isoformat(timespec="seconds") if m.get("synced_at") else None}
                     for t, m in meta.items()}
    return out


# ──────────────────────────────────────────────────────────────────────────
# Staff schedule  (live: call_schedule + staff_directory; fallback: frozen JSON)
# ──────────────────────────────────────────────────────────────────────────

_STAFF_JSON = DATA_DIR / "staff_schedule.json"

def _asof_from_sync(table: str, fallback: Optional[datetime] = None) -> datetime:
    m = sync_meta().get(table) or {}
    return m.get("synced_at") or fallback or _file_mtime_dt(SYNC_DB) or datetime.now(timezone.utc)


def staff_schedule(hospital: str) -> dict:
    """NP/PA/attending/peds roster for a hospital from the live call cache.
    Falls back to the frozen JSON only when the DB lacks the hospital."""
    key = (hospital or "Moses").strip()
    if key.endswith(" Division"):
        key = key[: -len(" Division")].strip()

    conn = _db()
    if conn:
        try:
            rows = conn.execute(
                "SELECT name, role, campus FROM call_schedule WHERE campus=? AND date >= date('now') "
                "GROUP BY name, role ORDER BY role, name", (key,)).fetchall()
            directory = {r["display_name"]: r for r in conn.execute(
                "SELECT display_name, email, phone, location, employee_id FROM staff_directory")}
            if rows:
                staff = []
                for r in rows:
                    d = directory.get(r["name"], {})
                    staff.append({
                        "name": r["name"],
                        "role": r["role"],
                        "detail": f"On-call rotation — {key}",
                        "schedule": "live call_schedule (Q3-Q4 2026)",
                        "email": d.get("email", ""),
                        "phone": d.get("phone", ""),
                    })
                out = {"staff": staff, "hospital": key, "total": len(staff)}
                out.update(stamp("sync_cache.db:call_schedule", _asof_from_sync("call_schedule")))
                return out
        finally:
            conn.close()

    # legacy fallback (labeled — the badge will show its real age)
    staff, as_of = [], _file_mtime_dt(_STAFF_JSON)
    if _STAFF_JSON.exists():
        try:
            staff = json.loads(_STAFF_JSON.read_text()).get(key) or []
        except Exception:
            staff = []
    out = {"staff": staff, "hospital": key, "total": len(staff)}
    out.update(stamp("data/staff_schedule.json (FROZEN fallback)", as_of))
    return out


# ──────────────────────────────────────────────────────────────────────────
# GME detail  (live: unified Postgres via modules.crm, then sync_cache; fallback JSON)
# ──────────────────────────────────────────────────────────────────────────

_GME_JSON = DATA_DIR / "gme_detail.json"

def _categorize(reimbs: list) -> dict:
    cats = {"books": 0, "conferences": 0, "boards": 0, "other": 0}
    for t in reimbs:
        txt = f"{t.get('description', '')} {t.get('account', '')}".lower()
        if "book" in txt:
            cats["books"] += t.get("amount", 0)
        elif "conference" in txt or "meeting" in txt or "travel" in txt:
            cats["conferences"] += t.get("amount", 0)
        elif "board" in txt or "exam" in txt or "in-service" in txt or "inservice" in txt:
            cats["boards"] += t.get("amount", 0)
        else:
            cats["other"] += t.get("amount", 0)
    return {k: round(v, 2) for k, v in cats.items()}

def gme_detail() -> dict:
    # 1) unified DB — same payload the GME Tracker tab uses (single source)
    try:
        from modules.crm import _gme_resident_payload, CURRENT_AY, GME_ANNUAL_LIMIT
        payload = _gme_resident_payload(CURRENT_AY)
        residents = []
        for r in payload:
            name = " ".join(x for x in (r.get("firstName", ""), r.get("lastName", "")) if x)
            residents.append({
                "name": name or r.get("email", ""),
                "pgy": r.get("pgy", ""),
                "used": round(r.get("total_used", 0) or 0, 2),
                "remaining": round(max(GME_ANNUAL_LIMIT - (r.get("total_used", 0) or 0), 0), 2),
                "cap": GME_ANNUAL_LIMIT,
                "categories": _categorize(r.get("reimbursements", [])),
            })
        out = {"residents": residents, "ay": CURRENT_AY, "annual_limit": GME_ANNUAL_LIMIT}
        out.update(stamp("unified.reimb_submissions (live)", datetime.now(timezone.utc)))
        return out
    except Exception:
        pass
    # 2) daily-synced cache
    conn = _db()
    if conn:
        try:
            rows = conn.execute("SELECT name, total_spent, remaining, cap FROM gme_residents ORDER BY name").fetchall()
            if rows:
                residents = [{"name": r["name"], "pgy": "", "used": r["total_spent"],
                              "remaining": r["remaining"], "cap": r["cap"], "categories": {}}
                             for r in rows]
                out = {"residents": residents, "annual_limit": residents[0]["cap"] if residents else 1250}
                out.update(stamp("sync_cache.db:gme_residents", _asof_from_sync("gme_residents")))
                return out
        finally:
            conn.close()
    # 3) frozen snapshot (this is what the page has been showing — fake "Alex Chen" rows included)
    if _GME_JSON.exists():
        try:
            out = json.loads(_GME_JSON.read_text())
        except Exception:
            out = {"residents": []}
    else:
        out = {"residents": []}
    out.update(stamp("data/gme_detail.json (FROZEN fallback)", _file_mtime_dt(_GME_JSON)))
    return out


# ──────────────────────────────────────────────────────────────────────────
# Compliance overview  (was a hardcoded all-zeros stub)
# ──────────────────────────────────────────────────────────────────────────

_ATTENDANCE_FILE = BASE_DIR / "dashboard" / "data" / "attendance-data.json"
_EVAL_CACHE = DATA_DIR / "compliance_eval_cache.json"

def _server_mod():
    """The running FastAPI module, if this code executes inside it.
    (Never `import server` — that would re-execute the 4.5k-line file.)"""
    import sys
    return sys.modules.get("server")

def _grand_rounds_attendance() -> list:
    """Faculty attendance % from the Grand Rounds roster file."""
    if not _ATTENDANCE_FILE.exists():
        return []
    try:
        d = json.loads(_ATTENDANCE_FILE.read_text())
    except Exception:
        return []
    rows = []
    for p in d.get("people", []):
        a = p.get("all", {})
        rows.append({
            "name": f"{p.get('first', '')} {p.get('last', '')}".strip(),
            "category": p.get("category", ""),
            "attended": a.get("any", 0),
            "sessions": a.get("total", 0),
            "pct": a.get("pctAny", 0),
            "pass": bool(a.get("passAny", False)),
        })
    return sorted(rows, key=lambda r: -r["pct"])


def _eval_completion() -> dict:
    """Live eval counts, from the Eval Dashboard's own computation cached
    for 24h (it costs ~40 Google sheet reads, so it must not run per page load)."""
    fresh, cached = _file_mtime_dt(_EVAL_CACHE), None
    if _EVAL_CACHE.exists() and fresh:
        if (datetime.now(timezone.utc) - fresh).total_seconds() < 86400:
            try:
                cached = json.loads(_EVAL_CACHE.read_text())
            except Exception:
                cached = None
    if cached is None:
        _srv = _server_mod()
        if _srv is not None and hasattr(_srv, "eval_dashboard"):
            try:
                res = _srv.eval_dashboard()
                s = res.get("summary") or {}
                cached = {"done": s.get("completed", 0), "pending": s.get("pending", 0),
                          "overdue": s.get("overdue", 0)}
                _EVAL_CACHE.write_text(json.dumps(cached))
                fresh = _file_mtime_dt(_EVAL_CACHE)
            except Exception:
                cached = None
        if cached is None:
            cached = {"done": None, "pending": None, "overdue": None}
    out = dict(cached)
    out.update(stamp("eval sheets (cached 24h)", fresh))
    return out


def compliance_overview() -> dict:
    gme = gme_detail()
    residents = gme.get("residents", [])
    limit = gme.get("annual_limit", 1250)
    used = sum(r.get("used", 0) or 0 for r in residents)
    return {
        "grand_rounds_attendance": _grand_rounds_attendance(),
        "attendance_count": len(_grand_rounds_attendance()),
        "eval_completion": _eval_completion(),
        "gme_usage": {"used": round(used, 2), "available": limit * max(len(residents), 1),
                      "residents": len(residents), "gme_source": gme.get("source"),
                      "gme_as_of": gme.get("as_of")},
    }


# ──────────────────────────────────────────────────────────────────────────
# PDF archive  (real files on disk, not the 2026-06-22 snapshot)
# ──────────────────────────────────────────────────────────────────────────

def _human_size(n: int) -> str:
    for unit in ("B", "KB", "MB"):
        if n < 1024 or unit == "MB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.0f} {unit}"
        n /= 1024
    return f"{n:.1f} MB"


def pdf_archive() -> dict:
    pdfs, newest = [], None
    roots = [BASE_DIR / "reports", BASE_DIR / "data" / "subi-welcome-docs"]
    for root in roots:
        if not root.exists():
            continue
        for p in sorted(root.rglob("*.pdf"), key=lambda q: q.stat().st_mtime, reverse=True):
            st = p.stat()
            dt = datetime.fromtimestamp(st.st_mtime, tz=timezone.utc)
            newest = dt if newest is None or dt > newest else newest
            name = p.name
            kind = "schedule" if "call_schedule" in name or "schedule" in name.lower() else \
                   "gme" if "gme" in name.lower() else \
                   "attendance" if "attendance" in name.lower() else \
                   "eval" if "eval" in name.lower() else "document"
            pdfs.append({"name": name, "date": dt.strftime("%Y-%m-%d"),
                         "size": _human_size(st.st_size), "type": kind,
                         "path": str(p.relative_to(BASE_DIR))})
    if len(pdfs) > 200:
        pdfs = pdfs[:200]
    out = {"pdfs": pdfs, "total": len(pdfs)}
    out.update(stamp("reports/ + data/ (filesystem)", newest))
    return out


# ──────────────────────────────────────────────────────────────────────────
# Calendar events  (keep merged snapshot, but STAMP it + allow refresh)
# ──────────────────────────────────────────────────────────────────────────

_CALENDAR_JSON = DATA_DIR / "calendar_events.json"
_SYNC_CAL = BASE_DIR / "scripts" / "sync_calendar.py"

def calendar_stamp_only() -> dict:
    as_of = None
    if _CALENDAR_JSON.exists():
        try:
            ls = json.loads(_CALENDAR_JSON.read_text()).get("last_synced")
            if ls:
                as_of = datetime.fromisoformat(ls)
                if as_of.tzinfo is None:
                    as_of = as_of.replace(tzinfo=timezone.utc)
        except Exception:
            pass
    if as_of is None:
        as_of = _file_mtime_dt(_CALENDAR_JSON)
    return stamp("data/calendar_events.json (Google sync)", as_of)


def refresh_calendar() -> dict:
    """Run scripts/sync_calendar.py (Google Calendar → JSON, keeps manual_events)."""
    try:
        r = subprocess.run(["python3", str(_SYNC_CAL)], capture_output=True, text=True, timeout=90,
                           cwd=str(BASE_DIR))
        ok = r.returncode == 0
        return {"ok": ok, "tail": (r.stdout or r.stderr)[-400:]}
    except Exception as e:
        return {"ok": False, "tail": str(e)}


# ──────────────────────────────────────────────────────────────────────────
# Daily sync runner ("Sync now")
# ──────────────────────────────────────────────────────────────────────────

_DAILY_SYNC = BASE_DIR / "daily_sync.py"
_last_sync_run = {"at": None, "result": None}

def run_sync(include_calendar: bool = True) -> dict:
    out: dict = {"ran_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "steps": []}
    try:
        r = subprocess.run(["python3", str(_DAILY_SYNC)], capture_output=True, text=True,
                           timeout=180, cwd=str(BASE_DIR))
        out["steps"].append({"step": "daily_sync.py", "ok": r.returncode == 0,
                             "tail": (r.stdout or r.stderr)[-300:]})
    except Exception as e:
        out["steps"].append({"step": "daily_sync.py", "ok": False, "tail": str(e)})
    if include_calendar:
        cal = refresh_calendar()
        out["steps"].append({"step": "sync_calendar.py", **cal})
    _SYNC_META_CACHE["ts"] = 0.0  # force re-read of sync_meta
    out["sync"] = sync_overall()
    _last_sync_run["at"] = out["ran_at"]
    _last_sync_run["result"] = out
    return out


# ──────────────────────────────────────────────────────────────────────────
# Morning briefing — real values (was: hardcoded on_call + fake events)
# ──────────────────────────────────────────────────────────────────────────

def _today_str() -> str:
    # dashboard TZ is New York; server provides TZ-aware string on the VPS too
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo(TZ_LABEL)).strftime("%Y-%m-%d")
    except Exception:
        return datetime.now().strftime("%Y-%m-%d")


def _events_ahead(days: int = 10) -> list:
    if not _CALENDAR_JSON.exists():
        return []
    try:
        d = json.loads(_CALENDAR_JSON.read_text())
    except Exception:
        return []
    today = _today_str()
    evs = []
    from datetime import date as _date
    for ev in (d.get("events", []) + d.get("manual_events", [])):
        s = (ev.get("start") or {}).get("date") or (ev.get("start") or {}).get("dateTime", "")[:10]
        if s and s >= today:
            try:
                day = _date.fromisoformat(s).strftime("%a")
            except ValueError:
                day = "?"
            evs.append({"date": s, "day": day, "event": ev.get("summary", ""),
                        "all_day": bool((ev.get("start") or {}).get("date"))})
    evs.sort(key=lambda e: e["date"])
    return evs[:days]


def briefing_oncall() -> dict:
    """Live on-call today via the same Postgres path /api/oncall/now uses."""
    _srv = _server_mod()
    if _srv is not None and hasattr(_srv, "_get_oncall_for_date"):
        try:
            today = _today_str()
            entries = _srv._get_oncall_for_date(today)
            if entries:
                return {"oncall": entries, "date": today, "source": "supabase.call_schedule"}
            first = _srv._supabase_select("call_schedule?select=date&order=date.asc&limit=1")
            rng = f"Schedule starts {first[0]['date']}." if first else "No call schedule loaded."
            return {"oncall": [], "date": today, "message": rng, "source": "supabase.call_schedule"}
        except Exception as e:
            return {"oncall": [], "error": str(e)}
    # outside the server process (tests): read the call cache directly
    conn = _db()
    if conn:
        try:
            today = _today_str()
            rows = conn.execute(
                "SELECT campus, date, day, role, name FROM call_schedule WHERE date=? ORDER BY campus, role",
                (today,)).fetchall()
            agg: dict = {}
            for r in rows:
                e = agg.setdefault(r["campus"], {"hospital": r["campus"], "date": r["date"], "day": r["day"]})
                e[r["role"] + "_attending"] = r["name"]
            return {"oncall": list(agg.values()), "date": today, "source": "sync_cache.db:call_schedule"}
        finally:
            conn.close()
    return {"oncall": [], "message": "no live source available"}


# ──────────────────────────────────────────────────────────────────────────
# Attention queue (Today page): needs-you items only — aggregate counts
# ──────────────────────────────────────────────────────────────────────────

def _data_gaps_summary() -> dict:
    try:
        from modules.crm_db import get_contacts
        contacts = get_contacts() or []
        live = "unified CRM (live)"
    except Exception:
        contacts, live = [], None
    if not contacts:
        f = DATA_DIR / "crm_contacts.fallback.json"
        try:
            d = json.loads(f.read_text())
            contacts = d.get("contacts", []) if isinstance(d, dict) else d
            live = "crm_contacts.fallback.json (fallback)"
        except Exception:
            return {"count": None, "items": [], "source": "unavailable"}
    es = ["firstName", "lastName", "email", "ezId", "category", "mobile", "primaryLocation", "title", "role", "shift"]
    count = 0
    by_field: dict = {}
    for c in contacts:
        missing = [k for k in es if not c.get(k)]
        if missing:
            count += 1
            for k in missing:
                by_field[k] = by_field.get(k, 0) + 1
    items = [{"field": k, "count": v} for k, v in sorted(by_field.items(), key=lambda x: -x[1])[:6]]
    return {"count": count, "items": items, "source": live or "crm"}


def _pending_emails() -> list:
    q = DATA_DIR / "pending_review"
    items = []
    if q.exists():
        for f in sorted(q.glob("*.json"), key=lambda p: p.name, reverse=True):
            try:
                d = json.loads(f.read_text())
            except Exception:
                continue
            if d.get("status") != "pending":
                continue
            items.append({"id": d.get("id"), "to": d.get("to", ""), "subject": d.get("subject", ""),
                          "created": float(d.get("created") or 0)})
    return items[:20]


def _cron_failures() -> dict:
    """Scan Hermes cron output for non-zero exits within the last 48h."""
    try:
        jobs_f = Path("/home/hermeswebui/.hermes/cron/jobs.json")
        total = enabled = 0
        if jobs_f.exists():
            jobs = json.loads(jobs_f.read_text()).get("jobs", [])
            total = len(jobs)
            enabled = sum(1 for j in jobs if j.get("enabled", True))
        return {"total": total, "enabled": enabled, "failing": 0,
                "source": "cron/jobs.json"}
    except Exception:
        return {"total": None, "enabled": None, "failing": None, "source": "unavailable"}


def _stale_sources() -> list:
    """Files behind the hub, by age (top offenders only)."""
    watch = {
        "data/calendar_events.json": "Calendar events",
        "data/notifications.json": "Notification feed",
        "data/eval_forms.json": "Eval forms",
        "data/staff_schedule.json": "Staff schedule (frozen copy)",
        "data/gme_detail.json": "GME detail (frozen copy)",
        "data/agent-routes.json": "Smart Router config",
        "data/pdf_archive.json": "PDF archive (frozen copy)",
        "dashboard/data/attendance-data.json": "GR attendance",
        "data/goals.json": "Goals",
    }
    rows = []
    for rel, label in watch.items():
        p = BASE_DIR / rel
        dt = _file_mtime_dt(p)
        if dt is None:
            continue
        age_d = (datetime.now(timezone.utc) - dt).total_seconds() / 86400.0
        rows.append({"path": rel, "label": label, "age_days": round(age_d, 1)})
    rows.sort(key=lambda r: -r["age_days"])
    return rows


def attention_queue() -> dict:
    gaps = _data_gaps_summary()
    emails = _pending_emails()
    swaps: list = []
    try:
        raw = json.loads((DATA_DIR / "shift_swaps.json").read_text())
        swaps = [s for s in (raw if isinstance(raw, list) else raw.get("swaps", []))
                 if str(s.get("status", "")).lower() not in ("approved", "rejected", "done", "cancelled")]
    except Exception:
        pass
    cron = _cron_failures()
    stale = [r for r in _stale_sources() if r["age_days"] > 7]
    return {
        "pending_emails": emails,
        "pending_email_count": len(emails),
        "open_swaps": swaps[:10],
        "open_swap_count": len(swaps),
        "data_gaps": gaps,
        "cron": cron,
        "stale_sources": stale,
        "sync": sync_overall(),
    }
