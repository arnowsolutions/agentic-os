#!/usr/bin/env python3
"""Run on July 1: increment all resident PGY levels by 1.
   Incoming interns (urologyStart == current year) stay at PGY-1.
   Writes to Supabase Postgres (source of truth) and JSON fallback."""

import json, re, os, sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from modules.crm_db import get_contacts

JSON_FILE = Path(__file__).resolve().parent.parent / "data" / "crm_contacts.fallback.json"
current_year = str(datetime.now().year)

# Read from Supabase PG
contacts = get_contacts()
if not contacts:
    print("No contacts loaded from database")
    sys.exit(1)

updated = 0
skipped_incoming = 0

for c in contacts:
    if c.get("archived"):
        continue
    if c.get("category") != "Resident":
        continue

    pgy_raw = str(c.get("pgy", "")).strip()
    if not pgy_raw:
        continue

    m = re.search(r"(\d+)", pgy_raw)
    if not m:
        continue

    current_pgy = int(m.group(1))
    uro_start = str(c.get("urologyStart", "") or c.get("rotation_start", "") or "").strip()

    # Incoming interns: urologyStart == current year, currently PGY-1 → stay PGY-1
    if current_pgy == 1 and uro_start == current_year:
        print(f"  SKIP (incoming): {c.get('firstName', '?')} {c.get('lastName', '?')} — stays PGY-1")
        skipped_incoming += 1
        continue

    new_pgy = current_pgy + 1
    new_str = pgy_raw.replace(str(current_pgy), str(new_pgy), 1)
    
    # Update in JSON (backward compat)
    json_contacts = []
    if JSON_FILE.exists():
        json_contacts = json.loads(JSON_FILE.read_text())
    for jc in json_contacts:
        if jc.get("id") == c.get("id") or (jc.get("firstName") == c.get("firstName") and jc.get("lastName") == c.get("lastName")):
            jc["pgy"] = new_str
    if json_contacts:
        JSON_FILE.write_text(json.dumps(json_contacts, indent=2))
    
    # Update in Supabase Postgres
    try:
        pw = os.environ.get("POSTGRES_PASSWORD", "")
        if not pw:
            import subprocess as _sp
            r = _sp.run(['grep', 'POSTGRES_PASSWORD', '/workspace/projects/unified/app/.env'],
                capture_output=True, text=True, timeout=5)
            if r.returncode == 0:
                pw = r.stdout.strip().split('=', 1)[1].strip()
        if pw:
            import psycopg2
            conn = psycopg2.connect(host="127.0.0.1", port=5432, dbname="postgres", user="postgres", password=pw, connect_timeout=3)
            cur = conn.cursor()
            cur.execute("UPDATE public.contacts SET pgy = %s WHERE id = %s", (new_str, c.get("id")))
            conn.commit()
            cur.close()
            conn.close()
    except Exception as e:
        print(f"  WARN: Could not update PG: {e}")
    
    updated += 1
    fn = c.get('firstName', '?') or '?'
    ln = c.get('lastName', '?') or '?'
    print(f"  {fn} {ln}: {pgy_raw} -> {new_str}")

print(f"\nUpdated: {updated} | Skipped incoming interns: {skipped_incoming}")
