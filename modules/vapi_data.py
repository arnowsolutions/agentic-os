"""Vapi data module — schedule, GME, and operational data queries."""
from datetime import date
from modules import vapi_unified

def schedule_today() -> dict:
    today = date.today().strftime("%Y-%m-%d")
    result = vapi_unified.schedule_by_date(today)
    if result.get("note"):
        return {"date": today, "note": "No data for today. Schedule covers July 2026 through January 2027."}
    return result

def schedule_weekend() -> dict:
    return vapi_unified.call_weekend()

def schedule_person(name: str) -> dict:
    sched = vapi_unified._load_schedule()
    name_lower = name.lower().strip()
    results = []
    for campus, rows in sched.items():
        for row in rows:
            for key in ("primary_clean", "backup_clean", "peds_clean"):
                val = row.get(key, "")
                if val and name_lower in val.lower():
                    results.append({"campus": campus.title(), "date": row["date"], "day": row["day"], "role": key.replace("_clean", "")})
                    break
    return {"results": results, "total": len(results)}

def schedule_month(name: str) -> dict:
    return vapi_unified.call_month(name)

def gme_balance_for(name: str) -> dict:
    return vapi_unified.gme_balance(name)
