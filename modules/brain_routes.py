"""
Agentic OS — Brain Routes
Extracted from server.py Phase 9 module extraction.
"""
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from modules.config import get_settings

router = APIRouter(prefix="/api/brain", tags=["brain"])

# ─── Models ──────────────────────────────────────────────────────

class BrainUpdate(BaseModel):
    content: str

class TaskUpdate(BaseModel):
    status: str | None = None
    content: str | None = None
    priority: str | None = None
    category: str | None = None
    due_date: str | None = None

# ─── Helpers ─────────────────────────────────────────────────────

def _read_file(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")

def _write_file(path: Path, content: str) -> bool:
    path.write_text(content, encoding="utf-8")
    return True

def _safe_path(base: Path, user_value: str) -> Path:
    """Prevent path traversal."""
    resolved = (base / user_value).resolve()
    base_resolved = base.resolve()
    if not str(resolved).startswith(str(base_resolved)):
        raise HTTPException(400, "Invalid path")
    return resolved

def _list_dir(path: Path):
    if not path.exists():
        return []
    return sorted([p.name for p in path.iterdir() if not p.name.startswith(".")])

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

# ─── Tasks endpoints — reads/writes /workspace/task-list.json ─────
# MUST be defined BEFORE the /{file_name} wildcard routes so specific
# paths like /tasks-data match first instead of being caught by {file_name}.

TASKS_PATH = Path("/workspace/task-list.json")


@router.get("/tasks-data")
def list_tasks():
    """Return the full task list."""
    if not TASKS_PATH.exists():
        return {"tasks": []}
    try:
        tasks = json.loads(TASKS_PATH.read_text(encoding="utf-8"))
        return {"tasks": tasks}
    except (json.JSONDecodeError, OSError):
        return {"tasks": []}


@router.put("/tasks-data")
def save_tasks(data: dict):
    """Replace the entire task list."""
    tasks = data.get("tasks", data)
    TASKS_PATH.write_text(json.dumps(tasks, indent=2), encoding="utf-8")
    # Also sync copy used by the dashboard static serve
    static_copy = Path("/workspace/agentic-os/dashboard/data/tasks.json")
    static_copy.write_text(json.dumps(tasks, indent=2), encoding="utf-8")
    return {"ok": True, "count": len(tasks) if isinstance(tasks, list) else 0}


@router.patch("/tasks-data/{task_id}")
def patch_task(task_id: str, data: TaskUpdate):
    """Update a single task's fields (status, content, priority, category, due_date)."""
    if not TASKS_PATH.exists():
        raise HTTPException(404, "Task list not found")
    try:
        tasks = json.loads(TASKS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        raise HTTPException(500, "Failed to read task list")

    updated = False
    for task in tasks:
        if task.get("id") == task_id:
            if data.status is not None:
                task["status"] = data.status
            if data.content is not None:
                task["content"] = data.content
            if data.priority is not None:
                task["priority"] = data.priority
            if data.category is not None:
                task["category"] = data.category
            if data.due_date is not None:
                task["due_date"] = data.due_date
            updated = True
            break

    if not updated:
        raise HTTPException(404, f"Task '{task_id}' not found")

    TASKS_PATH.write_text(json.dumps(tasks, indent=2), encoding="utf-8")
    static_copy = Path("/workspace/agentic-os/dashboard/data/tasks.json")
    static_copy.write_text(json.dumps(tasks, indent=2), encoding="utf-8")
    return {"ok": True, "task_id": task_id, "status": data.status}


# ─── Brain routes ────────────────────────────────────────────────

@router.get("")
def list_brain():
    base = _get_base_dir()
    brain_dir = base / "brain"
    files = _list_dir(brain_dir)
    brain_data = {}
    for f in files:
        path = brain_dir / f
        brain_data[f] = _read_file(path)
    return brain_data


@router.get("/{file_name}")
def get_brain_file(file_name: str):
    base = _get_base_dir()
    path = _safe_path(base / "brain", file_name)
    if not path.exists() or path.is_dir():
        raise HTTPException(404, "File not found")
    return {"name": file_name, "content": _read_file(path)}


@router.put("/{file_name}")
def update_brain_file(file_name: str, data: BrainUpdate):
    base = _get_base_dir()
    path = _safe_path(base / "brain", file_name)
    _write_file(path, data.content)
    _append_audit(base, {"action": "brain_update", "file": file_name})
    return {"status": "ok", "file": file_name}
