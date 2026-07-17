#!/usr/bin/env python3
"""Send Grand Rounds .ics calendar invites + weekly reminders.
   Phase 1 (bulk): Send .ics invites at 10/day until all 45 are sent.
   Phase 2 (Wed): Send HTML reminder with topics + Zoom info.
   Uses premium calendar_mailer.py template for all invites."""
import json, re, os, sys
from datetime import date, timedelta, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calendar_mailer import send_calendar_invite, send_reminder_email, _html_wrap

# ── Config ────────────────────────────────────────────────
ZOOM_LINK = "https://us02web.zoom.us/j/86773878358?pwd=RUxySVVzUjFWL0lyRWtjdDBacTVPZz09"
MEETING_ID = "867 7387 8358"
PASSCODE = "466916"
PROGRESS_FILE = "/workspace/agentic-os/data/grand_rounds_progress.json"

# TEST MODE — only send to this address until we go live
TEST_MODE = True
TEST_EMAIL = "sfrasier@montefiore.org"
PROD_RECIPIENTS = []  # Loaded from email_groups.json below

# ── Load production recipients ─────────────────────────────
EMAIL_GROUPS_FILE = "/workspace/agentic-os/data/email_groups.json"
def _load_prod_recipients(event_type=""):
    """Load the right email list based on event type.
    - "Faculty Meeting" -> faculty_meeting list
    - Everything else -> grand_rounds list (residents + faculty)
    """
    try:
        if os.path.exists(EMAIL_GROUPS_FILE):
            with open(EMAIL_GROUPS_FILE) as f:
                groups = json.load(f)
            group_key = "faculty_meeting" if "Faculty" in event_type else "grand_rounds"
            gr = groups.get(group_key, {})
            emails = gr.get("emails", [])
            return emails
    except Exception:
        pass
    return []

DAILY_LIMIT = 10
# ── Parse GR data ─────────────────────────────────────────
def parse_gr_data():
    with open("/workspace/agentic-os/dashboard/pages/grand-rounds.js") as f:
        js = f.read()
    start = js.index("const GR_DATA = ")
    start = js.index("[", start)
    depth = 0
    end = start
    for i, c in enumerate(js[start:]):
        if c == "[": depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                end = start + i + 1
                break
    array_str = js[start:end]
    array_str = re.sub(r",\s*]", "]", array_str)
    array_str = re.sub(r"//.*", "", array_str)
    return json.loads(array_str)

def get_all_grand_rounds():
    gr_data = parse_gr_data()
    events = []
    for row in gr_data:
        fri_date = row[7] if len(row) > 7 else ""
        if not fri_date or not fri_date.startswith("20"):
            continue
        gr_7_8 = row[8].strip('" ') if len(row) > 8 else ""
        gr_8_9 = row[9].strip('" ') if len(row) > 9 else ""
        if "NO GRAND ROUNDS" in gr_7_8 or "NO GRAND ROUNDS" in gr_8_9:
            continue
        if not gr_7_8 and not gr_8_9:
            continue

        meeting_type = "Grand Rounds"
        if "Peds" in gr_7_8 or "Peds" in gr_8_9:
            meeting_type = "Peds Grand Rounds"
        elif "FACULTY MEETING" in gr_7_8 or "FACULTY MEETING" in gr_8_9:
            meeting_type = "Faculty Meeting"
        elif "Journal Club" in gr_7_8 or "Journal Club" in gr_8_9:
            meeting_type = "Journal Club"

        topic_7_8 = gr_7_8 or gr_8_9
        topic_8_9 = gr_8_9 or gr_7_8

        events.append({"date": fri_date, "type": meeting_type, "topic_7_8": topic_7_8, "topic_8_9": topic_8_9})
    events.sort(key=lambda e: e["date"])
    return events


def _build_friday_title(event):
    """Build calendar summary matching last year's Outlook format.
    Returns (summary, description) tuple."""
    meeting_type = event['type']
    topic_7 = event['topic_7_8']
    topic_8 = event['topic_8_9']
    
    if "Faculty" in meeting_type:
        return ("Faculty Meeting", "Faculty Meeting")
    
    prefix = "PEDS: " if "Peds" in meeting_type else ""
    base = f"{prefix}Urology Grand Rounds [In-person]"
    
    # Build the topic suffix from excel data
    parts = []
    if topic_7:
        parts.append(topic_7)
    if topic_8 and topic_8 != topic_7:
        parts.append(topic_8)
    suffix = " / ".join(parts) if parts else ""
    
    summary = f"{base} - {suffix}" if suffix else base
    return (summary, "Grand Rounds")


def send_ics_invite(event, friday_date):
    """Send .ics calendar invite via premium calendar_mailer template."""
    try:
        summary, description = _build_friday_title(event)
        
        dt = datetime.strptime(friday_date, "%Y-%m-%d")
        formatted = dt.strftime("%A, %B %d, %Y")
        
        prod_emails = _load_prod_recipients(event.get("type", ""))
        to = TEST_EMAIL if TEST_MODE else ", ".join(prod_emails + (["sfrasier@montefiore.org"] if "sfrasier@montefiore.org" not in prod_emails else []))
        subject = f"Invitation: {summary}"
        
        mid = send_calendar_invite(
            to=to,
            subject=subject,
            summary=summary,
            description=description,
            location=ZOOM_LINK,
            date_str=friday_date,
            start_time="07:00",
            end_time="09:00",
            duration_minutes=120,
            zoom_link=ZOOM_LINK,
            meeting_id=MEETING_ID,
            passcode=PASSCODE,
            session_7_8=event['topic_7_8'],
            session_8_9=event['topic_8_9'],
            session_7_8_label="Grand Rounds",
            session_8_9_label="Grand Rounds Conference",
            physical_location="Hutch | PH2 Conf A & Conf B — both rooms used for both sessions",
        )
        return True, ""
    except Exception as e:
        return False, str(e)


def send_text_reminder(event, friday_date):
    """Send HTML reminder (Wednesday before)."""
    try:
        dt = datetime.strptime(friday_date, "%Y-%m-%d")
        formatted = dt.strftime("%A, %B %d, %Y")
        summary, _ = _build_friday_title(event)
        
        inner = f"""<table width="100%" cellpadding="0" cellspacing="0">
<tr><td style="padding-bottom:20px;text-align:center">
<p style="margin:0;font-size:15px;color:#111827;line-height:1.6">Kindly see this week's <strong>{summary}</strong> conference topics for <strong>{formatted}</strong>:</p>
</td></tr>
<tr><td style="padding-bottom:20px">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px">
<tr><td style="padding:12px 16px;font-size:11px;color:#6b7280;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;border-bottom:1px solid #e5e7eb;text-align:center">Agenda</td></tr>
<tr><td style="padding:10px 16px;border-bottom:1px solid #e5e7eb;text-align:center"><span style="font-size:13px;color:#374151"><strong>7:00 – 8:00 AM</strong></span> &nbsp; <span style="font-size:13px;color:#111827">{event['topic_7_8']}</span></td></tr>
<tr><td style="padding:10px 16px;text-align:center"><span style="font-size:13px;color:#374151"><strong>8:00 – 9:00 AM</strong></span> &nbsp; <span style="font-size:13px;color:#111827">{event['topic_8_9']}</span></td></tr>
</table>
</td></tr>
<tr><td style="padding-bottom:12px">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f0f7ff;border:1px solid #bfdbfe;border-radius:8px">
<tr><td style="padding:16px 20px;font-size:11px;color:#1d4ed8;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;border-bottom:1px solid #bfdbfe;text-align:center">Zoom Meeting</td></tr>
<tr><td style="padding:16px 20px;text-align:center">
<a href="{ZOOM_LINK}" style="display:inline-block;background-color:#1a3a5c;color:#ffffff;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;font-size:13px;font-weight:600;text-decoration:none;padding:10px 24px;border-radius:6px;margin-bottom:12px">Click Here to Join Zoom Meeting →</a>
<table cellpadding="0" cellspacing="0" style="margin:0 auto">
<tr><td style="font-size:12px;color:#6b7280;padding:2px 8px 2px 0">Meeting ID:</td><td style="font-size:13px;color:#111827;font-weight:600">{MEETING_ID}</td></tr>
<tr><td style="font-size:12px;color:#6b7280;padding:2px 8px 2px 0">Passcode:</td><td style="font-size:13px;color:#111827;font-weight:600">{PASSCODE}</td></tr>
</table>
</td></tr>
</table>
</td></tr>
</table>"""
        
        html_body = _html_wrap(f"Reminder: {summary}", inner)
        
        prod_emails = _load_prod_recipients(event.get("type", ""))
        to = TEST_EMAIL if TEST_MODE else ", ".join(prod_emails + (["sfrasier@montefiore.org"] if "sfrasier@montefiore.org" not in prod_emails else []))
        subject = f"REMINDER: {summary} — This Friday!"
        
        send_reminder_email(to, subject, html_body)
        return True, ""
    except Exception as e:
        return False, str(e)


def load_progress():
    if os.path.exists(PROGRESS_FILE):
        return json.load(open(PROGRESS_FILE))
    return {"ics_sent_dates": [], "last_run": None}

def save_progress(progress):
    os.makedirs(os.path.dirname(PROGRESS_FILE), exist_ok=True)
    json.dump(progress, open(PROGRESS_FILE, "w"), indent=2)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", type=str, default="", help="Single date to send for (YYYY-MM-DD)")
    args = parser.parse_args()

    all_events = get_all_grand_rounds()
    progress = load_progress()
    today = date.today()

    # ── Mode: Single-date resend ──
    if args.date:
        target_date = args.date
        # Override test mode from env if set
        recipients_env = os.environ.get("PROD_RECIPIENTS", "")
        test_mode_env = os.environ.get("TEST_MODE", "")
        global TEST_MODE, TEST_EMAIL, PROD_RECIPIENTS
        if test_mode_env == "false" and recipients_env:
            TEST_MODE = False
            PROD_RECIPIENTS = recipients_env.split(",")
        for event in all_events:
            if event["date"] == target_date:
                print(f"📅 Resending invite for {target_date} ({event['type']})")
                ok, err = send_ics_invite(event, target_date)
                print(f"  {'✅' if ok else '❌'} (err: {err[:60] if err else 'none'})")
                return
        print(f"No event found for {target_date}")
        return

    # ── Mode: Wednesday Reminder ──
    if today.weekday() == 2:  # Wednesday
        friday = (today + timedelta(days=3)).isoformat()
        for event in all_events:
            if event["date"] == friday:
                print(f"📅 Wednesday reminder for {friday}")
                ok, err = send_text_reminder(event, friday)
                print(f"  {'✅' if ok else '❌'} {event['type']} (err: {err[:60] if err else 'none'})")
                return
        print(f"No Grand Rounds found for {friday}")
        return

    # ── Mode: Bulk .ics send ──
    unsent = [e for e in all_events if e["date"] not in progress.get("ics_sent_dates", [])]
    if not unsent:
        print("✅ All .ics invites sent!")
        return

    today_batch = unsent[:DAILY_LIMIT]
    print(f"Sending {len(today_batch)} .ics invites ({len(unsent)} remaining)...")

    sent_count = 0
    for event in today_batch:
        ok, err = send_ics_invite(event, event["date"])
        if ok:
            progress.setdefault("ics_sent_dates", []).append(event["date"])
            sent_count += 1
            print(f"  ✅ {event['date']}: {event['type']}")
        else:
            print(f"  ❌ {event['date']}: {err[:100]}")
            break

    progress["last_run"] = datetime.now().isoformat()
    save_progress(progress)
    total = len(all_events)
    sent_total = len(progress.get("ics_sent_dates", []))
    print(f"\nSent: {sent_count} today, {sent_total}/{total} total")


if __name__ == "__main__":
    main()
