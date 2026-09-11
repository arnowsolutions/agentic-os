#!/usr/bin/env python3
"""Weekly report of Monday + Grand Rounds invite status.
Saves to file for cron delivery. Silent on success, shows gaps when any dates are unsent."""
import json, os, sys
from datetime import date, datetime, timedelta

SCRIPT_DIR = "/workspace/agentic-os"
MONDAY_PROGRESS = os.path.join(SCRIPT_DIR, "data/monday_sasp_progress.json")
GR_PROGRESS = os.path.join(SCRIPT_DIR, "data/grand_rounds_progress.json")
GR_DATA_FILE = os.path.join(SCRIPT_DIR, "dashboard/pages/grand-rounds.js")
EMAIL_GROUPS = os.path.join(SCRIPT_DIR, "data/email_groups.json")

def parse_gr_data():
    """Schedule now comes ONLY from the CANONICAL store: unified.grand_rounds."""
    from gr_schedule import fetch_rows
    return fetch_rows(include_tb=False)

def load_progress(path):
    if os.path.exists(path):
        return json.load(open(path))
    return {"ics_sent_dates": []}

def main():
    today = date.today()
    
    # Load events
    rows = parse_gr_data()
    
    # Separate Mondays and Fridays
    mondays = []
    fridays = []
    for row in rows:
        mon_date = row[1] if len(row) > 1 else ""
        fri_date = row[7] if len(row) > 7 else ""
        topic_mon = row[2].strip() if len(row) > 2 else ""
        resident = row[3].strip() if len(row) > 3 else ""
        attending = row[4].strip() if len(row) > 4 else ""
        gr_7_8 = row[8].strip() if len(row) > 8 else ""
        gr_8_9 = row[9].strip() if len(row) > 9 else ""
        
        # Skip holidays
        if topic_mon.lower() == "holiday":
            if mon_date: mondays.append({"date": mon_date, "topic": "HOLIDAY", "status": "holiday"})
            if fri_date: fridays.append({"date": fri_date, "topic": "HOLIDAY", "status": "holiday"})
            continue
        
        if mon_date and mon_date.startswith("20"):
            status = "unsent"
            mondays.append({"date": mon_date, "topic": topic_mon, "resident": resident, "attending": attending, "status": status})
        
        if fri_date and fri_date.startswith("20"):
            status = "unsent"
            fridays.append({"date": fri_date, "topic": f"{gr_7_8} / {gr_8_9}".strip(" / "), "status": status})
    
    # Load sent status — CANONICAL tracker (unified *_sent_at) + legacy progress backfill
    mon_sent = set()
    gr_sent = set()
    try:
        from gr_schedule import fetch_dicts
        for r in fetch_dicts():
            if r.get("mon_date") and r.get("mon_invite_sent_at"):
                mon_sent.add(r["mon_date"])
            if r.get("fri_date") and r.get("fri_invite_sent_at"):
                gr_sent.add(r["fri_date"])
    except Exception:
        pass
    mon_sent |= set(load_progress(MONDAY_PROGRESS).get("ics_sent_dates", []))
    gr_sent |= set(load_progress(GR_PROGRESS).get("ics_sent_dates", []))
    
    # Build report
    lines = []
    lines.append(f"📋 **Conference Invite Status Report**")
    lines.append(f"Generated: {today.strftime('%A, %B %d, %Y')}")
    lines.append("")
    
    # ── Monday section ──
    lines.append("**📅 Monday Conference (SASP)**")
    lines.append(f"| Date | Topic | Resident | Attending | Status |")
    lines.append(f"|------|-------|----------|-----------|--------|")
    
    mon_unsent = 0
    for e in mondays:
        if e.get("status") == "holiday":
            continue
        status = "✅ Sent" if e["date"] in mon_sent else "❌ Not sent"
        if e["date"] not in mon_sent:
            mon_unsent += 1
        lines.append(f"| {e['date']} | {e['topic'][:40]} | {e.get('resident','')[:20]} | {e.get('attending','')[:20]} | {status} |")
    
    lines.append("")
    
    # ── Grand Rounds section ──
    lines.append("**📅 Friday Grand Rounds**")
    lines.append(f"| Date | Topic | Status |")
    lines.append(f"|------|-------|--------|")
    
    gr_unsent = 0
    for e in fridays:
        if e.get("status") == "holiday":
            continue
        status = "✅ Sent" if e["date"] in gr_sent else "❌ Not sent"
        if e["date"] not in gr_sent:
            gr_unsent += 1
        lines.append(f"| {e['date']} | {e['topic'][:50]} | {status} |")
    
    lines.append("")
    
    # ── Summary ──
    lines.append("**📊 Summary**")
    lines.append(f"- Monday: {len(mondays) - sum(1 for e in mondays if e.get('status')=='holiday')} total, {mon_unsent} unsent")
    lines.append(f"- Grand Rounds: {len(fridays) - sum(1 for e in fridays if e.get('status')=='holiday')} total, {gr_unsent} unsent")
    lines.append(f"- Next Monday: {mondays[0]['date'] if mondays else 'N/A'} → {mondays[0].get('topic','')[:40] if mondays else 'N/A'}")
    
    # Find next unsent
    next_mon = next((e for e in mondays if e["date"] not in mon_sent), None)
    next_fri = next((e for e in fridays if e["date"] not in gr_sent), None)
    if next_mon:
        lines.append(f"- Next unsent Monday: {next_mon['date']} ({next_mon.get('topic','')[:30]})")
    if next_fri:
        lines.append(f"- Next unsent Friday: {next_fri['date']} ({next_fri.get('topic','')[:30]})")
    
    output = "\n".join(lines)
    print(output)
    return output

if __name__ == "__main__":
    main()
