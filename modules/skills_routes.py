"""
Agentic OS — Skills Routes
Extracted from server.py for maintainability. Phase 9 update: self-contained.
"""
import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException

from modules import skill_runner
from modules.config import get_settings

router = APIRouter(prefix="/api/skills", tags=["skills"])


def _get_base_dir() -> Path:
    settings = get_settings()
    return settings.BASE_DIR


def _read_file(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def _safe_path(base: Path, user_value: str) -> Path:
    """Prevent path traversal."""
    resolved = (base / user_value).resolve()
    base_resolved = base.resolve()
    if not str(resolved).startswith(str(base_resolved)):
        raise HTTPException(400, "Invalid path")
    return resolved


@router.get("")
def list_skills():
    base = _get_base_dir()
    skills = []
    skills_dir = base / "skills"
    for d in sorted(skills_dir.iterdir()):
        if d.is_dir() and not d.name.startswith("_"):
            skill_md = _read_file(d / "SKILL.md")
            learnings = _read_file(d / "learnings.md")
            eval_data = {}
            eval_path = d / "eval.json"
            if eval_path.exists():
                eval_data = json.loads(eval_path.read_text())
            score_history = []
            score_path = d / "score-history.json"
            if score_path.exists():
                score_history = json.loads(score_path.read_text())
            skills.append(
                {
                    "name": d.name,
                    "description": skill_md[:200] if skill_md else "",
                    "has_learnings": bool(learnings),
                    "eval_criteria": eval_data.get("criteria", []),
                    "scores": score_history,
                }
            )
    return skills


@router.get("/{name}")
def get_skill(name: str):
    base = _get_base_dir()
    path = _safe_path(base / "skills", name)
    if not path.exists():
        raise HTTPException(404, "Skill not found")
    return {
        "name": name,
        "skill": _read_file(path / "SKILL.md"),
        "learnings": _read_file(path / "learnings.md"),
        "eval": (
            json.loads((path / "eval.json").read_text())
            if (path / "eval.json").exists()
            else {}
        ),
        "score_history": (
            json.loads((path / "score-history.json").read_text())
            if (path / "score-history.json").exists()
            else []
        ),
        "context": (
            [f.name for f in (path / "context").iterdir()]
            if (path / "context").exists()
            else []
        ),
    }


@router.post("/{name}/run")
def run_skill(name: str, req: Optional[dict] = None):
    base = _get_base_dir()
    path = _safe_path(base / "skills", name)
    if not path.exists():
        raise HTTPException(404, "Skill not found")

    agent = req.get("agent", "auto") if req else "auto"
    input_text = req.get("input", "") if req else ""

    result = skill_runner.run_skill_sync(
        name,
        agent=agent,
        input=input_text,
    )
    return result


@router.get("/{name}/eval")
def get_skill_eval(name: str):
    base = _get_base_dir()
    path = base / "skills" / name / "score-history.json"
    if not path.exists():
        return {"scores": []}
    return {"scores": json.loads(path.read_text())}
