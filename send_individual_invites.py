#!/usr/bin/env python3
"""Send individual personalized .ics calendar invites to each recipient.
Batched: 3 emails per batch, 30s between batches to respect Gmail SMTP limits.
Each recipient gets their own .ics with ATTENDEE;RSVP=TRUE set to their email.
"""
import json, os, sys, time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the sending functions directly
from calendar_mailer import send_calendar_invite
from send_grand_rounds_email import get_all_grand_rounds, _build_friday_title

# ── Config ────────────────────────────────────────────────
ZOOM_LINK = "https://us02web.zoom.us/j/86773878358?pwd=RUxySVVzUjFWL0lyRWtjdDBacTVPZz09"
MEETING_ID = "867 7387 8358"
PASSCODE = "466916"
EMAIL_GROUPS_FILE = "/workspace/agentic-os/data/email_groups.json"

TARGET_DATES = ["2026-07-10", "2026-07-17"]
BATCH_SIZE = 3
BATCH_DELAY = 30  # seconds between batches

# ── Load recipients ───────────────────────────────────────
with open(EMAIL_GROUPS_FILE) as f:
    groups = json.load(f)
recipients = groups["grand_rounds"]["emails"]
print(f"📋 Loaded {len(recipients)} recipients from grand_rounds list")

# ── Load events ───────────────────────────────────────────
all_events = get_all_grand_rounds()
target_events = [e for e in all_events if e["date"] in TARGET_DATES]
target_events.sort(key=lambda e: e["date"])

print(f"📅 Sending invites for {len(target_events)} events:")
for e in target_events:
    summary, _ = _build_friday_title(e)
    print(f"   {e['date']}: {summary}")

print(f"\n📧 Total emails to send: {len(recipients) * len(target_events)}")
print(f"⏱️  Batch size: {BATCH_SIZE}, delay: {BATCH_DELAY}s between batches")
print(f"   Estimated time: ~{((len(recipients) * len(target_events)) // BATCH_SIZE) * BATCH_DELAY // 60} minutes\n")

# ── Send ──────────────────────────────────────────────────
total_sent = 0
total_failed = 0
queue = []

for event in target_events:
    summary, description = _build_friday_title(event)
    friday_date = event["date"]
    subject = f"Invitation: {summary}"
    
    for email in recipients:
        queue.append((email, event, summary, description, subject, friday_date))

print(f"Queue: {len(queue)} emails\n")

for i, (email, event, summary, description, subject, friday_date) in enumerate(queue):
    try:
        msg_id = send_calendar_invite(
            to=email,
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
        )
        total_sent += 1
        print(f"  ✅ [{total_sent}/{len(queue)}] {email} → {friday_date} ({summary[:40]}...)")
    except Exception as e:
        total_failed += 1
        print(f"  ❌ [{total_sent+total_failed}/{len(queue)}] {email} → {str(e)[:80]}")
    
    # Batch delay every BATCH_SIZE emails (except after the last one)
    if (i + 1) % BATCH_SIZE == 0 and (i + 1) < len(queue):
        batch_num = (i + 1) // BATCH_SIZE
        total_batches = (len(queue) + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"  ⏸️  Batch {batch_num}/{total_batches} done — waiting {BATCH_DELAY}s...")
        time.sleep(BATCH_DELAY)

print(f"\n{'='*60}")
print(f"✅ Sent: {total_sent}")
print(f"❌ Failed: {total_failed}")
print(f"📊 Total: {total_sent + total_failed}")
print(f"{'='*60}")
