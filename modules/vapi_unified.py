"""Unified data layer for Vapi voice queries.
   Reads from local xlsx + CSV files for schedule, GME, QGenda daily assignments.
   No Drive/Composio dependency needed.
"""
import csv
import json
import os
import sqlite3
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

# ── Paths — resolve relative to workspace root ──────────
_THIS_DIR = Path(__file__).resolve().parent  # modules/
_WORKSPACE = os.environ.get("WORKSPACE") or str(_THIS_DIR.parent.parent)  # agentic-os/../.. = /workspace
SCHEDULE_PATH = os.path.join(_WORKSPACE, "Call_Schedule_Q3_Q4_2026.xlsx")
GME_PATH = os.path.join(_WORKSPACE, "Resident_Trackers2025-2026.xlsx")
QGENDA_PATH = os.path.join(_WORKSPACE, "repos/qgenda/data/Montefiore_Medical_Center_-_Urology_Schedule_Export_1-1-2026_to_12-31-2026.csv")
REIMBURSEMENT_DB = os.path.join(_WORKSPACE, "repos/reimbursement/reimbursement.db")
STAFF_PATH = os.path.join(_WORKSPACE, "repos/sick-call-line/data/associates.csv")
GME_CAP = 1250.0

# ── Helpers ────────────────────────────────────────────
_qgenda_cache = None
_schedule_cache = None
_staff_cache = None


# ============================================================================
# QGENDA — Full-year daily assignments (4,272 rows)
# "Where is Dr. Sankin today?"  "What clinic am I at tomorrow?"
# ============================================================================

def _load_qgenda():
    global _qgenda_cache
    if _qgenda_cache is not None:
        return _qgenda_cache
    
    if not os.path.exists(QGENDA_PATH):
        return {"error": "QGenda data not available"}
    
    with open(QGENDA_PATH, encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # Index by person (multiple name forms) and by date
    by_person = defaultdict(list)
    by_date = defaultdict(list)
    by_task = defaultdict(list)
    all_names = set()
    
    for row in rows:
        first = row.get("Staff First Name", "").strip()
        last = row.get("Staff Last Name", "").strip()
        email = row.get("Staff Email", "").strip()
        date_str = row.get("Schedule Date", "").strip()
        task = row.get("Task Name", "").strip()
        
        full_name = f"{first} {last}"
        key = full_name.lower()
        
        entry = {"name": full_name, "first": first, "last": last, "email": email, "date": date_str, "task": task}
        
        # Index under multiple keys for fuzzy lookup
        by_person[key].append(entry)
        by_person[first.lower()].append(entry)
        by_person[last.lower()].append(entry)
        all_names.add(full_name)
        
        by_date[date_str].append(entry)
        by_task[task].append(entry)
    
    _qgenda_cache = {
        "by_person": dict(by_person),
        "by_date": dict(by_date),
        "by_task": dict(by_task),
        "all_names": sorted(all_names),
        "total_rows": len(rows),
    }
    return _qgenda_cache


def qgenda_today(name=None):
    """Get today's schedule. If name provided, filter for that person."""
    data = _load_qgenda()
    if isinstance(data, dict) and "error" in data:
        return data
    
    today = date.today()
    qfmt = f"{today.month}-{today.day}-{str(today.year)[-2:]}"
    
    if name:
        return qgenda_person_day(name, qfmt)
    
    entries = data["by_date"].get(qfmt, [])
    if not entries:
        return {"date": qfmt, "note": "No schedule data for today (weekend or holiday)", "entries": []}
    
    # Group by task
    by_task = defaultdict(list)
    for e in entries:
        by_task[e["task"]].append(e["name"])
    
    return {
        "date": qfmt,
        "total": len(entries),
        "summary": {task: {"count": len(names), "people": names[:10]} for task, names in sorted(by_task.items(), key=lambda x: -len(x[1]))},
        "entries": entries[:30],
    }


def qgenda_person_day(name: str, date_str: str = None):
    """Get a person's assignments on a specific date."""
    data = _load_qgenda()
    if isinstance(data, dict) and "error" in data:
        return data
    
    if date_str is None:
        today = date.today()
        date_str = f"{today.month}-{today.day}-{str(today.year)[-2:]}"
    
    name_lower = name.lower().strip()
    results = []
    
    # Check all indices for this name
    for key in [name_lower, name_lower.replace("dr. ", ""), name_lower.replace("dr ", "")]:
        entries = data["by_person"].get(key, [])
        for e in entries:
            if e["date"] == date_str:
                results.append(e)
    
    return {"name": name, "date": date_str, "assignments": results, "count": len(results)}


def qgenda_today_task(task_name: str):
    """Get all people doing a specific task today. 'Who's at the Stone Clinic?'"""
    data = _load_qgenda()
    if isinstance(data, dict) and "error" in data:
        return data
    
    today = date.today()
    qfmt = f"{today.month}-{today.day}-{str(today.year)[-2:]}"
    
    task_lower = task_name.lower().strip()
    matches = []
    for e in data["by_date"].get(qfmt, []):
        if task_lower in e["task"].lower():
            matches.append(e)
    
    return {"task": task_name, "date": qfmt, "people": [m["name"] for m in matches], "count": len(matches)}


def qgenda_person_upcoming(name: str, days: int = 7):
    """Get a person's upcoming schedule for the next N days."""
    data = _load_qgenda()
    if isinstance(data, dict) and "error" in data:
        return data
    
    name_lower = name.lower().strip()
    today = date.today()
    end = today + timedelta(days=days)
    
    results = []
    for key in [name_lower, name_lower.replace("dr. ", ""), name_lower.replace("dr ", "")]:
        for e in data["by_person"].get(key, []):
            # Parse date
            parts = e["date"].split("-")
            if len(parts) == 3:
                try:
                    d = date(2000 + int(parts[2]), int(parts[0]), int(parts[1]))
                    if today <= d <= end:
                        results.append({"date": e["date"], "day": d.strftime("%A"), "task": e["task"]})
                except:
                    pass
    
    results.sort(key=lambda x: x["date"])
    return {"name": name, "days": days, "assignments": results, "count": len(results)}


# ============================================================================
# CALL SCHEDULE — Attending call coverage (from xlsx)
# ============================================================================
# NOTE: call_today() and call_person() have been removed.
# Use vapi_data.schedule_today() and vapi_data.schedule_person() instead.
# schedule_by_date(), call_weekend(), and call_month() remain here.

def _load_schedule():
    global _schedule_cache
    if _schedule_cache is not None:
        return _schedule_cache
    
    import openpyxl
    wb = openpyxl.load_workbook(SCHEDULE_PATH, data_only=True)
    data = {}
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        rows = []
        for r in range(2, ws.max_row + 1):
            dv = ws.cell(r, 1).value
            if isinstance(dv, datetime):
                ds = dv.strftime("%Y-%m-%d")
            elif isinstance(dv, date):
                ds = dv.strftime("%Y-%m-%d")
            else:
                ds = str(dv or "").strip()[:10]
            rows.append({
                "date": ds,
                "day": str(ws.cell(r, 2).value or ""),
                "primary": str(ws.cell(r, 3).value or "").strip(),
                "backup": str(ws.cell(r, 4).value or "").strip(),
                "peds": str(ws.cell(r, 5).value or "").strip(),
                "primary_clean": str(ws.cell(r, 3).value or "").strip().split("(")[0].strip().split(",")[0].strip(),
                "backup_clean": str(ws.cell(r, 4).value or "").strip().split("(")[0].strip().split(",")[0].strip(),
                "peds_clean": str(ws.cell(r, 5).value or "").strip().split("(")[0].strip().split(",")[0].strip(),
            })
        data[sheet_name.lower()] = rows
    _schedule_cache = data
    return data


def call_weekend():
    """Get the upcoming weekend block (Fri-Mon)."""
    sched = _load_schedule()
    today = date.today()
    wd = today.weekday()
    if wd < 4:
        days_to = 4 - wd
    else:
        days_to = 0
    fri = today + timedelta(days=days_to)
    dates = [(fri + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(4)]
    result = {"dates": dates}
    for campus, rows in sched.items():
        campus_data = []
        for row in rows:
            if row["date"] in dates:
                campus_data.append({
                    "date": row["date"], "day": row["day"],
                    "primary": row["primary"] or "—",
                    "backup": row["backup"] or "—",
                    "peds": row["peds"] or "—",
                })
        result[campus.lower()] = campus_data
    return result


def call_month(name: str):
    """Get a person's upcoming 60-day call schedule."""
    sched = _load_schedule()
    name = name.lower().strip()
    today_str = date.today().strftime("%Y-%m-%d")
    cutoff = (date.today() + timedelta(days=60)).strftime("%Y-%m-%d")
    results = []
    for campus, rows in sched.items():
        for row in rows:
            if row["date"] < today_str or row["date"] > cutoff:
                continue
            for role in ["primary_clean", "backup_clean", "peds_clean"]:
                val = row[role]
                if val and name in val.lower():
                    results.append({
                        "campus": campus.title(), "date": row["date"],
                        "day": row["day"], "role": role.replace("_clean", ""),
                    })
                    break
    return {"results": results, "total": len(results)}


def schedule_by_date(date_str: str) -> dict:
    """Get call coverage for a specific date across all campuses."""
    sched = _load_schedule()
    result = {"date": date_str, "campuses": {}}
    for campus, rows in sched.items():
        for row in rows:
            if row["date"] == date_str:
                result["campuses"][campus.title()] = {
                    "primary": row["primary"] or "—",
                    "backup": row["backup"] or "—",
                    "peds": row["peds"] or "—",
                }
                break
    return result if result["campuses"] else {"date": date_str, "note": "No data for this date. Schedule covers July 2026 through January 2027."}


# ============================================================================
# GME — Resident reimbursement balances
# ============================================================================

def gme_balance(name: str):
    """Get a resident's GME balance. Case-insensitive, partial match."""
    if not os.path.exists(GME_PATH):
        return {"error": "GME data file not found"}
    
    import openpyxl
    try:
        wb = openpyxl.load_workbook(GME_PATH, data_only=True)
    except Exception as e:
        return {"error": f"Could not open GME file: {e}"}
    
    ws = wb["Sheet 2025-2026"]
    name_lower = name.lower().strip()
    
    total = 0.0
    txn_count = 0
    transactions = []
    matched_name = None
    
    for r in range(2, ws.max_row + 1):
        row_name = str(ws.cell(r, 1).value or "").strip()
        if not row_name:
            continue
        rl = row_name.lower()
        
        if name_lower == rl or name_lower in rl or rl in name_lower:
            if matched_name is None:
                matched_name = row_name
            amount = ws.cell(r, 5).value
            desc = str(ws.cell(r, 4).value or "")[:60]
            ds = ws.cell(r, 3).value or ws.cell(r, 2).value
            date_str = ds.strftime("%Y-%m-%d") if isinstance(ds, datetime) else str(ds or "?")
            
            if amount and isinstance(amount, (int, float)):
                total += abs(amount)
                txn_count += 1
                transactions.append({"date": date_str, "description": desc, "amount": round(abs(amount), 2)})
    
    if matched_name is None:
        return {"error": f"No GME records found for '{name}'"}
    
    remaining = max(0, GME_CAP - min(total, GME_CAP))
    return {
        "name": matched_name, "total_spent": round(total, 2),
        "remaining": round(remaining, 2), "cap": GME_CAP,
        "transaction_count": txn_count,
        "recent_transactions": sorted(transactions, key=lambda x: x["date"], reverse=True)[:5],
    }


# ============================================================================
# STAFF DIRECTORY (from sick-call associates)
# ============================================================================

def _load_staff():
    global _staff_cache
    if _staff_cache is not None:
        return _staff_cache
    
    if not os.path.exists(STAFF_PATH):
        return {"error": "Staff data not found"}
    
    with open(STAFF_PATH, encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        staff = []
        for row in reader:
            name = row.get("Employee Name", "").strip()
            email = row.get("Email", "").strip()
            phone = row.get("Phone", "").strip()
            location = row.get("Location Code", "").strip()
            emp_id = row.get("Employee ID", "").strip()
            
            # Parse "Last, First" format
            parts = name.split(",")
            if len(parts) >= 2:
                first = parts[1].strip().split()[0] if parts[1].strip() else ""
                last = parts[0].strip()
                display = f"{first} {last}"
            else:
                first = ""
                last = name
                display = name
            
            staff.append({
                "display_name": display,
                "first": first.lower(),
                "last": last.lower(),
                "full_lower": display.lower(),
                "email": email,
                "phone": phone,
                "location": location,
                "employee_id": emp_id,
            })
    
    _staff_cache = staff
    return staff


def staff_lookup(name: str):
    """Find a staff member by name."""
    staff = _load_staff()
    if isinstance(staff, dict) and "error" in staff:
        return staff
    
    name_lower = name.lower().strip()
    results = []
    for s in staff:
        if name_lower in s["full_lower"] or name_lower in s["first"] or name_lower in s["last"]:
            results.append({k: v for k, v in s.items() if k in ("display_name", "email", "phone", "location", "employee_id")})
    
    return {"results": results[:10], "count": len(results)}


def staff_by_location(location: str):
    """Find all staff at a location."""
    staff = _load_staff()
    if isinstance(staff, dict) and "error" in staff:
        return staff
    
    loc_lower = location.lower().strip()
    results = [s for s in staff if loc_lower in s["location"].lower()]
    
    return {"location": location, "staff": [s["display_name"] for s in results], "count": len(results)}
