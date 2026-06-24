#!/usr/bin/env python3
"""Standalone skill runner shared by the FastAPI server and APScheduler."""
import json
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.resolve()


def _read_file(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def _write_file(path: Path, content: str) -> bool:
    path.write_text(content, encoding="utf-8")
    return True


def _get_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append_audit(entry: dict) -> None:
    audit_file = BASE_DIR / "audit" / "audit.log"
    audit_file.parent.mkdir(parents=True, exist_ok=True)
    entry["timestamp"] = _get_timestamp()
    entry["id"] = str(uuid.uuid4())[:8]
    with open(audit_file, "a") as f:
        f.write(json.dumps(entry) + "\n")


def run_skill_sync(name: str, agent: str = "auto", input: str = "") -> dict:
    """Execute a skill synchronously.

    Returns a dict matching the ``/api/skills/{name}/run`` response shape.
    """
    skill_dir = BASE_DIR / "skills" / name
    if not skill_dir.exists() or not skill_dir.is_dir():
        return {
            "status": "error",
            "run_id": "",
            "skill": name,
            "agent": agent,
            "output": "",
            "message": f"Skill '{name}' not found",
        }

    agent_choice = agent if agent else "auto"
    skill_input = input if input else ""

    skill_md = _read_file(skill_dir / "SKILL.md")
    learnings = _read_file(skill_dir / "learnings.md")

    # Determine which agent based on skill type
    if agent_choice == "auto":
        devops_keywords = ["devops", "audit", "deploy", "k8s", "gcp", "infra", "terraform"]
        research_keywords = ["research", "synthesis", "analyze", "search", "compare"]
        if any(k in name for k in devops_keywords):
            agent_choice = "opencode"
        elif any(k in name for k in research_keywords):
            agent_choice = "gemini"
        else:
            # Check SKILL.md for explicit agent assignment
            for line in skill_md.split("\n"):
                line = line.strip()
                if "Primary:" in line:
                    candidate = line.split(":")[-1].strip().lower()
                    if candidate in ("opencode", "hermes", "gemini"):
                        agent_choice = candidate
                        break
            if agent_choice == "auto":
                agent_choice = "opencode"

    # Build prompt from skill instructions + learnings + user input
    prompt = f"Execute the '{name}' skill.\n\n"
    if skill_md:
        prompt += f"## Skill Instructions\n{skill_md}\n\n"
    if learnings and learnings.strip():
        prompt += f"## Past Learnings\n{learnings}\n\n"
    if skill_input:
        prompt += f"## User Input\n{skill_input}"

    run_id = str(uuid.uuid4())[:8]

    # Execute via agent
    try:
        # Lazy import breaks the import-time cycle: server.py imports this module,
        # and this module needs execute_agent from server.py at call time.
        from server import execute_agent
        response_text = execute_agent(agent_choice, prompt)
    except subprocess.TimeoutExpired:
        response_text = f"⏱ Skill '{name}' timed out on agent '{agent_choice}'."
    except FileNotFoundError:
        response_text = f"⚠ Agent '{agent_choice}' CLI not installed. Install it and try again."
    except Exception as e:
        response_text = f"⚠ Error executing skill: {str(e)}"

    # Save output to learnings.md
    timestamp = _get_timestamp()[:10]
    existing = _read_file(skill_dir / "learnings.md")
    new_entry = (
        f"\n## {timestamp} (Run {run_id})\n"
        f"- Agent: {agent_choice}\n"
        f"- Input: {skill_input or '(none)'}\n"
        f"- Output: {response_text[:500]}\n"
    )
    _write_file(skill_dir / "learnings.md", existing + new_entry)

    # Log execution
    _append_audit({
        "action": "skill_run",
        "skill": name,
        "agent": agent_choice,
        "run_id": run_id,
        "output_preview": response_text[:100],
    })

    return {
        "status": "completed",
        "run_id": run_id,
        "skill": name,
        "agent": agent_choice,
        "output": response_text,
        "message": f"Skill '{name}' completed via {agent_choice}",
    }
