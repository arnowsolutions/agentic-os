"""
Agentic OS — CRM Module
CRM contacts management, access logging, and GME reimbursement tracking.
Extracted from server.py for maintainability.
"""
import csv as _csv_module
import io as _io
import json
import uuid as _uuid
import time as _time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from modules.config import get_settings

router = APIRouter(prefix="/api/crm", tags=["crm"])

# ─── Settings-based Paths ─────────────────────────────────────

def _get_crm_paths():
    settings = get_settings()
    crm_file = settings.CRM_PATH
    # Place access log in same directory as CRM file
    crm_access_log = crm_file.parent / "crm_access_log.json"
    return crm_file, crm_access_log

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
        _, crm_access_log = _get_crm_paths()
        crm_access_log.parent.mkdir(parents=True, exist_ok=True)
        entries = []
        if crm_access_log.exists():
            try:
                entries = json.loads(crm_access_log.read_text())
                if not isinstance(entries, list):
                    entries = []
            except:
                entries = []
        cutoff = now - (CRM_ACCESS_LOG_DAYS * 86400)
        entries = [e for e in entries if e.get("timestamp", 0) >= cutoff]
        entries.append(entry)
        if len(entries) > 5000:
            entries = entries[-5000:]
        crm_access_log.write_text(json.dumps(entries, indent=2))
    except Exception as e:
        print(f"CRM access log error: {e}")

def _load_crm():
    """Load contacts from Supabase Postgres, fall back to JSON file."""
    try:
        from modules.crm_db import get_contacts as _db_contacts
        db_contacts = _db_contacts()
        if db_contacts:
            return db_contacts
    except Exception:
        pass
    crm_file, _ = _get_crm_paths()
    if crm_file.exists():
        try:
            return json.loads(crm_file.read_text())
        except:
            return []
    return []

def _save_crm(contacts):
    crm_file, _ = _get_crm_paths()
    crm_file.parent.mkdir(parents=True, exist_ok=True)
    crm_file.write_text(json.dumps(contacts, indent=2))

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
        _, crm_access_log = _get_crm_paths()
        if crm_access_log.exists():
            entries = json.loads(crm_access_log.read_text())
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
        _, crm_access_log = _get_crm_paths()
        crm_access_log.write_text("[]")
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


# ─── Email Groups (Grand Rounds / Resident Conference) ────────────

EMAIL_GROUPS_FILE = Path(__file__).resolve().parent.parent / "data" / "email_groups.json"

DEFAULT_EMAIL_GROUPS = {
    "grand_rounds": {
        "label": "Grand Rounds (Fridays)",
        "emails": [],
        "test_mode": True,
        "test_email": "sfrasier@montefiore.org",
    },
    "resident_conference": {
        "label": "Resident Conference (Mondays)",
        "emails": [],
        "test_mode": True,
        "test_email": "sfrasier@montefiore.org",
    },
}


def _load_email_groups():
    if EMAIL_GROUPS_FILE.exists():
        with open(EMAIL_GROUPS_FILE) as f:
            return json.load(f)
    _save_email_groups(DEFAULT_EMAIL_GROUPS)
    return dict(DEFAULT_EMAIL_GROUPS)


def _save_email_groups(data):
    EMAIL_GROUPS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(EMAIL_GROUPS_FILE, "w") as f:
        json.dump(data, f, indent=2)


class EmailGroupUpdate(BaseModel):
    emails: list[str] | None = None
    test_mode: bool | None = None
    test_email: str | None = None
    attendance_link: str | None = None


@router.get("/email-groups")
def get_email_groups():
    return _load_email_groups()


@router.put("/email-groups/{group_key}")
def update_email_group(group_key: str, update: EmailGroupUpdate):
    if group_key not in DEFAULT_EMAIL_GROUPS:
        raise HTTPException(404, f"Unknown group: {group_key}")
    data = _load_email_groups()
    if update.emails is not None:
        data[group_key]["emails"] = update.emails
    if update.test_mode is not None:
        data[group_key]["test_mode"] = update.test_mode
    if update.test_email is not None:
        data[group_key]["test_email"] = update.test_email
    if update.attendance_link is not None:
        data[group_key]["attendance_link"] = update.attendance_link
    _save_email_groups(data)
    return data[group_key]


# ─── Archive ───────────────────────────────────────────────────

@router.patch("/contacts/{contact_id}/archive")
def archive_contact(contact_id: str, archived: bool = True):
    contacts = _load_crm()
    for c in contacts:
        if c.get("id") == contact_id:
            cname = f"{c.get('firstName', '')} {c.get('lastName', '')}".strip()
            c["archived"] = archived
            _save_crm(contacts)
            _log_crm_access(
                action="archive" if archived else "unarchive",
                contact_id=contact_id, contact_name=cname,
                endpoint=f"/api/crm/contacts/{contact_id}/archive",
                method="PATCH", agent="dashboard"
            )
            return {"success": True, "archived": archived}
    raise HTTPException(status_code=404, detail="Contact not found")

@router.post("/contacts/bulk-archive")
def bulk_archive_contacts(graduation_year: str = "", category: str = "Resident"):
    """Archive all contacts matching graduation_year and category.
    Default: archives Residents whose graduationYear matches the current year (2026).
    Pass graduation_year='all' to archive all Residents regardless of year."""
    from datetime import datetime as _dt
    contacts = _load_crm()
    if not graduation_year:
        graduation_year = str(_dt.now().year)
    archived = []
    for c in contacts:
        if c.get("archived"):
            continue
        if category and c.get("category") != category:
            continue
        if graduation_year != "all":
            gy = str(c.get("graduationYear", "")).strip()
            if gy != graduation_year:
                continue
        c["archived"] = True
        cname = f"{c.get('firstName', '')} {c.get('lastName', '')}".strip()
        archived.append({"id": c.get("id"), "name": cname})
    if archived:
        _save_crm(contacts)
        for a in archived:
            _log_crm_access(
                action="bulk_archive", contact_id=a["id"], contact_name=a["name"],
                endpoint="/api/crm/contacts/bulk-archive", method="POST", agent="dashboard"
            )
    return {"success": True, "archived_count": len(archived), "archived": archived}

# ─── CSV Export ────────────────────────────────────────────────

@router.get("/contacts/export/csv")
def export_contacts_csv(include_archived: bool = False):
    """Export all contacts as CSV."""
    contacts = _load_crm()
    if not include_archived:
        contacts = [c for c in contacts if not c.get("archived")]
    if not contacts:
        return {"error": "No contacts to export"}
    fieldnames = ["id", "firstName", "lastName", "category", "pgy", "email",
                  "mobile", "pager", "ezid", "npi", "address", "proximity",
                  "birthday", "programStart", "urologyStart", "graduationYear",
                  "parkingChip", "archived"]
    output = _io.StringIO()
    writer = _csv_module.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    for c in contacts:
        writer.writerow({k: c.get(k, "") for k in fieldnames})
    csv_text = output.getvalue()
    return {"csv": csv_text, "count": len(contacts)}

# ─── Resend Invite ─────────────────────────────────────────────

class ResendInviteRequest(BaseModel):
    date: str  # YYYY-MM-DD
    group: str = "grand_rounds"  # grand_rounds or resident_conference
    test_mode: bool = True  # True = send only to test_email

@router.post("/email-groups/{group_key}/resend")
def resend_invite(group_key: str, req: ResendInviteRequest):
    """Queue a calendar invite resend for a specific conference date.
    Triggers the existing send script for the given date.
    Supports test_mode and passes attendance_link from email_groups.json."""
    import subprocess, sys
    if group_key not in ("grand_rounds", "resident_conference"):
        raise HTTPException(400, f"Unknown group: {group_key}")
    data = _load_email_groups()
    group = data.get(group_key)
    if not group:
        raise HTTPException(400, "Group not configured")
    if not group.get("emails") and not req.test_mode:
        raise HTTPException(400, "No recipients configured for this group")
    
    # Pick the right script
    if group_key == "resident_conference":
        script_path = Path(__file__).resolve().parent.parent / "send_monday_sasp_email.py"
    else:
        script_path = Path(__file__).resolve().parent.parent / "send_grand_rounds_email.py"
    
    if not script_path.exists():
        raise HTTPException(500, f"{script_path.name} not found")
    
    recipients = group["emails"]
    test_email = group.get("test_email", "sfrasier@montefiore.org")
    
    env = {**__import__("os").environ,
           "TEST_MODE": "true" if req.test_mode else "false",
           "TEST_EMAIL": test_email,
           "PROD_RECIPIENTS": ",".join(recipients),
           "SINGLE_DATE": req.date}
    try:
        result = subprocess.run(
            [sys.executable, str(script_path), "--date", req.date],
            capture_output=True, text=True, timeout=60, env=env
        )
        return {
            "success": result.returncode == 0,
            "output": result.stdout.strip()[-500:],
            "error": result.stderr.strip()[-200:] if result.returncode != 0 else "",
            "recipients": 1 if req.test_mode else len(recipients),
            "test_mode": req.test_mode,
            "attendance_link": group.get("attendance_link", ""),
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(504, "Resend timed out after 60s")
    except Exception as e:
        raise HTTPException(500, str(e))
