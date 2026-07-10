#!/usr/bin/env python3
"""Send individual invites ONLY to the 44 people who were missed in the first GR send.
Targets: July 10 and July 17 Grand Rounds.
"""
import json, os, sys, time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from calendar_mailer import send_calendar_invite
from send_grand_rounds_email import get_all_grand_rounds, _build_friday_title

# ── Config ────────────────────────────────────────────────
ZOOM_LINK = "https://us02web.zoom.us/j/86773878358?pwd=RUxySVVzUjFWL0lyRWtjdDBacTVPZz09"
MEETING_ID = "867 7387 8358"
PASSCODE = "466916"

TARGET_DATES = ["2026-07-10", "2026-07-17"]
BATCH_SIZE = 3
BATCH_DELAY = 30

# The 44 people who were missed (from Excel but not in original 43-person list)
MISSED_EMAILS = [
    "aalaimo@montefiore.org", "aasencio@montefiore.org", "arkrishnan@montefiore.org",
    "ashperdhej@montefiore.org", "avarughe@montefiore.org", "azallen@montefiore.org",
    "bgartrel@montefiore.org", "cdove@montefiore.org", "crysantos@montefiore.org",
    "dkarki@montefiore.org", "dosulli@montefiore.org", "equiachon@montefiore.org",
    "fkassam@montefiore.org", "hkanakka@montefiore.org", "hmary@montefiore.org",
    "hmelo@montefiore.org", "ilir.agalliu@einsteinmed.edu", "jcollazo@montefiore.org",
    "jdiazgonza@montefiore.org", "joodume@montefiore.org", "karamire@montefiore.org",
    "kmehta@montefiore.org", "marisoto@montefiore.org", "mbagcal@montefiore.org",
    "mgarg@montefiore.org", "midejes@montefiore.org", "mnwhite@montefiore.org",
    "mohara@montefiore.org", "nadchowdhu@montefiore.org", "pakeatle@montefiore.org",
    "pkareth@montefiore.org", "rheredia@montefiore.org", "sarodrigue@montefiore.org",
    "sasaji@montefiore.org", "sbalcarr@montefiore.org", "sipappac@montefiore.org",
    "skalnick@montefiore.org", "solsjon@montefiore.org", "swiafe@montefiore.org",
    "tafergus@montefiore.org", "tnardi@montefiore.org", "wbodner@montefiore.org",
    "wwint@montefiore.org", "yduchein@montefiore.org",
]

# ── Load events ───────────────────────────────────────────
all_events = get_all_grand_rounds()
target_events = [e for e in all_events if e["date"] in TARGET_DATES]
target_events.sort(key=lambda e: e["date"])

print(f"📋 Sending to {len(MISSED_EMAILS)} people who were missed")
print(f"📅 Events: {len(target_events)}")
for e in target_events:
    title, _ = _build_friday_title(e)
    print(f"   {e['date']}: {title}")
print(f"📧 Total emails: {len(MISSED_EMAILS) * len(target_events)}")
print(f"⏱️  Estimated: ~{((len(MISSED_EMAILS) * len(target_events)) // BATCH_SIZE) * BATCH_DELAY // 60} min\n")

# ── Build send queue ──────────────────────────────────────
queue = []
for event in target_events:
    fri_date = event["date"]
    title, _ = _build_friday_title(event)
    
    # Build description
    desc_parts = ["Urology Grand Rounds"]
    session_7_8 = event.get("topics_7_8", "") or event.get("topic_7_8", "")
    session_8_9 = event.get("topics_8_9", "") or event.get("topic_8_9", "")
    description = "\n".join(desc_parts)
    
    subject = f"Invitation: {title}"
    
    for email in MISSED_EMAILS:
        queue.append({
            "email": email,
            "fri_date": fri_date,
            "subject": subject,
            "cal_title": title,
            "description": description,
            "session_7_8": session_7_8,
            "session_8_9": session_8_9,
        })

print(f"Queue: {len(queue)} emails\n")

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
            date_str=item["fri_date"],
            start_time="07:00",
            end_time="09:00",
            duration_minutes=120,
            zoom_link=ZOOM_LINK,
            meeting_id=MEETING_ID,
            passcode=PASSCODE,
            session_7_8=item["session_7_8"],
            session_8_9=item["session_8_9"],
            session_7_8_label="7:00 - 8:00 AM",
            session_8_9_label="8:00 - 9:00 AM",
        )
        total_sent += 1
        print(f"  ✅ [{total_sent}/{len(queue)}] {item['email']} → {item['fri_date']}")
    except Exception as e:
        total_failed += 1
        print(f"  ❌ [{total_sent+total_failed}/{len(queue)}] {item['email']} → {str(e)[:80]}")

    if (i + 1) % BATCH_SIZE == 0 and (i + 1) < len(queue):
        batch_num = (i + 1) // BATCH_SIZE
        total_batches = (len(queue) + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"  ⏸️  Batch {batch_num}/{total_batches} — waiting {BATCH_DELAY}s...")
        time.sleep(BATCH_DELAY)

print(f"\n{'='*60}")
print(f"✅ Sent: {total_sent}")
print(f"❌ Failed: {total_failed}")
print(f"📊 Total: {total_sent + total_failed}")
print(f"{'='*60}")
