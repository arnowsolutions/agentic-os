#!/usr/bin/env python3
"""Agentic OS — APScheduler engine for recurring tasks"""
import html
import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
except ImportError:
    print("Install APScheduler: pip install apscheduler")
    sys.exit(1)

BASE_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = BASE_DIR.parent.resolve()
JOBS_DIR = BASE_DIR / "jobs"

# Make project modules importable from this separate process
sys.path.insert(0, str(PROJECT_ROOT))

from modules.config import get_settings  # noqa: E402


def _html_wrap(title: str, text: str) -> str:
    """Wrap plain text in minimal HTML for email delivery."""
    escaped_title = html.escape(title)
    escaped_text = html.escape(text).replace("\n", "<br>")
    return (
        f"<!DOCTYPE html>"
        f"<html><head><meta charset='utf-8'><title>{escaped_title}</title></head>"
        f"<body style='font-family: Arial, sans-serif; line-height: 1.5; color: #333;'>"
        f"<h2>{escaped_title}</h2>"
        f"<div>{escaped_text}</div>"
        f"</body></html>"
    )


def _append_audit(entry: dict) -> None:
    audit_file = PROJECT_ROOT / "audit" / "audit.log"
    audit_file.parent.mkdir(parents=True, exist_ok=True)
    entry["timestamp"] = datetime.now(timezone.utc).isoformat()
    with open(audit_file, "a") as f:
        f.write(json.dumps(entry) + "\n")


def run_skill(skill_name: str, job_data: dict, job_file: str):
    """Execute a skill, optionally email results, and write status back to the job JSON."""
    _append_audit({
        "action": "scheduler_run",
        "skill": skill_name,
        "job_id": job_data.get("id", skill_name),
        "job_name": job_data.get("name", skill_name),
    })
    print(f"[{datetime.now().isoformat()}] Running skill: {skill_name}")

    try:
        from modules.skill_runner import run_skill_sync

        result = run_skill_sync(skill_name)
        status = result.get("status", "error")
        output = result.get("output", "")

        # Delivery
        notify = job_data.get("notify") or {}
        if notify.get("channel") == "email" and status == "completed":
            settings = get_settings()
            recipient = (
                notify.get("recipient")
                or getattr(settings, "SCHEDULE_EMAIL_RECIPIENT", "")
                or getattr(settings, "ADMIN_EMAIL", "")
            )
            if recipient:
                try:
                    from modules.google_workspace import GoogleWorkspace
                    subject = f"Agentic OS — {job_data.get('name', skill_name)}"
                    body = _html_wrap(subject, output or "(no output)")
                    send_result = GoogleWorkspace().send_email(
                        user_id="default",
                        to=recipient,
                        subject=subject,
                        body=body,
                        is_html=True,
                    )
                    if not send_result.get("successful"):
                        print(f"  Email delivery failed: {send_result.get('error')}")
                except Exception as e:
                    print(f"  Email delivery skipped due to error: {e}")
                    traceback.print_exc()

        # Write-back
        job_data["last_run"] = datetime.now(timezone.utc).isoformat()
        job_data["last_status"] = "ok" if status == "completed" else "error"
        Path(job_file).write_text(json.dumps(job_data, indent=2))
        print(f"[{datetime.now().isoformat()}] Finished skill: {skill_name} ({job_data['last_status']})")

    except Exception as e:
        error_msg = f"Error running skill {skill_name}: {e}"
        print(error_msg)
        traceback.print_exc()
        _append_audit({
            "action": "scheduler_run_error",
            "skill": skill_name,
            "job_id": job_data.get("id", skill_name),
            "job_name": job_data.get("name", skill_name),
            "error": str(e),
        })
        try:
            job_data["last_run"] = datetime.now(timezone.utc).isoformat()
            job_data["last_status"] = "error"
            Path(job_file).write_text(json.dumps(job_data, indent=2))
        except Exception:
            pass


def load_jobs(scheduler: BackgroundScheduler):
    """Load job definitions from jobs/ directory."""
    for job_file in JOBS_DIR.glob("*.json"):
        data = json.loads(job_file.read_text())
        if not data.get("enabled", True):
            continue
        scheduler.add_job(
            run_skill,
            CronTrigger.from_crontab(data["cron"]),
            args=[data["skill"], data, str(job_file)],
            id=data.get("id", data["name"]),
            name=data["name"],
            replace_existing=True,
        )
        print(f"  Loaded job: {data['name']} ({data['cron']})")


def main():
    scheduler = BackgroundScheduler()
    load_jobs(scheduler)
    scheduler.start()
    print(f"Agentic OS Scheduler running. Jobs loaded from: {JOBS_DIR}")
    try:
        while True:
            import time
            time.sleep(60)
    except KeyboardInterrupt:
        scheduler.shutdown()
        print("Scheduler stopped.")


if __name__ == "__main__":
    main()
