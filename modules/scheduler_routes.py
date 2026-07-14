"""
Agentic OS — Scheduler Routes
Extracted from server.py Phase 9 module extraction.
"""
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from modules.config import get_settings

router = APIRouter(prefix="/api/scheduler", tags=["scheduler"])

# ─── Models ──────────────────────────────────────────────────────

class ScheduleJobRequest(BaseModel):
    name: str
    skill: str
    cron: str
    enabled: bool = True

# ─── Helpers ─────────────────────────────────────────────────────

def _get_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()

def _append_audit(base_dir: Path, entry: dict):
    audit_file = base_dir / "audit" / "audit.log"
    audit_file.parent.mkdir(parents=True, exist_ok=True)
    entry["timestamp"] = _get_timestamp()
    entry["id"] = str(uuid.uuid4())[:8]
    with open(audit_file, "a") as f:
        f.write(json.dumps(entry) + "\n")

def _get_base_dir() -> Path:
    settings = get_settings()
    return settings.BASE_DIR

# ─── Routes ──────────────────────────────────────────────────────

@router.get("/jobs")
def list_jobs():
    base = _get_base_dir()
    jobs_dir = base / "scheduler" / "jobs"
    if not jobs_dir.exists():
        return []
    jobs = []
    for f in sorted(jobs_dir.glob("*.json")):
        try:
            jobs.append(json.loads(f.read_text()))
        except (json.JSONDecodeError, Exception):
            pass
    return jobs


@router.post("/jobs")
def create_job(job: ScheduleJobRequest):
    base = _get_base_dir()
    jobs_dir = base / "scheduler" / "jobs"
    jobs_dir.mkdir(parents=True, exist_ok=True)
    job_data = {
        "id": str(uuid.uuid4())[:8],
        "name": job.name,
        "skill": job.skill,
        "cron": job.cron,
        "enabled": job.enabled,
        "created": _get_timestamp(),
        "last_run": None,
        "next_run": None,
    }
    safe_name = job.name.replace(" ", "_").replace("/", "_")
    (jobs_dir / f"{safe_name}.json").write_text(
        json.dumps(job_data, indent=2)
    )
    _append_audit(base, {"action": "job_created", "job": job.name})
    return job_data


@router.delete("/jobs/{job_id}")
def delete_job(job_id: str):
    base = _get_base_dir()
    jobs_dir = base / "scheduler" / "jobs"
    if not jobs_dir.exists():
        raise HTTPException(404, "No jobs directory found")
    for f in sorted(jobs_dir.glob("*.json")):
        try:
            data = json.loads(f.read_text())
        except (json.JSONDecodeError, Exception):
            continue
        if data.get("id") == job_id:
            f.unlink()
            _append_audit(base, {"action": "job_deleted", "job_id": job_id})
            return {"status": "deleted"}
    raise HTTPException(404, "Job not found")
