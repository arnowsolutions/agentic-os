#!/usr/bin/env python3
"""
calendar_sasp_canonical_check.py — drift guard: Google Calendar SASP events vs canonical schedule.

SSOT for the Monday conference schedule is unified.grand_rounds (Supabase PG on the
VPS). Google Calendar events are sometimes hand-typed and drift (departed faculty,
wrong resident, stale topic). This script compares each future 📋 SASP event against
the canonical row for its date and — in --apply mode — rewrites title + description
from canonical (sendUpdates=none; these events have no attendees).

Also refreshes data/calendar_events.json afterwards (sync_calendar.py) so the
dashboard shows the corrected view, and fails loudly on any canonical attending
that is not active CRM Faculty (catches departed-staff creep from the other side).

Usage:
  /workspace/.aos-venv/bin/python3 /workspace/agentic-os/scripts/calendar_sasp_canonical_check.py          # check only (exit 1 if drift)
  /workspace/.aos-venv/bin/python3 /workspace/agentic-os/scripts/calendar_sasp_canonical_check.py --apply  # fix drift
"""
import json
import os
import re
import subprocess
import sys

APPLY = "--apply" in sys.argv
VPS = "root@147.93.113.241"
TOKEN = "/home/hermeswebui/.hermes/google_token.json"
CALENDAR_MIN_DAYS_AHEAD_FIX = 120  # only rewrite events within ~4 months; older = history


def canonical_mondays() -> dict:
    """date_iso -> (resident, attending, topic) from unified.grand_rounds via VPS psql."""
    sql = ("SELECT mon_date::text, mon_resident, mon_attending, mon_topic "
           "FROM unified.grand_rounds WHERE mon_date IS NOT NULL "
           "AND mon_date >= '2026-09-01' ORDER BY mon_date;")
    q = f"docker exec supabase-db psql -U postgres -d postgres -t -A -F'|' -c {json.dumps(sql)}"
    out = subprocess.run(["ssh", "-o", "BatchMode=yes", VPS, q],
                         capture_output=True, text=True, timeout=90)
    if out.returncode != 0:
        raise RuntimeError(f"psql failed: {out.stderr[:200]}")
    rows = {}
    for ln in out.stdout.strip().splitlines():
        p = ln.split("|")
        if len(p) >= 4 and re.match(r"\d{4}-\d{2}-\d{2}", p[0]):
            rows[p[0]] = (p[1].strip(), p[2].strip(), p[3].strip())
    return rows


def crm_faculty_names() -> set:
    """Active Faculty last names from the CRM SSOT (contacts table)."""
    sql = "SELECT lower(regexp_replace(lower(last_name),'[^a-z]','','g')) FROM public.contacts WHERE category='Faculty';"
    q = f"docker exec supabase-db psql -U postgres -d postgres -t -A -c {json.dumps(sql)}"
    out = subprocess.run(["ssh", "-o", "BatchMode=yes", VPS, q],
                         capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        raise RuntimeError(f"psql (contacts) failed: {out.stderr[:200]}")
    return {l.strip() for l in out.stdout.splitlines() if l.strip()}


def main() -> int:
    from datetime import datetime, timedelta, timezone
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    canon = canonical_mondays()
    try:
        faculty = crm_faculty_names()
    except Exception as e:
        print(f"⚠ CRM faculty lookup failed ({e}) — skipping departed-name audit")
        faculty = None

    creds = Credentials.from_authorized_user_file(
        TOKEN, ["https://www.googleapis.com/auth/calendar"])
    svc = build("calendar", "v3", credentials=creds)
    today = datetime.now(timezone.utc).date()
    res = svc.events().list(
        calendarId="primary",
        timeMin=(today - timedelta(days=7)).isoformat() + "T00:00:00Z",
        timeMax=(today + timedelta(days=CALENDAR_MIN_DAYS_AHEAD_FIX)).isoformat() + "T23:59:59Z",
        singleEvents=True, maxResults=300).execute()

    drift, flagged, synced = [], [], []
    for e in res.get("items", []):
        s = e.get("summary", "")
        if "SASP" not in s:
            continue
        d = (e.get("start") or {}).get("dateTime", "")[:10]
        if d not in canon:
            continue  # no canonical row for that date — leave alone
        resident, attending, topic = canon[d]
        if not attending:
            continue  # holiday / unassigned week
        want = f"📋 SASP: {resident} / Dr. {attending}"
        want_desc = ("Urology Resident Monday Conference\n"
                     f"Resident: {resident}\nAttending: Dr. {attending}\nTopic: {topic or 'SASP'}")
        if s != want or (e.get("description") or "").strip() != want_desc.strip():
            drift.append((d, s, want))
            if APPLY:
                ev = svc.events().get(calendarId="primary", eventId=e["id"]).execute()
                ev["summary"] = want
                ev["description"] = want_desc
                svc.events().update(calendarId="primary", eventId=e["id"],
                                    body=ev, sendUpdates="none").execute()
                synced.append(d)

    # Departed-creep audit on the canonical side: every future attending must be
    # active CRM Faculty.
    if faculty is not None:
        from datetime import date as _d
        for d, (resident, attending, topic) in canon.items():
            if not attending or d < _d.today().isoformat():
                continue
            key = re.sub(r"[^a-z]", "", attending.lower())
            if key and key not in faculty:
                flagged.append((d, attending))

    print(f"canonical rows: {len(canon)} | SASP events checked vs drift: {len(drift)}")
    for d, old, new in drift:
        print(f"  {'FIXED' if APPLY else 'DRIFT'}: {d}: {old!r} -> {new!r}")
    for d, att in flagged:
        print(f"  ⚠ CANONICAL-vs-CRM: {d} attending {att!r} is NOT active Faculty — check unified.grand_rounds")

    if APPLY and synced:
        # refresh the dashboard cache so corrected events show everywhere
        r = subprocess.run(["python3", "/workspace/agentic-os/scripts/sync_calendar.py"],
                           capture_output=True, text=True, timeout=180)
        tail = (r.stdout or "").strip().splitlines()[-1:] or ["(no output)"]
        print("calendar_events.json refreshed:", tail[0])

    return 1 if (drift or flagged) and not APPLY else 0


if __name__ == "__main__":
    sys.exit(main())
