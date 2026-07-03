#!/usr/bin/env python3
"""Send Monday SASP Resident Meeting .ics invites + weekly reminders.
   Phase 1 (bulk): Send .ics invites at 10/day until all are sent.
   Phase 2 (Sun/Tue): Send HTML reminder with topics + Zoom info.
   Uses premium calendar_mailer.py template for all invites.

   Monday meetings are 1 HOUR (7:00–8:00 AM). Friday Grand Rounds are 2 hours."""
import json, re, os, sys
from datetime import date, timedelta, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calendar_mailer import send_calendar_invite, send_reminder_email, _html_wrap

# ── Monday Zoom Config ────────────────────────────────────
ZOOM_LINK = "https://montefiore.zoom.us/j/92009850717?pwd=25ask1SzLX2SdSrTbbhzb159UsyDFY.1"
MEETING_ID = "920 0985 0717"
PASSCODE = "808018"
PROGRESS_FILE = "/workspace/agentic-os/data/monday_sasp_progress.json"
DAILY_LIMIT = 10

# CRM data — read from Supabase Postgres
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from modules.crm_db import get_contacts
except ImportError:
    get_contacts = lambda: []

TEST_MODE = True
TEST_EMAIL = "sfrasier@montefiore.org"
PROD_RECIPIENTS = ["sfrasier@montefiore.org"]  # ⚠️ TEST MODE — only sends to test email

# ── Resident Name Resolution ────────────────────────────────

_resident_lookup = None

# Nickname → first-name mapping for PDF shorthand names
_RESIDENT_NICKNAMES = {
    "nate": "nathaniel",
    "sam": "samuel",
    "val": "valmic",
    "joe": "joseph",
    "jen": "jennifer",
}

def _load_resident_lookup():
    """Build a first-name → last-name map from CRM contacts (Resident category)."""
    global _resident_lookup
    if _resident_lookup is not None:
        return _resident_lookup
    _resident_lookup = {}
    try:
        for c in get_contacts():
            if c.get("category") == "Resident":
                fn = (c.get("firstName") or "").strip().lower()
                ln = (c.get("lastName") or "").strip()
                if fn and ln:
                    _resident_lookup[fn] = ln
    except Exception:
        pass
    return _resident_lookup

def _resolve_resident(name):
    """Given a resident name (first or last), return 'Dr. F. LastName' format.
    Resolves nicknames (Nate→Nathaniel), looks up CRM, uses first initial for
    disambiguation when multiple residents share a last name (e.g. Patel, Kim)."""
    if not name:
        return ""
    lookup = _load_resident_lookup()
    clean = name.strip().lower()
    # Try nickname → full first name first
    resolved_fn = _RESIDENT_NICKNAMES.get(clean, clean)
    ln = lookup.get(resolved_fn, "")
    if ln:
        # Check if this last name appears for multiple residents → use first initial
        dupes = sum(1 for v in lookup.values() if v.lower() == ln.lower())
        if dupes > 1:
            initial = resolved_fn[0].upper()
            return f"Dr. {initial}. {ln}"
        return f"Dr. {ln}"
    # Name might already be a last name (e.g. 'Hordines', 'Hill', 'Pak')
    return f"Dr. {name.strip()}"

_faculty_lookup = None

def _load_faculty_lookup():
    """Build a last-name → email map from CRM contacts (Faculty category)."""
    global _faculty_lookup
    if _faculty_lookup is not None:
        return _faculty_lookup
    _faculty_lookup = {}
    try:
        for c in get_contacts():
            if c.get("category") == "Faculty":
                ln = (c.get("lastName") or "").strip().lower()
                email = (c.get("email") or "").strip()
                if ln and email:
                    _faculty_lookup[ln] = email
    except Exception:
        pass
    return _faculty_lookup

def _resolve_attending_email(attending_name):
    """Given an attending last name, return their email from CRM."""
    if not attending_name:
        return ""
    # attending_name is "Dr. LastName" — strip prefix
    clean = attending_name.replace("Dr. ", "").strip().lower()
    lookup = _load_faculty_lookup()
    return lookup.get(clean, "")

# ── Parse GR data (contains Monday data too) ──────────────

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

def get_all_mondays():
    """Extract Monday SASP meetings from GR_DATA."""
    gr_data = parse_gr_data()
    events = []
    for row in gr_data:
        mon_date = row[1] if len(row) > 1 else ""
        if not mon_date or not mon_date.startswith("20"):
            continue
        topic = row[2].strip() if len(row) > 2 else "SASP"
        resident = row[3].strip() if len(row) > 3 else ""
        attending = row[4].strip() if len(row) > 4 else ""
        notes = row[10].strip() if len(row) > 10 else ""

        if not topic and not resident:
            continue

        # Skip holidays — no conference these days
        if topic.lower() == "holiday":
            continue

        # Resolve resident/attending to "Dr. LastName" format
        resident_dr = _resolve_resident(resident) if resident else ""
        attending_dr = f"Dr. {attending}" if attending else ""

        # Build title: topic + resident/attending
        if topic.lower().startswith("sasp") or not topic:
            if resident_dr and attending_dr:
                title = f"{topic}: {resident_dr} / {attending_dr}"
            elif resident_dr:
                title = f"{topic}: {resident_dr}"
            elif attending_dr:
                title = f"{topic}: {attending_dr}"
            else:
                title = topic
        else:
            title = topic

        events.append({"date": mon_date, "title": title, "topic": topic,
                        "resident": resident_dr, "attending": attending_dr,
                        "attending_email": _resolve_attending_email(attending_dr),
                        "notes": notes})
    events.sort(key=lambda e: e["date"])
    return events


def send_monday_ics(event, mon_date):
    """Send .ics invite for Monday SASP (1-hour: 7:00–8:00 AM)."""
    try:
        topic = event.get("topic", event["title"])

        # Build description with resident/attending
        desc_parts = ["Urology Resident Monday Conference"]
        if event.get("resident"):
            desc_parts.append(f"Resident: {event['resident']}")
        if event.get("attending"):
            desc_parts.append(f"Attending: {event['attending']}")
        description = "\n".join(desc_parts)

        # Session 7-8 only: Monday is a single 1-hour meeting
        session_7_8 = topic

        # Recipients: base list + this week's attending
        if TEST_MODE:
            to = TEST_EMAIL
        else:
            recipients = list(PROD_RECIPIENTS)
            att_email = event.get("attending_email", "")
            if att_email and att_email not in recipients:
                recipients.append(att_email)
            to = ", ".join(recipients)

        # ── Premium format matching memory specs ──
        # Subject: "Urology Monday Conference - {topic}, Dr. {attending}"
        subject = f"Invitation: Urology Monday Conference - {topic}"
        if event.get("attending"):
            subject += f", {event['attending']}"

        # Calendar title (shows on Outlook/Google Calendar):
        # 'Resident Weekly Conference YYYY : "Topic" - Attending / Resident'
        year = mon_date[:4]
        cal_title = f'Resident Weekly Conference {year} : "{topic}"'
        if event.get("attending") and event.get("resident"):
            cal_title += f" - {event['attending']} / {event['resident']}"
        elif event.get("attending"):
            cal_title += f" - {event['attending']}"
        elif event.get("resident"):
            cal_title += f" - {event['resident']}"

        # Premium format: pass session_7_8_label="Monday Conference" so the
        # Agenda section in the HTML body shows a proper label row
        mid = send_calendar_invite(
            to=to,
            subject=subject,
            summary=cal_title,
            description=description,
            location=ZOOM_LINK,
            date_str=mon_date,
            start_time="07:00",
            end_time="08:00",
            duration_minutes=60,
            zoom_link=ZOOM_LINK,
            meeting_id=MEETING_ID,
            passcode=PASSCODE,
            session_7_8=session_7_8,
            session_8_9="",
            session_7_8_label="Monday Conference",
            session_8_9_label="",
            resident=event.get("resident", ""),
            attending=event.get("attending", ""),
        )
        return True, ""
    except Exception as e:
        return False, str(e)


def send_monday_reminder(event, mon_date):
    """Send HTML reminder for Monday meeting (1-hour: 7:00–8:00 AM)."""
    try:
        dt = datetime.strptime(mon_date, "%Y-%m-%d")
        formatted = dt.strftime("%A, %B %d, %Y")
        topic = event.get("topic", event["title"])

        is_tuesday = date.today().weekday() == 1
        prefix = "TOMORROW" if is_tuesday else "THIS"

        resident_line = f"<tr><td style=\"font-size:12px;color:#6b7280;padding:2px 0\">Resident:</td><td style=\"font-size:13px;color:#111827;font-weight:500;padding-left:8px\">{event['resident']}</td></tr>" if event['resident'] else ""
        attending_line = f"<tr><td style=\"font-size:12px;color:#6b7280;padding:2px 0\">Attending:</td><td style=\"font-size:13px;color:#111827;font-weight:500;padding-left:8px\">{event['attending']}</td></tr>" if event['attending'] else ""

        inner = f"""<table width="100%" cellpadding="0" cellspacing="0">
<tr><td style="padding-bottom:20px;text-align:center">
<p style="margin:0;font-size:15px;color:#111827;line-height:1.6">{prefix} WEEK's <strong>Urology Monday Conference - {topic}</strong> - <strong>{formatted} 7:00\u20138:00 AM</strong>:</p>
</td></tr>
<tr><td style="padding-bottom:20px">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px">
<tr><td style="padding:12px 16px;font-size:11px;color:#6b7280;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;border-bottom:1px solid #e5e7eb;text-align:center">Details</td></tr>
<tr><td style="padding:12px 16px;text-align:center">
<table cellpadding="0" cellspacing="0" style="margin:0 auto">
<tr><td style="font-size:12px;color:#6b7280;padding:2px 0">Topic:</td><td style="font-size:13px;color:#111827;font-weight:600;padding-left:8px">{topic}</td></tr>
{resident_line}
{attending_line}
</table>
</td></tr>
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

        html_body = _html_wrap(f"{prefix} WEEK: Urology Monday Conference", inner)

        to = TEST_EMAIL if TEST_MODE else ", ".join(PROD_RECIPIENTS)
        subj_parts = [topic]
        if event.get("attending"):
            subj_parts.append(event["attending"])
        subject = f"{'TOMORROW' if is_tuesday else 'REMINDER'}: " + " - ".join(subj_parts)

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
    all_events = get_all_mondays()
    progress = load_progress()
    today = date.today()

    # ── Mode: Monday reminder (send Sunday or Tuesday) ──
    if today.weekday() in (6, 1):  # Sunday or Tuesday
        if today.weekday() == 6:  # Sunday
            monday = (today + timedelta(days=1)).isoformat()
        else:  # Tuesday
            print("📅 Tuesday check skipped (Monday already passed)")
            return

        for event in all_events:
            if event["date"] == monday:
                print(f"📅 Monday reminder for {monday}")
                ok, err = send_monday_reminder(event, monday)
                print(f"  {'✅' if ok else '❌'} {event['title'][:40]} (err: {err[:60] if err else 'none'})")
                return
        print(f"No Monday meeting found for {monday}")
        return

    # ── Mode: Bulk .ics send ──
    unsent = [e for e in all_events if e["date"] not in progress.get("ics_sent_dates", [])]
    if not unsent:
        print("✅ All Monday .ics invites sent!")
        return

    today_batch = unsent[:DAILY_LIMIT]
    print(f"Sending {len(today_batch)} .ics invites ({len(unsent)} remaining)...")

    sent_count = 0
    for event in today_batch:
        ok, err = send_monday_ics(event, event["date"])
        if ok:
            progress.setdefault("ics_sent_dates", []).append(event["date"])
            sent_count += 1
            print(f"  ✅ {event['date']}: {event['title'][:40]}")
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
