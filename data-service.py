#!/usr/bin/env python3
"""
Montefiore Urology — Unified Data Service
Aggregates data from 3 backend databases into a single API for Agentic OS.
  - Reimbursement: SQLite (local)
  - Sick Call Line: Supabase (when SUPA_URL/SUPA_KEY are set)
  - UroSched/QGenda: MySQL (when MYSQL_URL is set)

Usage: python3 data-service.py --port 8086
"""
import argparse
import json
import os
import sqlite3
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional
from collections import Counter
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ─── Config ───────────────────────────────────────────────────────

REIMBURSEMENT_DB = "/workspace/repos/reimbursement/reimbursement.db"
HERMES_CRM = Path.home() / ".hermes" / "crm_contacts.json"

# Supabase (sick-call) — the key is loaded automatically from /tmp/check_supa.py
# or set the SUPA_SERVICE_KEY env var to override

# MySQL (UroSched) — set MYSQL_URL to enable
MYSQL_URL = os.environ.get("MYSQL_URL", "")

# UroSched Supabase — load key from file
_URO_CLIENT = None
def get_uro():
    global _URO_CLIENT
    if _URO_CLIENT is not None:
        return _URO_CLIENT
    uro_key_file = Path("/tmp/urosched_key.txt")
    if uro_key_file.exists():
        uro_key = uro_key_file.read_text().strip()
        if len(uro_key) > 100:
            try:
                import httpx
                _URO_CLIENT = {"key": uro_key, "url": "https://zirrkvxzokknvrxoqaek.supabase.co/rest/v1/"}
                print(f"  UroSched connected ({len(uro_key)} chars)")
            except Exception as e:
                print(f"  UroSched connection failed: {e}")
    return _URO_CLIENT

# Supabase (sick-call) — load key from file to avoid truncation
SUPA_URL = "https://rcbsmvjcozvfkazzewiq.supabase.co"

_SUPA_CLIENT = None
def get_supa():
    global _SUPA_CLIENT
    if _SUPA_CLIENT is not None:
        return _SUPA_CLIENT
    
    # Try env var first, then look for key in check_supa.py
    supa_key = os.environ.get("SUPA_SERVICE_KEY", "")
    if not supa_key:
        key_file = Path("/tmp/check_supa.py")
        if key_file.exists():
            import re
            content = key_file.read_text()
            m = re.search(r'SUPA_KEY.*?"([^"]+)"', content)
            if m:
                supa_key = m.group(1)
    
    if supa_key:
        try:
            from supabase import create_client
            _SUPA_CLIENT = create_client(SUPA_URL, supa_key)
            print(f"  Supabase connected: {SUPA_URL[:30]}...")
        except Exception as e:
            print(f"  Supabase connection failed: {e}")
            _SUPA_CLIENT = None
    return _SUPA_CLIENT

def supa_enabled():
    return get_supa() is not None

# ─── DB Helpers ───────────────────────────────────────────────────

def sqlite_conn():
    """Get a read-only connection to the reimbursement SQLite DB."""
    conn = sqlite3.connect(f"file:{REIMBURSEMENT_DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn

def supa_enabled():
    client = get_supa()
    return client is not None

def mysql_enabled():
    return bool(MYSQL_URL)

def _is_resident_row(row):
    """Heuristic: a person with a cls (PGY/PG value) is a resident/fellow."""
    return row["cls"] is not None and str(row["cls"]).strip() != ""

# ─── App ──────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(f"  Reimbursement DB (SQLite): {'YES' if Path(REIMBURSEMENT_DB).exists() else 'NOT FOUND'}")
    print(f"  Sick Call (Supabase):      {'CONFIGURED' if supa_enabled() else 'Not configured (set SUPA_URL + SUPA_KEY)'}")
    print(f"  UroSched (MySQL):          {'CONFIGURED' if mysql_enabled() else 'Not configured (set MYSQL_URL)'}")
    yield

app = FastAPI(
    title="Montefiore Urology — Unified Data Service",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Health ───────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {
        "status": "ok",
        "reimbursement_db": Path(REIMBURSEMENT_DB).exists(),
        "supabase_configured": supa_enabled(),
        "mysql_configured": mysql_enabled(),
        "timestamp": datetime.utcnow().isoformat()
    }

# ─── CRM (Hermes contacts) ────────────────────────────────────────

@app.get("/api/crm/contacts")
def crm_contacts():
    if HERMES_CRM.exists():
        return json.loads(HERMES_CRM.read_text())
    return []

# ─── Reimbursement Endpoints ──────────────────────────────────────

@app.get("/api/reimbursement/residents")
def get_residents():
    """List all residents/staff with reimbursement data."""
    conn = sqlite_conn()
    rows = conn.execute("""
        SELECT p.id, p.name, p.cls, p.email, p.program_start_year,
               p.graduation_year, p.beneficiary_type, p.is_active
        FROM persons p
        WHERE p.cls IS NOT NULL AND p.cls != ''
        ORDER BY p.cls, p.name
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/api/reimbursement/residents/{person_id}")
def get_resident_detail(person_id: str):
    """Single resident with GME balance and submission history."""
    conn = sqlite_conn()
    person = conn.execute("""
        SELECT p.* FROM persons p WHERE p.id = ?
    """, (person_id,)).fetchone()
    if not person:
        conn.close()
        raise HTTPException(404, "Person not found")

    allocations = conn.execute("""
        SELECT a.*, pkg.name as package_name, pkg.status as package_status
        FROM allocations a
        LEFT JOIN packages pkg ON a.package_id = pkg.id
        WHERE a.beneficiary_id = ?
        ORDER BY a.created_at DESC LIMIT 50
    """, (person_id,)).fetchall()

    submissions = conn.execute("""
        SELECT s.* FROM submissions s
        WHERE s.target_id = ?
        ORDER BY s.created_at DESC LIMIT 50
    """, (person_id,)).fetchall()

    conn.close()
    return {
        "person": dict(person),
        "allocations": [dict(a) for a in allocations],
        "submissions": [dict(s) for s in submissions]
    }

@app.get("/api/reimbursement/gme-summary")
def gme_summary():
    """GME fund overview from Drive spreadsheet cache (preferred) or SQLite."""
    gme_cache = Path("/workspace/agentic-os/reports/gme_cache.json")
    if gme_cache.exists():
        try:
            data = json.loads(gme_cache.read_text())
            if data.get("source") != "sqlite_fallback":
                return data
        except:
            pass
    
    conn = sqlite_conn()
    annual_cap = 1250.0

    rows = conn.execute("""
        SELECT p.id, p.name, p.cls, p.beneficiary_type,
               COALESCE(SUM(a.amount), 0) as total_allocated,
               COUNT(DISTINCT a.id) as allocation_count
        FROM persons p
        LEFT JOIN allocations a ON a.beneficiary_id = p.id
            AND a.account LIKE '%GME%'
            AND a.status NOT IN ('CANCELLED', 'VOIDED')
        WHERE p.cls IS NOT NULL AND p.cls != ''
        GROUP BY p.id
        ORDER BY p.cls, p.name
    """).fetchall()

    residents = []
    total_used = 0.0
    for r in rows:
        d = dict(r)
        d["annual_cap"] = annual_cap
        d["remaining"] = round(max(0, annual_cap - d["total_allocated"]), 2)
        d["usage_pct"] = round((d["total_allocated"] / annual_cap) * 100, 1) if annual_cap > 0 else 0
        total_used += d["total_allocated"]
        residents.append(d)

    total_residents = len(residents)
    conn.close()
    return {
        "annual_cap_per_resident": annual_cap,
        "total_residents": total_residents,
        "total_cap": round(total_residents * annual_cap, 2),
        "total_used": round(total_used, 2),
        "total_remaining": round(max(0, (total_residents * annual_cap) - total_used), 2),
        "residents": residents
    }

@app.get("/api/reimbursement/allocations")
def get_allocations(
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
    account: Optional[str] = Query(None, description="Account name filter (e.g. GME)"),
    person_id: Optional[str] = None
):
    conn = sqlite_conn()
    params = []
    where = []
    if account:
        where.append("a.account LIKE ?")
        params.append(f"%{account}%")
    if person_id:
        where.append("a.beneficiary_id = ?")
        params.append(person_id)

    where_clause = "WHERE " + " AND ".join(where) if where else ""

    total = conn.execute(f"SELECT COUNT(*) FROM allocations a {where_clause}", params).fetchone()[0]
    rows = conn.execute(f"""
        SELECT a.*, p.name as beneficiary_name, p.cls, pkg.name as package_name
        FROM allocations a
        LEFT JOIN persons p ON a.beneficiary_id = p.id
        LEFT JOIN packages pkg ON a.package_id = pkg.id
        {where_clause}
        ORDER BY a.created_at DESC
        LIMIT ? OFFSET ?
    """, params + [limit, offset]).fetchall()
    conn.close()
    return {"total": total, "limit": limit, "offset": offset, "items": [dict(r) for r in rows]}

@app.get("/api/reimbursement/submissions")
def get_submissions(
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    status: Optional[str] = None
):
    conn = sqlite_conn()
    params = []
    where = []
    if status:
        where.append("s.status = ?")
        params.append(status)
    where_clause = "WHERE " + " AND ".join(where) if where else ""

    total = conn.execute(f"SELECT COUNT(*) FROM submissions s {where_clause}", params).fetchone()[0]
    rows = conn.execute(f"""
        SELECT s.*, p.name as submitted_by_name
        FROM submissions s
        LEFT JOIN persons p ON s.submitted_by = p.id
        {where_clause}
        ORDER BY s.created_at DESC
        LIMIT ? OFFSET ?
    """, params + [limit, offset]).fetchall()
    conn.close()
    return {"total": total, "limit": limit, "offset": offset, "items": [dict(r) for r in rows]}

@app.get("/api/reimbursement/packages")
def get_packages(limit: int = Query(20, le=100)):
    conn = sqlite_conn()
    rows = conn.execute("""
        SELECT pkg.*, p.name as owner_name
        FROM packages pkg
        LEFT JOIN persons p ON pkg.owner_id = p.id
        ORDER BY pkg.created_at DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return {"items": [dict(r) for r in rows]}

# ─── Unified Dashboard Endpoints ──────────────────────────────────

@app.get("/api/unified/today")
def unified_today():
    """Today's snapshot across all available data sources."""
    today = date.today()
    result = {
        "date": today.isoformat(),
        "reimbursement": {},
        "sick_call": {"available": supa_enabled()},
        "urosched": {"available": get_uro() is not None}
    }

    # ─── Reimbursement data ────────────────────────────────────────
    conn = sqlite_conn()
    pending = conn.execute("""
        SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as total
        FROM submissions WHERE status = 'pending'
    """).fetchone()
    result["reimbursement"]["pending_submissions"] = dict(pending)

    cap = 1250.0
    gme_used = conn.execute("""
        SELECT COALESCE(SUM(amount), 0) as total
        FROM allocations WHERE account LIKE '%GME%'
        AND status NOT IN ('CANCELLED', 'VOIDED')
    """).fetchone()[0]
    resident_count = conn.execute("""
        SELECT COUNT(*) FROM persons WHERE cls IS NOT NULL AND cls != ''
    """).fetchone()[0]
    result["reimbursement"]["gme_used"] = round(gme_used, 2)
    result["reimbursement"]["gme_cap_total"] = round(resident_count * cap, 2)
    result["reimbursement"]["gme_remaining"] = round(max(0, (resident_count * cap) - gme_used), 2)
    result["reimbursement"]["active_residents"] = resident_count
    conn.close()

    # ─── Sick Call data (if Supabase connected) ────────────────────
    supa = get_supa()
    if supa:
        try:
            # ... existing sick call code stays ...
            r = supa.table('absence_requests').select(
                'employee_name, department, start_date, end_date, reason, status, channel, is_late_callout'
            ).gte('start_date', today.isoformat()).lte('start_date', (today + timedelta(days=6)).isoformat()).execute()
            
            absences = r.data
            result["sick_call"]["absences_this_week"] = len(absences)
            result["sick_call"]["pending"] = len([a for a in absences if a.get('status') == 'pending'])
            result["sick_call"]["approved"] = len([a for a in absences if a.get('status') == 'approved'])
            result["sick_call"]["absences"] = absences

            r = supa.table('shifts').select('id', count='exact').eq('date', today.isoformat()).execute()
            result["sick_call"]["today_shifts"] = r.count if r.count else len(r.data)

            r = supa.table('users').select('department').execute()
            depts = Counter(u.get('department', 'Unknown') for u in r.data)
            result["sick_call"]["employees_by_dept"] = dict(depts)
            
            r = supa.table('locations').select('id, name, code').execute()
            result["sick_call"]["locations"] = len(r.data)
            
        except Exception as e:
            result["sick_call"]["error"] = str(e)[:100]

    # ─── UroSched data (if key file exists) ────────────────────────
    uro = get_uro()
    if uro:
        try:
            import httpx
            h = {"apikey": uro["key"], "Authorization": "Bearer " + uro["key"]}
            
            # Today's call schedule across all locations
            r = httpx.get(uro["url"] + "Shift?date=eq." + today.isoformat() + "&select=id,date,locationId,status,period", headers=h, timeout=10)
            if r.status_code == 200:
                today_shifts = r.json()
                result["urosched"]["today_shifts"] = len(today_shifts)
            else:
                result["urosched"]["today_shifts"] = 0
            
            # All locations
            r = httpx.get(uro["url"] + "Location?select=id,name,code", headers=h, timeout=10)
            if r.status_code == 200:
                locs = r.json()
                result["urosched"]["locations"] = [{"id": l["id"], "name": l["name"], "code": l["code"]} for l in locs]
            
            # Total shifts seeded
            r = httpx.get(uro["url"] + "Shift?select=id&limit=1", headers={**h, "Prefer": "count=exact"}, timeout=10)
            if r.status_code in (200, 206):
                cr = r.headers.get("content-range", "0-0/0")
                total = cr.split("/")[-1] if "/" in cr else "?"
                result["urosched"]["total_shifts"] = int(total) if total.isdigit() else len(r.json())
            
            # Future shifts count  
            future = (today + timedelta(days=1)).isoformat()
            r = httpx.get(uro["url"] + "Shift?select=id&date=gte." + future + "&limit=1", headers={**h, "Prefer": "count=exact"}, timeout=10)
            if r.status_code in (200, 206):
                cr = r.headers.get("content-range", "0-0/0")
                total = cr.split("/")[-1] if "/" in cr else "?"
                result["urosched"]["future_shifts"] = int(total) if total.isdigit() else 0
            
        except Exception as e:
            result["urosched"]["error"] = str(e)[:100]

    return result

@app.get("/api/unified/residents")
def unified_residents():
    """All residents with combined data from available sources."""
    conn = sqlite_conn()
    rows = conn.execute("""
        SELECT p.id, p.name, p.cls, p.email, p.program_start_year,
               p.graduation_year, p.beneficiary_type, p.is_active,
               COALESCE(SUM(CASE WHEN a.account LIKE '%GME%' AND a.status NOT IN ('CANCELLED','VOIDED') THEN a.amount ELSE 0 END), 0) as gme_used,
               COUNT(DISTINCT a.id) as allocation_count
        FROM persons p
        LEFT JOIN allocations a ON a.beneficiary_id = p.id
        WHERE p.cls IS NOT NULL AND p.cls != ''
        AND (a.id IS NULL OR a.id LIKE 'al\_xlsx\_%' OR a.id NOT LIKE 'al\_xlsx\_%')
        GROUP BY p.id
        ORDER BY p.cls, p.name
    """).fetchall()
    conn.close()

    residents = []
    for r in rows:
        d = dict(r)
        d["annual_cap"] = 1250.0
        d["gme_remaining"] = round(max(0, 1250.0 - d["gme_used"]), 2)
        d["gme_pct"] = round((d["gme_used"] / 1250.0) * 100, 1)
        residents.append(d)

    return {"items": residents}

@app.get("/api/unified/stats")
def unified_stats():
    """High-level stats for dashboard widgets."""
    conn = sqlite_conn()

    total_residents = conn.execute("""
        SELECT COUNT(*) FROM persons WHERE cls IS NOT NULL AND cls != '' AND is_active = 1
    """).fetchone()[0]

    pending_reimbursements = conn.execute("""
        SELECT COUNT(*) FROM submissions WHERE status = 'pending'
    """).fetchone()[0]

    total_allocated = conn.execute("""
        SELECT COALESCE(SUM(amount), 0) FROM allocations WHERE status NOT IN ('CANCELLED','VOIDED')
    """).fetchone()[0]

    this_month = date.today().strftime("%Y-%m")
    month_allocations = conn.execute("""
        SELECT COALESCE(SUM(amount), 0) FROM allocations
        WHERE strftime('%Y-%m', created_at) = ? AND status NOT IN ('CANCELLED','VOIDED')
    """, (this_month,)).fetchone()[0]

    conn.close()

    return {
        "total_residents": total_residents,
        "pending_reimbursements": pending_reimbursements,
        "total_allocated": round(total_allocated, 2),
        "month_allocations": round(month_allocations, 2),
        "supabase_available": supa_enabled(),
        "mysql_available": mysql_enabled(),
        "as_of": datetime.utcnow().isoformat()
    }

@app.get("/api/unified/status")
def integration_status():
    """Shows which data sources are connected."""
    return {
        "reimbursement_db": {
            "connected": Path(REIMBURSEMENT_DB).exists(),
            "path": REIMBURSEMENT_DB,
            "tables_available": True
        },
        "sick_call_supabase": {
            "connected": supa_enabled(),
            "note": "Set SUPA_URL and SUPA_KEY env vars to enable" if not supa_enabled() else "Ready"
        },
        "urosched_mysql": {
            "connected": mysql_enabled(),
            "note": "Set MYSQL_URL env var to enable" if not mysql_enabled() else "Ready"
        }
    }

# ─── Main ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8086)
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
