"""
Agentic OS — Kanban Board Module
Task management with columns, comments, links, and subtask decomposition.
"""
import json
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/api/kanban", tags=["kanban"])

# Paths — will be set by init_app()
KANBAN_DIR = None

def init_app(base_dir: Path):
    global KANBAN_DIR
    KANBAN_DIR = base_dir / "data" / "kanban"
    KANBAN_DIR.mkdir(parents=True, exist_ok=True)

# ─── Models ──────────────────────────────────────────────────

class KanbanTaskCreate(BaseModel):
    title: str
    body: str = ""
    status: str = "triage"
    priority: str = "medium"
    assignee: str = ""

class KanbanTaskUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assignee: Optional[str] = None

class KanbanComplete(BaseModel):
    summary: str = ""

class KanbanBlock(BaseModel):
    reason: str = ""

class KanbanCommentCreate(BaseModel):
    message: str

class KanbanLinkCreate(BaseModel):
    parent_id: str
    child_id: str

# ─── Helpers ──────────────────────────────────────────────────

def get_timestamp():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()

def ensure_dir(d: Path):
    d.mkdir(parents=True, exist_ok=True)

def load_kanban_tasks():
    ensure_dir(KANBAN_DIR)
    tasks = []
    for f in sorted(KANBAN_DIR.glob("*.json")):
        tasks.append(json.loads(f.read_text()))
    return tasks

def save_kanban_task(task: dict):
    ensure_dir(KANBAN_DIR)
    (KANBAN_DIR / f"{task['id']}.json").write_text(json.dumps(task, indent=2))

# ─── Routes ──────────────────────────────────────────────────

@router.get("/board")
def kanban_board(status: Optional[str] = None):
    try:
        tasks = load_kanban_tasks()
        if status:
            tasks = [t for t in tasks if t.get("status") == status]
        columns = {"triage": [], "todo": [], "ready": [], "in_progress": [], "blocked": [], "done": []}
        for t in tasks:
            s = t.get("status", "triage")
            if s in columns:
                columns[s].append(t)
        return {"columns": columns, "total": len(tasks)}
    except Exception as e:
        return {"error": str(e), "columns": {}, "total": 0}

@router.get("/tasks/{task_id}")
def kanban_get_task(task_id: str):
    path = KANBAN_DIR / f"{task_id}.json"
    if not path.exists():
        raise HTTPException(404, "Task not found")
    return json.loads(path.read_text())

@router.post("/tasks")
def kanban_create_task(data: KanbanTaskCreate):
    try:
        task = {
            "id": str(uuid.uuid4())[:8],
            "title": data.title,
            "body": data.body,
            "status": data.status,
            "priority": data.priority,
            "assignee": data.assignee,
            "comments": [],
            "links": [],
            "created": get_timestamp(),
            "updated": get_timestamp(),
        }
        save_kanban_task(task)
        return task
    except Exception as e:
        raise HTTPException(500, str(e))

@router.patch("/tasks/{task_id}")
def kanban_update_task(task_id: str, data: KanbanTaskUpdate):
    path = KANBAN_DIR / f"{task_id}.json"
    if not path.exists():
        raise HTTPException(404, "Task not found")
    task = json.loads(path.read_text())
    for field in ["title", "body", "status", "priority", "assignee"]:
        val = getattr(data, field, None)
        if val is not None:
            task[field] = val
    task["updated"] = get_timestamp()
    save_kanban_task(task)
    return task

@router.post("/tasks/{task_id}/complete")
def kanban_complete_task(task_id: str, data: KanbanComplete):
    path = KANBAN_DIR / f"{task_id}.json"
    if not path.exists():
        raise HTTPException(404, "Task not found")
    task = json.loads(path.read_text())
    task["status"] = "done"
    task["summary"] = data.summary
    task["completed_at"] = get_timestamp()
    task["updated"] = get_timestamp()
    save_kanban_task(task)
    return task

@router.post("/tasks/{task_id}/block")
def kanban_block_task(task_id: str, data: KanbanBlock):
    path = KANBAN_DIR / f"{task_id}.json"
    if not path.exists():
        raise HTTPException(404, "Task not found")
    task = json.loads(path.read_text())
    task["status"] = "blocked"
    task["block_reason"] = data.reason
    task["updated"] = get_timestamp()
    save_kanban_task(task)
    return task

@router.post("/tasks/{task_id}/unblock")
def kanban_unblock_task(task_id: str):
    path = KANBAN_DIR / f"{task_id}.json"
    if not path.exists():
        raise HTTPException(404, "Task not found")
    task = json.loads(path.read_text())
    task["status"] = "ready"
    task["block_reason"] = ""
    task["updated"] = get_timestamp()
    save_kanban_task(task)
    return task

@router.post("/tasks/{task_id}/comments")
def kanban_add_comment(task_id: str, data: KanbanCommentCreate):
    path = KANBAN_DIR / f"{task_id}.json"
    if not path.exists():
        raise HTTPException(404, "Task not found")
    task = json.loads(path.read_text())
    comment = {
        "id": str(uuid.uuid4())[:8],
        "message": data.message,
        "timestamp": get_timestamp(),
    }
    task.setdefault("comments", []).append(comment)
    task["updated"] = get_timestamp()
    save_kanban_task(task)
    return task

@router.post("/links")
def kanban_add_link(data: KanbanLinkCreate):
    for tid in [data.parent_id, data.child_id]:
        path = KANBAN_DIR / f"{tid}.json"
        if not path.exists():
            raise HTTPException(404, f"Task {tid} not found")
        t = json.loads(path.read_text())
        t.setdefault("links", [])
        link = {"parent": data.parent_id, "child": data.child_id}
        if link not in t["links"]:
            t["links"].append(link)
        t["updated"] = get_timestamp()
        save_kanban_task(t)
    return {"status": "linked"}

@router.delete("/links")
def kanban_remove_link(parent_id: str = Query(...), child_id: str = Query(...)):
    for tid in [parent_id, child_id]:
        path = KANBAN_DIR / f"{tid}.json"
        if path.exists():
            t = json.loads(path.read_text())
            t.setdefault("links", [])
            t["links"] = [l for l in t["links"] if not (l.get("parent") == parent_id and l.get("child") == child_id)]
            t["updated"] = get_timestamp()
            save_kanban_task(t)
    return {"status": "unlinked"}

@router.post("/dispatch")
def kanban_dispatch():
    return {"status": "dispatch_triggered", "message": "Dispatcher notified"}

@router.post("/tasks/{task_id}/specify")
def kanban_specify_task(task_id: str):
    path = KANBAN_DIR / f"{task_id}.json"
    if not path.exists():
        raise HTTPException(404, "Task not found")
    task = json.loads(path.read_text())
    if task.get("status") == "triage":
        task["status"] = "todo"
        task["updated"] = get_timestamp()
        save_kanban_task(task)
    return task

@router.post("/tasks/{task_id}/decompose")
def kanban_decompose_task(task_id: str):
    path = KANBAN_DIR / f"{task_id}.json"
    if not path.exists():
        raise HTTPException(404, "Task not found")
    task = json.loads(path.read_text())
    children = []
    for i, subtask in enumerate(task.get("body", "").split("\n")):
        subtask = subtask.strip().lstrip("-* ")
        if subtask:
            child = {
                "id": str(uuid.uuid4())[:8],
                "title": subtask[:80],
                "body": subtask,
                "status": "todo",
                "priority": task.get("priority", "medium"),
                "comments": [],
                "links": [{"parent": task_id, "child": str(uuid.uuid4())[:8]}],
                "created": get_timestamp(),
                "updated": get_timestamp(),
            }
            save_kanban_task(child)
            children.append(child)
    return {"parent": task_id, "children": children}
