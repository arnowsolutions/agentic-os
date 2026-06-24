"""
Agentic OS — CRM Module
CRM contacts management, access logging, and GME reimbursement tracking.
Extracted from server.py for maintainability.
"""
import json
import uuid as _uuid
import time as _time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/crm", tags=["crm"])

# ─── Paths ────────────────────────────────────────────────────

CRM_FILE = Path("/home/hermeswebui/.hermes/crm_contacts.json")
CRM_ACCESS_LOG = Path("/home/hermeswebui/.hermes/crm_access_log.json")
CRM_ACCESS_LOG_DAYS = 30
GME_ANNUAL_LIMIT = 1250

# ─── AY Filtering ────────────────────────────────────────────────
CURRENT_AY = "2025-26"

def _compute_ay(date_str: str) -> str:
    """Compute academic year from a date string (MM/DD/YYYY format).
    AY runs July 1 - June 30.
    """
    if not date_str:
        return CURRENT_AY
    try:
        parts = date_str.split("/")
        if len(parts) == 3:
            month = int(parts[0])
            year = int(parts[2])
            if month >= 7:
                return f"{year}-{str(year+1)[-2:]}"
            else:
                return f"{year-1}-{str(year)[-2:]}"
    except (ValueError, IndexError):
        pass
    return CURRENT_AY

def _ay_filter(reimbursements, ay: str) -> list:
    """Filter reimbursements by academic year.
    
    AY runs July 1 - June 30. Current is 2025-26.
    - ay='all': return all (capped per-resident by GME_ANNUAL_LIMIT)
    - ay='2025-26' etc: only transactions from that AY
    """
    if not ay or ay == "all":
        return reimbursements
    return [rem for rem in reimbursements if rem.get("ay") == ay]

def _calc_total_used(reimbursements, ay: str) -> float:
    """Calculate total used amount for a resident, filtered by AY, capped."""
    filtered = _ay_filter(reimbursements, ay)
    raw = sum(rem.get("amount", 0) for rem in filtered)
    return round(min(raw, GME_ANNUAL_LIMIT), 2)

# ─── Helpers ──────────────────────────────────────────────────

def _log_crm_access(action: str, contact_id: str = "", contact_name: str = "",
                    endpoint: str = "", method: str = "", agent: str = "dashboard"):
    now = _time.time()
    dt = datetime.now(timezone.utc)
    entry = {
        "timestamp": now,
        "datetime": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "action": action,
        "contact_id": contact_id,
        "contact_name": contact_name,
        "endpoint": endpoint,
        "method": method,
        "agent": agent,
    }
    try:
        CRM_ACCESS_LOG.parent.mkdir(parents=True, exist_ok=True)
        entries = []
        if CRM_ACCESS_LOG.exists():
            try:
                entries = json.loads(CRM_ACCESS_LOG.read_text())
                if not isinstance(entries, list):
                    entries = []
            except:
                entries = []
        cutoff = now - (CRM_ACCESS_LOG_DAYS * 86400)
        entries = [e for e in entries if e.get("timestamp", 0) >= cutoff]
        entries.append(entry)
        if len(entries) > 5000:
            entries = entries[-5000:]
        CRM_ACCESS_LOG.write_text(json.dumps(entries, indent=2))
    except Exception as e:
        print(f"CRM access log error: {e}")

def _load_crm():
    if CRM_FILE.exists():
        try:
            return json.loads(CRM_FILE.read_text())
        except:
            return []
    return []

def _save_crm(contacts):
    CRM_FILE.parent.mkdir(parents=True, exist_ok=True)
    CRM_FILE.write_text(json.dumps(contacts, indent=2))

# ─── Pydantic Models ──────────────────────────────────────────

class ReimbursementRequest(BaseModel):
    resident_id: str
    date: str
    amount: float
    category: str
    status: str = "paid"

# ─── Routes: Access Log ────────────────────────────────────────

@router.get("/access-log")
def crm_access_log():
    try:
        if CRM_ACCESS_LOG.exists():
            entries = json.loads(CRM_ACCESS_LOG.read_text())
            if not isinstance(entries, list):
                entries = []
            entries.reverse()
            return {"entries": entries[:50]}
        return {"entries": []}
    except Exception as e:
        return {"entries": [], "error": str(e)}

@router.post("/access-log/clear")
def crm_access_log_clear(confirm: bool = False):
    if not confirm:
        return {"success": False, "error": "confirm=true parameter required"}
    try:
        CRM_ACCESS_LOG.write_text("[]")
        return {"success": True, "message": "Access log cleared"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ─── Routes: Contacts CRUD ─────────────────────────────────────

@router.get("/contacts")
def crm_list():
    contacts = _load_crm()
    for c in contacts:
        _log_crm_access(
            action="read",
            contact_id=c.get("id", ""),
            contact_name=f"{c.get('firstName', '')} {c.get('lastName', '')}".strip(),
            endpoint="/api/crm/contacts",
            method="GET",
            agent="dashboard"
        )
    return {"contacts": contacts}

@router.post("/contacts")
def crm_add(data: dict):
    contact = {k: (v.strip() if isinstance(v, str) else v) for k, v in data.items()}
    contact["id"] = str(_uuid.uuid4())[:8]
    cid = contact["id"]
    cname = f"{contact.get('firstName', '')} {contact.get('lastName', '')}".strip()
    contacts = _load_crm()
    contacts.append(contact)
    _save_crm(contacts)
    _log_crm_access(
        action="add", contact_id=cid, contact_name=cname,
        endpoint="/api/crm/contacts", method="POST", agent="dashboard"
    )
    return {"success": True, "id": contact["id"]}

@router.put("/contacts/{contact_id}")
def crm_update(contact_id: str, data: dict):
    contacts = _load_crm()
    for c in contacts:
        if c.get("id") == contact_id:
            cname = f"{c.get('firstName', '')} {c.get('lastName', '')}".strip()
            for k, v in data.items():
                c[k] = v.strip() if isinstance(v, str) else v
            _save_crm(contacts)
            _log_crm_access(
                action="write", contact_id=contact_id, contact_name=cname,
                endpoint=f"/api/crm/contacts/{contact_id}", method="PUT", agent="dashboard"
            )
            return {"success": True}
    raise HTTPException(status_code=404, detail="Contact not found")

@router.delete("/contacts/{contact_id}")
def crm_delete(contact_id: str):
    contacts = _load_crm()
    deleted_name = ""
    for c in contacts:
        if c.get("id") == contact_id:
            deleted_name = f"{c.get('firstName', '')} {c.get('lastName', '')}".strip()
            break
    new_contacts = [c for c in contacts if c.get("id") != contact_id]
    if len(new_contacts) == len(contacts):
        raise HTTPException(status_code=404, detail="Contact not found")
    _save_crm(new_contacts)
    _log_crm_access(
        action="delete", contact_id=contact_id, contact_name=deleted_name,
        endpoint=f"/api/crm/contacts/{contact_id}", method="DELETE", agent="dashboard"
    )
    return {"success": True}

# ─── Routes: GME Reimbursement ──────────────────────────────────

@router.get("/gme/summary")
def gme_summary(ay: str = CURRENT_AY):
    contacts = _load_crm()
    _log_crm_access(
        action="read", contact_id="", contact_name="GME Summary",
        endpoint="/api/crm/gme/summary", method="GET", agent="dashboard"
    )
    residents = [c for c in contacts if c.get("category") == "Resident"]
    total_pool = len(residents) * GME_ANNUAL_LIMIT
    total_used = 0
    residents_with_funds = 0
    for r in residents:
        used = _calc_total_used(r.get("reimbursements") or [], ay)
        total_used += used
        if used < GME_ANNUAL_LIMIT:
            residents_with_funds += 1
    return {
        "total_pool": total_pool,
        "total_used": total_used,
        "total_remaining": total_pool - total_used,
        "residents_with_funds": residents_with_funds,
        "total_residents": len(residents),
        "ay": ay,
    }

@router.get("/gme/residents")
def gme_residents(ay: str = CURRENT_AY):
    contacts = _load_crm()
    residents = [c for c in contacts if c.get("category") == "Resident"]
    for r in residents:
        cname = f"{r.get('firstName', '')} {r.get('lastName', '')}".strip()
        _log_crm_access(
            action="read", contact_id=r.get("id", ""), contact_name=cname,
            endpoint="/api/crm/gme/residents", method="GET", agent="dashboard"
        )
    result = []
    for r in residents:
        reimbursements = r.get("reimbursements") or []
        filtered_reims = _ay_filter(reimbursements, ay)
        total_used = _calc_total_used(reimbursements, ay)
        result.append({
            "id": r.get("id"), "firstName": r.get("firstName", ""),
            "lastName": r.get("lastName", ""), "pgy": r.get("pgy", ""),
            "email": r.get("email", ""), "total_used": total_used,
            "reimbursements": sorted(filtered_reims, key=lambda x: x.get("date", "")),
        })
    return {"residents": result, "ay": ay}

@router.post("/gme/reimbursement")
def gme_add_reimbursement(req: ReimbursementRequest):
    contacts = _load_crm()
    for c in contacts:
        if c.get("id") == req.resident_id:
            if c.get("category") != "Resident":
                return {"success": False, "error": "Contact is not a resident"}
            reimbursements = c.get("reimbursements") or []
            total_used = sum(rem.get("amount", 0) for rem in reimbursements)
            if total_used + req.amount > GME_ANNUAL_LIMIT:
                return {"success": False, "error": f"Exceeds remaining funds (${GME_ANNUAL_LIMIT - total_used:.2f})"}
            new_rem = {
                "date": req.date, "amount": req.amount,
                "category": req.category, "status": req.status,
                "ay": _compute_ay(req.date),
            }
            reimbursements.append(new_rem)
            c["reimbursements"] = reimbursements
            _save_crm(contacts)
            cname = f"{c.get('firstName', '')} {c.get('lastName', '')}".strip()
            _log_crm_access(
                action="write", contact_id=req.resident_id, contact_name=cname,
                endpoint="/api/crm/gme/reimbursement", method="POST", agent="dashboard"
            )
            return {"success": True, "remaining": GME_ANNUAL_LIMIT - total_used - req.amount}
    raise HTTPException(status_code=404, detail="Resident not found")
