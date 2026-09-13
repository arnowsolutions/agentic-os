"""
Agentic OS — AI-generalist layer routes (Stage 5).

Endpoints:
  GET  /api/skill-manifest           → machine contract (cached manifest)
  POST /api/skill-manifest/regenerate → rebuild from NAV_CONFIG + sources
  GET  /api/agent-activity           → unified agent-activity feed for Today:
                                        audit events (chat/skill/run) + cron
                                        job next/last run + router stats
"""
import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter

from modules.config import get_settings
from modules import skill_manifest, ssot

router = APIRouter(prefix="/api", tags=["generalist"])


@router.get("/skill-manifest")
def get_skill_manifest():
    m = skill_manifest.load()
    out = {
        "version": m.get("version"),
        "generated_at": m.get("generated_at"),
        "page_count": len(m.get("pages", {})),
        "route_count": len(m.get("api_routes", [])),
        "pages": m.get("pages", {}),
    }
    out.update(ssot.stamp("data/skill-manifest.json", _manifest_dt()))
    return out


@router.get("/skill-manifest/page/{page}")
def get_skill_manifest_page(page: str):
    return skill_manifest.page_context(page)


@router.post("/skill-manifest/regenerate")
def regenerate_skill_manifest():
    m = skill_manifest.generate(force=True)
    return {
        "status": "ok",
        "generated_at": m.get("generated_at"),
        "page_count": len(m.get("pages", {})),
        "route_count": len(m.get("api_routes", [])),
    }


def _manifest_dt():
    p = get_settings().BASE_DIR / "data" / "skill-manifest.json"
    if p.exists():
        return datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
    return None


def _audit_events(limit_events: int = 40) -> list:
    """Recent normalized agent events from audit.log (newest first)."""
    audit_file = get_settings().BASE_DIR / "audit" / "audit.log"
    if not audit_file.exists():
        return []
    actions = {"chat_message", "skill_run", "agent_run", "task_routed", "scheduler_run"}
    events = []
    try:
        lines = audit_file.read_text().strip().splitlines()
    except Exception:
        return []
    for line in reversed(lines[-4000:]):
        try:
            e = json.loads(line)
        except Exception:
            continue
        if e.get("action") in actions:
            meta = e.get("metadata") or {}
            events.append({
                "ts": e.get("timestamp"),
                "kind": e.get("action"),
                "agent": e.get("agent") or e.get("source") or "—",
                "status": e.get("status", "success"),
                "summary": (meta.get("msg_preview") or meta.get("skill") or
                            meta.get("task") or meta.get("job") or ""),
                "page": meta.get("page", ""),
            })
        if len(events) >= limit_events:
            break
    return events


def _cron_jobs() -> dict:
    """Enabled cron jobs with name + last/next run for the activity feed."""
    for p in [Path("/home/hermeswebui/.hermes/cron/jobs.json"),
              Path("/var/lib/docker/volumes/hermes-webui-gsga_hermes-home/_data/cron/jobs.json")]:
        if p.exists():
            try:
                payload = json.loads(p.read_text())
                jobs = payload.get("jobs", [])
                return {
                    "count": len(jobs),
                    "enabled": sum(1 for j in jobs if j.get("enabled")),
                    "items": [{
                        "name": j.get("name") or j.get("id"),
                        "enabled": bool(j.get("enabled")),
                        "schedule": j.get("schedule") or j.get("cron") or "",
                        "last_run": j.get("last_run") or j.get("last_delivery"),
                    } for j in jobs],
                    "source": str(p),
                }
            except Exception:
                pass
    return {"count": 0, "enabled": 0, "items": [], "source": "unavailable"}


@router.get("/agent-activity")
def agent_activity():
    """One feed: what the AI workers did recently — chat turns, skill runs,
    router decisions, cron schedule — for the Today activity rail."""
    events = _audit_events()
    cron = _cron_jobs()
    by_kind = {}
    for e in events:
        by_kind[e["kind"]] = by_kind.get(e["kind"], 0) + 1
    return {
        "events": events,
        "counts": by_kind,
        "cron": {k: cron[k] for k in ("count", "enabled")},
        "recent_cron": [c for c in cron["items"] if c["enabled"]][:8],
    }
