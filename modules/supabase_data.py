#!/usr/bin/env python3
"""
Unified Supabase data access module.
Single source of truth for all data formerly in JSON files.
Used by: email scripts, cron jobs, Agentic OS dashboard, Hermes agents.
"""
import os, json, re
import psycopg2

DB_HOST = "147.93.113.241"
DB_PORT = 5432
DB_NAME = "postgres"
DB_USER = "postgres"

def _get_db_pw():
    """Find DB password from env files."""
    paths = [
        "/workspace/projects/unified/app/.env",
        os.path.expanduser("~/.hermes/profiles/opencode-acct2/.env"),
        os.path.expanduser("~/.hermes/.env"),
    ]
    for path in paths:
        if os.path.isfile(path):
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" not in line:
                        continue
                    key, val = line.split("=", 1)
                    if "PASS" in key.upper():
                        return val
    raise RuntimeError("Cannot find DB password in any .env")

def _connect():
    pw = _get_db_pw()
    return psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=pw)

# ─── Tasks ───

def get_tasks(status=None):
    conn = _connect()
    cur = conn.cursor()
    if status:
        cur.execute("SELECT id, content, status, priority, notes FROM unified.tasks WHERE status = %s ORDER BY priority='high' DESC, id", (status,))
    else:
        cur.execute("SELECT id, content, status, priority, notes FROM unified.tasks ORDER BY priority='high' DESC, id")
    rows = [{"id": r[0], "content": r[1], "status": r[2], "priority": r[3], "notes": r[4]} for r in cur.fetchall()]
    conn.close()
    return rows

def update_task(task_id, status=None, content=None, priority=None):
    conn = _connect()
    cur = conn.cursor()
    parts = []
    vals = []
    if status: parts.append("status=%s"); vals.append(status)
    if content: parts.append("content=%s"); vals.append(content)
    if priority: parts.append("priority=%s"); vals.append(priority)
    if status == "completed": parts.append("completed_at=now()")
    parts.append("updated_at=now()")
    vals.append(task_id)
    cur.execute(f"UPDATE unified.tasks SET {', '.join(parts)} WHERE id = %s RETURNING id, content, status", vals)
    row = cur.fetchone()
    conn.commit()
    conn.close()
    return row

# ─── Email Groups ───

def get_email_group(group_key):
    conn = _connect()
    cur = conn.cursor()
    cur.execute("SELECT emails, test_mode, test_email FROM unified.email_groups WHERE group_key = %s", (group_key,))
    r = cur.fetchone()
    conn.close()
    if not r: return None
    emails = json.loads(r[0]) if isinstance(r[0], str) else r[0]
    return {"emails": emails, "test_mode": r[1], "test_email": r[2]}

def get_all_email_groups():
    conn = _connect()
    cur = conn.cursor()
    cur.execute("SELECT group_key, label, test_mode FROM unified.email_groups ORDER BY group_key")
    rows = [{"key": r[0], "label": r[1], "test_mode": r[2]} for r in cur.fetchall()]
    conn.close()
    return rows

# ─── Staff Schedule ───

def get_staff_schedule(location=None):
    conn = _connect()
    cur = conn.cursor()
    if location:
        cur.execute("SELECT name, role, detail, schedule FROM unified.staff_schedule WHERE location = %s ORDER BY id", (location,))
    else:
        cur.execute("SELECT location, name, role, detail, schedule FROM unified.staff_schedule ORDER BY location, id")
    rows = []
    for r in cur.fetchall():
        if location:
            rows.append({"name": r[0], "role": r[1], "detail": r[2], "schedule": r[3]})
        else:
            rows.append({"location": r[0], "name": r[1], "role": r[2], "detail": r[3], "schedule": r[4]})
    conn.close()
    return rows

# ─── Resident Addresses ───

def get_resident_addresses():
    conn = _connect()
    cur = conn.cursor()
    cur.execute("SELECT name, first_name, last_name, address, pgy, mobile, email FROM unified.resident_addresses ORDER BY id")
    rows = [{"name": r[0], "firstName": r[1], "lastName": r[2], "address": r[3], "pgy": r[4], "mobile": r[5], "email": r[6]} for r in cur.fetchall()]
    conn.close()
    return rows

# ─── Shift Swaps ───

def get_shift_swaps():
    conn = _connect()
    cur = conn.cursor()
    cur.execute("SELECT swap_date, from_person, to_person, reason, logged_at FROM unified.shift_swaps ORDER BY swap_date DESC")
    rows = [{"date": str(r[0]), "from": r[1], "to": r[2], "reason": r[3], "logged_at": str(r[4]) if r[4] else None} for r in cur.fetchall()]
    conn.close()
    return rows

if __name__ == "__main__":
    tasks = get_tasks("pending")
    print(f"Pending tasks: {len(tasks)}")
    groups = get_all_email_groups()
    print(f"Email groups: {len(groups)}")
    staff = get_staff_schedule("Moses")
    print(f"Moses staff: {len(staff)}")
    addrs = get_resident_addresses()
    print(f"Addresses: {len(addrs)}")
    swaps = get_shift_swaps()
    print(f"Swaps: {len(swaps)}")
    print("All Supabase reads OK")
