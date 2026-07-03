#!/usr/bin/env python3
"""
Telegram Business Dashboard — Daily Summary
============================================
Delivers a daily business summary to Telegram:

  Today's Call Coverage  |  GME Snapshot  |  Upcoming Events  |  Reminders

Runs as a no_agent cron job. Output is delivered verbatim to Telegram.
If there's nothing notable to report, it stays silent.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Configuration ──────────────────────────────────────────
DATA_SERVICE_URL = os.environ.get("DATA_SERVICE_URL", "http://localhost:8086")
GME_CACHE = Path("/workspace/agentic-os/reports/gme_cache.json")
SCHEDULE_CACHE = Path("/workspace/agentic-os/reports/call_schedule_cache.json")

# NYC timezone offset
NYC_OFFSET = -4  # EDT (June); change to -5 for EST

TODAY = datetime.now(timezone.utc)
TODAY_STR = TODAY.strftime("%Y-%m-%d")
TODAY_DISPLAY = TODAY.strftime("%A, %B %d, %Y")


def http_get(path: str, timeout: int = 5):
    """Simple HTTP GET helper."""
    import urllib.request, json
    try:
        url = f"{DATA_SERVICE_URL}{path}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)}


def get_today_schedule() -> str:
    """Fetch today's call coverage from data service."""
    try:
        data = http_get("/api/unified/today")
        if "error" in data:
            return f"  ⚠️ Data service unavailable: {data['error']}"

        sections = []
        for campus in ["moses", "wakefield", "weiler"]:
            entries = data.get(campus, [])
            if entries:
                lines = []
                for e in entries:
                    primary = e.get("primary", e.get("attending", "—"))
                    backup = e.get("backup", "—")
                    peds = e.get("peds", "—")
                    line = f"    Primary: {primary}"
                    if backup and backup != "—":
                        line += f" | Backup: {backup}"
                    if peds and peds != "—":
                        line += f" | PEDS: {peds}"
                    lines.append(line)
                sections.append(f"  🏥 {campus.title()}\n" + "\n".join(lines))
            else:
                sections.append(f"  🏥 {campus.title()}\n    No call today")

        return "\n\n".join(sections) if sections else "  No schedule data available"
    except Exception as e:
        return f"  ⚠️ Error: {e}"


def get_gme_summary() -> str:
    """Get the GME spending snapshot."""
    try:
        # Check cache first
        if GME_CACHE.exists():
            data = json.loads(GME_CACHE.read_text())
        else:
            data = http_get("/api/reimbursement/gme-summary")

        if isinstance(data, dict):
            total = data.get("total_remaining", data.get("remaining", 0))
            used = data.get("total_used", data.get("used", 0))
            pool = data.get("total_budget", data.get("budget", 18750))
            pct = round((used / pool) * 100) if pool else 0
            return f"  💰 ${total:,} remaining of ${pool:,} (${used:,} used, {pct}%)"
        return "  💰 GME data unavailable"
    except Exception as e:
        return f"  ⚠️ GME error: {e}"


def get_coverage_gaps() -> str:
    """Check for any coverage gaps (sick calls, unfilled spots)."""
    try:
        data = http_get("/api/unified/today")
        if "error" in data:
            return ""

        gaps = []
        for campus in ["moses", "wakefield", "weiler"]:
            entries = data.get(campus, [])
            for e in entries:
                for role in ["primary", "backup", "peds", "call1", "call2", "chief"]:
                    val = e.get(role, "")
                    if not val or val.strip() in ("", "—", "TBD", "tbd"):
                        gaps.append(f"  ⚠️ {campus.title()} — {role.replace('_', ' ').title()} is empty")

        return "\n".join(gaps[:5]) if gaps else ""
    except Exception:
        return ""


def get_reminders() -> str:
    """Check for reminders — swap history, etc."""
    swap_log = Path(os.path.expanduser("~/.hermes/call_schedule_history/_swap_log.json"))
    if swap_log.exists():
        try:
            swaps = json.loads(swap_log.read_text())
            # Count swaps in last 7 days
            recent = [s for s in swaps if s.get("timestamp", "").startswith(TODAY_STR[:10])]
            if recent:
                return f"  🔄 {len(recent)} swap(s) processed today"
        except (json.JSONDecodeError, OSError):
            pass
    return ""


def count_faculty_on_call() -> dict:
    """Count how many faculty are on call today across campuses."""
    try:
        data = http_get("/api/unified/today")
        if "error" in data:
            return {}
        counts = {"faculty": set(), "backup": set(), "peds": set(), "residents": set()}
        for campus in ["moses", "wakefield", "weiler"]:
            for e in data.get(campus, []):
                for name in [e.get("primary"), e.get("backup"), e.get("peds")]:
                    if name and name not in ("—", ""):
                        counts["faculty"].add(name)
                for name in [e.get("call1"), e.get("call2"), e.get("chief")]:
                    if name and name not in ("—", ""):
                        counts["residents"].add(name)
        return {k: len(v) for k, v in counts.items()}
    except Exception:
        return {}


def get_gme_transactions() -> str:
    """Get concise per-resident GME transaction list."""
    try:
        import gme_transactions
        grouped = gme_transactions.transactions_by_resident(
            status='complete', account_filter='GME'
        )
        if not grouped:
            return "  📋 No approved GME transactions"

        summary = gme_transactions.transaction_summary(grouped)
        lines = [
            f"  📋 Approved Transactions: "
            f"{summary['resident_count']} residents, "
            f"{summary['transaction_count']} txns, "
            f"${summary['total_amount']:,.2f}"
        ]
        for resident_name in sorted(grouped.keys()):
            txns = grouped[resident_name]
            resident_total = sum(float(t.get('amount', 0) or 0) for t in txns)
            lines.append(f"  *{resident_name}* — ${resident_total:,.2f}")
            for t in txns:
                date = t.get('date', '')
                desc = t.get('description', '')
                amount = float(t.get('amount', 0) or 0)
                lines.append(f"    `{date}` {desc}  ${amount:,.2f}")
        return "\n".join(lines)
    except Exception as e:
        return f"  ⚠️ Transaction error: {e}"


def main():
    schedule = get_today_schedule()
    gme = get_gme_summary()
    gaps = get_coverage_gaps()
    reminders = get_reminders()
    counts = count_faculty_on_call()
    gme_txns = get_gme_transactions()

    # Build message
    lines = [
        f"📋 **Montefiore Urology — Daily Briefing**",
        f"**{TODAY_DISPLAY}**",
        "",
        "━━━━━━━━━━━━━━━━━━━",
        "",
    ]

    # Coverage summary
    if counts:
        on_call = []
        if counts.get("faculty"):
            on_call.append(f"👨‍⚕️ {counts['faculty']} attendings")
        if counts.get("residents"):
            on_call.append(f"🩺 {counts['residents']} residents")
        if on_call:
            lines.append(f"**On Call Today:** {' | '.join(on_call)}")
            lines.append("")

    lines.append("**📅 Today's Coverage**")
    lines.append(schedule)
    lines.append("")

    if gaps:
        lines.append("**⚠️ Coverage Gaps**")
        lines.append(gaps)
        lines.append("")

    lines.append("**💰 GME Budget**")
    lines.append(gme)
    lines.append("")
    lines.append(gme_txns)
    lines.append("")

    if reminders:
        lines.append("**🔄 Recent Activity**")
        lines.append(reminders)
        lines.append("")

    lines.append("━━━━━━━━━━━━━━━━━━━")
    lines.append(f"_Automated daily briefing · {TODAY_DISPLAY}_")

    print("\n".join(lines))


if __name__ == "__main__":
    main()
