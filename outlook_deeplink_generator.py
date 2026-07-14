#!/usr/bin/env python3
"""
Outlook Calendar Deeplink Generator
====================================
Generates an HTML page with buttons that open pre-filled Outlook calendar
compose forms. No login, no API, no token — just URL deeplinks.

Each button opens outlook.office.com/calendar/deeplink/compose with:
  - Subject pre-filled
  - Body pre-filled (plain text, nicely formatted)
  - Recipients pre-filled (or test email in test mode)
  - Start/end time pre-filled
  - Location set to Zoom

The user just clicks a button → Outlook opens → clicks Send.

Usage:
  python3 outlook_deeplink_generator.py                    # Generate HTML page (test mode)
  python3 outlook_deeplink_generator.py --no-test           # Real recipients
  python3 outlook_deeplink_generator.py --type monday        # Monday SASP only
  python3 outlook_deeplink_generator.py --type grand-rounds  # Friday GR only
  python3 outlook_deeplink_generator.py --start-date 2026-07-13  # From this date forward
"""
import json, re, os, argparse, urllib.parse, sys
from datetime import datetime
from pathlib import Path

# CRM lookup for attending emails
sys.path.insert(0, str(Path(__file__).parent))
try:
    from modules.crm_db import get_contacts
except ImportError:
    get_contacts = lambda: []

# ── Paths ──────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.resolve()
GR_DATA_FILE = BASE_DIR / "dashboard" / "pages" / "grand-rounds.js"
EMAIL_GROUPS_FILE = BASE_DIR / "data" / "email_groups.json"
OUTPUT_DIR = BASE_DIR / "data" / "outlook_deeplinks"
TEST_EMAIL = "sfrasier@montefiore.org"

# ── Zoom Config ─────────────────────────────────────────────
GR_ZOOM_LINK = "https://us02web.zoom.us/j/86773878358?pwd=RUxySVVzUjFWL0lyRWtjdDBacTVPZz09"
GR_MEETING_ID = "867 7387 8358"
GR_PASSCODE = "466916"

MON_ZOOM_LINK = "https://montefiore.zoom.us/j/92009850717?pwd=25ask1SzLX2SdSrTbbhzb159UsyDFY.1"
MON_MEETING_ID = "920 0985 0717"
MON_PASSCODE = "808018"


# ══════════════════════════════════════════════════════════════
#  DATA SOURCES
# ══════════════════════════════════════════════════════════════

def parse_gr_data():
    """Parse GR_DATA from grand-rounds.js into a Python list."""
    with open(GR_DATA_FILE) as f:
        js = f.read()
    start = js.index("const GR_DATA = ")
    start = js.index("[", start)
    depth = 0
    end = start
    for i, c in enumerate(js[start:]):
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                end = start + i + 1
                break
    array_str = js[start:end]
    array_str = re.sub(r",\s*]", "]", array_str)
    array_str = re.sub(r"//.*", "", array_str)
    return json.loads(array_str)


def _get_db_conn():
    """Get a psycopg2 connection to the urology_qgenda database. Returns None on failure."""
    import psycopg2, subprocess
    pw = os.environ.get("POSTGRES_PASSWORD", "")
    if not pw:
        try:
            r = subprocess.run(['grep', 'POSTGRES_PASSWORD', '/workspace/projects/unified/app/.env'],
                capture_output=True, text=True, timeout=5)
            if r.returncode == 0:
                pw = r.stdout.strip().split('=', 1)[1].strip()
        except Exception:
            return None
    if not pw:
        # Try without password — local PostgreSQL often trusts local connections
        pass
    try:
        kwargs = dict(host="127.0.0.1", port=5432, dbname="urology_qgenda", user="postgres", connect_timeout=3)
        if pw:
            kwargs["password"] = pw
        return psycopg2.connect(**kwargs)
    except Exception:
        return None


def get_schedule_from_db():
    """Read all schedule rows from the grand_rounds_schedule table."""
    conn = _get_db_conn()
    if not conn:
        # Fallback to JS file
        return parse_gr_data()
    try:
        cur = conn.cursor()
        cur.execute('''
            SELECT id, month, mon_date::text, mon_topic, resident, attending,
                   fri_date::text, gr_7_8, gr_8_9, notes
            FROM grand_rounds_schedule ORDER BY COALESCE(mon_date, fri_date)
        ''')
        rows = []
        for r in cur.fetchall():
            row = [r[1] or "", r[2] or "", r[3] or "", r[4] or "", r[5] or "",
                   "", "", r[6] or "", r[7] or "", r[8] or "", r[9] or ""]
            row[1] = r[2] if r[2] else ""
            row[7] = r[6] if r[6] else ""
            rows.append(row)
        cur.close()
        conn.close()
        return rows
    except Exception as e:
        print(f"  DB error, falling back to JS: {e}")
        return parse_gr_data()


def get_monday_events(start_date=None):
    gr_data = get_schedule_from_db()
    events = []
    for row in gr_data:
        mon_date = row[1] if len(row) > 1 else ""
        if not mon_date or not mon_date.startswith("20"):
            continue
        if start_date and mon_date < start_date:
            continue
        topic = (row[2] or "").strip()
        resident = (row[3] or "").strip()
        attending = (row[4] or "").strip()
        if not topic or "holiday" in topic.lower():
            continue
        if "[see next yr" in topic.lower():
            continue
        events.append({
            "date": mon_date, "type": "monday", "topic": topic,
            "resident": resident, "attending": attending,
            "zoom_link": MON_ZOOM_LINK, "meeting_id": MON_MEETING_ID, "passcode": MON_PASSCODE,
        })
    events.sort(key=lambda e: e["date"])
    return events


def get_grand_rounds_events(start_date=None):
    gr_data = get_schedule_from_db()
    events = []
    for row in gr_data:
        fri_date = row[7] if len(row) > 7 else ""
        if not fri_date or not fri_date.startswith("20"):
            continue
        if start_date and fri_date < start_date:
            continue
        gr_7_8 = (row[8] or "").strip()
        gr_8_9 = (row[9] or "").strip()
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
        elif "Quality Improvement" in gr_7_8 or "Quality Improvement" in gr_8_9:
            meeting_type = "QI"
        events.append({
            "date": fri_date, "type": "grand-rounds", "meeting_type": meeting_type,
            "topic_7_8": gr_7_8, "topic_8_9": gr_8_9,
            "zoom_link": GR_ZOOM_LINK, "meeting_id": GR_MEETING_ID, "passcode": GR_PASSCODE,
        })
    events.sort(key=lambda e: e["date"])
    return events


def load_email_groups():
    if not EMAIL_GROUPS_FILE.exists():
        return {}
    return json.load(open(EMAIL_GROUPS_FILE))


def get_recipients_for_grand_rounds(meeting_type=""):
    groups = load_email_groups()
    if "Faculty" in meeting_type:
        return groups.get("faculty_meeting", {}).get("emails", [])
    return groups.get("grand_rounds", {}).get("emails", [])


def get_recipients_for_monday():
    groups = load_email_groups()
    return groups.get("resident_conference", {}).get("emails", [])


def lookup_attending_email(attending_name):
    """Look up a faculty attending's email from the CRM by matching last name.
    Returns the email string, or None if not found."""
    if not attending_name or attending_name in ("N/A", "TBD", "", "None"):
        return None
    # Normalize: take the first word after comma as last name, or first word
    name = attending_name.strip()
    # Handle "Lastname, Firstname" format
    if "," in name:
        lastname = name.split(",")[0].strip().lower()
    else:
        # Single name — assume it's the last name or first word
        parts = name.split()
        lastname = parts[-1].strip().lower() if parts else name.lower()
    # Search CRM Faculty contacts
    try:
        for c in get_contacts():
            if c.get("category") == "Faculty":
                c_last = (c.get("lastName") or "").strip().lower()
                if c_last == lastname:
                    email = c.get("email", "").strip()
                    if email:
                        return email
    except Exception:
        pass
    return None


# ══════════════════════════════════════════════════════════════
#  SUBJECT & BODY BUILDERS (nicely formatted plain text)
# ══════════════════════════════════════════════════════════════

def build_monday_subject(event):
    topic = event["topic"]
    attending = event["attending"]
    if attending and attending not in ("N/A", "TBD", "", "None"):
        return f"Invitation: Urology Monday Conference - {topic}, Dr. {attending}"
    return f"Invitation: Urology Monday Conference - {topic}"


def build_monday_body(event):
    d = datetime.strptime(event["date"], "%Y-%m-%d")
    formatted = d.strftime("%A, %B %d, %Y")
    zoom_link = event['zoom_link']
    def esc(s):
        return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    def dr(name):
        if not name or name in ("N/A", "TBD", "", "None"):
            return "TBD"
        return f"Dr. {esc(name)}"
    return (
        f"<strong>Montefiore Urology - Resident AM Conference</strong>"
        f"<hr>"
        f"<table cellpadding='4' style='border-collapse:collapse;'>"
        f"<tr><td><strong>Date</strong></td><td>{esc(formatted)}</td></tr>"
        f"<tr><td><strong>Time</strong></td><td>7:00 - 8:00 AM (Eastern)</td></tr>"
        f"<tr><td><strong>Location</strong></td><td><a href='{esc(zoom_link)}'>Zoom Meeting</a></td></tr>"
        f"</table>"
        f"<hr>"
        f"<strong>PRESENTATION</strong>"
        f"<table cellpadding='4' style='border-collapse:collapse;'>"
        f"<tr><td><strong>Topic</strong></td><td>{esc(event['topic'])}</td></tr>"
        f"<tr><td><strong>Resident</strong></td><td>{dr(event['resident'])}</td></tr>"
        f"<tr><td><strong>Attending</strong></td><td>{dr(event['attending'])}</td></tr>"
        f"</table>"
        f"<hr>"
        f"<strong>ZOOM MEETING DETAILS</strong>"
        f"<table cellpadding='4' style='border-collapse:collapse;'>"
        f"<tr><td><strong>Join</strong></td><td><a href='{esc(zoom_link)}'>Click here to join Zoom</a></td></tr>"
        f"<tr><td><strong>Meeting ID</strong></td><td style='background:#f0f0f0; padding:4px 10px; font-size:15px;'><strong>{esc(event['meeting_id'])}</strong></td></tr>"
        f"<tr><td><strong>Passcode</strong></td><td style='background:#f0f0f0; padding:4px 10px; font-size:15px;'><strong>{esc(event['passcode'])}</strong></td></tr>"
        f"</table>"
        f"<hr>"
        f"<strong>PHONE DIAL-IN</strong>"
        f"<table cellpadding='4' style='border-collapse:collapse;'>"
        f"<tr><td valign='top'>&bull;</td><td>+1 646-558-8656 (New York)</td></tr>"
        f"<tr><td valign='top'>&bull;</td><td>+1 301-715-8592 (Washington, DC)</td></tr>"
        f"<tr><td valign='top'>&bull;</td><td>+1 312-626-6799 (Chicago)</td></tr>"
        f"</table>"
        f"<em>Enter Meeting ID, then Passcode when prompted.</em>"
        f"<hr>"
        f"<strong>Montefiore Medical Center &nbsp;|&nbsp; Department of Urology</strong><br>"
        f"1250 Waters Place, Tower One, PH-2, Bronx, NY 10461"
    )


def build_grand_rounds_subject(event):
    mt = event["meeting_type"]
    t7 = event["topic_7_8"]
    t8 = event["topic_8_9"]
    if "Faculty" in mt:
        summary = "[FACULTY] Faculty Meeting"
    elif "Peds" in mt:
        summary = "Urology Grand Rounds - Peds / Peds Multidisciplinary"
    elif "Journal" in mt:
        summary = "Urology Grand Rounds - Journal Club"
    else:
        topics = " / ".join(p for p in [t7, t8] if p and p.strip())
        summary = f"Urology Grand Rounds - {topics}" if topics else "Urology Grand Rounds"
    return f"Invitation: {summary}"


def build_grand_rounds_body(event):
    d = datetime.strptime(event["date"], "%Y-%m-%d")
    formatted = d.strftime("%A, %B %d, %Y")
    t7 = event["topic_7_8"]
    t8 = event["topic_8_9"]
    # If only one slot is filled and the event likely covers both hours, copy to both
    if t7 and not t8:
        t8 = t7
    elif t8 and not t7:
        t7 = t8
    zoom_link = event['zoom_link']
    def esc(s):
        return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return (
        f"<strong>Montefiore Urology - Grand Rounds</strong>"
        f"<hr>"
        f"<table cellpadding='4' style='border-collapse:collapse;'>"
        f"<tr><td><strong>Date</strong></td><td>{esc(formatted)}</td></tr>"
        f"<tr><td><strong>Time</strong></td><td>7:00 - 9:00 AM (Eastern)</td></tr>"
        f"<tr><td><strong>Location</strong></td><td>Hutch I PH2 Conf A (7-8) / Conf B (8-9)</td></tr>"
        f"<tr><td><strong>Type</strong></td><td>{esc(event['meeting_type'])}</td></tr>"
        f"</table>"
        f"<hr>"
        f"<strong>AGENDA</strong>"
        f"<table cellpadding='4' style='border-collapse:collapse;'>"
        f"<tr><td><strong>7:00 - 8:00 AM</strong></td><td>{esc(t7)}</td></tr>"
        f"<tr><td><strong>8:00 - 9:00 AM</strong></td><td>{esc(t8)}</td></tr>"
        f"</table>"
        f"<hr>"
        f"<strong>ZOOM MEETING DETAILS</strong>"
        f"<table cellpadding='4' style='border-collapse:collapse;'>"
        f"<tr><td><strong>Join</strong></td><td><a href='{esc(zoom_link)}'>Click here to join Zoom</a></td></tr>"
        f"<tr><td><strong>Meeting ID</strong></td><td style='background:#f0f0f0; padding:4px 10px; font-size:15px;'><strong>{esc(event['meeting_id'])}</strong></td></tr>"
        f"<tr><td><strong>Passcode</strong></td><td style='background:#f0f0f0; padding:4px 10px; font-size:15px;'><strong>{esc(event['passcode'])}</strong></td></tr>"
        f"</table>"
        f"<hr>"
        f"<strong>PHONE DIAL-IN</strong>"
        f"<table cellpadding='4' style='border-collapse:collapse;'>"
        f"<tr><td valign='top'>&bull;</td><td>+1 646-558-8656 (New York)</td></tr>"
        f"<tr><td valign='top'>&bull;</td><td>+1 301-715-8592 (Washington, DC)</td></tr>"
        f"<tr><td valign='top'>&bull;</td><td>+1 312-626-6799 (Chicago)</td></tr>"
        f"</table>"
        f"<em>Enter Meeting ID, then Passcode when prompted.</em>"
        f"<hr>"
        f"<strong>Montefiore Medical Center &nbsp;|&nbsp; Department of Urology</strong><br>"
        f"1250 Waters Place, Tower One, PH-2, Bronx, NY 10461"
    )


# ══════════════════════════════════════════════════════════════
#  DEEPLINK BUILDER
# ══════════════════════════════════════════════════════════════

def build_deeplink(subject, body, to_param, start_dt, end_dt, location="Zoom"):
    # Body is now pre-built HTML directly from the body builders.
    # Just URL-encode and pass through with bodyType=HTML.
    params = urllib.parse.urlencode({
        "subject": subject,
        "body": body,
        "bodyType": "HTML",
        "to": to_param,
        "startdt": start_dt,
        "enddt": end_dt,
        "location": location,
    }, quote_via=urllib.parse.quote)
    return f"https://outlook.office.com/calendar/deeplink/compose?{params}"


# ══════════════════════════════════════════════════════════════
#  HTML PAGE GENERATOR
# ══════════════════════════════════════════════════════════════

def _build_event_rows(events, test_mode, test_email):
    """Build HTML table rows for a list of events, grouped by month."""
    from collections import OrderedDict
    by_month = OrderedDict()
    for ev in events:
        month_label = datetime.strptime(ev["date"], "%Y-%m-%d").strftime("%B %Y")
        if month_label not in by_month:
            by_month[month_label] = []
        by_month[month_label].append(ev)

    rows_html = ""
    for month_label, month_events in by_month.items():
        rows_html += f'<tr style="background:#0b1220"><td colspan="5" style="padding:10px 14px;font-weight:700;font-size:14px;color:#fbbf24">{month_label}</td></tr>\n'
        for ev in month_events:
            display_subject = ev["subject"].replace("Invitation: ", "")
            if len(display_subject) > 55:
                display_subject = display_subject[:52] + "..."
            date_display = datetime.strptime(ev["date"], "%Y-%m-%d").strftime("%b %d, %Y")
            date_dow = datetime.strptime(ev["date"], "%Y-%m-%d").strftime("%a")
            event_id = ev["event_id"]
            rows_html += f'''<tr id="row-{event_id}" style="border-bottom:1px solid #1e293b">
  <td style="padding:10px 14px;white-space:nowrap;font-size:13px"><strong>{date_display}</strong><br><span style="color:#64748b;font-size:11px">{date_dow}</span></td>
  <td style="padding:10px 14px"><span style="background:{ev['type_color']};color:#fff;padding:2px 8px;border-radius:999px;font-size:11px;font-weight:600">{ev['type_label']}</span></td>
  <td style="padding:10px 14px;font-size:12px;color:#94a3b8;max-width:300px;overflow:hidden;text-overflow:ellipsis">{display_subject}</td>
  <td style="padding:10px 14px;white-space:nowrap" id="status-{event_id}"><span id="saved-badge-{event_id}"></span></td>
  <td style="padding:10px 14px;white-space:nowrap">
    <a href="{ev['url']}" target="_blank" data-event-id="{event_id}" data-normal-url="{ev['url']}" data-update-url="{ev['update_url']}" class="invite-btn" style="display:inline-block;background:{ev['type_color']};color:#fff;padding:6px 14px;border-radius:6px;text-decoration:none;font-size:12px;font-weight:600">Open in Outlook</a>
    <button onclick="openEditor('{event_id}')" style="display:inline-block;background:transparent;color:#94a3b8;border:1px solid #475569;padding:5px 12px;border-radius:6px;cursor:pointer;font-size:12px;margin-left:6px">Edit</button>
  </td>
</tr>
'''
    return rows_html


def generate_html_page(monday_events, gr_events, test_mode=True, test_email=TEST_EMAIL):
    """Generate the HTML invites page with two tabs: Monday and Friday."""

    TYPE_COLORS = {
        "Monday SASP": "#1a3a5c",
        "Grand Rounds": "#1a3a5c",
        "Peds Grand Rounds": "#2E7D32",
        "Faculty Meeting": "#6A1B9A",
        "Journal Club": "#E65100",
        "QI": "#E65100",
    }

    # Build Monday events
    monday_rows = []
    event_data_json = {}
    for ev in monday_events:
        recipients = get_recipients_for_monday()
        # Add attending's email if found in CRM
        attending_email = lookup_attending_email(ev.get("attending", ""))
        if attending_email:
            # Prepend attending to the front so it's before residents
            recipients = [attending_email] + [r for r in recipients if r != attending_email]
        to_param = test_email if test_mode else ",".join(recipients)
        subject = build_monday_subject(ev)
        update_subject = f"**UPDATE** {subject}"
        body = build_monday_body(ev)
        location = ev["zoom_link"]
        start_dt = f"{ev['date']}T07:00:00"
        end_dt = f"{ev['date']}T08:00:00"
        url = build_deeplink(subject, body, to_param, start_dt, end_dt, location)
        update_url = build_deeplink(update_subject, body, to_param, start_dt, end_dt, location)
        eid = f"mon_{ev['date']}"
        monday_rows.append({
            "date": ev["date"], "type_label": "Monday SASP",
            "type_color": TYPE_COLORS["Monday SASP"],
            "subject": subject, "url": url, "update_url": update_url,
            "event_id": eid,
        })
        event_data_json[eid] = {
            "subject": subject, "body": body, "to": to_param,
            "startdt": start_dt, "enddt": end_dt, "location": location,
        }

    # Build Friday events
    friday_rows = []
    for ev in gr_events:
        recipients = get_recipients_for_grand_rounds(ev["meeting_type"])
        to_param = test_email if test_mode else ",".join(recipients)
        subject = build_grand_rounds_subject(ev)
        update_subject = f"**UPDATE** {subject}"
        body = build_grand_rounds_body(ev)
        location = "Hutch I PH2 Conf A (7-8) / Conf B (8-9)"
        start_dt = f"{ev['date']}T07:00:00"
        end_dt = f"{ev['date']}T09:00:00"
        url = build_deeplink(subject, body, to_param, start_dt, end_dt, location)
        update_url = build_deeplink(update_subject, body, to_param, start_dt, end_dt, location)
        eid = f"fri_{ev['date']}"
        friday_rows.append({
            "date": ev["date"], "type_label": ev["meeting_type"],
            "type_color": TYPE_COLORS.get(ev["meeting_type"], "#1a3a5c"),
            "subject": subject, "url": url, "update_url": update_url,
            "event_id": eid,
        })
        event_data_json[eid] = {
            "subject": subject, "body": body, "to": to_param,
            "startdt": start_dt, "enddt": end_dt, "location": location,
        }

    # Sort each by date
    monday_rows.sort(key=lambda e: e["date"])
    friday_rows.sort(key=lambda e: e["date"])

    # Build table HTML for each tab
    monday_table_html = _build_event_rows(monday_rows, test_mode, test_email)
    friday_table_html = _build_event_rows(friday_rows, test_mode, test_email)

    total = len(monday_rows) + len(friday_rows)
    mode_label = f"TEST MODE — all invites go to {test_email}" if test_mode else "LIVE MODE — full recipient lists"
    test_html = f'<span class="test"><strong>TEST MODE</strong> — all invites go to {test_email} only</span>' if test_mode else '<strong>LIVE MODE</strong> — invites go to the full recipient list'

    # Load server-side sent data from progress files
    MON_PROGRESS_FILE = BASE_DIR / "data" / "monday_sasp_progress.json"
    GR_PROGRESS_FILE = BASE_DIR / "data" / "grand_rounds_progress.json"
    sent_dates = {"monday": set(), "grand_rounds": set()}
    try:
        if MON_PROGRESS_FILE.exists():
            mon_data = json.loads(MON_PROGRESS_FILE.read_text())
            sent_dates["monday"] = set(mon_data.get("ics_sent_dates", []))
    except Exception:
        pass
    try:
        if GR_PROGRESS_FILE.exists():
            gr_data = json.loads(GR_PROGRESS_FILE.read_text())
            sent_data = gr_data.get("ics_sent_dates", [])
            if isinstance(sent_data, list):
                sent_dates["grand_rounds"] = set(sent_data)
    except Exception:
        pass
    # Also check send_log for additional sent dates
    SEND_LOG_FILE = BASE_DIR / "data" / "grand_rounds_send_log.json"
    try:
        if SEND_LOG_FILE.exists():
            log_data = json.loads(SEND_LOG_FILE.read_text())
            for ev in log_data.get("real_sends", {}).get("sent_events", []):
                sent_dates["grand_rounds"].add(ev["date"])
    except Exception:
        pass
    sent_json = json.dumps({
        "monday": sorted(list(sent_dates["monday"])),
        "grand_rounds": sorted(list(sent_dates["grand_rounds"])),
    })

    # Build schedule editor data from DB
    raw_data = get_schedule_from_db()
    schedule_rows = []
    try:
        conn = _get_db_conn()
        if conn:
            cur = conn.cursor()
            cur.execute('SELECT id, mon_date::text, mon_topic, resident, attending, fri_date::text, gr_7_8, gr_8_9 FROM grand_rounds_schedule ORDER BY COALESCE(mon_date, fri_date)')
            for r in cur.fetchall():
                schedule_rows.append({
                    "db_id": r[0],
                    "mon_date": r[1] or "",
                    "mon_topic": r[2] or "",
                    "resident": r[3] or "",
                    "attending": r[4] or "",
                    "fri_date": r[5] or "",
                    "gr_7_8": r[6] or "",
                    "gr_8_9": r[7] or "",
                })
            cur.close()
            conn.close()
        else:
            raise Exception("No DB connection — falling back to JS data")
    except Exception:
        # Fallback to raw data without IDs
        for row in raw_data:
            mon_date = row[1] if len(row) > 1 and row[1] and row[1].startswith("20") else ""
            fri_date = row[7] if len(row) > 7 and row[7] and row[7].startswith("20") else ""
            if not mon_date and not fri_date:
                continue
            schedule_rows.append({
                "db_id": None,
                "mon_date": mon_date,
                "mon_topic": row[2] if len(row) > 2 else "",
                "resident": row[3] if len(row) > 3 else "",
                "attending": row[4] if len(row) > 4 else "",
                "fri_date": fri_date,
                "gr_7_8": row[8] if len(row) > 8 else "",
                "gr_8_9": row[9] if len(row) > 9 else "",
            })
    schedule_json = json.dumps(schedule_rows)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Montefiore Urology - Calendar Invites</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box }}
  body {{ background:#0f172a; color:#e2e8f0; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif; padding:20px; max-width:900px; margin:0 auto }}
  h1 {{ font-size:22px; margin-bottom:4px }}
  .subtitle {{ color:#94a3b8; font-size:14px; margin-bottom:20px }}
  .info {{ background:#1e293b; border:1px solid #334155; border-radius:8px; padding:14px 18px; margin-bottom:20px; font-size:13px; line-height:1.6 }}
  .info strong {{ color:#fbbf24 }}
  .info .test {{ color:#ef4444 }}
  /* Update toggle */
  .toggle-bar {{ display:flex; align-items:center; gap:16px; background:#1e293b; border:1px solid #334155; border-radius:8px; padding:12px 18px; margin-bottom:20px; font-size:13px }}
  .toggle-bar label {{ font-weight:600; color:#e2e8f0 }}
  .switch {{ position:relative; display:inline-block; width:44px; height:24px }}
  .switch input {{ opacity:0; width:0; height:0 }}
  .slider {{ position:absolute; cursor:pointer; top:0; left:0; right:0; bottom:0; background:#334155; border-radius:24px; transition:0.2s }}
  .slider:before {{ content:''; position:absolute; height:18px; width:18px; left:3px; bottom:3px; background:#94a3b8; border-radius:50%; transition:0.2s }}
  input:checked + .slider {{ background:#f59e0b }}
  input:checked + .slider:before {{ transform:translateX(20px); background:#fff }}
  .toggle-bar .hint {{ color:#64748b; font-size:12px }}
  .toggle-bar .reset-btn {{ margin-left:auto; background:#334155; color:#94a3b8; border:1px solid #475569; padding:5px 12px; border-radius:6px; cursor:pointer; font-size:12px }}
  .toggle-bar .reset-btn:hover {{ background:#475569; color:#e2e8f0 }}
  /* Sent status */
  .sent-badge {{ display:inline-flex; align-items:center; gap:4px; background:#064e3b; color:#34d399; padding:3px 10px; border-radius:999px; font-size:11px; font-weight:600 }}
  .sent-badge:before {{ content:'\\2713' }}
  .row-sent {{ opacity:0.5 }}
  .row-sent .invite-btn {{ background:#334155 !important; cursor:default }}
  .edit-badge {{ display:inline-flex; align-items:center; gap:4px; background:#451a03; color:#fbbf24; padding:3px 8px; border-radius:999px; font-size:10px; font-weight:600 }}
  /* Editor modal */
  .modal-overlay {{ display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.7); z-index:1000; justify-content:center; align-items:flex-start; padding:40px 20px; overflow-y:auto }}
  .modal-overlay.open {{ display:flex }}
  .modal {{ background:#1e293b; border:1px solid #334155; border-radius:12px; width:100%; max-width:700px; padding:24px; box-shadow:0 20px 60px rgba(0,0,0,0.5) }}
  .modal h2 {{ font-size:18px; margin-bottom:16px; color:#fbbf24 }}
  .modal label {{ display:block; font-size:12px; color:#94a3b8; margin-bottom:4px; font-weight:600; text-transform:uppercase; letter-spacing:0.5px }}
  .modal input[type=text] {{ width:100%; background:#0f172a; border:1px solid #334155; color:#e2e8f0; padding:10px 12px; border-radius:6px; font-size:14px; margin-bottom:16px }}
  .modal .body-editor {{ width:100%; min-height:300px; background:#fff; color:#1a1a1a; border:1px solid #334155; border-radius:6px; padding:16px; font-size:14px; line-height:1.6; overflow-y:auto; margin-bottom:16px }}
  .modal .body-editor:focus {{ outline:2px solid #fbbf24 }}
  .modal .modal-actions {{ display:flex; gap:12px; justify-content:flex-end }}
  .modal .btn-send {{ background:#f59e0b; color:#0f172a; border:none; padding:10px 24px; border-radius:6px; cursor:pointer; font-size:14px; font-weight:700 }}
  .modal .btn-send:hover {{ background:#fbbf24 }}
  .modal .btn-cancel {{ background:#334155; color:#94a3b8; border:1px solid #475569; padding:10px 20px; border-radius:6px; cursor:pointer; font-size:14px }}
  .modal .btn-cancel:hover {{ background:#475569; color:#e2e8f0 }}
  /* Tabs */
  .tabs {{ display:flex; gap:0; margin-bottom:0; border-bottom:2px solid #334155 }}
  .tab {{ padding:12px 24px; cursor:pointer; font-size:14px; font-weight:600; color:#64748b; border:none; background:none; border-bottom:3px solid transparent; transition:all 0.2s }}
  .tab:hover {{ color:#e2e8f0 }}
  .tab.active {{ color:#fbbf24; border-bottom-color:#fbbf24 }}
  .tab .badge {{ display:inline-block; background:#334155; color:#94a3b8; padding:1px 8px; border-radius:999px; font-size:11px; margin-left:6px }}
  .tab.active .badge {{ background:#fbbf24; color:#0f172a }}
  /* Tab content */
  .tab-content {{ display:none }}
  .tab-content.active {{ display:block }}
  /* Table */
  .count {{ color:#94a3b8; font-size:13px; margin:14px 0 }}
  table {{ width:100%; border-collapse:collapse; font-size:13px }}
  th {{ text-align:left; padding:8px 14px; color:#64748b; font-size:11px; text-transform:uppercase; letter-spacing:0.5px; border-bottom:2px solid #334155 }}
  a:hover {{ opacity:0.85 }}
  .footer {{ margin-top:24px; padding-top:16px; border-top:1px solid #334155; font-size:12px; color:#64748b; line-height:1.5 }}
</style>
</head>
<body>
  <h1>Montefiore Urology Calendar Invites</h1>
  <p class="subtitle">Click any button to open a pre-filled Outlook compose form — then click Send</p>

  <div class="info">
    <strong>How it works:</strong> Each button opens Outlook Web with everything pre-filled
    (subject, formatted body, Zoom link, time, location, attendees).<br>
    Just click <strong>Send</strong> in the Outlook tab that opens.<br><br>
    {test_html}
  </div>

  <div class="toggle-bar">
    <label>UPDATE Mode</label>
    <label class="switch">
      <input type="checkbox" id="updateToggle">
      <span class="slider"></span>
    </label>
    <span class="hint">When ON, subject line includes <strong>**UPDATE**</strong> prefix for resending changed invites</span>
    <button class="reset-btn" onclick="resetSent()">Reset All Sent Status</button>
  </div>

  <div class="tabs">
    <button class="tab active" onclick="switchTab('monday')">Monday Conference <span class="badge">{len(monday_rows)}</span></button>
    <button class="tab" onclick="switchTab('friday')">Friday Grand Rounds <span class="badge">{len(friday_rows)}</span></button>
    <button class="tab" onclick="switchTab('edit')">Edit Schedule <span class="badge">CSV</span></button>
  </div>

  <div id="tab-monday" class="tab-content active">
    <div class="count">{len(monday_rows)} Monday SASP events · 7:00–8:00 AM · Zoom Meeting ID {MON_MEETING_ID}</div>
    <table>
      <thead><tr>
        <th style="width:120px">Date</th>
        <th style="width:130px">Type</th>
        <th>Topic</th>
        <th style="width:80px">Status</th>
        <th style="width:220px">Action</th>
      </tr></thead>
      <tbody>
{monday_table_html}      </tbody>
    </table>
  </div>

  <div id="tab-friday" class="tab-content">
    <div class="count">{len(friday_rows)} Friday Grand Rounds events · 7:00–9:00 AM · Zoom Meeting ID {GR_MEETING_ID}</div>
    <table>
      <thead><tr>
        <th style="width:120px">Date</th>
        <th style="width:160px">Type</th>
        <th>Topic</th>
        <th style="width:80px">Status</th>
        <th style="width:220px">Action</th>
      </tr></thead>
      <tbody>
{friday_table_html}      </tbody>
    </table>
  </div>

  <div id="tab-edit" class="tab-content">
    <div class="count">Edit schedule data below — changes save directly to the database. No download needed.</div>
    <div style="margin:14px 0;display:flex;gap:12px;align-items:center">
      <button onclick="saveAllChanges()" id="saveBtn" style="background:#f59e0b;color:#0f172a;border:none;padding:10px 24px;border-radius:6px;cursor:pointer;font-size:14px;font-weight:700">Save All Changes</button>
      <span id="saveStatus" style="color:#64748b;font-size:12px"></span>
    </div>
    <div style="overflow-x:auto">
    <table id="scheduleTable" style="font-size:12px;min-width:1100px">
      <thead><tr>
        <th style="width:100px">Mon Date</th>
        <th>Monday Topic</th>
        <th style="width:80px">Resident</th>
        <th style="width:100px">Attending</th>
        <th style="width:100px">Fri Date</th>
        <th>GR 7-8</th>
        <th>GR 8-9</th>
      </tr></thead>
      <tbody id="scheduleBody"></tbody>
    </table>
    </div>
  </div>

  <div class="footer">
    {total} total events · {mode_label}<br>
    Location field auto-filled with Zoom Meeting ID · Generated by outlook_deeplink_generator.py
  </div>

  <!-- Editor Modal -->
  <div class="modal-overlay" id="editorModal" onclick="if(event.target===this)closeEditor()">
    <div class="modal">
      <h2>Edit Email Content</h2>
      <label>Subject</label>
      <input type="text" id="editSubject">
      <label>Email Body (click to edit text directly)</label>
      <div class="body-editor" id="editBody" contenteditable="true"></div>
      <div class="modal-actions">
        <button class="btn-cancel" onclick="discardEdits()" style="background:transparent;color:#ef4444;border:1px solid #ef4444;padding:10px 16px;border-radius:6px;cursor:pointer;font-size:13px">Discard Saved</button>
        <button class="btn-cancel" onclick="closeEditor()">Cancel</button>
        <button class="btn-send" onclick="saveEditedChanges()" style="background:#475569;color:#e2e8f0;border:none;padding:10px 20px;border-radius:6px;cursor:pointer;font-size:14px">Save Changes</button>
        <button class="btn-send" id="modalSendBtn" onclick="sendEdited()">Open in Outlook</button>
      </div>
      <div style="margin-top:10px;text-align:right"><span id="editSaveStatus" style="font-size:12px"></span></div>
    </div>
  </div>

  <script>
    // Event data — all subjects, bodies, and params for inline editing
    const eventData = {json.dumps(event_data_json)};
    const scheduleData = {schedule_json};
    const serverSentData = {sent_json};
    // Quick lookup: is a date already sent from the server's perspective?
    function isDateSent(eventId) {{
      // eventId format: mon_YYYY-MM-DD or fri_YYYY-MM-DD
      const parts = eventId.split('_');
      const date = parts[1];
      const type = parts[0] === 'mon' ? 'monday' : 'grand_rounds';
      return (serverSentData[type] || []).includes(date);
    }}

    // Schedule editor — populate table on page load
    function initScheduleEditor() {{
      const tbody = document.getElementById('scheduleBody');
      let html = '';
      scheduleData.forEach((row, i) => {{
        const dbId = row.db_id || '';
        html += `<tr id="sched-row-${{i}}" style="border-bottom:1px solid #1e293b" data-db-id="${{dbId}}">`;
        html += `<td style="padding:6px"><input type="text" value="${{row.mon_date}}" data-row="${{i}}" data-col="mon_date" data-db-id="${{dbId}}" style="width:90px;background:#0f172a;border:1px solid #334155;color:#e2e8f0;padding:4px 6px;border-radius:4px;font-size:12px"></td>`;
        html += `<td style="padding:6px"><input type="text" value="${{row.mon_topic}}" data-row="${{i}}" data-col="mon_topic" data-db-id="${{dbId}}" style="width:220px;background:#0f172a;border:1px solid #334155;color:#e2e8f0;padding:4px 6px;border-radius:4px;font-size:12px"></td>`;
        html += `<td style="padding:6px"><input type="text" value="${{row.resident}}" data-row="${{i}}" data-col="resident" data-db-id="${{dbId}}" style="width:110px;background:#0f172a;border:1px solid #334155;color:#e2e8f0;padding:4px 6px;border-radius:4px;font-size:12px"></td>`;
        html += `<td style="padding:6px"><input type="text" value="${{row.attending}}" data-row="${{i}}" data-col="attending" data-db-id="${{dbId}}" style="width:130px;background:#0f172a;border:1px solid #334155;color:#e2e8f0;padding:4px 6px;border-radius:4px;font-size:12px"></td>`;
        html += `<td style="padding:6px"><input type="text" value="${{row.fri_date}}" data-row="${{i}}" data-col="fri_date" data-db-id="${{dbId}}" style="width:90px;background:#0f172a;border:1px solid #334155;color:#e2e8f0;padding:4px 6px;border-radius:4px;font-size:12px"></td>`;
        html += `<td style="padding:6px"><input type="text" value="${{row.gr_7_8}}" data-row="${{i}}" data-col="gr_7_8" data-db-id="${{dbId}}" style="width:200px;background:#0f172a;border:1px solid #334155;color:#e2e8f0;padding:4px 6px;border-radius:4px;font-size:12px"></td>`;
        html += `<td style="padding:6px"><input type="text" value="${{row.gr_8_9}}" data-row="${{i}}" data-col="gr_8_9" data-db-id="${{dbId}}" style="width:200px;background:#0f172a;border:1px solid #334155;color:#e2e8f0;padding:4px 6px;border-radius:4px;font-size:12px"></td>`;
        html += '</tr>';
      }});
      tbody.innerHTML = html;
    }}
    initScheduleEditor();

    // Track which cells changed
    const changedRows = new Set();
    document.addEventListener('change', function(e) {{
      if (e.target && e.target.dataset && e.target.dataset.dbId) {{
        const rowIdx = e.target.dataset.row;
        changedRows.add(rowIdx);
        e.target.style.borderColor = '#f59e0b';
      }}
    }});

    async function saveAllChanges() {{
      if (changedRows.size === 0) {{
        document.getElementById('saveStatus').textContent = 'No changes to save.';
        return;
      }}
      const btn = document.getElementById('saveBtn');
      const status = document.getElementById('saveStatus');
      btn.disabled = true;
      btn.textContent = 'Saving...';
      status.textContent = '';
      let saved = 0, errors = 0;

      for (const rowIdx of changedRows) {{
        const inputs = document.querySelectorAll(`input[data-row="${{rowIdx}}"]`);
        const dbId = inputs[0]?.dataset.dbId;
        if (!dbId) {{ errors++; continue; }}

        const payload = {{}};
        inputs.forEach(inp => {{
          payload[inp.dataset.col] = inp.value;
        }});

        try {{
          const resp = await fetch(`/api/conference/schedule/${{dbId}}`, {{
            method: 'PUT',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify(payload),
          }});
          if (resp.ok) {{
            saved++;
            inputs.forEach(inp => inp.style.borderColor = '#334155');
          }} else {{
            errors++;
          }}
        }} catch(err) {{
          errors++;
        }}
      }}

      changedRows.clear();
      btn.disabled = false;
      btn.textContent = 'Save All Changes';
      if (errors === 0) {{
        status.innerHTML = `<span style="color:#34d399">✓ Saved ${{saved}} row(s) to database.</span>`;
      }} else {{
        status.innerHTML = `<span style="color:#ef4444">Saved ${{saved}}, ${{errors}} error(s).</span>`;
      }}
      setTimeout(() => status.textContent = '', 5000);
    }}

    // Editor modal functions
    let currentEditId = null;

    function openEditor(eventId) {{
      const data = eventData[eventId];
      if (!data) return;
      currentEditId = eventId;
      const saved = getSavedEdit(eventId);
      document.getElementById('editSubject').value = saved.subject || data.subject;
      document.getElementById('editBody').innerHTML = saved.body || data.body;
      document.getElementById('editSaveStatus').textContent = saved ? 'Loaded saved edits' : '';
      document.getElementById('editorModal').classList.add('open');
    }}

    function getSavedEdit(eventId) {{
      try {{
        const data = localStorage.getItem('edit_' + eventId);
        return data ? JSON.parse(data) : null;
      }} catch(e) {{ return null; }}
    }}

    function saveEditedChanges() {{
      if (!currentEditId) return;
      const subject = document.getElementById('editSubject').value;
      const body = document.getElementById('editBody').innerHTML;
      localStorage.setItem('edit_' + currentEditId, JSON.stringify({{subject: subject, body: body}}));
      const status = document.getElementById('editSaveStatus');
      status.innerHTML = '<span style="color:#34d399">✓ Saved</span>';
      setTimeout(() => status.textContent = '', 3000);
      // Add saved badge to row
      const badge = document.getElementById('saved-badge-' + currentEditId);
      if (badge) badge.innerHTML = '<span class="edit-badge">Edited</span>';
    }}

    function discardEdits() {{
      if (!currentEditId) return;
      localStorage.removeItem('edit_' + currentEditId);
      // Reload original data
      const data = eventData[currentEditId];
      document.getElementById('editSubject').value = data.subject;
      document.getElementById('editBody').innerHTML = data.body;
      const status = document.getElementById('editSaveStatus');
      status.innerHTML = '<span style="color:#94a3b8">Discarded saved edits</span>';
      setTimeout(() => status.textContent = '', 3000);
      const badge = document.getElementById('saved-badge-' + currentEditId);
      if (badge) badge.innerHTML = '';
    }}

    function closeEditor() {{
      document.getElementById('editorModal').classList.remove('open');
      currentEditId = null;
    }}

    function sendEdited() {{
      if (!currentEditId) return;
      const data = eventData[currentEditId];
      let subject = document.getElementById('editSubject').value;
      const body = document.getElementById('editBody').innerHTML;
      // Check UPDATE toggle
      if (document.getElementById('updateToggle').checked) {{
        subject = '**UPDATE** ' + subject;
      }}
      // Build deeplink URL
      const params = new URLSearchParams();
      params.set('subject', subject);
      params.set('body', body);
      params.set('bodyType', 'HTML');
      params.set('to', data.to);
      params.set('startdt', data.startdt);
      params.set('enddt', data.enddt);
      params.set('location', data.location);
      const url = 'https://outlook.office.com/calendar/deeplink/compose?' + params.toString();
      window.open(url, '_blank');
      markSent(currentEditId);
      closeEditor();
    }}

    // Tab switching
    function switchTab(tabName) {{
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      event.target.closest('.tab').classList.add('active');
      document.getElementById('tab-' + tabName).classList.add('active');
    }}

    // UPDATE toggle — swaps all button URLs between normal and update
    const toggle = document.getElementById('updateToggle');
    toggle.addEventListener('change', function() {{
      document.querySelectorAll('.invite-btn').forEach(btn => {{
        const newUrl = this.checked ? btn.dataset.updateUrl : btn.dataset.normalUrl;
        btn.href = newUrl;
      }});
    }});

    // Sent tracking — marks events as sent. Server-side sent dates from progress files are the primary source.
    // localStorage overrides are a secondary fallback for client-side clicks.
    function getSentKey(eventId) {{ return 'montefiore_sent_' + eventId; }}

    function isSent(eventId) {{
      // First check: server-side progress files
      if (isDateSent(eventId)) return true;
      // Second check: localStorage override (user clicked since page load)
      return localStorage.getItem(getSentKey(eventId)) === 'true';
    }}

    function markSent(eventId) {{
      localStorage.setItem(getSentKey(eventId), 'true');
      updateRowSent(eventId);
    }}

    function updateRowSent(eventId) {{
      const row = document.getElementById('row-' + eventId);
      const status = document.getElementById('status-' + eventId);
      if (isSent(eventId)) {{
        row.classList.add('row-sent');
        status.innerHTML = '<span class="sent-badge">Sent</span>';
      }}
    }}

    // Attach click handlers to all buttons
    document.querySelectorAll('.invite-btn').forEach(btn => {{
      const eventId = btn.dataset.eventId;
      btn.addEventListener('click', function(e) {{
        markSent(eventId);
      }});
    }});

    // On page load — restore sent status and edit badges from localStorage
    document.querySelectorAll('.invite-btn').forEach(btn => {{
      updateRowSent(btn.dataset.eventId);
      const eid = btn.dataset.eventId;
      if (getSavedEdit(eid)) {{
        const badge = document.getElementById('saved-badge-' + eid);
        if (badge) badge.innerHTML = '<span class=\"edit-badge\">Edited</span>';
      }}
    }});

    // Reset all sent status
    function resetSent() {{
      if (!confirm('Reset all sent status? This will mark all events as not sent.')) return;
      document.querySelectorAll('.invite-btn').forEach(btn => {{
        const eventId = btn.dataset.eventId;
        localStorage.removeItem(getSentKey(eventId));
        const row = document.getElementById('row-' + eventId);
        const status = document.getElementById('status-' + eventId);
        row.classList.remove('row-sent');
        status.innerHTML = '';
      }});
    }}
  </script>
</body>
</html>'''

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / "invites.html"
    with open(output_file, "w") as f:
        f.write(html)
    print(f"\n  Monday events: {len(monday_rows)}")
    print(f"  Friday events: {len(friday_rows)}")
    print(f"  Total: {total} event buttons → {output_file}")
    return output_file


# ══════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Outlook Calendar Deeplink Generator")
    parser.add_argument("--type", choices=["monday", "grand-rounds", "all"], default="all")
    parser.add_argument("--start-date", type=str, default="", help="Start from this date (YYYY-MM-DD)")
    parser.add_argument("--test-email", type=str, default=TEST_EMAIL)
    parser.add_argument("--no-test", action="store_true", help="Use real recipient lists")
    args = parser.parse_args()

    test_mode = not args.no_test
    start_date = args.start_date or None

    monday_events = []
    gr_events = []

    if args.type in ("all", "monday"):
        monday_events = get_monday_events(start_date)
        print(f"  Monday SASP events: {len(monday_events)}")

    if args.type in ("all", "grand-rounds"):
        gr_events = get_grand_rounds_events(start_date)
        print(f"  Grand Rounds events: {len(gr_events)}")

    if not monday_events and not gr_events:
        print("  No events found.")
        return

    output_file = generate_html_page(monday_events, gr_events, test_mode, args.test_email)
    print(f"\n  ✅ Done! Open this file in a browser:")
    print(f"     {output_file}")
    print(f"\n  Each button opens Outlook with pre-filled details — just click Send.")


if __name__ == "__main__":
    main()
