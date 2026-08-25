#!/usr/bin/env python3
"""
subi_auto_welcome.py — Auto-draft Sub-I welcome emails as students approach onboarding.

For every student in subi_welcome_config.json with welcome=true whose rotation starts
within WINDOW_DAYS (default 7), generate the welcome email and queue it through the
review gate as a DRAFT (preview to Shareef, NOT auto-sent).

This implements option 1 (automatic N-days-before-onboarding) while still routing
through review_gate so no email reaches a student without Shareef's approval.

Also prints a short summary for Telegram delivery.

Usage:
  python3 subi_auto_welcome.py                 # draft for students starting within 7 days
  python3 subi_auto_welcome.py --days 10       # 10-day window
  python3 subi_auto_welcome.py --once          # (for manual run)
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent
CFG = BASE / "data" / "subi_welcome_config.json"
GEN = BASE / "subi_welcome_email.py"


def parse_date(s):
    if not s:
        return None
    for fmt in ("%m/%d/%y", "%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(s).strip(), fmt).date()
        except ValueError:
            continue
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    a = ap.parse_args()
    cfg = json.loads(CFG.read_text())
    today = date.today()
    due = []
    for key, st in (cfg.get("students") or {}).items():
        if not st.get("welcome"):
            continue
        start = parse_date(st.get("rotation_start"))
        if start and today <= start <= today + timedelta(days=a.days):
            due.append((key, st, start))

    lines = []
    if not due:
        lines.append(f"[SILENT] No Sub-I welcome emails due in next {a.days} days.")
        print("\n".join(lines))
        return

    header = f"📧 SUB-I WELCOME EMAILS TO REVIEW — starting within {a.days} days"
    lines.append(header)
    for key, st, start in due:
        print(f"Drafting welcome for {st.get('first_name')} ({st.get('email')}) start {start.isoformat()}")
        r = subprocess.run([sys.executable, str(GEN), "--draft", "--student", key],
                           capture_output=True, text=True, timeout=120)
        out = (r.stdout + r.stderr).strip().splitlines()
        last = out[-1] if out else "(no output)"
        lines.append(f"  • {st.get('first_name')} <{st.get('email')}> — {last}")
        # flag if schedule data missing
        if st.get("_needs"):
            lines.append(f"      ⚠️  {st['_needs']} for {st.get('first_name')} (fill before approving send)")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
