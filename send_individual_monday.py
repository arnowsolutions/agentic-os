#!/usr/bin/env python3
"""Send individual personalized .ics calendar invites for Monday SASP meetings.
Each recipient gets their own .ics with ATTENDEE;RSVP=TRUE.
Batched: 3 emails per batch, 30s between batches.
"""
import json, os, sys, time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from calendar_mailer import send_calendar_invite
from send_monday_sasp_email import get_all_mondays, _load_prod_recipients, _resolve_attending_email

# ── Config ────────────────────────────────────────────────
ZOOM_LINK = "https://montefiore.zoom.us/j/92009850717?pwd=25ask1SzLX2SdSrTbbhzb159UsyDFY.1"
MEETING_ID = "920 0985 0717"
PASSCODE = "808018"
EMAIL_GROUPS_FILE = "/workspace/agentic-os/data/email_groups.json"

# Set target dates here
TARGET_DATES = ["2026-07-13", "2026-07-20"]
BATCH_SIZE = 3
BATCH_DELAY = 30

# ── Load recipients ───────────────────────────────────────
with open(EMAIL_GROUPS_FILE) as f:
    groups = json.load(f)
recipients = groups["resident_conference"]["emails"]
print(f"📋 Loaded {len(recipients)} recipients from resident_conference list")

# ── Load events ───────────────────────────────────────────
all_events = get_all_mondays()
target_events = [e for e in all_events if e["date"] in TARGET_DATES]
target_events.sort(key=lambda e: e["date"])

print(f"📅 Sending invites for {len(target_events)} Monday meetings:")
for e in target_events:
    print(f"   {e['date']}: {e['title']}")

# ── Build send queue ──────────────────────────────────────
queue = []
for event in target_events:
    mon_date = event["date"]
    topic = event.get("topic", event["title"])

    # Build description
    desc_parts = ["Urology Resident Monday Conference"]
    if event.get("resident"):
        desc_parts.append(f"Resident: {event['resident']}")
    if event.get("attending"):
        desc_parts.append(f"Attending: {event['attending']}")
    description = "\n".join(desc_parts)

    # Subject
    subject = f"Invitation: Urology Monday Conference - {topic}"
    if event.get("attending"):
        subject += f", {event['attending']}"

    # Calendar title
    year = mon_date[:4]
    cal_title = f'Resident Weekly Conference {year} : "{topic}"'
    if event.get("attending") and event.get("resident"):
        cal_title += f" - {event['attending']} / {event['resident']}"
    elif event.get("attending"):
        cal_title += f" - {event['attending']}"
    elif event.get("resident"):
        cal_title += f" - {event['resident']}"

    # Recipients for this event: base list + this week's attending (if not already in list)
    event_recipients = list(recipients)
    att_email = event.get("attending_email", "")
    if att_email and att_email not in event_recipients:
        event_recipients.append(att_email)

    for email in event_recipients:
        queue.append({
            "email": email,
            "mon_date": mon_date,
            "subject": subject,
            "cal_title": cal_title,
            "description": description,
            "topic": topic,
            "resident": event.get("resident", ""),
            "attending": event.get("attending", ""),
        })

print(f"\n📧 Total emails to send: {len(queue)}")
print(f"⏱️  Batch size: {BATCH_SIZE}, delay: {BATCH_DELAY}s between batches")
print(f"   Estimated time: ~{((len(queue) // BATCH_SIZE) * BATCH_DELAY) // 60} minutes\n")

# ── Send ──────────────────────────────────────────────────
total_sent = 0
total_failed = 0

for i, item in enumerate(queue):
    try:
        msg_id = send_calendar_invite(
            to=item["email"],
            subject=item["subject"],
            summary=item["cal_title"],
            description=item["description"],
            location=ZOOM_LINK,
            date_str=item["mon_date"],
            start_time="07:00",
            end_time="08:00",
            duration_minutes=60,
            zoom_link=ZOOM_LINK,
            meeting_id=MEETING_ID,
            passcode=PASSCODE,
            session_7_8=item["topic"],
            session_8_9="",
            session_7_8_label="Monday Conference",
            session_8_9_label="",
            resident=item["resident"],
            attending=item["attending"],
        )
        total_sent += 1
        print(f"  ✅ [{total_sent}/{len(queue)}] {item['email']} → {item['mon_date']} ({item['topic'][:30]}...)")
    except Exception as e:
        total_failed += 1
        print(f"  ❌ [{total_sent+total_failed}/{len(queue)}] {item['email']} → {str(e)[:80]}")

    # Batch delay
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
