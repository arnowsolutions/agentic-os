#!/usr/bin/env python3
"""Generate the weekly task-list + rotation-onboarding reminder report.

Reads /workspace/task-list.json (source of truth per persistent-task-list skill)
and prints a Telegram-friendly HTML digest with overdue / high / medium grouping.

Usage:
  python3 weekly_task_report.py            # print Telegram digest (stdout)
  python3 weekly_task_report.py --json     # raw parsed tasks
  python3 weekly_task_report.py --email    # also email via smtp_sender

Pitfalls (see skill 'persistent-task-list'):
  - $HOME is overridden to ~/.hermes/home in cron; never rely on Path.home()
  - SMTP App Passwords ship with display spaces -> strip before auth
  - Set os.environ BEFORE importing smtp_sender
"""
import json
import os
import sys
from datetime import date, datetime

TASK_FILE = os.environ.get("TASK_LIST_FILE", "/workspace/task-list.json")

PRIO_ICON = {"high": "\U0001f534", "medium": "\U0001f7e1", "low": "\U0001f7e2"}


def load_tasks(path=TASK_FILE):
    with open(path) as fh:
        return json.load(fh)


def parse_due(task):
    raw = task.get("due_date")
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        return None


def categorize(tasks, today=None):
    today = today or date.today()
    buckets = {"overdue": [], "high": [], "medium": [], "low": []}
    for t in tasks:
        if t.get("status") == "completed":
            continue
        due = parse_due(t)
        if due and due < today:
            buckets["overdue"].append((t, due))
            continue
        prio = t.get("priority", "medium")
        buckets[prio if prio in buckets else "medium"].append((t, due))
    for key in buckets:
        buckets[key].sort(key=lambda pair: (pair[1] or date.max, pair[0]["content"]))
    return buckets


def human_due(due):
    if not due:
        return ""
    return due.strftime("%-m/%-d")


def render(tasks, today=None):
    today = today or date.today()
    b = categorize(tasks, today)
    pending = sum(len(b[k]) for k in ("overdue", "high", "medium", "low"))
    out = [
        f"\U0001f4cb <b>Weekly Task List</b> \u2014 {today.strftime('%A, %b %-d, %Y')}",
        f"{pending} pending "
        f"({len(b['overdue'])} overdue, {len(b['high'])} high, "
        f"{len(b['medium'])} medium, {len(b['low'])} low)",
        "",
    ]

    if b["overdue"]:
        out.append("\u26a0\ufe0f <b>OVERDUE</b>")
        for t, due in b["overdue"]:
            out.append(f"\u2022 {t['content']}  <i>(due {human_due(due)})</i>")
        out.append("")

    for key, label in (("high", "\U0001f534 HIGH"), ("medium", "\U0001f7e1 MEDIUM"),
                       ("low", "\U0001f7e2 LOW")):
        if not b[key]:
            continue
        out.append(f"<b>{label} PRIORITY</b>")
        for t, due in b[key]:
            suffix = f"  <i>(due {human_due(due)})</i>" if due else ""
            out.append(f"\u2022 {t['content']}{suffix}")
        out.append("")

    return "\n".join(out).rstrip()


if __name__ == "__main__":
    tasks = load_tasks()
    if "--json" in sys.argv:
        print(json.dumps(categorize(tasks), default=str, indent=2))
    else:
        print(render(tasks))
