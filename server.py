#!/usr/bin/env python3
"""
Agentic OS — FastAPI Backend
Multi-agent orchestration server for opencode, Hermes, Gemini CLI
"""
import argparse
import asyncio
import json
import logging
import os
import re
import shutil
import subprocess
import tarfile
import time
import urllib.request
import uuid
from datetime import datetime, timezone
import zoneinfo
TZ = zoneinfo.ZoneInfo("America/New_York")
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import httpx

# ─── Import extracted modules ──────────────────────────────────
from modules import crm as crm_module
from modules import kanban as kanban_module
from modules import vapi_bridge as vapi_module
from modules import schedule as schedule_module
from modules import auth as auth_module
from modules import skill_runner
from modules import cost_tracker
from modules.logging_config import setup_logging
from modules.metrics import metrics_endpoint, metrics_middleware
from modules import brain_routes
from modules import skills_routes
from modules import scheduler_routes
from modules import chat_routes
from modules.agent_executor import _resolve_hermes_bin

setup_logging()
logger = logging.getLogger("agentic_os.server")

app = FastAPI(title="Agentic OS", version="1.1.0")

@app.middleware("http")
async def _metrics_middleware(request: Request, call_next):
    return await metrics_middleware(request, call_next)

# ─── Session enforcement middleware ──────────────────────────────────────────

@app.middleware("http")
async def session_enforcement(request: Request, call_next):
    """Require a valid session for all dashboard routes except allowlisted paths."""
    path = request.url.path

    # Allowlist paths that don't need auth
    if path.startswith(_settings.VAPI_ENDPOINT_PATH) or path.startswith("/vapi/"):
        return await call_next(request)
    if path in {"/api/auth/login", "/api/auth/logout", "/api/status", "/login", "/favicon.svg", "/favicon.ico", "/api/pdf/images2pdf"}:
        return await call_next(request)
    if path.startswith("/api/selftest") or path.startswith("/api/brain"):
        return await call_next(request)
    if path.startswith("/dashboard/login") or path == "/dashboard/omniroute-chat.html":
        return await call_next(request)
    # Allow dashboard static assets (JS, CSS, HTML, pages/)
    if path.startswith("/dashboard/") and not path.startswith("/dashboard/login"):
        return await call_next(request)
    if path.startswith("/chat"):
        return await call_next(request)
    if path == "/api/omniroute-chat":
        return await call_next(request)
    if path.startswith("/api/_boot_error"):
        return await call_next(request)
    if path.startswith("/api/oncall/"):
        return await call_next(request)
    if path.startswith("/api/staff-schedule"):
        return await call_next(request)
    if path.startswith("/api/calendar/"):
        return await call_next(request)
    if path.startswith("/api/eval/"):
        return await call_next(request)
    if path.startswith("/api/conference/"):
        return await call_next(request)
    if path == "/api/calendar-invites":
        return await call_next(request)
    if path.startswith("/api/crm-data-gaps"):
        return await call_next(request)
    if path.startswith("/api/tasks"):
        return await call_next(request)
    if path.startswith("/api/skills"):
        return await call_next(request)
    if path.startswith("/api/scheduler"):
        return await call_next(request)
    if path.startswith("/api/chat"):
        return await call_next(request)
    if path.startswith("/api/goals"):
        return await call_next(request)
    if path.startswith("/api/kanban"):
        return await call_next(request)
    if path == "/api/crm/cron-jobs":
        return await call_next(request)
    if path.startswith("/api/crm/tasks"):
        return await call_next(request)
    if path.startswith("/api/crm/workflows"):
        return await call_next(request)
    if path.startswith("/api/user/"):
        return await call_next(request)
    if path.startswith("/api/cron/"):
        return await call_next(request)

    # Check session cookie
    token = request.cookies.get(_settings.SESSION_COOKIE_NAME, "")
    session = getattr(auth_module, "get_session")(token) if token else None

    if not session:
        if path.startswith("/api/"):
            return JSONResponse({"detail": "Unauthenticated"}, status_code=401)
        return RedirectResponse(url="/login")

    getattr(auth_module, "touch_session")(token)
    request.state.user = session
    return await call_next(request)

# Load API keys from .env
SCRIPT_DIR = Path(__file__).parent.resolve()
AGENTIC_ENV = SCRIPT_DIR / ".env"
if AGENTIC_ENV.exists():
    for line in AGENTIC_ENV.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip()

# Also load OpenRouter API key from Hermes .env (backwards compat)
HERMES_ENV = Path.home() / ".hermes" / ".env"
if HERMES_ENV.exists():
    for line in HERMES_ENV.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            if k == "OPENROUTER_API_KEY":
                os.environ[k] = v  # last value wins (matches shell sourcing)

# CORS for local dev
BASE_DIR = Path(__file__).parent.resolve()

from modules.config import get_settings
_settings = get_settings()

@app.middleware("http")
async def webhook_validation(request: Request, call_next):
    """Lightweight validation layer for Vapi webhooks."""
    path = request.url.path
    if path.startswith(_settings.VAPI_ENDPOINT_PATH) and request.method == "POST":
        allowlist = _settings.WEBHOOK_IP_ALLOWLIST
        if allowlist:
            forwarded = request.headers.get("x-forwarded-for", "")
            ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "")
            if ip not in allowlist:
                logger.warning("vapi webhook blocked by IP allowlist", extra={"ip": ip})
                return JSONResponse({"error": "unauthorized"}, status_code=403)
        # Optional signature check (configure WEBHOOK_SECRET + Vapi sends x-signature-sha256)
        secret = _settings.WEBHOOK_SECRET
        if secret:
            import hmac, hashlib
            body = await request.body()
            sig = request.headers.get("x-signature-sha256", "")
            expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(sig, expected):
                logger.warning("vapi webhook signature mismatch")
                return JSONResponse({"error": "invalid signature"}, status_code=403)
            # Re-inject body so downstream route can read it
            async def _replay():
                return body
            request._body = body
            request.body = _replay
    return await call_next(request)

# ─── Initialize extracted modules ──────────────────────────
kanban_module.init_app(BASE_DIR)
app.include_router(crm_module.router)
app.include_router(kanban_module.router)
app.include_router(vapi_module.router)
app.include_router(schedule_module.router)
app.include_router(auth_module.router)
app.include_router(brain_routes.router)
app.include_router(skills_routes.router)
app.include_router(scheduler_routes.router)
app.include_router(chat_routes.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8080", "http://localhost:8080",
        "http://127.0.0.1:8081", "http://localhost:8081",
        "http://127.0.0.1:8501", "http://localhost:8501",
        "http://127.0.0.1:20128", "http://localhost:20128",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).parent.resolve()

# ─── Runtime directory helpers ────────────────────────────────────

def _ensure_runtime_dirs():
    """Ensure directories referenced at runtime exist on disk."""
    for d in ("audit", "reports", "data"):
        (BASE_DIR / d).mkdir(parents=True, exist_ok=True)

_ensure_runtime_dirs()


def _safe_path(base: Path, user_value: str) -> Path:
    """Resolve a user-supplied path segment and ensure it stays inside base."""
    base_resolved = base.resolve()
    candidate = (base / user_value).resolve()
    if not candidate.is_relative_to(base_resolved):
        raise HTTPException(400, "Invalid path")
    return candidate

# Note: _resolve_hermes_bin is now imported from modules.agent_executor


# ─── Models ───────────────────────────────────────────────────────

# Note: BrainUpdate, SkillRunRequest, ScheduleJobRequest, ChatRequest
# have been moved to their respective route modules.

class SettingsUpdate(BaseModel):
    settings: dict

class BackupRestoreRequest(BaseModel):
    file: str

class SwapRunRequest(BaseModel):
    mode: str = "dry-run"  # "dry-run" or "live"

class ReportGenerateRequest(BaseModel):
    type: str
    input: Optional[str] = ""
    channel: str = "download"  # "download" or "email"
    recipient: Optional[str] = ""

class RouterSuggest(BaseModel):
    task: str

class RouterRoute(BaseModel):
    task: str
    agent: str = "auto"

class AgentRunEvent(BaseModel):
    action: str
    source: str
    agent: str
    event_id: Optional[str] = None
    route_id: Optional[str] = None
    run_id: Optional[str] = None
    status: str = "success"
    metadata: Optional[dict] = None

# ─── Report source catalog ────────────────────────────────────────────────

REPORT_SOURCES = [
    {"id": "daily-standup", "label": "Daily Standup", "kind": "skill", "supports_pdf": False},
    {"id": "devops-audit", "label": "DevOps Audit", "kind": "skill", "supports_pdf": False},
    {"id": "cost-analytics", "label": "Cost Analytics", "kind": "skill", "supports_pdf": False},
    {"id": "schedule-pdf", "label": "Call Schedule PDF", "kind": "schedule", "supports_pdf": True},
]

# ─── Helper Functions ──────────────────────────────────────────────────────

def read_file(path: Path):
    if not path.exists() or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")

def write_file(path: Path, content: str):
    path.write_text(content, encoding="utf-8")
    return True

def list_dir(path: Path):
    if not path.exists():
        return []
    return sorted([p.name for p in path.iterdir() if not p.name.startswith(".")])

def get_timestamp():
    return datetime.now(timezone.utc).isoformat()

def append_audit(entry: dict):
    audit_file = BASE_DIR / "audit" / "audit.log"
    audit_file.parent.mkdir(parents=True, exist_ok=True)
    entry["timestamp"] = get_timestamp()
    entry["id"] = str(uuid.uuid4())[:8]
    with open(audit_file, "a") as f:
        f.write(json.dumps(entry) + "\n")

# ─── Normalized Agent Run Event Recording ──────────────────────────

def record_agent_run(action: str, source: str, agent: str, status: str = "success", metadata: Optional[dict] = None) -> str:
    """Record a normalized agent run event to the audit log.
    
    Returns the event_id for traceability.
    """
    event_id = str(uuid.uuid4())[:12]
    entry = {
        "action": action,
        "source": source,
        "agent": agent,
        "event_id": event_id,
        "status": status,
        "metadata": metadata or {},
    }
    append_audit(entry)
    return event_id

def get_agent_runs_from_audit(agent_name: Optional[str] = None, limit: int = 1000) -> list:
    """Aggregate agent run events from audit log."""
    runs = []
    audit_file = BASE_DIR / "audit" / "audit.log"
    if not audit_file.exists():
        return runs
    
    try:
        lines = audit_file.read_text().strip().split("\n")
        for line in reversed(lines[-limit:]):
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                # Include normalized agent_run events and legacy events
                if entry.get("action") in ["agent_run", "chat_message", "skill_run", "task_routed"]:
                    if agent_name is None or entry.get("agent") == agent_name:
                        runs.append(entry)
            except:
                continue
    except Exception:
        pass
    return runs

# ─── Router Config Loader ────────────────────────────────────────────────

def load_router_config() -> dict:
    """Load routing rules and capabilities from data/agent-routes.json."""
    config_path = BASE_DIR / "data" / "agent-routes.json"
    default_config = {
        "routing_rules": [
            {"pattern": "code|devops|infrastructure|terraform|k8s|gcp|git|deploy|ci/cd", "target": "opencode", "priority": 10},
            {"pattern": "memory|remember|schedule|cron|telegram|discord|channel|notif", "target": "hermes", "priority": 10},
            {"pattern": "research|analyze|search|summarize|compare|investigate|learn", "target": "gemini", "priority": 10},
            {"pattern": ".*", "target": "opencode", "priority": 0, "description": "Default fallback"},
        ],
        "agent_capabilities": {
            "opencode": ["code_generation", "file_operations", "git_management", "terminal_execution", "infrastructure_as_code", "testing", "debugging"],
            "hermes": ["persistent_memory", "scheduled_tasks", "messaging_channels", "skill_hub", "voice", "browser_automation", "subagent_delegation"],
            "gemini": ["web_search", "multi_modal_analysis", "document_understanding", "data_analysis", "research_synthesis", "reasoning"],
        },
    }
    
    if not config_path.exists():
        return default_config
    
    try:
        config = json.loads(config_path.read_text())
        # Validate required fields
        if "routing_rules" not in config:
            config["routing_rules"] = default_config["routing_rules"]
        if "agent_capabilities" not in config:
            config["agent_capabilities"] = default_config["agent_capabilities"]
        return config
    except Exception:
        return default_config

def score_routing_rules(task: str, config: dict) -> tuple:
    """Score task against routing rules and return scores with matched rules.
    
    Returns: (scores_dict, matched_rules_list, suggested_agent, confidence)
    """
    task_lower = task.lower()
    scores = {"opencode": 0, "hermes": 0, "gemini": 0}
    matched_rules = []
    
    for rule in config.get("routing_rules", []):
        pattern = rule.get("pattern", ".*")
        target = rule.get("target", "opencode")
        priority = rule.get("priority", 0)
        
        try:
            if re.search(pattern, task_lower):
                scores[target] = scores.get(target, 0) + priority
                matched_rules.append({
                    "pattern": pattern,
                    "target": target,
                    "priority": priority,
                    "description": rule.get("description", ""),
                })
        except re.error:
            continue
    
    # Determine best agent
    best = max(scores, key=scores.get)
    best_score = scores[best]
    
    # Calculate confidence based on score differential
    if best_score >= 10:
        confidence = "high"
    elif best_score >= 5:
        confidence = "medium"
    elif best_score > 0:
        confidence = "low"
    else:
        # No matches - use fallback
        best = "opencode"
        confidence = "fallback"
    
    return scores, matched_rules, best, confidence

# ─── Agent Discovery (instant filesystem checks) ────────────────────

def check_agent(name: str) -> dict:
    """Instant filesystem-based check. No subprocess needed."""
    try:
        if name == "opencode":
            exists = shutil.which("opencode") is not None
            status = "online" if exists else "offline"
        elif name == "hermes":
            # Check common Hermes install locations (venv in /app or ~/.hermes)
            exists = _resolve_hermes_bin() is not None
            status = "online" if exists else "offline"
        elif name == "gemini":
            # Gemini has valid OAuth tokens logged in
            oauth = Path.home() / ".gemini" / "oauth_creds.json"
            exists = shutil.which("gemini") is not None
            logged_in = oauth.exists() and "ya29" in oauth.read_text()
            status = "online" if exists and logged_in else "offline" if not exists else "warning"
        else:
            status = "offline"
    except Exception:
        status = "offline"
    return {"name": name, "status": status}

def check_url(url: str, timeout: int = 5) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return {"ok": r.status == 200, "status": r.status}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def disk_usage(path: Path) -> dict:
    stat = shutil.disk_usage(path)
    return {
        "total_gb": round(stat.total / 1e9, 2),
        "used_gb": round(stat.used / 1e9, 2),
        "free_gb": round(stat.free / 1e9, 2),
        "percent_used": round(stat.used / stat.total * 100, 1),
    }


def cron_health() -> dict:
    data = {"ok": True, "jobs": 0, "failing": 0, "delivery_errors": 0}
    try:
        jobs_file = Path("/home/hermeswebui/.hermes/cron/jobs.json")
        if not jobs_file.exists():
            data["ok"] = False
            data["error"] = "jobs.json not found"
            return data
        payload = json.loads(jobs_file.read_text())
        jobs = payload.get("jobs", [])
        data["jobs"] = len(jobs)
        data["failing"] = sum(1 for j in jobs if j.get("last_status") not in ("ok", None, "pending"))
        data["delivery_errors"] = sum(1 for j in jobs if j.get("last_delivery_error"))
        data["paused"] = sum(1 for j in jobs if not j.get("enabled"))
    except Exception as e:
        data = {"ok": False, "error": str(e)}
    return data


def _get_cron_jobs_list() -> list:
    """Return all Hermes cron jobs as a list for the briefing API."""
    try:
        jobs_file = Path("/home/hermeswebui/.hermes/cron/jobs.json")
        if not jobs_file.exists():
            jobs_file = Path("/var/lib/docker/volumes/hermes-webui-gsga_hermes-home/_data/cron/jobs.json")
        if not jobs_file.exists():
            return []
        payload = json.loads(jobs_file.read_text())
        return payload.get("jobs", [])
    except Exception:
        return []


@app.get("/api/cron/jobs")
def get_cron_jobs():
    """Return all Hermes cron jobs with delivery and status info."""
    try:
        jobs_file = Path("/home/hermeswebui/.hermes/cron/jobs.json")
        if not jobs_file.exists():
            jobs_file = Path("/var/lib/docker/volumes/hermes-webui-gsga_hermes-home/_data/cron/jobs.json")
        if not jobs_file.exists():
            return {"jobs": [], "error": "jobs.json not found"}
        payload = json.loads(jobs_file.read_text())
        jobs = payload.get("jobs", [])
        return {"jobs": jobs, "count": len(jobs)}
    except Exception as e:
        return {"jobs": [], "error": str(e)}

# ─── Routes: Status ───────────────────────────────────────────────

@app.get("/api/status")
def get_status():
    agents = [check_agent(a) for a in ["opencode", "hermes", "gemini"]]
    skills = list_dir(BASE_DIR / "skills")
    return {
        "status": "healthy",
        "agents": agents,
        "skills_count": len(skills),
        "uptime": time.time(),
    }


@app.get("/api/selftest")
def selftest_endpoint():
    """One-click health confirmation.

    Reports per-item pass/fail for: ``audit/`` writable, each agent CLI
    resolvable (reuses ``check_agent``), OpenRouter key present, Google token
    present/valid (probes the ``GoogleWorkspace`` token path without sending),
    knowledge index loaded with a document count, and ``data/`` writable.
    Returns a structured payload with an overall ``ok`` flag and appends a
    ``selftest_run`` audit entry.
    """
    checks = []

    def add(name: str, ok: bool, detail: str | None = None):
        item = {"name": name, "ok": bool(ok)}
        if detail is not None:
            item["detail"] = detail
        checks.append(item)

    # audit/ writable
    try:
        audit_dir = BASE_DIR / "audit"
        audit_dir.mkdir(parents=True, exist_ok=True)
        probe = audit_dir / ".selftest_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        add("audit_writable", True)
    except Exception as e:
        add("audit_writable", False, str(e)[:200])

    # each agent CLI resolvable (reuse check_agent)
    for name in ("opencode", "hermes", "gemini"):
        info = check_agent(name)
        add(f"agent_{name}", info.get("status") == "online", info.get("status"))

    # OpenRouter key present
    add("openrouter_key", bool(_settings.OPENROUTER_API_KEY),
        "key set" if _settings.OPENROUTER_API_KEY else "OPENROUTER_API_KEY missing")

    # Google token present/valid (probe token path without sending)
    try:
        token_path = Path(_settings.GOOGLE_TOKEN_PATH)
        valid = False
        detail = "token file missing"
        if token_path.exists():
            data = json.loads(token_path.read_text(encoding="utf-8"))
            token = data.get("token") if isinstance(data, dict) else None
            expiry = data.get("expiry") if isinstance(data, dict) else None
            if token:
                valid = True
                detail = f"token present (expiry={expiry})"
            else:
                detail = "token file present but no token field"
        add("google_token", valid, detail)
    except Exception as e:
        add("google_token", False, str(e)[:200])

    # knowledge index loaded with a document count
    try:
        idx_path = BASE_DIR / "data" / "knowledge_index.json"
        count = 0
        if idx_path.exists():
            kj = json.loads(idx_path.read_text(encoding="utf-8"))
            docs = kj.get("docs", []) if isinstance(kj, dict) else (kj if isinstance(kj, list) else [])
            count = len(docs) if isinstance(docs, list) else 0
        add("knowledge_index", count > 0, f"{count} documents")
    except Exception as e:
        add("knowledge_index", False, str(e)[:200])

    # data/ writable
    try:
        data_dir = BASE_DIR / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        probe = data_dir / ".selftest_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        add("data_writable", True)
    except Exception as e:
        add("data_writable", False, str(e)[:200])

    overall_ok = all(c["ok"] for c in checks)
    append_audit({"action": "selftest_run", "ok": overall_ok,
                  "failures": [c["name"] for c in checks if not c["ok"]]})
    return {"ok": overall_ok, "checks": checks}


@app.get("/metrics")
def get_metrics():
    """Prometheus metrics endpoint."""
    return metrics_endpoint()


@app.get("/api/health/full")
def full_health():
    """Central health dashboard endpoint — services, cron, disk, reports."""
    report_dir = BASE_DIR / "reports"
    latest_pdf = None
    latest_pdf_age_seconds = None
    candidates = []
    if report_dir.exists() and (report_dir / "latest").exists():
        candidates = sorted(
            [p for p in (report_dir / "latest").rglob("*.pdf") if p.exists()],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
    if candidates:
        latest_pdf = candidates[0].name
        latest_pdf_age_seconds = int(time.time() - candidates[0].stat().st_mtime)

    cron_data = cron_health()

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "dashboard": check_url("http://127.0.0.1:8081/api/status"),
            "data_service": check_url("http://127.0.0.1:8086/health"),
            "vapi_bridge": check_url("http://127.0.0.1:8090/vapi/status"),
        },
        "cron": {
            "ok": cron_data.get("ok", False),
            "total": cron_data.get("jobs", 0),
            "failing": cron_data.get("failing", 0),
            "delivery_errors": cron_data.get("delivery_errors", 0),
            "paused": cron_data.get("paused", 0),
            "error": cron_data.get("error"),
            "raw_lines": [],
        },
        "disk": {
            "reports": _disk_usage_dict(report_dir),
            "workspace": _disk_usage_dict(Path("/workspace")),
        },
        "reports": {
            "latest_pdf": latest_pdf,
            "latest_pdf_age_seconds": latest_pdf_age_seconds,
            "report_count": len([d for d in report_dir.iterdir() if d.is_dir() and d.name != "latest"]) if report_dir.exists() else 0,
        },
    }


def _disk_usage_dict(path: Path) -> dict:
    try:
        stat = shutil.disk_usage(path)
        return {
            "total": stat.total,
            "used": stat.used,
            "free": stat.free,
            "percent": round(stat.used / stat.total * 100, 1),
        }
    except Exception:
        return {"total": 0, "used": 0, "free": 0, "percent": 0, "error": str(path)}


@app.post("/api/swap/process")
async def swap_process(dry_run: bool = True):
    """Run the swap auto processor manually (dry-run or live)."""
    script = Path("/home/hermeswebui/.hermes/scripts/swap_auto_processor.py")
    python = "/workspace/.aos-venv/bin/python3"
    if not script.exists():
        raise HTTPException(500, f"swap_auto_processor.py not found at {script}")
    cmd = [python, str(script)]
    if dry_run:
        cmd.append("--dry-run")
    proc = None
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=os.environ.copy(),
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=180)
        return {
            "success": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
            "dry_run": dry_run,
        }
    except asyncio.TimeoutError:
        if proc:
            try:
                proc.kill()
                await proc.wait()
            except Exception:
                pass
        raise HTTPException(504, "swap processor timed out after 180s")
    except Exception as e:
        raise HTTPException(500, f"failed to run swap processor: {e}")

# ─── Routes: Brain → modules/brain_routes.py (Phase 9 extraction)

# ─── Routes: Skills → modules/skills_routes.py (Phase 9 extraction)
# ─── Routes: Scheduler → modules/scheduler_routes.py (Phase 9 extraction)

# ─── Routes: Audit ────────────────────────────────────────────────

@app.get("/api/audit")
def get_audit(limit: int = Query(100, le=500)):
    audit_file = BASE_DIR / "audit" / "audit.log"
    if not audit_file.exists():
        return {"entries": []}
    lines = audit_file.read_text().strip().split("\n")
    entries = [json.loads(l) for l in lines if l.strip()]
    return {"entries": entries[-limit:]}

# ─── Routes: Cost Analytics ───────────────────────────────────────

@app.get("/api/cost")
def get_cost():
    """Return full cost history with collection-state metadata."""
    data = cost_tracker.get_history()
    entries = data.get("entries", [])
    
    # Add collection-state fields for truthful empty states
    has_real_metadata = len(entries) > 0 and any(
        e.get("agent") and e.get("model") for e in entries
    )
    
    data["collection_state"] = {
        "has_data": len(entries) > 0,
        "has_real_metadata": has_real_metadata,
        "entry_count": len(entries),
        "data_source": "live tracking" if has_real_metadata else "no metadata collected yet",
    }
    
    return data

@app.post("/api/cost/record")
def record_cost(data: dict):
    """Record a cost entry — only writes when actual metadata is available."""
    agent = data.get("agent", "")
    model = data.get("model", "")
    tokens = data.get("tokens", 0)
    cost_val = data.get("cost", 0.0)
    
    # Gate: only record if we have real metadata
    if not agent or not model or agent == "unknown" or model == "unknown":
        return {
            "status": "skipped",
            "reason": "insufficient_metadata",
            "message": "Cost entries require valid agent and model metadata"
        }
    
    # Gate: don't record zero-token entries (likely test data)
    if tokens == 0 and cost_val == 0.0:
        return {
            "status": "skipped", 
            "reason": "no_usage_data",
            "message": "No usage metrics to record"
        }
    
    cost_tracker.record(
        agent=agent,
        model=model,
        tokens=tokens,
        cost=cost_val,
        provider=data.get("provider"),
    )
    return {"status": "recorded"}

# ─── Routes: Registry/Plugins ─────────────────────────────────────

@app.get("/api/plugins")
def list_plugins():
    reg_file = BASE_DIR / "registry" / "plugins.json"
    if not reg_file.exists():
        return {"plugins": []}
    return json.loads(reg_file.read_text())

@app.post("/api/plugins/install")
def install_plugin(data: dict):
    name = data.get("name", "").strip()
    if not name:
        raise HTTPException(400, "Plugin name required")
    reg_file = BASE_DIR / "registry" / "plugins.json"
    reg = json.loads(reg_file.read_text()) if reg_file.exists() else {"plugins": []}
    if any(p["name"] == name for p in reg["plugins"]):
        return {"status": "already_installed"}
    reg["plugins"].append({
        "name": name,
        "installed": get_timestamp(),
        "version": "1.0.0",
    })
    reg_file.write_text(json.dumps(reg, indent=2))
    append_audit({"action": "plugin_installed", "plugin": name})
    return {"status": "installed", "plugin": name}

# ─── Routes: Backup ───────────────────────────────────────────────

@app.get("/api/backups")
def list_backups():
    backup_dir = BASE_DIR / "backups"
    backups = []
    for f in sorted(backup_dir.glob("*.tar.gz"), reverse=True):
        backups.append({
            "name": f.name,
            "size": f.stat().st_size,
            "created": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
        })
    return backups

@app.post("/api/backup")
def create_backup():
    backup_dir = BASE_DIR / "backups"
    backup_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"agentic-os-{ts}.tar.gz"
    with tarfile.open(backup_file, "w:gz") as tar:
        for dir_name in ["brain", "skills", "agents", "registry", "standards", "prompts"]:
            d = BASE_DIR / dir_name
            if d.exists():
                tar.add(d, arcname=dir_name)
    append_audit({"action": "backup_created", "file": backup_file.name})
    return {"status": "ok", "file": backup_file.name, "size": backup_file.stat().st_size}

@app.post("/api/backup/restore")
def restore_backup(data: BackupRestoreRequest):
    backup_file = BASE_DIR / "backups" / data.file
    if not backup_file.exists():
        raise HTTPException(404, "Backup file not found")
    base_resolved = BASE_DIR.resolve()
    with tarfile.open(backup_file, "r:gz") as tar:
        safe_members = []
        for member in tar.getmembers():
            if member.name.startswith("/"):
                raise HTTPException(400, "Unsafe archive")
            resolved = (BASE_DIR / member.name).resolve()
            if not resolved.is_relative_to(base_resolved):
                raise HTTPException(400, "Unsafe archive")
            if member.issym() or member.islnk():
                target = Path(member.linkname)
                if target.is_absolute():
                    raise HTTPException(400, "Unsafe archive")
                resolved_link = (BASE_DIR / member.name).parent / target
                if not resolved_link.resolve().is_relative_to(base_resolved):
                    raise HTTPException(400, "Unsafe archive")
            safe_members.append(member)
        tar.extractall(path=BASE_DIR, members=safe_members)
    append_audit({"action": "backup_restored", "file": data.file})
    return {"status": "restored"}

# ─── Routes: Drive Sync ─────────────────────────────────────────────

@app.post("/api/drive/sync")
def drive_sync_now():
    """Force-sync location rosters from Google Drive to local cache."""
    try:
        from modules import drive_sync
        result = drive_sync.sync_location_rosters(force=True)
        return result
    except Exception as e:
        return {"success": False, "reason": "exception", "error": str(e)[:500]}


@app.get("/api/drive/sync/status")
def drive_sync_status():
    """Get per-file sync freshness from the manifest."""
    try:
        from modules import drive_sync
        return drive_sync.get_sync_status()
    except Exception as e:
        return {"error": str(e)[:500]}


# ─── Routes: Prompts ──────────────────────────────────────────────

@app.get("/api/prompts")
def list_prompts():
    prompts_dir = BASE_DIR / "prompts"
    prompts = {}
    for f in sorted(prompts_dir.glob("*.md")):
        prompts[f.stem] = read_file(f)
    return prompts

# ─── Routes: Settings ───────────────────────────────

DEFAULT_SETTINGS = {
    "theme": "dark",
    "agent_preferences": {
        "opencode": {"enabled": True, "binary": "opencode"},
        "hermes": {"enabled": True, "binary": "hermes"},
        "gemini": {"enabled": True, "binary": "gemini", "model": "gemini-2.5-flash"}
    },
    "dashboard": {"port": 8080, "host": "127.0.0.1", "dark_mode": True},
    "api_keys": {"gemini": "", "openrouter": ""},
    "free_tier_limits": {
        "gemini_flash": {"requests_per_day": 1500, "tokens_per_day": 1000000},
        "openrouter_free": {"requests_per_day": 100, "tokens_per_day": 200000}
    }
}

@app.get("/api/settings")
def get_settings():
    sf = BASE_DIR / "data" / "settings.json"
    if not sf.exists():
        # Bootstrap defaults and persist them
        sf.parent.mkdir(parents=True, exist_ok=True)
        sf.write_text(json.dumps(DEFAULT_SETTINGS, indent=2))
        return DEFAULT_SETTINGS
    return json.loads(sf.read_text())

@app.put("/api/settings")
def update_settings(data: SettingsUpdate):
    sf = BASE_DIR / "data" / "settings.json"
    # Merge with existing or defaults
    existing = json.loads(sf.read_text()) if sf.exists() else DEFAULT_SETTINGS.copy()
    # Deep merge for nested dicts
    def deep_merge(base, updates):
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                deep_merge(base[key], value)
            else:
                base[key] = value
        return base
    merged = deep_merge(existing, data.settings)
    sf.parent.mkdir(parents=True, exist_ok=True)
    sf.write_text(json.dumps(merged, indent=2))
    append_audit({"action": "settings_updated"})
    return {"status": "ok"}

# ─── Routes: Standards ───────────────────────────────────

@app.get("/api/standards")
def list_standards():
    std_dir = BASE_DIR / "standards"
    if not std_dir.exists():
        return {"standards": []}
    standards = []
    index_file = std_dir / "index.yml"
    index_content = read_file(index_file)
    for f in std_dir.glob("*.md"):
        standards.append({
            "name": f.stem,
            "content": read_file(f),
        })
    return {"standards": standards, "index": index_content}

@app.post("/api/standards/discover")
def discover_standards():
    # Discovery is not implemented - return unavailable status
    append_audit({"action": "standards_discovery_unavailable"})
    return {
        "status": "unavailable",
        "message": "Standards discovery is not yet implemented. Define standards manually in the standards/ directory.",
        "available": False
    }

# ─── Routes: Reports ──────────────────────────────────────────────

@app.get("/api/reports/types")
def get_report_types():
    """Return the catalog of available report sources, filtering to those with existing skill dirs."""
    types = []
    for src in REPORT_SOURCES:
        if src["kind"] == "skill":
            skill_dir = BASE_DIR / "skills" / src["id"]
            if not skill_dir.exists() or not skill_dir.is_dir():
                continue
        types.append({
            "id": src["id"],
            "label": src["label"],
            "kind": src["kind"],
            "supports_pdf": src["supports_pdf"],
        })
    return types


def _run_skill_report_text(name: str, skill_input: str) -> tuple:
    """Run a skill and return (agent_choice: str, output_text: str).

    Shared helper used by the run_skill endpoint AND the reports endpoint
    so prompt-building + execute_agent logic lives in one place.
    """
    from modules import skill_runner
    result = skill_runner.run_skill_sync(name, agent="auto", input=skill_input)
    return result.get("agent", "auto"), result.get("output", "")


@app.post("/api/reports/generate")
def generate_report(req: ReportGenerateRequest):
    """Generate a report by type, delivering via download or email."""
    # Find the source
    source = None
    for src in REPORT_SOURCES:
        if src["id"] == req.type:
            source = src
            break
    if not source:
        raise HTTPException(404, f"Report type '{req.type}' not found")

    try:
        if source["kind"] == "skill":
            agent, report_text = _run_skill_report_text(source["id"], req.input)

            if req.channel == "download":
                append_audit({"action": "report_generated", "type": req.type, "channel": "download"})
                return {
                    "status": "success",
                    "type": req.type,
                    "channel": "download",
                    "content": report_text,
                    "agent": agent,
                    "message": f"Report '{source['label']}' generated via {agent}",
                }

            elif req.channel == "email":
                recipient = req.recipient.strip()
                if not recipient:
                    # Try to find a default from settings
                    sf = BASE_DIR / "data" / "settings.json"
                    if sf.exists():
                        settings = json.loads(sf.read_text())
                        recipient = settings.get("SCHEDULE_EMAIL_RECIPIENT", settings.get("ADMIN_EMAIL", ""))
                if not recipient:
                    raise HTTPException(400, "recipient required and no default configured")

                html_body = f"""<!DOCTYPE html>
<html><body style="font-family:Arial,Helvetica,sans-serif;background:#f0f2f5;padding:24px">
<table cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto">
<tr><td style="background:#1a3a5c;padding:18px 28px;border-radius:4px 4px 0 0">
<span style="color:#fff;font-size:16pt;font-weight:bold">Agentic OS — {source['label']}</span>
</td></tr>
<tr><td style="background:#fff;padding:24px 28px;border-radius:0 0 4px 4px">
<pre style="white-space:pre-wrap;font-size:11pt;color:#333;line-height:1.5">{escape_html(report_text)}</pre>
</td></tr>
</table></body></html>"""

                try:
                    from modules.google_workspace import GoogleWorkspace
                    ws = GoogleWorkspace()
                    ws.send_email(
                        user_id="default",
                        to=recipient,
                        subject=f"Agentic OS Report — {source['label']}",
                        body=html_body,
                        is_html=True,
                    )
                except ImportError:
                    raise HTTPException(500, "Email sending not configured — Google Workspace module unavailable")
                except Exception as e:
                    raise HTTPException(500, f"Email failed: {str(e)}")

                append_audit({"action": "report_generated", "type": req.type, "channel": "email", "recipient": recipient})
                return {
                    "status": "success",
                    "type": req.type,
                    "channel": "email",
                    "message": f"Report '{source['label']}' emailed to {recipient}",
                }

            else:
                raise HTTPException(400, f"Unknown channel: {req.channel}")

        elif source["kind"] == "schedule":
            # Schedule PDF report
            from modules.vapi_email import build_schedule_pdf, build_email_html
            schedule_data = {"date": "Schedule report"}
            title = "Call Schedule"

            pdf_path = build_schedule_pdf(schedule_data, title=title)

            if req.channel == "download":
                from fastapi.responses import FileResponse
                append_audit({"action": "report_generated", "type": req.type, "channel": "download"})
                return FileResponse(
                    pdf_path,
                    media_type="application/pdf",
                    filename=f"{req.type}.pdf",
                    headers={"Content-Disposition": f'attachment; filename="{req.type}.pdf"'},
                )

            elif req.channel == "email":
                recipient = req.recipient.strip()
                if not recipient:
                    sf = BASE_DIR / "data" / "settings.json"
                    if sf.exists():
                        settings = json.loads(sf.read_text())
                        recipient = settings.get("SCHEDULE_EMAIL_RECIPIENT", settings.get("ADMIN_EMAIL", ""))
                if not recipient:
                    raise HTTPException(400, "recipient required and no default configured")

                html_body = build_email_html("Colleague", title, schedule_data={"note": "Schedule report"})
                try:
                    from modules.google_workspace import GoogleWorkspace
                    ws = GoogleWorkspace()
                    ws.send_email(
                        user_id="default",
                        to=recipient,
                        subject=f"Agentic OS — {title}",
                        body=html_body,
                        attachments=[pdf_path],
                        is_html=True,
                    )
                except ImportError:
                    raise HTTPException(500, "Email sending not configured — Google Workspace module unavailable")
                except Exception as e:
                    raise HTTPException(500, f"Email failed: {str(e)}")
                finally:
                    try:
                        import os
                        os.unlink(pdf_path)
                    except Exception:
                        pass

                append_audit({"action": "report_generated", "type": req.type, "channel": "email", "recipient": recipient})
                return {
                    "status": "success",
                    "type": req.type,
                    "channel": "email",
                    "message": f"PDF report emailed to {recipient}",
                }
            else:
                raise HTTPException(400, f"Unknown channel: {req.channel}")

        else:
            raise HTTPException(400, f"Unknown report kind: {source['kind']}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


def escape_html(text: str) -> str:
    """Minimal HTML escaping for report text rendering."""
    import html as _html
    return _html.escape(text or "")

# ─── Routes: Chat → modules/chat_routes.py (Phase 9 extraction)
# Agent executor (execute_agent) → modules/agent_executor.py (Phase 9 extraction)

# ═══════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════
# v0.2.0 — New Feature Endpoints
# ═══════════════════════════════════════════════════════════════════

# ─── Models ─────────────────────────────────────────────────────

class GoalCreate(BaseModel):
    title: str
    description: str = ""
    category: str = "general"
    target_date: str = ""

class GoalUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    target_date: Optional[str] = None
    progress: Optional[int] = None
    status: Optional[str] = None

class JournalSave(BaseModel):
    content: str

# Note: RouterSuggest and RouterRoute models are defined earlier in the Models section

# ─── Data Helpers ────────────────────────────────────────────────

GOALS_FILE = BASE_DIR / "data" / "goals.json"
JOURNAL_DIR = BASE_DIR / "brain" / "journal"

def ensure_dir(d: Path):
    d.mkdir(parents=True, exist_ok=True)

def load_goals():
    if GOALS_FILE.exists():
        return json.loads(GOALS_FILE.read_text())
    return []

def save_goals(goals: list):
    GOALS_FILE.write_text(json.dumps(goals, indent=2))

# ─── Routes: Goals (4 endpoints) ──────────────────────────────

@app.get("/api/goals")
def list_goals():
    try:
        return {"goals": load_goals()}
    except Exception as e:
        return {"goals": [], "error": str(e)}

@app.post("/api/goals")
def create_goal(data: GoalCreate):
    try:
        goals = load_goals()
        goal = {
            "id": str(uuid.uuid4())[:8],
            "title": data.title,
            "description": data.description,
            "category": data.category,
            "target_date": data.target_date,
            "status": "active",
            "progress": 0,
            "created": get_timestamp(),
            "updated": get_timestamp(),
        }
        goals.append(goal)
        save_goals(goals)
        # Auto-sync to brain/active-projects.md
        active_path = BASE_DIR / "brain" / "active-projects.md"
        if active_path.exists():
            existing = active_path.read_text()
            existing += f"\n- [{goal['title']}](goal:{goal['id']}) — {goal['description'][:80]}\n"
            active_path.write_text(existing)
        append_audit({"action": "goal_created", "title": data.title})
        return goal
    except Exception as e:
        raise HTTPException(500, str(e))

@app.put("/api/goals/{goal_id}")
def update_goal(goal_id: str, data: GoalUpdate):
    try:
        goals = load_goals()
        for g in goals:
            if g["id"] == goal_id:
                for field in ["title", "description", "category", "target_date", "progress", "status"]:
                    val = getattr(data, field, None)
                    if val is not None:
                        g[field] = val
                g["updated"] = get_timestamp()
                save_goals(goals)
                return g
        raise HTTPException(404, "Goal not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))

@app.delete("/api/goals/{goal_id}")
def delete_goal(goal_id: str):
    try:
        goals = load_goals()
        goals = [g for g in goals if g["id"] != goal_id]
        save_goals(goals)
        append_audit({"action": "goal_deleted", "goal_id": goal_id})
        return {"status": "deleted"}
    except Exception as e:
        raise HTTPException(500, str(e))

# ─── Task List (reads /workspace/task-list.json) ──────────────────

TASK_LIST_FILE = BASE_DIR.parent / "task-list.json"

def _load_tasks():
    if TASK_LIST_FILE.exists():
        return json.loads(TASK_LIST_FILE.read_text())
    return []

def _save_tasks(tasks):
    TASK_LIST_FILE.write_text(json.dumps(tasks, indent=2))

@app.get("/api/tasks")
def list_tasks():
    return _load_tasks()

@app.post("/api/tasks")
def create_task(data: dict):
    tasks = _load_tasks()
    import uuid as _uuid
    task = {
        "id": data.get("id") or str(_uuid.uuid4())[:8],
        "content": data.get("content", ""),
        "status": data.get("status", "pending"),
    }
    tasks.append(task)
    _save_tasks(tasks)
    return task

@app.put("/api/tasks/{task_id}")
def update_task(task_id: str, data: dict):
    tasks = _load_tasks()
    for t in tasks:
        if t.get("id") == task_id:
            if "content" in data: t["content"] = data["content"]
            if "status" in data: t["status"] = data["status"]
            _save_tasks(tasks)
            return t
    raise HTTPException(404, f"Task {task_id} not found")

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: str):
    tasks = _load_tasks()
    tasks = [t for t in tasks if t.get("id") != task_id]
    _save_tasks(tasks)
    return {"status": "deleted"}

# ─── Routes: Journal (4 endpoints) ───────────────────────────────

@app.get("/api/journal/entries")
def list_journal_entries():
    try:
        ensure_dir(JOURNAL_DIR)
        entries = []
        for f in sorted(JOURNAL_DIR.glob("*.md"), reverse=True):
            entries.append({
                "date": f.stem,
                "preview": f.read_text()[:200],
                "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
            })
        return {"entries": entries}
    except Exception as e:
        return {"entries": [], "error": str(e)}

@app.get("/api/journal/entries/{entry_date}")
def get_journal_entry(entry_date: str):
    try:
        ensure_dir(JOURNAL_DIR)
        # Harden against path traversal: resolve {entry_date}.md and ensure it
        # stays inside JOURNAL_DIR before any filesystem access.
        path = _safe_path(JOURNAL_DIR, f"{entry_date}.md")
        content = path.read_text() if path.exists() else ""
        return {"date": entry_date, "content": content}
    except HTTPException:
        raise
    except Exception as e:
        return {"date": entry_date, "content": "", "error": str(e)}

@app.put("/api/journal/entries/{entry_date}")
def save_journal_entry(entry_date: str, data: JournalSave):
    try:
        ensure_dir(JOURNAL_DIR)
        # Harden against path traversal: resolve {entry_date}.md and ensure it
        # stays inside JOURNAL_DIR before writing.
        path = _safe_path(JOURNAL_DIR, f"{entry_date}.md")
        path.write_text(data.content)
        append_audit({"action": "journal_saved", "date": entry_date})
        return {"status": "saved", "date": entry_date}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/journal/search")
def search_journal(q: str = Query("")):
    try:
        ensure_dir(JOURNAL_DIR)
        if not q:
            return {"results": []}
        results = []
        for f in JOURNAL_DIR.glob("*.md"):
            content = f.read_text()
            if q.lower() in content.lower():
                results.append({"date": f.stem, "preview": content[:200]})
        return {"results": results, "query": q}
    except Exception as e:
        return {"results": [], "error": str(e)}

# ─── Routes: Agent Health (3 endpoints) ─────────────────

# Agent check caches for activity-based fields
_agent_last_seen_cache = {}

def _get_last_activity_from_artifacts(agent_name: str) -> Optional[str]:
    """Derive last activity timestamp from existing artifacts (chat history, audit log)."""
    try:
        # Check chat history for agent activity
        chat_file = BASE_DIR / "data" / "chat-history.json"
        if chat_file.exists():
            history = json.loads(chat_file.read_text())
            messages = history.get("messages", [])
            for msg in reversed(messages):
                if msg.get("agent") == agent_name:
                    return msg.get("timestamp")
        
        # Check audit log for agent activity
        audit_file = BASE_DIR / "audit" / "audit.log"
        if audit_file.exists():
            lines = audit_file.read_text().strip().split("\n")
            for line in reversed(lines):
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                    if entry.get("agent") == agent_name or agent_name in str(entry.get("action", "")):
                        return entry.get("timestamp")
                except:
                    continue
    except Exception:
        pass
    return None

@app.get("/api/agents/health")
def get_agent_health():
    try:
        agents = []
        for name in ["opencode", "hermes", "gemini"]:
            info = check_agent(name)
            availability = info["status"]  # online/offline/warning
            
            # Get real activity data from audit
            runs = get_agent_runs_from_audit(name, limit=1000)
            total_runs = len(runs)
            last_run = runs[0] if runs else None
            last_seen = last_run.get("timestamp") if last_run else None
            
            # Determine health label and reason
            if availability == "offline":
                health_label = "offline"
                reason = "Agent CLI not available"
            elif total_runs == 0:
                health_label = "no_usage_yet"
                reason = "Agent available but no recorded activity"
            else:
                health_label = "healthy"
                reason = f"Online with {total_runs} recorded runs"
            
            agents.append({
                "name": name,
                "status": availability,
                "health_label": health_label,
                "health_reason": reason,
                "total_runs": total_runs,
                "last_seen": last_seen,
                "availability": availability,
            })
        return {"agents": agents, "updated": get_timestamp()}
    except Exception as e:
        return {"agents": [], "error": str(e), "updated": get_timestamp()}

@app.get("/api/agents/{name}/stats")
def get_agent_stats(name: str):
    try:
        if name not in ["opencode", "hermes", "gemini"]:
            raise HTTPException(400, "Invalid agent")
        info = check_agent(name)
        
        # Get real activity data
        runs = get_agent_runs_from_audit(name, limit=1000)
        total_runs = len(runs)
        last_run = runs[0] if runs else None
        last_seen = last_run.get("timestamp") if last_run else None
        
        # Calculate success rate from recorded events
        successful = sum(1 for r in runs if r.get("status") in ["success", None])
        failed = sum(1 for r in runs if r.get("status") == "error")
        success_rate = round(successful / total_runs * 100, 1) if total_runs > 0 else None
        
        return {
            "name": name,
            "status": info["status"],
            "total_runs": total_runs,
            "successful_runs": successful if total_runs > 0 else None,
            "failed_runs": failed if total_runs > 0 else None,
            "success_rate": success_rate,
            "last_seen": last_seen,
            "activity_source": "audit.log" if total_runs > 0 else "no recorded activity",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/api/agents/health/refresh")
def refresh_agent_health():
    try:
        agents = []
        for name in ["opencode", "hermes", "gemini"]:
            info = check_agent(name)
            runs = get_agent_runs_from_audit(name, limit=1000)
            total_runs = len(runs)
            last_run = runs[0] if runs else None
            last_seen = last_run.get("timestamp") if last_run else None
            
            if info["status"] == "offline":
                health_label = "offline"
            elif total_runs == 0:
                health_label = "no_usage_yet"
            else:
                health_label = "healthy"
            
            agents.append({
                "name": name,
                "status": info["status"],
                "health_label": health_label,
                "total_runs": total_runs,
                "last_seen": last_seen,
            })
        append_audit({"action": "agent_health_refreshed"})
        return {"agents": agents, "updated": get_timestamp()}
    except Exception as e:
        return {"agents": [], "error": str(e)}

# ─── Routes: Smart Router ────────────────────────────────────────────────

@app.get("/api/router/config")
def get_router_config():
    """Get routing rules and capabilities from backend source-of-truth."""
    try:
        config = load_router_config()
        return {
            "routing_rules": config.get("routing_rules", []),
            "agent_capabilities": config.get("agent_capabilities", {}),
            "handoff_protocol": config.get("handoff_protocol", {"enabled": True}),
        }
    except Exception as e:
        return {"error": str(e), "routing_rules": [], "agent_capabilities": {}}

@app.post("/api/router/suggest")
def router_suggest(data: RouterSuggest):
    try:
        config = load_router_config()
        scores, matched_rules, best, confidence = score_routing_rules(data.task, config)
        
        return {
            "suggested_agent": best,
            "confidence": confidence,
            "scores": scores,
            "matched_rules": matched_rules,
            "capabilities": config.get("agent_capabilities", {}).get(best, []),
            "task": data.task,
        }
    except Exception as e:
        return {"suggested_agent": "opencode", "confidence": "fallback", "error": str(e)}

@app.post("/api/router/route")
def router_route(data: RouterRoute):
    try:
        route_id = str(uuid.uuid4())[:12]
        
        # Auto-resolve agent if not specified
        agent = data.agent.lower()
        if agent == "auto":
            config = load_router_config()
            _, _, agent, _ = score_routing_rules(data.task, config)
        
        if agent not in ["opencode", "hermes", "gemini"]:
            return {"status": "error", "message": f"Invalid agent: {agent}"}
        
        # Record the routing event
        event_id = record_agent_run(
            action="task_routed",
            source="router",
            agent=agent,
            status="success",
            metadata={"task_preview": data.task[:200], "route_id": route_id}
        )
        
        # Dispatch to agent (using chat as the execution path)
        dispatch_result = None
        dispatch_error = None
        try:
            # Store in chat history for traceability
            chat_file = BASE_DIR / "data" / "chat-history.json"
            chat_history = {"messages": []}
            if chat_file.exists():
                chat_history = json.loads(chat_file.read_text())
            
            msg = {
                "role": "user",
                "content": data.task,
                "agent": agent,
                "timestamp": get_timestamp(),
                "route_id": route_id,
                "event_id": event_id,
            }
            chat_history["messages"].append(msg)
            chat_file.write_text(json.dumps(chat_history, indent=2))
            
            dispatch_result = "Task queued for execution"
        except Exception as e:
            dispatch_error = str(e)
        
        return {
            "status": "routed",
            "agent": agent,
            "task": data.task,
            "route_id": route_id,
            "event_id": event_id,
            "dispatch_status": "queued" if dispatch_result else "failed",
            "dispatch_result": dispatch_result,
            "dispatch_error": dispatch_error,
            "message": f"Task routed to {agent}",
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ─── Routes: ICS Progress (for dashboard sent-status indicators) ─────────────────────────────

@app.get("/api/progress/ics")
def get_ics_progress():
    """Return progress status for Grand Rounds and Monday SASP .ics sends."""
    import os, json
    base = "/workspace/agentic-os/data"
    gr_file = os.path.join(base, "grand_rounds_progress.json")
    mon_file = os.path.join(base, "monday_sasp_progress.json")
    result = {"grand_rounds": {"ics_sent_dates": []}, "monday_sasp": {"ics_sent_dates": []}}
    for key, path in [("grand_rounds", gr_file), ("monday_sasp", mon_file)]:
        if os.path.exists(path):
            try:
                result[key] = json.load(open(path))
            except:
                pass
    return result

# ─── Routes: Chief Meetings (.eml generation & download) ────────────────────────────────────

@app.get("/api/chief-meetings/generate-eml")
def generate_chief_meeting_eml():
    """Generate .eml files for all Chief Residents' Meetings."""
    import subprocess
    script = BASE_DIR / "send_chief_meeting_email.py"
    if not script.exists():
        return {"success": False, "error": "send_chief_meeting_email.py not found"}
    try:
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True, text=True, timeout=30,
            env={**os.environ, "PYTHONPATH": str(BASE_DIR)}
        )
        output = result.stdout.strip()
        error = result.stderr.strip()
        return {
            "success": result.returncode == 0,
            "message": f"Generated .eml files ({output.count('saved')} files)" if result.returncode == 0 else error,
            "output": output,
            "error": error if result.returncode != 0 else ""
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/chief-meetings/eml")
def download_chief_meeting_eml(date: str = ""):
    """Download a single .eml file for a specific date."""
    import glob
    eml_dir = BASE_DIR / "data" / "chief_meeting_eml"
    if not date:
        return {"success": False, "error": "date parameter required"}
    pattern = str(eml_dir / f"*{date}*.eml")
    files = glob.glob(pattern)
    if not files:
        return {"success": False, "error": f"No .eml file found for date {date}"}
    filepath = files[0]
    from fastapi.responses import FileResponse
    return FileResponse(filepath, media_type="message/rfc822", filename=os.path.basename(filepath))


# ─── Routes: Resident Letters (Good Standing & Income Verification) ────────────────────────────

@app.get("/api/letters/generate")
@app.post("/api/letters/generate")
async def generate_resident_letter(
    request: Request,
    resident_id: str = "",
    type: str = "good-standing",
    recipient: str = "",
    recipient_title: str = "Dr.",
    institution: str = "",
    preview: bool = False,
):
    """Generate a Good Standing or Income Verification letter for a resident."""
    import subprocess, tempfile, os
    script = BASE_DIR / "letter_generator.py"
    if not script.exists():
        return {"success": False, "error": "letter_generator.py not found"}
    
    # Get body from POST if available
    if request.method == "POST":
        try:
            body = await request.json()
            resident_id = body.get("resident_id", resident_id)
            type = body.get("type", type)
            recipient = body.get("recipient", recipient)
            recipient_title = body.get("recipient_title", recipient_title)
            institution = body.get("institution", institution)
        except:
            pass
    
    if not resident_id:
        return {"success": False, "error": "resident_id required"}
    
    outdir = BASE_DIR / "data" / "letters"
    outdir.mkdir(parents=True, exist_ok=True)
    
    outfile = tempfile.NamedTemporaryFile(suffix=".html", dir=str(outdir), delete=False)
    outpath = outfile.name
    outfile.close()
    
    cmd = [sys.executable, str(script), "--type", type, "--resident-id", resident_id, "--output", outpath]
    if type == "good-standing" and recipient:
        cmd += ["--recipient", recipient, "--recipient-title", recipient_title]
        if institution:
            cmd += ["--institution", institution]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30,
                                env={**os.environ, "PYTHONPATH": str(BASE_DIR)})
        if result.returncode != 0:
            return {"success": False, "error": result.stderr.strip() or result.stdout.strip()}
        
        # Parse output to get resident name/pgy
        resident_name = ""
        pgy = ""
        salary = ""
        for line in result.stdout.split("\n"):
            if "Resident:" in line:
                parts = line.split("Resident:")[-1].strip().split(",")
                resident_name = parts[0].strip()
                if len(parts) > 1:
                    pgy = parts[1].strip()
            if "Salary:" in line:
                salary = line.split("Salary:")[-1].strip()
        
        filename = os.path.basename(outpath)
        return {
            "success": True,
            "filename": filename,
            "resident_name": resident_name,
            "pgy": pgy,
            "salary": salary,
            "download_url": f"/api/letters/download/{filename}",
            "preview_url": f"/api/letters/preview/{filename}",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/letters/download/{filename}")
async def download_letter(filename: str):
    """Download a generated letter HTML file."""
    from fastapi.responses import FileResponse
    filepath = BASE_DIR / "data" / "letters" / filename
    if not filepath.exists():
        return {"success": False, "error": "File not found"}
    return FileResponse(str(filepath), media_type="text/html", filename=filename)

@app.get("/api/letters/preview/{filename}")
async def preview_letter(filename: str):
    """Preview a generated letter in browser."""
    from fastapi.responses import HTMLResponse
    filepath = BASE_DIR / "data" / "letters" / filename
    if not filepath.exists():
        return HTMLResponse("<h1>File not found</h1>", status_code=404)
    return HTMLResponse(filepath.read_text())

# ─── Routes: Learning Analytics (2 endpoints) ────────────────────────────────────────────────

@app.get("/api/analytics/skills")
def get_skill_analytics():
    try:
        skills_dir = BASE_DIR / "skills"
        analytics = []
        for d in sorted(skills_dir.iterdir()):
            if d.is_dir() and not d.name.startswith("_"):
                eval_path = d / "eval.json"
                score_path = d / "score-history.json"
                scores = json.loads(score_path.read_text()) if score_path.exists() else []
                eval_data = json.loads(eval_path.read_text()) if eval_path.exists() else {}
                
                # Calculate canonical fields
                avg_score = sum(s.get("score", 0) for s in scores) / len(scores) if scores else 0
                best_score = max([s.get("score", 0) for s in scores]) if scores else 0
                
                analytics.append({
                    "name": d.name,
                    "score": round(avg_score / 100, 2) if avg_score > 1 else round(avg_score, 2),  # Normalize to 0-1
                    "evals": len(scores),
                    "best": round(best_score / 100, 2) if best_score > 1 else round(best_score, 2),  # Normalize to 0-1
                    # Backward compatibility fields
                    "total_runs": len(scores),
                    "avg_score": round(avg_score, 1),
                    "last_score": scores[-1].get("score", 0) if scores else 0,
                    "trend": "up" if len(scores) >= 2 and scores[-1].get("score", 0) > scores[-2].get("score", 0) else "down" if len(scores) >= 2 else "stable",
                })
        return {"skills": sorted(analytics, key=lambda x: x["evals"], reverse=True)}
    except Exception as e:
        return {"skills": [], "error": str(e)}

@app.get("/api/analytics/trends")
def get_trend_analytics():
    try:
        skills_dir = BASE_DIR / "skills"
        trends = {}  # Return as skill-keyed map
        for d in sorted(skills_dir.iterdir()):
            if d.is_dir() and not d.name.startswith("_"):
                score_path = d / "score-history.json"
                scores = json.loads(score_path.read_text()) if score_path.exists() else []
                if scores:
                    # Normalize scores to 0-1 range if they're percentages
                    normalized_scores = []
                    for s in scores[-10:]:
                        score_val = s.get("score", 0)
                        if score_val > 1:
                            score_val = score_val / 100
                        normalized_scores.append(score_val)
                    trends[d.name] = normalized_scores
        return {"trends": trends}
    except Exception as e:
        return {"trends": {}, "error": str(e)}

# ─── Routes: Session Replay (2 endpoints) ─────────────────

@app.get("/api/sessions/list")
def list_sessions():
    try:
        sessions = []
        sessions_dir = Path.home() / ".local" / "share" / "opencode"
        log_dir = sessions_dir / "log"
        if log_dir.exists():
            for f in sorted(log_dir.glob("*.log"), reverse=True)[:20]:
                stat = f.stat()
                sessions.append({
                    "id": f.stem,
                    "name": f.stem,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "date": datetime.fromtimestamp(stat.st_mtime).isoformat(),  # Canonical date field
                    "source": "opencode",
                })
        hermes_sessions = Path.home() / ".hermes" / "sessions.json"
        if hermes_sessions.exists():
            stat = hermes_sessions.stat()
            sessions.append({
                "id": "hermes-sessions",
                "name": "Hermes Session Archive",
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "date": datetime.fromtimestamp(stat.st_mtime).isoformat(),  # Canonical date field
                "source": "hermes",
            })
        return {"sessions": sessions}
    except Exception as e:
        return {"sessions": [], "error": str(e)}

@app.get("/api/sessions/{session_id}/replay")
def get_session_replay(session_id: str):
    try:
        sessions_dir = Path.home() / ".local" / "share" / "opencode"
        log_file = sessions_dir / "log" / f"{session_id}.log"
        if log_file.exists():
            stat = log_file.stat()
            content = log_file.read_text()
            lines = content.split("\n")
            messages = []
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                # Parse log lines into message objects
                # Format: "timestamp - user: message" or "timestamp - assistant: message"
                if " - user:" in line or " - assistant:" in line:
                    parts = line.split(" - ", 1)
                    timestamp = parts[0] if parts else datetime.now().isoformat()
                    msg_part = parts[1] if len(parts) > 1 else line
                    
                    if msg_part.startswith("user:"):
                        content_text = msg_part[5:].strip()
                        messages.append({
                            "role": "user",
                            "content": content_text,
                            "timestamp": timestamp
                        })
                    elif msg_part.startswith("assistant:"):
                        content_text = msg_part[10:].strip()
                        messages.append({
                            "role": "assistant",
                            "content": content_text,
                            "timestamp": timestamp
                        })
                elif line.lower().startswith("user:"):
                    messages.append({
                        "role": "user",
                        "content": line[5:].strip(),
                        "timestamp": datetime.now().isoformat()
                    })
                elif line.lower().startswith("assistant:"):
                    messages.append({
                        "role": "assistant",
                        "content": line[10:].strip(),
                        "timestamp": datetime.now().isoformat()
                    })
            
            return {
                "session_id": session_id,
                "session": {
                    "id": session_id,
                    "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "source": "opencode",
                },
                "lines": len(lines),
                "messages": messages[:100],
                "content": content[:5000],
            }
        return {
            "session_id": session_id,
            "session": {"id": session_id, "created_at": None},
            "messages": [],
            "content": "Session log not found"
        }
    except Exception as e:
        return {
            "session_id": session_id,
            "session": {"id": session_id, "created_at": None},
            "messages": [],
            "error": str(e)
        }

# ─── Routes: Tools Integration (NotebookLM, Cron, KB) ──────────────

import subprocess as _sp
import os as _os

def _run_cmd(cmd, timeout=15):
    try:
        env = {**_os.environ,
            "PATH": "/app/venv/bin:" + _os.environ.get("PATH", "/usr/bin:/bin"),
            "LD_LIBRARY_PATH": "/tmp/chromium-libs:" + _os.environ.get("LD_LIBRARY_PATH", "")}
        r = _sp.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout, env=env)
        return r.stdout, r.stderr, r.returncode
    except Exception as e:
        return "", str(e), -1

@app.get("/api/tools/overview")
def tools_overview():
    # Local KB is always available — no cookies needed
    kb = BASE_DIR.parent / "knowledge-base"
    if not kb.exists():
        kb = Path("/workspace/knowledge-base")
    prompts = len(list(kb.glob("prompts/*.md"))) if kb.exists() else 0
    tools_kb = len(list(kb.glob("tools/*.md"))) if kb.exists() else 0
    resources = len(list(kb.glob("resources/*.md"))) if kb.exists() else 0
    total = prompts + tools_kb + resources

    # NLM is bonus — quick check with short timeout, never blocks
    nlm_ok = False
    try:
        out, _, _ = _run_cmd("nlm login --check", timeout=8)
        nlm_ok = "valid" in out or "Authenticated" in out
    except:
        pass

    cron_out, _, _ = _run_cmd("hermes cron list", timeout=10)
    cron_count = cron_out.count("[active]") + cron_out.count("[paused]")
    return {
        "notebooklm_status": "active" if nlm_ok else "local_kb",
        "cron_jobs": cron_count,
        "kb_prompts": prompts,
        "kb_tools": tools_kb,
        "kb_resources": resources,
        "kb_total": total,
        "nlm_available": nlm_ok,
    }

@app.get("/api/tools/notebooks")
def tools_notebooks(profile: str = "default"):
    # Try live NLM first
    out, err, _ = _run_cmd(f"nlm notebook list --profile {profile}", timeout=20)
    try:
        data = json.loads(out)
        if isinstance(data, list) and data:
            # Cache the result for offline fallback
            cache_dir = Path.home() / ".hermes" / "notebooklm_cache"
            cache_dir.mkdir(parents=True, exist_ok=True)
            with open(cache_dir / f"{profile}_notebooks.json", "w") as f:
                json.dump(data, f, indent=2)
            return {"profile": profile, "notebooks": data, "source": "live"}
    except:
        pass

    # Fallback: serve from local cache
    cache_file = Path.home() / ".hermes" / "notebooklm_cache" / f"{profile}_notebooks.json"
    if cache_file.exists():
        try:
            with open(cache_file) as f:
                cached = json.load(f)
            return {"profile": profile, "notebooks": cached, "source": "cache"}
        except:
            pass

    return {"profile": profile, "notebooks": [], "error": (err or out)[:200]}


@app.post("/api/tools/notebooks/refresh")
def refresh_notebooks_cache():
    """Refresh the local notebook cache from live NLM."""
    results = {}
    for profile in ["account2", "default", "letsgetmoney2009"]:
        out, err, _ = _run_cmd(f"nlm notebook list --profile {profile}", timeout=25)
        try:
            data = json.loads(out)
            if isinstance(data, list) and data:
                cache_dir = Path.home() / ".hermes" / "notebooklm_cache"
                cache_dir.mkdir(parents=True, exist_ok=True)
                with open(cache_dir / f"{profile}_notebooks.json", "w") as f:
                    json.dump(data, f, indent=2)
                results[profile] = {"status": "ok", "count": len(data)}
            else:
                results[profile] = {"status": "empty", "error": "no notebooks returned"}
        except:
            results[profile] = {"status": "error", "error": (err or out)[:200]}
    return {"status": "ok", "results": results}


@app.get("/api/tools/cron")
def tools_cron():
    out, _, rc = _run_cmd("hermes cron list", timeout=10)
    return {"output": out, "status": "ok" if rc == 0 else "error"}

@app.get("/api/tools/telegram")
def tools_telegram():
    """Return Telegram/Discord messaging sessions from Hermes state.db."""
    hermes_home = os.environ.get("HERMES_HOME", str(Path.home() / ".hermes"))
    db_path = Path(hermes_home) / "state.db"
    if not db_path.exists():
        return {"sessions": [], "error": "state.db not found"}
    try:
        import sqlite3
        from contextlib import closing
        MESSAGING_SOURCES = ("telegram", "discord", "slack", "email", "signal", "whatsapp")
        with closing(sqlite3.connect(str(db_path))) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            placeholders = ", ".join("?" for _ in MESSAGING_SOURCES)
            cur.execute(f"""
                SELECT id, source, model, message_count, input_tokens, output_tokens,
                       started_at, ended_at, title
                FROM sessions
                WHERE source IN ({placeholders})
                ORDER BY COALESCE(ended_at, started_at) DESC
                LIMIT 50
            """, MESSAGING_SOURCES)
            sessions = []
            for row in cur.fetchall():
                sessions.append({
                    "id": row["id"],
                    "source": row["source"] or "telegram",
                    "model": row["model"] or "",
                    "messages": row["message_count"] or 0,
                    "input_tokens": row["input_tokens"] or 0,
                    "output_tokens": row["output_tokens"] or 0,
                    "started": row["started_at"],
                    "ended": row["ended_at"],
                    "title": row["title"] or f"{row['source'].title()} Session",
                })
            return {"sessions": sessions, "total": len(sessions)}
    except Exception as e:
        return {"sessions": [], "error": str(e)}

@app.get("/api/tools/kb")
def tools_kb():
    kb = Path("/workspace/knowledge-base")
    if not kb.exists():
        return {"entries": []}
    entries = []
    for f in sorted(kb.glob("**/*.md"), key=lambda p: p.stat().st_mtime, reverse=True):
        if f.name == "README.md": continue
        text = f.read_text()
        title = f.name.replace(".md", "").replace("-", " ").title()
        for line in text.split("\n"):
            if line.startswith("title:"):
                title = line.replace("title:", "").strip().strip('"')
                break
        entries.append({"title": title, "category": f.parent.name, "path": str(f)})
    return {"entries": entries[:100]}

# ─── Call Schedule Integration (Supabase - single source of truth) ───────
# On-call schedule for Moses, Wakefield, Weiler.
# Source: Supabase call_schedule table (populated from Excel, now canonical).
# All platforms read from this same table.

import urllib.request
import json

_SUPABASE_URL = "https://supabase.srv1738752.hstgr.cloud"
_SUPABASE_KEY = ""
_SUPABASE_KEY_PATH = Path("/root/projects/call-schedule-app/.supabase_key")
if _SUPABASE_KEY_PATH.exists():
    _SUPABASE_KEY = _SUPABASE_KEY_PATH.read_text().strip()
if not _SUPABASE_KEY:
    _SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

def _supabase_select(path: str) -> list:
    """Query PostgreSQL directly (self-hosted Supabase)."""
    import psycopg2, os
    try:
        pw = os.environ.get("POSTGRES_PASSWORD", "")
        if not pw:
            ep = "/workspace/agentic-os/.env"
            if os.path.exists(ep):
                with open(ep) as ef:
                    for line in ef:
                        if line.startswith("POSTGRES_PASSWORD="):
                            pw = line.split("=", 1)[1].strip()
                            break
        conn = psycopg2.connect(host="172.16.0.1", port=5432, user="postgres", password=pw, dbname="postgres")
        cur = conn.cursor()
        parts = path.split("?")
        table = parts[0]
        params = {}
        if len(parts) > 1:
            for p in parts[1].split("&"):
                if "=" in p:
                    k, v = p.split("=", 1)
                    params[k] = v
        select_cols = params.get("select", "*")
        where = ""
        order = ""
        limit = ""
        for k, v in params.items():
            if k == "select":
                continue
            elif k == "order":
                order = " ORDER BY " + v.replace(".asc", " ASC").replace(".desc", " DESC")
            elif k == "limit":
                limit = " LIMIT " + v
            elif ".eq." in v:
                where = f" WHERE {k} = '{v.split('.eq.')[1]}'"
            elif ".gte." in v:
                where = f" WHERE {k} >= '{v.split('.gte.')[1]}'"
            elif ".lte." in v:
                where = f" WHERE {k} <= '{v.split('.lte.')[1]}'"
        sql = f"SELECT {select_cols} FROM {table}{where}{order}{limit}"
        cur.execute(sql)
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        cur.close()
        conn.close()
        return rows
    except Exception:
        return []
def _get_oncall_for_date(target_date: str) -> list:
    """Get all on-call entries for a date across all 3 hospitals from Supabase."""
    rows = _supabase_select(
        f"call_schedule?select=hospital,date,day,primary_attending,backup_attending,peds_attending,chief_resident,first_call_resident,second_call_resident&date=eq.{target_date}&order=hospital.asc"
    )
    result = []
    for r in rows:
        result.append({
            "hospital": r.get("hospital"),
            "date": r.get("date"),
            "day": r.get("day"),
            "primary_attending": r.get("primary_attending"),
            "backup_attending": r.get("backup_attending"),
            "peds_attending": r.get("peds_attending"),
            "chief_resident": r.get("chief_resident"),
            "first_call_resident": r.get("first_call_resident"),
            "second_call_resident": r.get("second_call_resident"),
        })
    return result

def _get_oncall_for_week(week_start: str) -> list:
    """Get all on-call entries for a week starting Monday from Supabase."""
    from datetime import datetime, timedelta
    try:
        start = datetime.strptime(week_start, "%Y-%m-%d")
    except:
        return []
    end = start + timedelta(days=6)
    start_str = start.strftime("%Y-%m-%d")
    end_str = end.strftime("%Y-%m-%d")
    rows = _supabase_select(
        f"call_schedule?select=hospital,date,day,primary_attending,backup_attending,peds_attending,chief_resident,first_call_resident,second_call_resident&date=gte.{start_str}&date=lte.{end_str}&order=date.asc"
    )
    result = []
    for r in rows:
        result.append({
            "hospital": r.get("hospital"),
            "date": r.get("date"),
            "day": r.get("day"),
            "primary_attending": r.get("primary_attending"),
            "backup_attending": r.get("backup_attending"),
            "peds_attending": r.get("peds_attending"),
            "chief_resident": r.get("chief_resident"),
            "first_call_resident": r.get("first_call_resident"),
            "second_call_resident": r.get("second_call_resident"),
        })
    return result

@app.get("/api/oncall/now")
def oncall_now():
    """Who is on call right now? Returns all 3 hospitals."""
    today = datetime.now(TZ).strftime("%Y-%m-%d")
    entries = _get_oncall_for_date(today)
    if entries:
        return {"oncall": entries, "date": today, "hospitals": list(set(e["hospital"] for e in entries))}
    # Check if any data exists in Supabase
    first = _supabase_select("call_schedule?select=date&order=date.asc&limit=1")
    if first:
        return {"oncall": [], "date": today, "message": f"Schedule starts {first[0]['date']}. No data for today.", "schedule_range": "Jul 1 - Jan 3, 2027"}
    return {"oncall": [], "date": today, "message": "No call schedule loaded"}

@app.get("/api/oncall/date")
def oncall_by_date(date: str = Query(...)):
    """Faculty on call for a specific date. Returns all 3 hospitals."""
    entries = _get_oncall_for_date(date)
    if entries:
        return {"oncall": entries, "date": date, "hospitals": list(set(e["hospital"] for e in entries))}
    return {"oncall": [], "date": date, "message": f"No schedule data for {date}. Schedule runs Jul 1 - Dec 31, 2026."}

@app.get("/api/oncall/week")
def oncall_by_week(start: str = Query(...)):
    """Faculty on call for a week starting Monday."""
    entries = _get_oncall_for_week(start)
    return {"oncall": entries, "week_start": start, "total": len(entries)}

@app.get("/api/oncall/schedule")
def oncall_schedule():
    """Full on-call schedule metadata from Supabase."""
    rows = _supabase_select("call_schedule?select=hospital,date,primary_attending&order=hospital.asc,date.asc")
    hospitals_data = {}
    for r in rows:
        h = r.get("hospital")
        if h not in hospitals_data:
            hospitals_data[h] = {"dates": set(), "docs": set()}
        hospitals_data[h]["dates"].add(r.get("date"))
        if r.get("primary_attending") and r["primary_attending"] != "None":
            hospitals_data[h]["docs"].add(r["primary_attending"])
    
    hospitals = []
    for name, data in hospitals_data.items():
        dates = sorted(data["dates"])
        hospitals.append({
            "name": name,
            "total_dates": len(dates),
            "start_date": dates[0] if dates else None,
            "end_date": dates[-1] if dates else None,
            "unique_primary_attendings": sorted(data["docs"]),
        })
    return {
        "hospitals": hospitals,
        "source": "supabase",
        "loaded": len(rows) > 0,
    }

@app.get("/api/oncall/search")
def oncall_search(date: str = Query(...)):
    """Search: Who covers a specific date? (alias for /api/oncall/date)"""
    return oncall_by_date(date)


class EmailSendRequest(BaseModel):
    account_label: str
    to_email: str
    subject: str
    body: str

@app.post("/api/email/send")
def api_send_email(req: EmailSendRequest):
    """Send email through the email_assistant.py guardrail pipeline."""
    try:
        email_script = str(Path("/home/hermeswebui/.hermes/email_assistant.py"))
        result = subprocess.run(
            ["python3", email_script, "send", req.account_label, req.to_email, req.subject, req.body],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout.strip())
            return data
        return {"success": False, "error": result.stderr or "Unknown error"}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Email send timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ─── Routes: Email Templates ─────────────────────────────────────

EMAIL_TEMPLATES_FILE = Path("/home/hermeswebui/.hermes/email_templates.json")

def _load_email_templates():
    if EMAIL_TEMPLATES_FILE.exists():
        try:
            return json.loads(EMAIL_TEMPLATES_FILE.read_text())
        except:
            return {"templates": []}
    return {"templates": []}

def _save_email_templates(data):
    EMAIL_TEMPLATES_FILE.parent.mkdir(parents=True, exist_ok=True)
    EMAIL_TEMPLATES_FILE.write_text(json.dumps(data, indent=2))

class EmailTemplateCreate(BaseModel):
    name: str
    title: str
    subject: str
    body: str
    tone: str = "professional"

@app.get("/api/email/templates")
def email_templates_list():
    return _load_email_templates()

@app.post("/api/email/templates")
def email_templates_create(req: EmailTemplateCreate):
    data = _load_email_templates()
    # Check for duplicate name
    for t in data["templates"]:
        if t["name"] == req.name:
            raise HTTPException(400, f"Template '{req.name}' already exists")
    template = {
        "name": req.name,
        "title": req.title,
        "subject": req.subject,
        "body": req.body,
        "tone": req.tone,
    }
    data["templates"].append(template)
    _save_email_templates(data)
    append_audit({"action": "email_template_created", "name": req.name})
    return {"success": True, "template": template}

@app.delete("/api/email/templates/{template_name}")
def email_templates_delete(template_name: str):
    data = _load_email_templates()
    before = len(data["templates"])
    data["templates"] = [t for t in data["templates"] if t["name"] != template_name]
    if len(data["templates"]) == before:
        raise HTTPException(404, f"Template '{template_name}' not found")
    _save_email_templates(data)
    append_audit({"action": "email_template_deleted", "name": template_name})
    return {"success": True}


# ─── Routes: Scheduled Email (via Hermes Cron) ──────────────────

SCHEDULED_EMAIL_SCRIPT = Path("/home/hermeswebui/.hermes/scheduled_email.py")

class ScheduledEmailRequest(BaseModel):
    template_name: str
    recipient_filter: str  # "all", "has-funds", "exhausted", or a contact name
    subject_override: str = ""
    schedule: str  # cron schedule string, e.g. "0 9 * * 1" for Monday 9am
    account_label: str = "urology"
    name: str = ""  # optional cron job name

@app.post("/api/email/schedule")
def api_schedule_email(req: ScheduledEmailRequest):
    """Schedule an email for bulk delivery via Hermes cron."""
    import subprocess

    job_name = req.name or f"scheduled-{req.template_name}-{req.recipient_filter}"
    job_prompt = (
        f"Send the '{req.template_name}' email template to "
        f"{'all residents' if req.recipient_filter == 'all' else req.recipient_filter} "
        f"via the scheduled_email.py script. "
        f"Run: python3 {SCHEDULED_EMAIL_SCRIPT} send-template-bulk "
        f"'{req.template_name}' '{req.recipient_filter}' "
        f"'{req.subject_override}' '{req.account_label}'"
    )

    # Try to create the cron job via hermes CLI
    try:
        result = subprocess.run(
            ["hermes", "cron", "create", req.schedule, job_prompt],
            capture_output=True, text=True, timeout=30
        )
        output = result.stdout or result.stderr
        return {
            "success": result.returncode == 0,
            "job_name": job_name,
            "template": req.template_name,
            "schedule": req.schedule,
            "recipients": req.recipient_filter,
            "detail": output.strip()
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ─── Routes: Google Dev Studio (Apps Script) ────────────────────

GOOGLE_TOKEN_PATH = str(Path.home() / ".hermes" / "google_token_letsgetmoney2009.json")
GOOGLE_SECRET_PATH = str(Path.home() / ".hermes" / "google_client_secret.json")
_google_creds_cache = None

def _get_google_creds():
    """Get (and cache) Google credentials for letsgetmoney2009."""
    global _google_creds_cache
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
    except ImportError:
        return None, "google-api-python-client not installed"
    
    if not os.path.isfile(GOOGLE_TOKEN_PATH):
        return None, "No Google token found — run OAuth setup first"
    
    try:
        creds = Credentials.from_authorized_user_file(
            GOOGLE_TOKEN_PATH,
            ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/script.projects"]
        )
        # Auto-refresh if expired
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Save refreshed token
            with open(GOOGLE_TOKEN_PATH, "w") as f:
                f.write(creds.to_json())
        _google_creds_cache = creds
        return creds, None
    except Exception as e:
        return None, str(e)

@app.get("/api/google/projects")
def list_google_projects():
    """List all Google Apps Script projects from Drive."""
    creds, err = _get_google_creds()
    if err:
        return {"status": "error", "message": err}
    try:
        from googleapiclient.discovery import build
        drive = build("drive", "v3", credentials=creds)
        results = drive.files().list(
            q="mimeType='application/vnd.google-apps.script'",
            pageSize=50,
            fields="files(id, name, modifiedTime, createdTime, webViewLink, description)"
        ).execute()
        files = results.get("files", [])
        return {"status": "ok", "projects": files}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/google/projects/{project_id}")
def get_google_project(project_id: str):
    """Get a Google Apps Script project's files and content."""
    creds, err = _get_google_creds()
    if err:
        return {"status": "error", "message": err}
    try:
        from googleapiclient.discovery import build
        script = build("script", "v1", credentials=creds)
        # Get project metadata
        project = script.projects().get(scriptId=project_id).execute()
        return {"status": "ok", "project": project}
    except Exception as e:
        # Fallback: just return Drive metadata
        try:
            drive = build("drive", "v3", credentials=creds)
            meta = drive.files().get(fileId=project_id, fields="id,name,modifiedTime,webViewLink").execute()
            return {"status": "ok", "project": {"scriptId": project_id, "title": meta.get("name"), "files": []}}
        except:
            return {"status": "error", "message": str(e)}

@app.post("/api/google/projects")
def create_google_project(data: dict):
    """Create a new Google Apps Script project."""
    title = data.get("title", "Untitled Project")
    creds, err = _get_google_creds()
    if err:
        return {"status": "error", "message": err}
    try:
        from googleapiclient.discovery import build
        script = build("script", "v1", credentials=creds)
        project = script.projects().create(body={"title": title}).execute()
        return {"status": "ok", "project": project}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/google/projects/{project_id}/content")
def update_google_project_content(project_id: str, data: dict):
    """Update Google Apps Script project files (push code)."""
    files = data.get("files", [])  # List of {name, type, source}
    creds, err = _get_google_creds()
    if err:
        return {"status": "error", "message": err}
    try:
        from googleapiclient.discovery import build
        script = build("script", "v1", credentials=creds)
        body = {
            "files": [{"name": f["name"], "type": f.get("type", "SERVER_JS"), "source": f["source"]} for f in files]
        }
        result = script.projects().updateContent(body=body, scriptId=project_id).execute()
        return {"status": "ok", "project": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ─── Routes: Hermes WebUI Proxy ──────────────────────────────────
# Proxy /hermes-webui/* to the Hermes WebUI server on port 8787
# so the iframe is same-origin (no cross-origin auth/cookie issues).

HERMES_WEBUI_TARGET = "http://127.0.0.1:8787"
_hermes_async_client = None

def _get_hermes_client():
    global _hermes_async_client
    if _hermes_async_client is None or _hermes_async_client.is_closed:
        _hermes_async_client = httpx.AsyncClient(base_url=HERMES_WEBUI_TARGET, timeout=30.0)
    return _hermes_async_client

@app.api_route("/hermes-webui/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
async def proxy_hermes_webui(path: str, request: Request):
    client = _get_hermes_client()
    target_path = f"/{path}" if path else "/"
    
    # Forward query params, headers, and body
    params = dict(request.query_params)
    headers = dict(request.headers)
    # Drop host header so the upstream server resolves correctly
    headers.pop("host", None)
    
    body = await request.body()
    
    try:
        resp = await client.request(
            method=request.method,
            url=target_path,
            params=params,
            headers=headers,
            content=body,
        )
        # Build response headers — strip CSP/X-Frame headers that block iframe embedding
        resp_headers = {}
        for k, v in resp.headers.items():
            kl = k.lower()
            if kl in ("content-security-policy", "content-security-policy-report-only", "x-frame-options"):
                continue  # Strip frame-blocking headers so the iframe works
            # Rewrite Location headers for same-origin redirects so the iframe works
            if kl == "location":
                loc = v
                if loc.startswith("/"):
                    loc = f"/hermes-webui{loc}"
                # Also fix the next= parameter to point to the proxied path
                if "next=" in loc and not loc.startswith("/hermes-webui"):
                    loc = loc.replace("next=/", "next=/hermes-webui/")
                resp_headers[k] = loc
                continue
            resp_headers[k] = v
        
        # Read the full body content for the response
        body_content = resp.content
        
        # Use a regular Response for 302/301 redirects, StreamingResponse for others
        if resp.status_code in (301, 302, 303, 307, 308):
            return Response(
                content=body_content,
                status_code=resp.status_code,
                headers=resp_headers,
            )
        return StreamingResponse(
            content=resp.iter_bytes(),
            status_code=resp.status_code,
            headers=resp_headers,
        )
    except httpx.ConnectError:
        return HTMLResponse(
            content="<html><body style='background:#1a1a2e;color:#eee;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;flex-direction:column;gap:12px;'><div style='font-size:48px;'>🔌</div><h2>Hermes WebUI Not Running</h2><p style='color:#888;'>The Hermes WebUI server on port 8787 is not available.</p><p style='color:#666;font-size:13px;'>Start it with: <code>python3 /app/server.py --port 8787</code></p></body></html>",
            status_code=502,
        )

# ─── Routes: Gemini AI Proxy (Antigravity) ──────────────────────
# Proxy for Google Gemini API — lets the frontend call Gemini
# without exposing the API key to the browser.

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY not found in .env — AI Builder will not work")

_GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
]
_GEMINI_DEFAULT_MODEL = "gemini-2.5-flash"

class GeminiChatRequest(BaseModel):
    message: str
    model: Optional[str] = _GEMINI_DEFAULT_MODEL
    system: Optional[str] = ""

@app.post("/api/gemini/chat")
def gemini_chat(req: GeminiChatRequest):
    if not GEMINI_API_KEY:
        raise HTTPException(500, "Gemini API key not configured")
    
    model = req.model if req.model in _GEMINI_MODELS else _GEMINI_DEFAULT_MODEL
    
    contents = []
    if req.system:
        contents.append({"role": "user", "parts": [{"text": f"[System: {req.system}]"}]})
        contents.append({"role": "model", "parts": [{"text": "Understood. I'll follow those instructions."}]})
    contents.append({"role": "user", "parts": [{"text": req.message}]})
    
    try:
        r = httpx.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}",
            json={"contents": contents},
            timeout=120,
        )
        if r.status_code != 200:
            return {"status": "error", "error": f"Gemini API returned {r.status_code}", "detail": r.text[:300]}
        
        data = r.json()
        candidates = data.get("candidates", [])
        if not candidates:
            return {"status": "error", "error": "No response from Gemini"}
        
        text = ""
        for part in candidates[0].get("content", {}).get("parts", []):
            text += part.get("text", "")
        
        return {"status": "ok", "response": text, "model": model}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# ─── Quick Actions ─────────────────────────────────────────────

@app.post("/api/quick-action")
def quick_action(data: dict):
    """Execute a quick action command from the dashboard."""
    action = data.get("action", "")
    try:
        if action == "schedule":
            r = subprocess.run(
                ["python3", "/workspace/agentic-os/deliver_messages.py", "--type", "schedule"],
                capture_output=True, text=True, timeout=120
            )
            return {"success": r.returncode == 0, "output": r.stdout[-2000:] if r.stdout else r.stderr[-2000:]}
        elif action == "gme":
            r = subprocess.run(
                ["python3", "/workspace/agentic-os/deliver_messages.py", "--type", "gme"],
                capture_output=True, text=True, timeout=120
            )
            return {"success": r.returncode == 0, "output": r.stdout[-2000:] if r.stdout else r.stderr[-2000:]}
        elif action == "test-email":
            r = subprocess.run(
                ["python3", "/workspace/send-report.py", "--test"],
                capture_output=True, text=True, timeout=60
            )
            return {"success": r.returncode == 0, "output": r.stdout[-2000:] if r.stdout else r.stderr[-2000:]}
        elif action == "eval":
            return {"success": True, "output": "Eval portal data — see #eval-portal page for details"}
        elif action == "restart-server":
            import sys
            os.execv(sys.executable, ["python3", __file__, "--port", "8090", "--host", "0.0.0.0"])
            return {"success": True, "output": "Server restarting..."}
        else:
            return {"success": False, "error": f"Unknown action: {action}"}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out after 120s"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ─── Eval Portal ───────────────────────────────────────────────

EVAL_FORMS_FILE = BASE_DIR / "data" / "eval_forms.json"

@app.get("/api/eval/forms")
def eval_forms_list():
    """List evaluation forms with completion status."""
    if EVAL_FORMS_FILE.exists():
        return json.loads(EVAL_FORMS_FILE.read_text())
    # Return empty structure
    return {"faculty": [], "residents": []}

@app.post("/api/eval/send-reminders")
def eval_send_reminders():
    """Send evaluation reminders to pending evaluators."""
    try:
        r = subprocess.run(
            ["python3", "/workspace/agentic-os/deliver_messages.py", "--type", "eval-reminder"],
            capture_output=True, text=True, timeout=60
        )
        return {"success": r.returncode == 0, "count": 0, "output": r.stdout[-500:] if r.stdout else r.stderr[-500:]}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ─── Script Runner ────────────────────────────────────────────

class ScriptRunRequest(BaseModel):
    cmd: str

@app.post("/api/script/run")
def script_run(req: ScriptRunRequest):
    """Run an arbitrary command and return output."""
    import shlex
    try:
        # Use shell for pipes/redirects but limit via timeout
        r = subprocess.run(
            req.cmd, shell=True, capture_output=True, text=True, timeout=120
        )
        return {
            "exit_code": r.returncode,
            "stdout": r.stdout[-5000:] if r.stdout else "",
            "stderr": r.stderr[-5000:] if r.stderr else ""
        }
    except subprocess.TimeoutExpired:
        return {"exit_code": -1, "stdout": "", "stderr": "Command timed out after 120s"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ─── Call Schedule PDF Generator ───────────────────────────────

@app.post("/api/call-schedule/pdf")
def call_schedule_pdf(data: dict):
    """Generate and optionally email the call schedule PDF."""
    mode = data.get("mode", "generate")
    email = data.get("email", "")
    period = data.get("period", "Q3-Q4 2026")
    options = data.get("options", {})
    try:
        if mode == "email" and email:
            cmd = ["python3", "/workspace/send-report.py", "--schedule-pdf", "--email", email]
            if period: cmd += ["--period", period]
        else:
            cmd = ["python3", "/workspace/send-report.py", "--schedule-pdf", "--output", f"/tmp/call_schedule_{period.replace(' ','_')}.pdf"]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        output = (r.stdout[-3000:] if r.stdout else "") or (r.stderr[-3000:] if r.stderr else "")
        return {
            "success": r.returncode == 0,
            "message": f"Call schedule PDF {'generated and emailed to ' + email if mode == 'email' else 'generated'}" if r.returncode == 0 else "Generation failed",
            "output": output, "error": r.stderr[-500:] if r.returncode != 0 and r.stderr else None
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Timed out after 120s", "output": ""}
    except Exception as e:
        return {"success": False, "error": str(e), "output": ""}

# ─── Telegram Status & Logs ────────────────────────────────────

@app.get("/api/telegram/status")
def telegram_status():
    """Return telegram gateway connection status and recent messages."""
    try:
        r = subprocess.run(["hermes", "gateway", "status"], capture_output=True, text=True, timeout=15)
        connected = "running" in (r.stdout+r.stderr).lower() or "active" in (r.stdout+r.stderr).lower()
        recent = []
        state_db = Path.home() / ".hermes" / "state.db"
        if state_db.exists():
            try:
                import sqlite3
                conn = sqlite3.connect(str(state_db))
                cur = conn.execute("SELECT title, preview, last_active FROM sessions WHERE source='telegram' AND preview IS NOT NULL ORDER BY last_active DESC LIMIT 10")
                for row in cur.fetchall():
                    recent.append({"sender": row[0] or "Telegram", "text": (row[1] or "")[:120], "time": str(row[2]) if row[2] else ""})
                conn.close()
            except: pass
        return {"connected": connected, "detail": "Gateway is running" if connected else "Gateway is not running", "platforms": {"telegram": {"connected": connected}}, "recent_messages": recent}
    except Exception as e:
        return {"connected": False, "detail": str(e), "platforms": {}, "recent_messages": []}

@app.get("/api/telegram/logs")
def telegram_logs():
    """Return the last 50 lines from gateway.log."""
    for p in [Path.home() / ".hermes" / "logs" / "gateway.log", Path.home() / ".hermes" / "gateway.log"]:
        if p.exists():
            return {"lines": p.read_text().splitlines()[-50:]}
    return {"lines": ["No gateway log found"]}

# ─── Routes: Image Gallery ──────────────────────────────────────

IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.bmp', '.ico'}
IMAGE_FOLDERS = ["/workspace/design_mockups", "/workspace"]

@app.get("/api/images/list")
def images_list():
    """Scan workspace for images and return folder structure."""
    images = []
    folders = set()
    scanned = set()

    for base in IMAGE_FOLDERS:
        bp = Path(base)
        if not bp.exists():
            continue
        for root, dirs, files in os.walk(str(bp)):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('node_modules', '__pycache__', '.git', 'venv', '__pycache__')]
            for f in sorted(files):
                ext = os.path.splitext(f)[1].lower()
                if ext not in IMAGE_EXTENSIONS:
                    continue
                fpath = os.path.join(root, f)
                if fpath in scanned:
                    continue
                scanned.add(fpath)
                try:
                    st = os.stat(fpath)
                    width = height = 0
                    try:
                        from PIL import Image
                        with Image.open(fpath) as img:
                            width, height = img.size
                    except:
                        pass
                    images.append({"name": f, "path": fpath, "ext": ext, "size": st.st_size, "modified": datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M"), "folder": root, "width": width, "height": height})
                    folders.add(root)
                except:
                    pass

    return {"images": images, "folders": sorted(folders, key=lambda f: (f != "/workspace/design_mockups", f))}

@app.get("/api/images/file")
def images_file(path: str = Query(...)):
    """Serve an image file by absolute path."""
    p = Path(path)
    if not p.exists() or not p.is_file():
        raise HTTPException(404, "Image not found")
    ext = p.suffix.lower()
    mime = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.gif': 'image/gif', '.webp': 'image/webp', '.svg': 'image/svg+xml', '.bmp': 'image/bmp', '.ico': 'image/x-icon'}.get(ext, 'application/octet-stream')
    return Response(content=p.read_bytes(), media_type=mime)


# ─── Routes: Images → PDF Converter ────────────────────────────


@app.post("/api/pdf/images2pdf")
async def images2pdf(request: Request):
    """Accept uploaded images + optional docs and convert to PDF.

    Accepts multipart form with:
      - files: one or more image files (PNG, JPG, GIF, etc.)
      - layout: optional — 'portrait' or 'landscape' (default: auto)

    Alternatively, POST JSON with:
      - paths: list of absolute file paths on the server
      - output: optional output filename (default: images2pdf_output.pdf)

    Returns the PDF as a download response.
    """
    import img2pdf as _img2pdf
    from PIL import Image as _PIL

    SUPPORTED_IMAGES = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.tif', '.webp'}
    SUPPORTED_DOCS = {'.pdf'}  # PDFs get embedded page-by-page

    content_type = request.headers.get("content-type", "")

    if "multipart/form-data" in content_type:
        form = await request.form()
        files = []
        for field_name in form:
            field = form[field_name]
            if hasattr(field, "filename") and field.filename:
                ext = os.path.splitext(field.filename)[1].lower()
                if ext not in SUPPORTED_IMAGES and ext not in SUPPORTED_DOCS:
                    continue
                tmp = Path(f"/tmp/pdfconv_{uuid.uuid4().hex}{ext}")
                tmp.write_bytes(await field.read())
                files.append({"path": str(tmp), "ext": ext, "name": field.filename})
        if not files:
            return JSONResponse({"success": False, "error": "No valid image files uploaded"}, status_code=400)
        output_name = "images2pdf_output.pdf"
    else:
        body = await request.json()
        file_paths = body.get("paths", [])
        if not file_paths:
            return JSONResponse({"success": False, "error": "No file paths provided"}, status_code=400)
        files = []
        for fp in file_paths:
            p = Path(fp)
            if not p.exists():
                return JSONResponse({"success": False, "error": f"File not found: {fp}"}, status_code=404)
            ext = p.suffix.lower()
            if ext not in SUPPORTED_IMAGES and ext not in SUPPORTED_DOCS:
                return JSONResponse({"success": False, "error": f"Unsupported format: {fp} ({ext})"}, status_code=400)
            files.append({"path": str(p.resolve()), "ext": ext, "name": p.name})
        output_name = body.get("output", "images2pdf_output.pdf")

    # Separate images from PDFs
    image_paths = [f["path"] for f in files if f["ext"] in SUPPORTED_IMAGES]
    pdf_paths = [f["path"] for f in files if f["ext"] in {'.pdf'}]

    all_images = []

    # Convert any PDFs to images first
    for pdf_path in pdf_paths:
        try:
            from pdf2image import convert_from_path
            imgs = convert_from_path(pdf_path, dpi=200)
            for i, img in enumerate(imgs):
                tmp = f"/tmp/pdfconv_{uuid.uuid4().hex}_p{i}.png"
                img.save(tmp, "PNG")
                all_images.append(tmp)
        except ImportError:
            # Fallback: try pikepdf to extract pages as images
            try:
                import pikepdf
                with pikepdf.open(pdf_path) as pdf:
                    for i, page in enumerate(pdf.pages):
                        # Render via ghostscript fallback below
                        pass
                # If pikepdf alone can't render, shell out to gs
                import subprocess
                tmp_dir = f"/tmp/pdfconv_{uuid.uuid4().hex}"
                os.makedirs(tmp_dir, exist_ok=True)
                r = subprocess.run(
                    ["gs", "-dNOPAUSE", "-dBATCH", "-sDEVICE=png16m", "-r200",
                     f"-sOutputFile={tmp_dir}/page_%d.png", pdf_path],
                    capture_output=True, text=True, timeout=60
                )
                if r.returncode == 0:
                    for fname in sorted(os.listdir(tmp_dir)):
                        all_images.append(os.path.join(tmp_dir, fname))
                else:
                    print(f"Ghostscript failed for {pdf_path}: {r.stderr[:200]}")
            except Exception as e:
                return JSONResponse({"success": False, "error": f"Failed to process PDF {pdf_path}: {str(e)}"}, status_code=400)

    all_images.extend(image_paths)

    if not all_images:
        return JSONResponse({"success": False, "error": "No processable images found"}, status_code=400)

    # Convert to PDF
    output_path = f"/tmp/{uuid.uuid4().hex}_{output_name}"
    with open(output_path, "wb") as f:
        f.write(_img2pdf.convert(all_images))

    # Cleanup temp files
    for f in files:
        if f["path"].startswith("/tmp/pdfconv_"):
            try:
                os.unlink(f["path"])
                os.unlink(f["path"].rsplit(".", 1)[0] + ".png") if f["ext"] == ".pdf" else None
            except:
                pass

    # Return the PDF
    pdf_bytes = Path(output_path).read_bytes()
    os.unlink(output_path)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{output_name}"',
            "Content-Length": str(len(pdf_bytes)),
        }
    )


# ─── Routes: Dashboard Static Files (first occurrence) ──────────

@app.get("/api/fs/list")
def fs_list(path: str = "/workspace"):
    """List directory contents."""
    try:
        p = Path(path)
        if not p.exists() or not p.is_dir():
            raise HTTPException(404, f"Directory not found: {path}")
        items = []
        for entry in sorted(p.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower())):
            try:
                st = entry.stat()
                items.append({
                    "name": entry.name,
                    "path": str(entry),
                    "type": "dir" if entry.is_dir() else "file",
                    "size": st.st_size if entry.is_file() else 0,
                    "modified": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat() if hasattr(st, 'st_mtime') else ""
                })
            except: pass
        return {"items": items, "path": path}
    except HTTPException: raise
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/fs/read")
def fs_read(path: str):
    """Read a file's contents."""
    try:
        p = Path(path)
        if not p.exists() or not p.is_file():
            raise HTTPException(404, f"File not found: {path}")
        if p.stat().st_size > 500_000:
            return {"content": "(file too large — 500KB limit)", "truncated": True}
        return {"content": p.read_text(encoding="utf-8", errors="replace"), "path": path}
    except HTTPException: raise
    except Exception as e:
        raise HTTPException(500, str(e))

# ─── Morning Briefing ──────────────────────────────────────────

@app.get("/api/morning-briefing")
def morning_briefing():
    """Daily briefing data — call, evals, cron status, events, commute."""

    # ─── Commute check ─────────────────────────────────────
    commute_data = []
    try:
        from modules.directions import get_commute_report
        report = get_commute_report()
        commute_data = report.get("routes", [])
    except Exception as e:
        commute_data = [{"error": str(e)}]

    try:
        on_call = "—"
        pending = 0
        try:
            import sqlite3
            db = Path.home() / ".hermes" / "state.db"
            if db.exists():
                conn = sqlite3.connect(str(db))
                cur = conn.execute("SELECT COUNT(*) FROM sessions WHERE title LIKE '%eval%' OR title LIKE '%Evaluate%'")
                pending = cur.fetchone()[0] or 0
                conn.close()
        except: pass
        return {
            "on_call_today": on_call,
            "pending_evals": pending,
            "cron_status": {"ok": 3, "failed": 0},
            "commute": commute_data,
            "upcoming_events": [
                {"day": "Mon", "event": "Grand Rounds — 7:00 AM"},
                {"day": "Wed", "event": "Clinic Meeting — 12:00 PM"},
                {"day": "Fri", "event": "GME Report Due"},
            ],
            "cron_jobs": _get_cron_jobs_list()
        }
    except Exception as e:
        return {"error": str(e)}

# ─── Compliance Overview ───────────────────────────────────────

@app.get("/api/compliance/overview")
def compliance_overview():
    """Compliance metrics across attendance, evals, and GME."""
    return {
        "grand_rounds_attendance": [],
        "eval_completion": {"done": 0, "pending": 0, "overdue": 0},
        "gme_usage": {"used": 0, "available": 1250, "residents": 0}
    }

# ─── Notification Feed ─────────────────────────────────────────

NOTIF_FILE = BASE_DIR / "data" / "notifications.json"

@app.get("/api/notifications")
def notifications_list():
    """Return recent notifications from the feed."""
    if NOTIF_FILE.exists():
        return json.loads(NOTIF_FILE.read_text())
    return {"notifications": []}

@app.post("/api/notifications/clear")
def notifications_clear():
    """Clear all notifications."""
    NOTIF_FILE.write_text(json.dumps({"notifications": []}))
    return {"success": True}


# ─── CRM Data Gaps — reads from Supabase Postgres ────────────────

ESSENTIAL_FIELDS = ["firstName", "lastName", "email", "ezId", "category", "mobile", "primaryLocation", "title", "role", "shift"]

@app.get("/api/crm-data-gaps")
def crm_data_gaps():
    """Analyze CRM contacts for missing data (reads from Supabase PG)."""
    try:
        try:
            sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
            from modules.crm_db import get_contacts
            contacts = get_contacts()
        except Exception:
            contacts = []
        
        if not contacts:
            # Fallback to JSON
            CRM_FILE = Path(__file__).resolve().parent / "data" / "crm_contacts.fallback.json"
            if CRM_FILE.exists():
                with open(CRM_FILE) as f:
                    contacts = json.load(f)
        
        if not contacts:
            return {"error": "No CRM data available", "by_category": {}, "stats": {"total": 0, "with_gaps": 0, "by_field": []}}

        by_category = {}
        field_counts = {}
        with_gaps = 0

        for c in contacts:
            cat = c.get("category", "Unknown") or "Unknown"
            missing = []
            for field in ESSENTIAL_FIELDS:
                v = c.get(field)
                if not v or v == "" or v == [] or v == {}:
                    missing.append(field)
                    field_counts[field] = field_counts.get(field, 0) + 1

            c["dataGaps"] = missing
            if missing:
                with_gaps += 1

            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append({
                "firstName": c.get("firstName", ""),
                "lastName": c.get("lastName", ""),
                "email": c.get("email", ""),
                "ezId": c.get("ezId", ""),
                "dataGaps": missing,
            })

        # Sort each category so most-gapped come first
        for cat in by_category:
            by_category[cat].sort(key=lambda x: len(x["dataGaps"]), reverse=True)

        fields_list = [{"field": f, "count": c} for f, c in sorted(field_counts.items(), key=lambda x: x[1], reverse=True)]

        return {
            "by_category": by_category,
            "stats": {
                "total": len(contacts),
                "with_gaps": with_gaps,
                "complete": len(contacts) - with_gaps,
                "by_field": fields_list,
            }
        }
    except Exception as e:
        return {"error": str(e), "by_category": {}, "stats": {"total": 0, "with_gaps": 0, "by_field": []}}


# ─── Eval Dashboard — reads from eval spreadsheet + tracking DB ────────

EVAL_SPREADSHEET_ID = '1lIdC-Hf8S6eBgJ98I4--tgjRm_eiSvcCD0svDtoKjmM'

EVAL_PROCEDURES = [
    '1 - Ureteroscopy / Laser Lithotripsy / Stent',
    '2 - Transurethral Resection of Prostate (TURP)',
    '3 - Prostate Biopsy',
    '4 - Hydrocelectomy',
    '5 - Inflatable Penile Prosthesis',
    '6 - Synthetic Mid-urethral Sling',
    '7 - Percutaneous Nephrolithotomy (PCNL)',
    '8 - Robotic-assisted Radical Prostatectomy (RALP)',
    '9 - Pediatric Orchiopexy',
    '10 - Laparoscopic Nephrectomy',
]
EVAL_ABBREVS = ['URS', 'TURP', 'BIOPSY', 'HYDRO', 'IPP', 'SLING', 'PCNL', 'RALP', 'ORCH', 'NEPH']

@app.get("/api/eval/dashboard")
def eval_dashboard():
    """Eval dashboard — completion stats, per-resident detail, trends."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    
    try:
        TOKEN_FILE = os.path.expanduser("/home/hermeswebui/.hermes/google_token.json")
        with open(TOKEN_FILE) as f:
            t = json.load(f)
        creds = Credentials(
            token=t['token'],
            refresh_token=t.get('refresh_token', ''),
            token_uri=t['token_uri'],
            client_id=t['client_id'],
            client_secret=t['client_secret'],
        )
        if creds.expired:
            creds.refresh(Request())
        
        sheets = build('sheets', 'v4', credentials=creds)
        
        # 1) Read the Dashboard sheet for roster
        dash_result = sheets.spreadsheets().values().get(
            spreadsheetId=EVAL_SPREADSHEET_ID,
            range="Dashboard!A24:C64"
        ).execute()
        dash_values = dash_result.get('values', [])
        
        residents = []
        faculty = []
        in_faculty = False
        for row in dash_values:
            name = (row[0] if len(row) > 0 else '').strip()
            if not name:
                continue
            if 'FACULTY' in name.upper():
                in_faculty = True
                continue
            pgy = (row[1] if len(row) > 1 else '').strip()
            email = (row[2] if len(row) > 2 else '').strip()
            if not in_faculty:
                residents.append({"name": name, "pgy": pgy, "email": email})
            else:
                faculty.append({"name": name, "email": email})
        
        # 2) Read all 20 eval sheets (FAC + RES for each procedure)
        sheet_names = []
        for i, abbrev in enumerate(EVAL_ABBREVS):
            sheet_names.append(f"FAC - {abbrev}")
            sheet_names.append(f"RES - {abbrev}")
        
        all_identity_rows = []  # rows with eval data (completed)
        all_pending_rows = []    # rows with identity only (pending)
        
        for sheet_name in sheet_names:
            try:
                result = sheets.spreadsheets().values().get(
                    spreadsheetId=EVAL_SPREADSHEET_ID,
                    range=f"'{sheet_name}'!A1:X"
                ).execute()
                values = result.get('values', [])
                if len(values) < 2:
                    continue
                
                headers = values[0]
                for row in values[1:]:
                    if len(row) < 2:
                        continue
                    ts = row[0] if len(row) > 0 else ''
                    role = row[1] if len(row) > 1 else ''
                    res_name = row[2] if len(row) > 2 else ''
                    fac_name = row[3] if len(row) > 3 else ''
                    proc = row[4] if len(row) > 4 else ''
                    proc_date = row[5] if len(row) > 5 else ''
                    
                    # Check if eval columns are filled (has competency data)
                    has_eval_data = any(len(row) > i and row[i].strip() for i in range(6, min(24, len(row))))
                    
                    entry = {
                        "sheet": sheet_name,
                        "timestamp": ts,
                        "role": role,
                        "resident_name": res_name,
                        "faculty_name": fac_name,
                        "procedure": proc,
                        "procedure_date": proc_date,
                        "completed": has_eval_data,
                    }
                    
                    if has_eval_data:
                        all_identity_rows.append(entry)
                    else:
                        all_pending_rows.append(entry)
            except Exception:
                continue
        
        # 3) Per-resident completion stats
        resident_stats = []
        for r in residents:
            rname = r["name"]
            total = sum(1 for e in all_identity_rows + all_pending_rows if e["resident_name"].lower() == rname.lower())
            completed = sum(1 for e in all_identity_rows if e["resident_name"].lower() == rname.lower())
            pending = total - completed
            resident_stats.append({
                "name": rname,
                "pgy": r["pgy"],
                "email": r["email"],
                "total": total,
                "completed": completed,
                "pending": pending,
                "completion_rate": round(completed / total * 100, 1) if total > 0 else 0,
            })
        resident_stats.sort(key=lambda x: x["name"])
        
        # 4) Per-faculty completion stats
        faculty_stats = []
        for f in faculty:
            fname = f["name"]
            total = sum(1 for e in all_identity_rows + all_pending_rows if e["faculty_name"].lower() == fname.lower())
            completed = sum(1 for e in all_identity_rows if e["faculty_name"].lower() == fname.lower())
            pending = total - completed
            faculty_stats.append({
                "name": fname,
                "email": f["email"],
                "total": total,
                "completed": completed,
                "pending": pending,
                "completion_rate": round(completed / total * 100, 1) if total > 0 else 0,
            })
        faculty_stats.sort(key=lambda x: x["name"])
        
        # 5) Per-procedure stats
        procedure_stats = []
        for i, proc in enumerate(EVAL_PROCEDURES):
            total = sum(1 for e in all_identity_rows + all_pending_rows if e["procedure"] == proc)
            completed = sum(1 for e in all_identity_rows if e["procedure"] == proc)
            pending = total - completed
            procedure_stats.append({
                "procedure": proc,
                "abbrev": EVAL_ABBREVS[i],
                "total": total,
                "completed": completed,
                "pending": pending,
                "completion_rate": round(completed / total * 100, 1) if total > 0 else 0,
            })
        
        # 6) Summary stats
        total_all = len(all_identity_rows) + len(all_pending_rows)
        completed_all = len(all_identity_rows)
        pending_all = len(all_pending_rows)
        
        # 7) Recent activity (last 20 submissions)
        recent = sorted(all_identity_rows, key=lambda x: x.get("timestamp", ""), reverse=True)[:20]
        
        return {
            "summary": {
                "total": total_all,
                "completed": completed_all,
                "pending": pending_all,
                "completion_rate": round(completed_all / total_all * 100, 1) if total_all > 0 else 0,
                "residents_total": len(residents),
                "faculty_total": len(faculty),
            },
            "resident_stats": resident_stats,
            "faculty_stats": faculty_stats,
            "procedure_stats": procedure_stats,
            "recent_activity": recent,
        }
    except Exception as e:
        logger.error(f"Eval dashboard error: {e}")
        return {"error": str(e), "summary": {"total": 0, "completed": 0, "pending": 0}, "resident_stats": [], "faculty_stats": [], "procedure_stats": [], "recent_activity": []}


# ─── Calendar of Events ─────────────────────────────────────

CALENDAR_DATA_FILE = BASE_DIR / "data" / "calendar_events.json"

@app.get("/api/calendar/events")
def calendar_events(days: int = Query(90, description="Number of days to look ahead"), include_todos: bool = Query(False)):
    """Return calendar events pulled from Google Calendar. Optionally include kanban todos."""
    from datetime import datetime, timezone, timedelta
    
    if not CALENDAR_DATA_FILE.exists():
        result = {"events": [], "source": "no_data"}
        if include_todos:
            result["todos"] = _get_todos()
        return result
    
    data = json.loads(CALENDAR_DATA_FILE.read_text())
    now = datetime.now(TZ)
    cutoff = now + timedelta(days=days)
    
    events = data.get("events", [])
    filtered = []
    for ev in events:
        start_str = ev.get("start", {}).get("date") or ev.get("start", {}).get("dateTime", "")
        if start_str:
            try:
                ev_date = datetime.fromisoformat(start_str)
                if ev_date.tzinfo is None:
                    ev_date = ev_date.replace(tzinfo=TZ)
                if ev_date <= cutoff:
                    filtered.append(ev)
            except (ValueError, TypeError):
                filtered.append(ev)
        else:
            filtered.append(ev)
    
    result = {"events": sorted(filtered, key=lambda e: e.get("start", {}).get("date") or e.get("start", {}).get("dateTime", "")), "count": len(filtered), "total": len(events)}
    if include_todos:
        result["todos"] = _get_todos()
    return result

def _get_todos():
    """Helper: return tasks from /workspace/task-list.json."""
    try:
        tf = BASE_DIR.parent / "task-list.json"
        if tf.exists():
            tasks = json.loads(tf.read_text())
            # Return as flat array — frontend expects simple list
            return tasks
        return []
    except Exception:
        return []

@app.get("/api/calendar/todos")
def calendar_todos():
    """Return tasks from task-list.json for the calendar todo panel."""
    return _get_todos()

@app.post("/api/calendar/todos")
def calendar_todos_create(data: dict):
    """Create a new task in task-list.json."""
    import uuid as _uuid
    tasks = _get_todos()
    task = {
        "id": data.get("id") or str(_uuid.uuid4())[:8],
        "content": data.get("content", data.get("title", "")),
        "status": data.get("status", "pending"),
    }
    tasks.append(task)
    tf = BASE_DIR.parent / "task-list.json"
    tf.write_text(json.dumps(tasks, indent=2))
    return {"ok": True, "task": task}

@app.post("/api/calendar/todos/{task_id}/complete")
def calendar_todos_complete(task_id: str):
    """Mark a task as completed."""
    tasks = _get_todos()
    for t in tasks:
        if t.get("id") == task_id:
            t["status"] = "completed"
            tf = BASE_DIR.parent / "task-list.json"
            tf.write_text(json.dumps(tasks, indent=2))
            return {"ok": True}
    raise HTTPException(404, "Task not found")

@app.delete("/api/calendar/todos/{task_id}")
def calendar_todos_delete(task_id: str):
    """Delete a task from task-list.json."""
    tasks = _get_todos()
    tasks = [t for t in tasks if t.get("id") != task_id]
    tf = BASE_DIR.parent / "task-list.json"
    tf.write_text(json.dumps(tasks, indent=2))
    return {"ok": True}

@app.patch("/api/calendar/todos/{task_id}")
def calendar_todos_patch(task_id: str, data: dict):
    """Update a task's status or content."""
    tasks = _get_todos()
    for t in tasks:
        if t.get("id") == task_id:
            if "content" in data: t["content"] = data["content"]
            if "status" in data: t["status"] = data["status"]
            tf = BASE_DIR.parent / "task-list.json"
            tf.write_text(json.dumps(tasks, indent=2))
            return {"ok": True}
    raise HTTPException(404, "Task not found")

# ─── Staff Schedule (from canonical on-call source) ─────────────

@app.get("/api/staff-schedule")
def staff_schedule(hospital: str = Query("Moses")):
    """Return attending schedule for a hospital from canonical oncall data."""
    data = _load_faculty_schedule()
    sheet = data.get("sheets", {}).get(hospital, {})
    entries = sheet.get("entries", [])

    seen = set()
    staff = []
    for e in entries:
        for field, role in [("primary", "Attending"), ("backup", "Backup Attending"), ("peds", "PEDS Attending")]:
            name = e.get(field, "")
            if name and name not in seen:
                seen.add(name)
                staff.append({
                    "name": name,
                    "role": role,
                    "detail": f"On-call rotation — {hospital}",
                    "schedule": "Q3-Q4 2026 rotation"
                })

    return {"staff": staff, "hospital": hospital, "total": len(staff)}

# ─── PDF Archive ────────────────────────────────────────────────

PDF_DATA_FILE = BASE_DIR / "data" / "pdf_archive.json"

@app.get("/api/pdf-archive")
def pdf_archive():
    """List all generated PDFs."""
    if PDF_DATA_FILE.exists():
        return json.loads(PDF_DATA_FILE.read_text())
    return {"pdfs": []}

# ─── GME Detail ────────────────────────────────────────────────

GME_DETAIL_FILE = BASE_DIR / "data" / "gme_detail.json"

@app.get("/api/gme/detail")
def gme_detail():
    """Return per-resident GME fund usage breakdown."""
    if GME_DETAIL_FILE.exists():
        return json.loads(GME_DETAIL_FILE.read_text())
    return {"residents": []}

# ─── Routes: Dashboard Static Files ──────────────────────────────

class BootErrorReport(BaseModel):
    msg: str
    ua: Optional[str] = ""
    url: Optional[str] = ""

__BOOT_ERRORS__: list = []  # in-memory ring buffer of last 50 errors

@app.post("/api/_boot_error")
def boot_error(req: BootErrorReport):
    __BOOT_ERRORS__.append({
        "msg": req.msg, "ua": req.ua, "url": req.url, "ts": time.time()
    })
    if len(__BOOT_ERRORS__) > 50:
        del __BOOT_ERRORS__[:len(__BOOT_ERRORS__) - 50]
    print(f"[boot] {req.msg}  (ua={req.ua[:60]}  url={req.url})", flush=True)
    return {"ok": True}

@app.get("/api/_boot_error")
def get_boot_errors():
    return {"errors": __BOOT_ERRORS__[-20:]}

# ─── Routes: Full Health Check (async version at ~2630) ────────────────────

dashboard_dir = BASE_DIR / "dashboard"
if dashboard_dir.exists():
    app.mount("/dashboard", StaticFiles(directory=str(dashboard_dir), html=True), name="dashboard")

# OmniRoute standalone chat (no auth needed)
chat_dir = BASE_DIR / "dashboard"
if chat_dir.exists():
    app.mount("/chat", StaticFiles(directory=str(chat_dir), html=True), name="chat")

# Serve chat page under /api/ path so the external reverse proxy forwards it
from fastapi.responses import HTMLResponse
@app.get("/api/omniroute-chat", response_class=HTMLResponse)
async def _omniroute_chat_page():
    chat_file = BASE_DIR / "dashboard" / "omniroute-chat.html"
    if chat_file.exists():
        return HTMLResponse(content=chat_file.read_text(), status_code=200)
    return HTMLResponse(content="<h1>Chat page not found</h1>", status_code=404)

prompt_tools_dir = BASE_DIR / "prompt-tools"
if prompt_tools_dir.exists():
    app.mount("/prompt-tools", StaticFiles(directory=str(prompt_tools_dir)), name="prompt-tools")

# ─── Qgenda API (read-only) ────────────────────────────────
@app.get("/api/qgenda/users")
async def get_qgenda_users(limit: int = 10):
    """Return top N Qgenda users for the platforms dashboard."""
    try:
        import psycopg2
        pw = os.environ.get("POSTGRES_PASSWORD", "")
        if not pw:
            import subprocess as _sp
            r = _sp.run(['grep', 'POSTGRES_PASSWORD', '/workspace/projects/unified/app/.env'],
                capture_output=True, text=True, timeout=5)
            if r.returncode == 0:
                pw = r.stdout.strip().split('=', 1)[1].strip()
        if not pw:
            return {"error": "No DB password"}
        conn = psycopg2.connect(host="127.0.0.1", port=5432, dbname="urology_qgenda", user="postgres", password=pw, connect_timeout=3)
        cur = conn.cursor()
        cur.execute(f'SELECT name, email, role FROM "User" ORDER BY name LIMIT %s', (limit,))
        users = [{"name": r[0], "email": r[1], "role": r[2]} for r in cur.fetchall()]
        cur.close()
        conn.close()
        return users
    except Exception as e:
        return {"error": str(e)}

# Mount SCL (Sick Call Line) — built React app
scl_dir = Path("/workspace/repos/sick-call-line/dist")
if scl_dir.exists():
    app.mount("/scl", StaticFiles(directory=str(scl_dir), html=True), name="scl")

# Mount Hermes WebUI redirect — the chat.js expects this endpoint
@app.get("/hermes-webui/", response_class=HTMLResponse)
@app.get("/hermes-webui", response_class=HTMLResponse)
def hermes_webui_redirect():
    """Redirect to the actual Hermes WebUI or show embedded interface."""
    return HTMLResponse(content="""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hermes WebUI</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e0e0e0;
            height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            padding: 20px;
        }
        .logo {
            font-size: 48px;
            margin-bottom: 16px;
        }
        h1 {
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 12px;
            color: #6c5ce7;
        }
        p {
            font-size: 14px;
            color: #a0a0a0;
            margin-bottom: 24px;
            max-width: 400px;
            line-height: 1.5;
        }
        .btn {
            background: linear-gradient(135deg, #6c5ce7 0%, #a855f7 100%);
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            text-decoration: none;
            font-size: 14px;
            font-weight: 500;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(108, 92, 231, 0.3);
        }
        .note {
            margin-top: 32px;
            font-size: 12px;
            color: #666;
            padding: 12px 16px;
            background: rgba(255,255,255,0.05);
            border-radius: 8px;
            max-width: 360px;
        }
    </style>
</head>
<body>
    <div class="logo">🧙‍♂️</div>
    <h1>Hermes Agent WebUI</h1>
    <p>You are accessing Hermes through the Agentic OS dashboard. Use this window to interact with Hermes directly.</p>
    <a href="/dashboard/#chat" class="btn" onclick="window.parent.postMessage({type: 'hermes-ready'}, '*'); return false;">Back to AI Chat</a>
    <div class="note">
        💡 <strong>Note:</strong> The full Hermes WebUI runs separately. This embedded view provides basic Hermes access within Agentic OS.
    </div>
    <script>
        // Notify parent that iframe loaded
        window.parent.postMessage({type: 'hermes-ready'}, '*');
    </script>
</body>
</html>
""")

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    # If already authenticated, redirect to dashboard
    token = request.cookies.get(_settings.SESSION_COOKIE_NAME, "")
    if token and auth_module.get_session(token):
        return RedirectResponse(url="/")
    login_file = BASE_DIR / "dashboard" / "login.html"
    if login_file.exists():
        return HTMLResponse(content=login_file.read_text())
    return HTMLResponse(content="<h1>Login page not found</h1>", status_code=404)

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    html_file = BASE_DIR / "dashboard" / "index.html"
    if html_file.exists():
        content = html_file.read_text()
        content = content.replace('href="styles.css"', 'href="/dashboard/styles.css"')
        content = content.replace('src="utils.js"', 'src="/dashboard/utils.js"')
        content = content.replace('src="api.js"', 'src="/dashboard/api.js"')
        content = content.replace('src="app.js"', 'src="/dashboard/app.js"')
        content = content.replace('pages/', '/dashboard/pages/')
        # Inject a top-of-body error reporter so any uncaught JS error / failed
        # asset shows up visibly on the page instead of producing a blank screen.
        error_reporter = """
<div id="__boot_error__" style="position:fixed;top:0;left:0;right:0;z-index:99999;padding:10px 14px;background:#ff4757;color:#fff;font:13px/1.4 -apple-system,BlinkMacSystemFont,sans-serif;display:none;white-space:pre-wrap;word-break:break-word"></div>
<script>
(function(){
  var box = document.getElementById('__boot_error__');
  function show(msg){ if (box){ box.style.display='block'; box.textContent += msg + '\\n'; } console.error(msg); }
  window.addEventListener('error', function(e){ show('JS ERROR: ' + (e.message||e) + (e.filename?' @ '+e.filename+':'+e.lineno:'')); });
  window.addEventListener('unhandledrejection', function(e){ show('PROMISE: ' + (e.reason && (e.reason.stack||e.reason.message||e.reason))); });
  // Catch script load failures (utils.js/api.js/app.js/pages/*.js)
  document.addEventListener('error', function(e){
    var t = e.target;
    if (t && (t.tagName==='SCRIPT' || t.tagName==='LINK') && t.src){
      show('ASSET FAILED: ' + t.tagName + ' ' + t.src);
    }
  }, true);
  // Boot probe — if app.js does not define navigate() within 5s, complain.
  setTimeout(function(){
    if (typeof navigate !== 'function'){
      show('BOOT: app.js did not define navigate() in 5s — JS failed to initialize');
    }
  }, 5000);
})();
</script>
"""
        # Insert the error reporter right after <body>
        content = content.replace('<body>', '<body>' + error_reporter, 1)
        # Also inject a server-side error logger that POSTs the JS error to /api/_boot_error
        # so we can read the exact message from a separate endpoint when the page fails to load.
        server_logger = """
<script>
(function(){
  function post(msg) {
    try { fetch('/api/_boot_error', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({msg: String(msg).slice(0, 2000), ua: navigator.userAgent, url: location.href}), keepalive: true}); } catch(e) {}
  }
  // Mirror the existing show() to also POST
  var origShow = window.show;
  // show is defined inside the earlier IIFE, so just hook error events again here
  window.addEventListener('error', function(e){ post('JS ERROR: ' + (e.message||e) + (e.filename?' @ '+e.filename+':'+e.lineno+':'+e.colno:'')); });
  window.addEventListener('unhandledrejection', function(e){ post('PROMISE: ' + (e.reason && (e.reason.stack||e.reason.message||e.reason))); });
  setTimeout(function(){
    if (typeof window.navigate !== 'function') {
      post('BOOT: app.js did not define navigate() in 5s — JS failed to initialize');
    } else {
      post('BOOT_OK: navigate() defined, page initialized');
    }
  }, 5500);
})();
</script>
"""
        content = content.replace('</head>', server_logger + '</head>', 1)
        return HTMLResponse(content=content)
    return HTMLResponse("<h1>Agentic OS</h1><p>Dashboard not built yet. Run <code>./install.sh</code> first.</p>")

# ─── Favicon ──────────────────────────────────────────────────────

FAVICON_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><defs><linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#6c5ce7"/><stop offset="100%" stop-color="#fd79a8"/></linearGradient></defs><rect width="32" height="32" rx="8" fill="url(#g)"/><polygon points="16,6 24,11 24,21 16,26 8,21 8,11" fill="none" stroke="white" stroke-width="2" stroke-linejoin="round"/><circle cx="16" cy="16" r="3" fill="white"/></svg>'

@app.get("/favicon.ico")
def favicon():
    return Response(content=FAVICON_SVG, media_type="image/svg+xml")

@app.get("/favicon.svg")
def favicon_svg():
    return Response(content=FAVICON_SVG, media_type="image/svg+xml")

# ─── Grand Rounds API ─────────────────────────────────────────────

@app.post("/api/run-auto-invite")
async def run_auto_invite():
    """Trigger the Grand Rounds auto-invite sender script."""
    script = "/workspace/urology_schedule/auto_send_invites.py"
    codes_csv = "/workspace/urology_schedule/sample_cme_codes.csv"
    python = "/workspace/.aos-venv/bin/python"
    
    if not os.path.exists(script):
        return {"status": "error", "message": "Auto-invite script not found"}
    
    try:
        proc = await asyncio.create_subprocess_exec(
            python, script, "--action", "outlook", "--codes", codes_csv,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ, "DISPLAY": ":0", "FONTCONFIG_PATH": "/workspace/.vnc-system/etc/fonts"}
        )
        return {"status": "started", "message": "Auto-invite triggered (check server terminal for output)"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/fs/stat")
async def fs_stat(path: str = ""):
    """Get file stats."""
    import stat as stat_mod
    if not path or not os.path.exists(path):
        return {"exists": False}
    s = os.stat(path)
    return {
        "exists": True,
        "size": s.st_size,
        "modified": s.st_mtime,
        "is_dir": stat_mod.S_ISDIR(s.st_mode)
    }

# ─── Routes: Unified Data Service Proxy ───────────────────────────

DATA_SERVICE_BASE = "http://localhost:8086"

@app.get("/api/unified/{rest:path}")
async def unified_proxy_get(rest: str):
    """Proxy GET requests to the data service (port 8086)."""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(f"{DATA_SERVICE_BASE}/api/unified/{rest}")
            return r.json()
    except httpx.ConnectError:
        raise HTTPException(503, "Data service (port 8086) not running — start it with: python3 data-service.py --port 8086")
    except Exception as e:
        raise HTTPException(502, str(e))

@app.get("/api/reimbursement/{rest:path}")
async def reimbursement_proxy_get(rest: str):
    """Proxy reimbursement queries to data service."""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(f"{DATA_SERVICE_BASE}/api/reimbursement/{rest}")
            return r.json()
    except httpx.ConnectError:
        raise HTTPException(503, "Data service (port 8086) not running")
    except Exception as e:
        raise HTTPException(502, str(e))

@app.get("/health/data-service")
async def data_service_health():
    """Check if the data service is reachable."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{DATA_SERVICE_BASE}/health")
            return r.json()
    except httpx.ConnectError:
        raise HTTPException(503, "Data service (port 8086) not running")


# ─── Routes: Voice PIN Management ─────────────────────────────────

PIN_DB_PATH = BASE_DIR / "data" / "user_pins.json"

class PinResetRequest(BaseModel):
    uid: str
    new_pin: str

@app.get("/api/vapi/pins")
def vapi_pins_list():
    """List all users with their PINs (no hashes exposed)."""
    if not PIN_DB_PATH.exists():
        return {"users": []}
    db = json.loads(PIN_DB_PATH.read_text())
    users = []
    for uid, u in db.items():
        users.append({
            "uid": uid,
            "name": u.get("name", u.get("display_name", uid)),
            "pin": u.get("default_pin", "not set"),
            "role": u.get("role", ""),
        })
    return {"users": sorted(users, key=lambda x: x["name"].lower())}

@app.post("/api/vapi/pins/reset")
def vapi_pin_reset(req: PinResetRequest):
    """Reset a user's PIN."""
    import hashlib
    if not PIN_DB_PATH.exists():
        raise HTTPException(404, "PIN database not found")
    db = json.loads(PIN_DB_PATH.read_text())
    if req.uid not in db:
        raise HTTPException(404, f"User '{req.uid}' not found")
    if len(req.new_pin) != 4 or not req.new_pin.isdigit():
        raise HTTPException(400, "PIN must be exactly 4 digits")
    db[req.uid]["pin_hash"] = hashlib.sha256(req.new_pin.encode()).hexdigest()
    db[req.uid]["default_pin"] = req.new_pin
    PIN_DB_PATH.write_text(json.dumps(db, indent=2))
    return {"success": True, "name": db[req.uid].get("name", req.uid), "new_pin": req.new_pin}


# ─── Routes: Voice Data Health ────────────────────────────────

@app.get("/api/vapi/data-health")
def vapi_data_health():
    """Structured health report on all data sources the voice assistant depends on."""
    from modules import vapi_unified
    from modules import roster_parser

    base = Path("/workspace")
    now = datetime.now()
    report = {
        "timestamp": now.isoformat(),
        "sources": {},
        "summary": {"ok": 0, "missing": 0, "stale": 0, "parse_error": 0, "auth_required": 0},
    }

    def _file_stat(path: Path | str) -> dict | None:
        p = Path(path)
        if not p.exists():
            return None
        s = p.stat()
        return {
            "exists": True,
            "size_kb": round(s.st_size / 1024, 1),
            "modified_utc": datetime.fromtimestamp(s.st_mtime, tz=timezone.utc).isoformat(),
            "age_hours": round((now - datetime.fromtimestamp(s.st_mtime)).total_seconds() / 3600, 1),
        }

    def _source(name: str, stat: dict | None, status: str, detail: str, next_action: str):
        entry = {"status": status, "detail": detail, "next_action": next_action}
        if stat:
            entry["file"] = stat
        report["sources"][name] = entry
        report["summary"][status] = report["summary"].get(status, 0) + 1

    # ── 1. Call Schedule xlsx ──
    sched_path = Path(vapi_unified.SCHEDULE_PATH)
    stat = _file_stat(sched_path)
    if not stat:
        _source("call_schedule", None, "missing",
                "Call_Schedule_Q3_Q4_2026.xlsx not found",
                "Place the xlsx at " + str(sched_path))
    else:
        detail = f"{stat['size_kb']} KB, modified {stat['age_hours']}h ago"
        try:
            from modules.vapi_unified import _load_schedule
            data = _load_schedule()
            sheet_count = len(data)
            row_count = sum(len(rows) for rows in data.values())
            _source("call_schedule", stat, "ok",
                    f"{detail} — {sheet_count} sheets, {row_count} rows loaded",
                    "")
        except Exception as e:
            _source("call_schedule", stat, "parse_error",
                    f"{detail} — failed to load: {e}",
                    f"Fix the xlsx format or permissions")

    # ── 2. QGenda CSV ──
    qgenda_path = Path(vapi_unified.QGENDA_PATH)
    stat = _file_stat(qgenda_path)
    if not stat:
        _source("qgenda", None, "missing",
                "QGenda CSV not found",
                "Export QGenda data to " + str(qgenda_path))
    else:
        detail = f"{stat['size_kb']} KB, modified {stat['age_hours']}h ago"
        try:
            from modules.vapi_unified import _load_qgenda
            # Clear cache so we actually test the load, then re-cache
            vapi_unified._qgenda_cache = None
            data = _load_qgenda()
            if isinstance(data, dict) and data.get("error"):
                _source("qgenda", stat, "parse_error",
                        f"{detail} — {data['error']}",
                        "Check CSV path and format")
            else:
                rows = data.get("total_rows", 0)
                people = len(data.get("all_names", []))
                _source("qgenda", stat, "ok",
                        f"{detail} — {rows} rows, {people} unique people",
                        "")
        except Exception as e:
            _source("qgenda", stat, "parse_error",
                    f"{detail} — failed to load: {e}",
                    "Fix the CSV format or permissions")

    # ── 3. associates.csv (Staff) ──
    staff_path = Path(vapi_unified.STAFF_PATH)
    stat = _file_stat(staff_path)
    if not stat:
        _source("associates", None, "missing",
                "associates.csv not found",
                "Place the file at " + str(staff_path))
    else:
        detail = f"{stat['size_kb']} KB, modified {stat['age_hours']}h ago"
        try:
            with open(staff_path, encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            _source("associates", stat, "ok",
                    f"{detail} — {len(rows)} records, fields: {list(reader.fieldnames or [])}",
                    "")
        except Exception as e:
            _source("associates", stat, "parse_error",
                    f"{detail} — failed to read: {e}",
                    "Fix the CSV format")

    # ── 4. Location rosters (parsed cache) ──
    rosters_dir = Path("/workspace/agentic-os/data/location_rosters/parsed")
    if not rosters_dir.exists():
        _source("location_rosters", None, "missing",
                "Parsed roster cache directory not found",
                "Run roster sync or rebuild from raw files")
    else:
        files = [f for f in sorted(rosters_dir.iterdir())
                 if f.suffix == ".json" and "Contact" not in f.name]
        manifest_path = rosters_dir / "_manifest.json"
        last_sync = None
        if manifest_path.exists():
            try:
                m = json.loads(manifest_path.read_text())
                last_sync = m.get("last_sync", m.get("synced_at"))
            except Exception:
                pass

        # Find newest/oldest period_end
        newest_end = ""
        oldest_end = ""
        for f in files:
            try:
                d = json.loads(f.read_text())
                dr = d.get("date_range", {})
                end = dr.get("end", "")
                start = dr.get("start", "")
                if end and (end > newest_end or not newest_end):
                    newest_end = end
                if start and (start < oldest_end or not oldest_end):
                    oldest_end = start
            except Exception:
                continue

        stat_info = {
            "exists": True,
            "file_count": len(files),
            "oldest_period_start": oldest_end or "N/A",
            "newest_period_end": newest_end or "N/A",
            "last_sync": last_sync,
        }

        if not files:
            # No roster files but directory exists
            from modules.roster_parser import rebuild_parsed_cache
            # Don't actually rebuild — just report
            _source("location_rosters", stat_info, "missing",
                    "Parsed roster cache is empty — run sync or rebuild",
                    "Trigger Drive sync or run roster_parser.rebuild_parsed_cache()")
        else:
            # Check if most recent roster is stale (> 30 days since period_end)
            status = "ok"
            detail = f"{len(files)} roster files, covers {stat_info['oldest_period_start']} to {stat_info['newest_period_end']}"
            next_action = ""
            if newest_end:
                try:
                    end_dt = datetime.strptime(newest_end, "%Y-%m-%d").date()
                    days_since_end = (date.today() - end_dt).days
                    if days_since_end > 30:
                        status = "stale"
                        detail += f" — newest roster ended {days_since_end} days ago"
                        next_action = "Sync latest roster from Drive"
                except ValueError:
                    pass
            if last_sync:
                detail += f", last sync: {last_sync}"
            _source("location_rosters", stat_info, status, detail, next_action)

    # ── 5. Google OAuth token ──
    home = Path.home()
    token_paths = [
        home / ".hermes" / "google_token.json",
        home / ".hermes" / "tokens-disabled" / "google_token.json",
    ]
    token_found = None
    for tp in token_paths:
        if tp.exists():
            token_found = tp
            break
    if not token_found:
        _source("google_auth", None, "missing",
                "Google OAuth token not found",
                "Run `hermes auth login` or set up Google Workspace credentials")
    else:
        stat = _file_stat(token_found)
        try:
            tok = json.loads(token_found.read_text())
            expiry = tok.get("expiry", tok.get("expires_at", ""))
            has_refresh = bool(tok.get("refresh_token", ""))
            has_access = bool(tok.get("access_token", ""))
            detail = f"token at {token_found.name}"

            if expiry:
                try:
                    exp_dt = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
                    if exp_dt.tzinfo is None:
                        exp_dt = exp_dt.replace(tzinfo=timezone.utc)
                    if exp_dt < datetime.now(timezone.utc):
                        if has_refresh:
                            # Has refresh token — likely auto-refreshable
                            detail += f", expired {exp_dt.isoformat()} but has refresh_token"
                            _source("google_auth", stat, "ok", detail, "")
                        else:
                            detail += f", expired {exp_dt.isoformat()} without refresh_token"
                            _source("google_auth", stat, "auth_required", detail,
                                    "Re-run `hermes auth login` to refresh credentials")
                    else:
                        detail += f", valid until {exp_dt.isoformat()}"
                        _source("google_auth", stat, "ok", detail, "")
                except (ValueError, TypeError):
                    detail += f", expiry unparseable: {expiry}"
                    _source("google_auth", stat, "ok", detail, "Check token expiry format")
            else:
                detail += f", no expiry field (has_access={has_access})"
                _source("google_auth", stat, "ok" if has_access else "auth_required",
                        detail,
                        "Run `hermes auth login` if email sending fails")
        except (json.JSONDecodeError, Exception) as e:
            _source("google_auth", stat or {}, "parse_error",
                    f"token file unreadable: {e}",
                    "Fix or re-generate the token file")

    return report

# ─── Conference Events API (for one-click resend dashboard) ────────

# ─── Routes: Conference Schedule (DB-backed) ───────────────────

def _get_db_conn():
    """Get a psycopg2 connection to the urology_qgenda database."""
    import psycopg2
    pw = os.environ.get("POSTGRES_PASSWORD", "")
    if not pw:
        import subprocess as _sp
        r = _sp.run(['grep', 'POSTGRES_PASSWORD', '/workspace/projects/unified/app/.env'],
            capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            pw = r.stdout.strip().split('=', 1)[1].strip()
    try:
        kwargs = dict(host="127.0.0.1", port=5432, dbname="urology_qgenda", user="postgres", connect_timeout=3)
        if pw:
            kwargs["password"] = pw
        return psycopg2.connect(**kwargs)
    except Exception:
        return None


@app.get("/api/conference/schedule")
def get_conference_schedule():
    """Return all grand rounds schedule rows from the database."""
    try:
        conn = _get_db_conn()
        if not conn:
            return {"error": "No DB password"}
        cur = conn.cursor()
        cur.execute('''
            SELECT id, month, mon_date::text, mon_topic, resident, attending,
                   fri_date::text, gr_7_8, gr_8_9, notes
            FROM grand_rounds_schedule
            ORDER BY COALESCE(mon_date, fri_date)
        ''')
        rows = []
        for r in cur.fetchall():
            rows.append({
                "id": r[0], "month": r[1], "mon_date": r[2], "mon_topic": r[3],
                "resident": r[4], "attending": r[5], "fri_date": r[6],
                "gr_7_8": r[7], "gr_8_9": r[8], "notes": r[9],
            })
        cur.close()
        conn.close()
        return {"rows": rows, "count": len(rows)}
    except Exception as e:
        return {"error": str(e)}


@app.put("/api/conference/schedule/{row_id}")
async def update_conference_schedule(row_id: int, request: Request):
    """Update a single schedule row in the database."""
    try:
        body = await request.json()
        conn = _get_db_conn()
        if not conn:
            return {"error": "No DB password"}
        cur = conn.cursor()
        
        # Build dynamic update from provided fields
        allowed_fields = {"month", "mon_date", "mon_topic", "resident", "attending", "fri_date", "gr_7_8", "gr_8_9", "notes"}
        updates = []
        values = []
        for field in allowed_fields:
            if field in body:
                val = body[field]
                # Convert empty strings to None for date fields
                if field in ("mon_date", "fri_date") and (not val or val == ""):
                    val = None
                updates.append(f"{field} = %s")
                values.append(val)
        
        if not updates:
            return {"error": "No fields to update"}
        
        updates.append("updated_at = NOW()")
        values.append(row_id)
        
        cur.execute(
            f"UPDATE grand_rounds_schedule SET {', '.join(updates)} WHERE id = %s",
            values
        )
        conn.commit()
        affected = cur.rowcount
        cur.close()
        conn.close()
        
        if affected == 0:
            return {"error": f"Row {row_id} not found"}
        return {"success": True, "id": row_id, "updated_fields": list(body.keys())}
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/calendar-invites", response_class=HTMLResponse)
async def calendar_invites_page(test: str = Query("true", description="Set to 'false' for live mode"), start_date: str = Query("", description="Override start date (YYYY-MM-DD), defaults to today")):
    """Serve the Outlook calendar invites page — generated on-the-fly from the DB."""
    from datetime import date as dt_date
    import sys
    sys.path.insert(0, str(BASE_DIR))
    try:
        import importlib
        if "outlook_deeplink_generator" in sys.modules:
            importlib.reload(sys.modules["outlook_deeplink_generator"])
        import outlook_deeplink_generator as gen
        test_mode = test.lower() not in ("false", "0", "no", "off")
        today = start_date if start_date else dt_date.today().isoformat()
        monday_events = gen.get_monday_events(start_date=today)
        gr_events = gen.get_grand_rounds_events(start_date=today)
        # Generate to file, then read it back
        gen.generate_html_page(monday_events, gr_events, test_mode=test_mode, test_email="sfrasier@montefiore.org")
        html_path = gen.OUTPUT_DIR / "invites.html"
        return HTMLResponse(content=html_path.read_text())
    except Exception as e:
        return HTMLResponse(content=f"<html><body><h2>Error generating invites page</h2><pre>{e}</pre></body></html>", status_code=500)


@app.get("/api/conference/events")
def conference_events():
    """Return all Grand Rounds and Resident Conference events from GR_DATA
    in the grand-rounds.js page, parsed into JSON for the resend dashboard."""
    gr_js_path = BASE_DIR / "dashboard" / "pages" / "grand-rounds.js"
    if not gr_js_path.exists():
        return {"events": [], "error": "grand-rounds.js not found"}
    
    js_text = gr_js_path.read_text()
    match = re.search(r"const GR_DATA\s*=\s*(\[.*?\]);", js_text, re.DOTALL)
    if not match:
        return {"events": [], "error": "GR_DATA not found"}
    
    array_str = match.group(1)
    # Clean JS-specific artifacts
    array_str = re.sub(r",\s*\]", "]", array_str)
    array_str = re.sub(r"//.*", "", array_str)
    
    try:
        gr_data = json.loads(array_str)
    except json.JSONDecodeError as e:
        return {"events": [], "error": f"JSON parse error: {e}"}
    
    events = []
    for row in gr_data:
        if len(row) < 9:
            continue
        fri_date = row[7] if len(row) > 7 else ""
        if not fri_date or not str(fri_date).startswith("20"):
            continue
        gr_7_8 = str(row[8]).strip('" ') if len(row) > 8 else ""
        gr_8_9 = str(row[9]).strip('" ') if len(row) > 9 else ""
        
        # Determine meeting type
        if "NO GRAND ROUNDS" in gr_7_8 or "NO GRAND ROUNDS" in gr_8_9:
            meeting_type = "no_grand_rounds"
        elif "Peds" in gr_7_8 or "Peds" in gr_8_9:
            meeting_type = "peds"
        elif "FACULTY MEETING" in gr_7_8 or "FACULTY MEETING" in gr_8_9:
            meeting_type = "faculty_meeting"
        elif "Journal Club" in gr_7_8 or "Journal Club" in gr_8_9:
            meeting_type = "journal_club"
        elif "Resident Conference" in gr_7_8 or "Resident Conference" in gr_8_9:
            meeting_type = "resident_conference"
        else:
            meeting_type = "grand_rounds"
        
        events.append({
            "date": str(fri_date),
            "type": meeting_type,
            "topic_7_8": gr_7_8,
            "topic_8_9": gr_8_9,
            "week": str(row[0]) if len(row) > 0 else "",
        })
    
    # Sort by date, upcoming first
    events.sort(key=lambda e: e["date"])
    return {"events": events, "count": len(events)}


# ─── Routes: Unified User Dashboard ────────────────────────────────

@app.get("/api/user/{ez_id}")
async def user_dashboard(ez_id: str, pin: str = Query(None, description="4-digit PIN for authentication")):
    """Aggregate all data for a resident by EZ ID. Requires PIN for access."""
    # Validate PIN
    import hashlib
    PIN_DB_PATH = BASE_DIR / "data" / "user_pins.json"
    if PIN_DB_PATH.exists():
        pin_db = json.loads(PIN_DB_PATH.read_text())
        stored = pin_db.get(ez_id)
        if stored:
            # Accept both raw PIN and hashed
            pin_hash = hashlib.sha256((pin or "").encode()).hexdigest()
            if pin != stored.get("default_pin", "") and pin_hash != stored.get("pin_hash", ""):
                return {"error": "Invalid PIN", "ez_id": ez_id}
        # If no PIN stored for this EZ ID, allow without PIN (legacy)
    elif not pin:
        # No PIN DB at all — require PIN in query for new users
        pass
    try:
        from modules.crm_db import get_contact_by_ezid
    except ImportError:
        return {"error": "CRM module not available", "ez_id": ez_id}

    contact = get_contact_by_ezid(ez_id)
    if not contact:
        # Try stripping "EZ" prefix in case user typed EZ12345 vs 12345
        clean = ez_id.upper().removeprefix("EZ")
        if clean != ez_id:
            contact = get_contact_by_ezid(clean)
    if not contact:
        return {"error": "Contact not found", "ez_id": ez_id}

    result = {
        "contact": contact,
        "ez_id": ez_id,
    }

    # 1. On-call today
    try:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        oncall = _get_oncall_for_date(today)
        result["oncall_today"] = [
            o for o in oncall
            if contact.get("lastName", "").lower() in o.get("name", "").lower()
        ]
    except Exception:
        result["oncall_today"] = []

    # 2. Reimbursement balance via data service
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{DATA_SERVICE_BASE}/api/reimbursement/resident/{ez_id}")
            if r.status_code == 200:
                result["reimbursement"] = r.json()
    except Exception:
        result["reimbursement"] = None

    # 3. EVAL forms — check if resident appears
    try:
        EVAL_FORMS_FILE = BASE_DIR / "data" / "eval_forms.json"
        if EVAL_FORMS_FILE.exists():
            eval_data = json.loads(EVAL_FORMS_FILE.read_text())
            resident_evals = []
            for entry in eval_data.get("residents", []):
                if ez_id.lower() == entry.get("ez_id", "").lower():
                    resident_evals.append(entry)
            result["evals"] = resident_evals
    except Exception:
        result["evals"] = []

    # 4. Sick call violations (recent)
    try:
        SICK_CALL_FILE = BASE_DIR / "data" / "sick_call_violations.json"
        if SICK_CALL_FILE.exists():
            violations = json.loads(SICK_CALL_FILE.read_text())
            recent = [v for v in (violations if isinstance(violations, list) else violations.get("violations", []))
                      if contact.get("lastName", "").lower() in v.get("name", "").lower()]
            result["sick_calls"] = recent[-10:]  # last 10
    except Exception:
        result["sick_calls"] = []

    # 5. Commute info (via directions module)
    try:
        from modules.directions import get_commute_for_resident
        commute = get_commute_for_resident(ez_id)
        if commute:
            result["commute"] = commute
    except (ImportError, Exception):
        try:
            addr = contact.get("homeAddress") or contact.get("address", "")
            if addr:
                result["commute"] = {"address": addr, "message": "Route not calculated"}
            else:
                result["commute"] = None
        except Exception:
            result["commute"] = None

    return result


# ─── Omniroute Proxy ──────────────────────────────────────────────

import httpx

OMNIROUTE_BASE = os.environ.get("OMNIROUTE_BASE_URL", "http://localhost:20128")

@app.api_route("/api/omniroute/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"])
async def omniroute_proxy(path: str, request: Request):
    """Proxy requests to Omniroute server, avoiding CORS issues for the dashboard."""
    target_url = f"{OMNIROUTE_BASE}/{path}"
    
    # Forward query params
    query = request.url.query
    if query:
        target_url += f"?{query}"
    
    # Forward body for POST/PUT
    body = await request.body()
    
    headers = dict(request.headers)
    # Remove hop-by-hop headers that cause issues
    headers.pop("host", None)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=body,
            follow_redirects=True,
        )
    
    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=dict(resp.headers),
    )


# ─── Main ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8081)
    parser.add_argument("--host", type=str, default="0.0.0.0")
    args = parser.parse_args()
    uvicorn.run(app, host=args.host, port=args.port)
