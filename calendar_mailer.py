#!/usr/bin/env python3
"""
Premium Calendar Mailer — sends .ics calendar invites and HTML reminders
with branded Montefiore Urology email templates.
"""
import smtplib
import os
import sys
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta
from pathlib import Path


# ── Load .env if present ────────────────────────────────────
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

# ── SMTP Config ─────────────────────────────────────────────
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "") or os.environ.get("SMTP_APP_PASSWORD", "")
FROM_EMAIL = os.environ.get("FROM_EMAIL", SMTP_USER)
FROM_NAME = os.environ.get("FROM_NAME", "Montefiore Urology")


def _html_wrap(title: str, body_html: str) -> str:
    """Wrap body content in a premium branded HTML email template."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background-color:#f3f4f6;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif">
<table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f3f4f6;padding:20px">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08)">
<!-- Header -->
<tr><td style="background:#1a3a5c;padding:20px 40px;text-align:center">
<h1 style="margin:0;color:#ffffff;font-size:18px;font-weight:700">Montefiore Urology</h1>
<p style="margin:4px 0 0 0;color:rgba(255,255,255,0.80);font-size:13px">{title}</p>
</td></tr>
<!-- Body -->
<tr><td style="padding:24px 40px">
{body_html}
</td></tr>
<!-- Footer -->
<tr><td style="background:#f9fafb;padding:16px 40px;text-align:center;border-top:1px solid #e5e7eb">
<p style="margin:0;font-size:11px;color:#9ca3af">Montefiore Medical Center · Department of Urology</p>
</td></tr>
</table>
</td></tr>
</table>
</body>
</html>"""


def _build_ics(summary: str, description: str, location: str, date_str: str,
               start_time: str = "07:00", end_time: str = "09:00",
               uid: str = "", attendee_email: str = "") -> str:
    """Build an iCalendar .ics file content string with Eastern timezone.
    
    Includes ORGANIZER and ATTENDEE with RSVP=TRUE so Outlook/Gmail
    show Accept/Decline buttons and request responses from the organizer.
    """
    # Use Eastern timezone (America/New_York) so calendar clients show correct local time
    tzid = "America/New_York"

    # Ensure location is never empty — some email clients drop RSVP buttons
    # when the ICS LOCATION field is blank
    if not location:
        location = "No Meeting — Holiday"

    dt_start = datetime.strptime(f"{date_str} {start_time}", "%Y-%m-%d %H:%M")
    dt_end = datetime.strptime(f"{date_str} {end_time}", "%Y-%m-%d %H:%M")
    if not uid:
        # Sanitize summary for UID: remove em dashes and special chars
        safe = summary[:30].replace("\u2014", "-").replace(" ", "-")
        safe = "".join(c for c in safe if c.isalnum() or c == "-")
        uid = f"{date_str}-{safe}@montefiore-urology"
    dtstamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    dtstart = dt_start.strftime("%Y%m%dT%H%M%S")
    dtend = dt_end.strftime("%Y%m%dT%H%M%S")

    # Organizer line
    org_email = os.environ.get("FROM_EMAIL", "urologyresidencyprogram@gmail.com")
    org_name = os.environ.get("FROM_NAME", "Urology Residency Program")

    # Attendee line with RSVP=TRUE — this is what triggers "request a response"
    attendee_line = ""
    if attendee_email:
        attendee_line = f"\nATTENDEE;CN={attendee_email};ROLE=REQ-PARTICIPANT;RSVP=TRUE:mailto:{attendee_email}"

    return f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Montefiore Urology//Grand Rounds//EN
METHOD:REQUEST
BEGIN:VTIMEZONE
TZID:{tzid}
BEGIN:DAYLIGHT
TZOFFSETFROM:-0500
TZOFFSETTO:-0400
TZNAME:EDT
DTSTART:19700308T020000
RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU
END:DAYLIGHT
BEGIN:STANDARD
TZOFFSETFROM:-0400
TZOFFSETTO:-0500
TZNAME:EST
DTSTART:19701101T020000
RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU
END:STANDARD
END:VTIMEZONE
BEGIN:VEVENT
UID:{uid}
DTSTAMP:{dtstamp}
DTSTART;TZID={tzid}:{dtstart}
DTEND;TZID={tzid}:{dtend}
SUMMARY:{summary}
DESCRIPTION:{description}
LOCATION:{location}
STATUS:CONFIRMED
TRANSP:OPAQUE
ORGANIZER;CN={org_name}:mailto:{org_email}{attendee_line}
END:VEVENT
END:VCALENDAR"""


def _build_mime_message(to: str, subject: str, html_body: str,
                         ics_content: str = "", filename: str = "invite.ics") -> MIMEMultipart:
    """Build a proper MIME message with optional calendar invite.
    
    Uses multipart/alternative so Outlook/Exchange auto-processes the .ics
    and places it on the recipient's calendar without requiring a manual open.
    Structure:
      multipart/alternative
        ├── text/html  (branded email body)
        └── text/calendar; method=REQUEST  (inline .ics for auto-processing)
    """
    if ics_content:
        # Calendar invite — use multipart/alternative so the .ics is treated
        # as an alternative view, not a downloadable attachment. This is what
        # makes Outlook/Gmail auto-add the event to the calendar.
        msg = MIMEMultipart("alternative")
    else:
        msg = MIMEMultipart("mixed")
    
    msg["From"] = f"{FROM_NAME} <{FROM_EMAIL}>"
    msg["To"] = to
    msg["Subject"] = subject
    
    # HTML body (first alternative — clients prefer the last part, so calendar goes second)
    msg.attach(MIMEText(html_body, "html"))
    
    # Calendar invite as inline alternative (method=REQUEST triggers Accept/Reject buttons)
    if ics_content:
        cal_part = MIMEBase("text", "calendar", method="REQUEST", name=filename)
        cal_part.set_payload(ics_content)
        encoders.encode_base64(cal_part)
        # INLINE — not attachment. This is critical for Outlook auto-processing.
        cal_part.add_header("Content-Disposition", f'inline; filename="{filename}"')
        cal_part.add_header("Content-Class", "urn:content-classes:calendarmessage")
        msg.attach(cal_part)
    
    return msg


def _get_tz_abbrev(date_str: str) -> str:
    """Return 'EDT' or 'EST' based on US DST rules for the given date.
    DST: 2nd Sunday in March → 1st Sunday in November."""
    d = datetime.strptime(date_str, "%Y-%m-%d")
    year = d.year
    # 2nd Sunday in March
    mar1 = datetime(year, 3, 1)
    second_sunday = 1 + ((6 - mar1.weekday()) % 7) + 7
    dst_start = datetime(year, 3, second_sunday)
    # 1st Sunday in November
    nov1 = datetime(year, 11, 1)
    first_sunday = 1 + ((6 - nov1.weekday()) % 7)
    dst_end = datetime(year, 11, first_sunday)
    return "EDT" if dst_start <= d < dst_end else "EST"


def send_calendar_invite(to: str, subject: str, summary: str, description: str,
                         location: str, date_str: str, start_time: str = "07:00",
                         end_time: str = "09:00", duration_minutes: int = 120,
                         zoom_link: str = "", meeting_id: str = "",
                         passcode: str = "", session_7_8: str = "",
                         session_8_9: str = "",
                         resident: str = "", attending: str = "",
                         session_7_8_label: str = "", session_8_9_label: str = "",
                         physical_location: str = "") -> str:
    """Send a calendar .ics invite with premium HTML template.
    Returns the message ID on success."""
    
    # Build HTML body
    zoom_section = ""
    if zoom_link:
        zoom_section = f"""
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f0f7ff;border:1px solid #bfdbfe;border-radius:8px;margin-bottom:16px">
<tr><td style="padding:16px 20px;text-align:center">
<p style="margin:0 0 12px 0;font-size:11px;color:#1d4ed8;font-weight:600;text-transform:uppercase;letter-spacing:0.5px">Zoom Meeting</p>
<a href="{zoom_link}" style="display:inline-block;background-color:#1a3a5c;color:#ffffff;font-size:13px;font-weight:600;text-decoration:none;padding:10px 24px;border-radius:6px;margin-bottom:8px">Click Here to Join Zoom Meeting →</a>
<table cellpadding="0" cellspacing="0" style="margin:0 auto">
<tr><td style="font-size:12px;color:#6b7280;padding:2px 8px 2px 0">Meeting ID:</td><td style="font-size:13px;color:#111827;font-weight:600">{meeting_id}</td></tr>
<tr><td style="font-size:12px;color:#6b7280;padding:2px 8px 2px 0">Passcode:</td><td style="font-size:13px;color:#111827;font-weight:600">{passcode}</td></tr>
</table>
</td></tr>
</table>"""

    location_section = ""
    if physical_location:
        location_section = f"""
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;margin-bottom:16px">
<tr><td style="padding:14px 20px;text-align:center">
<p style="margin:0;font-size:11px;color:#15803d;font-weight:600;text-transform:uppercase;letter-spacing:0.5px">In-Person Location</p>
<p style="margin:4px 0 0 0;font-size:14px;color:#111827;font-weight:500">{physical_location}</p>
</td></tr>
</table>"""

    agenda = ""
    if session_7_8 or session_8_9:
        # If only one session provided, duplicate it into both time slots
        if session_7_8 and not session_8_9:
            session_8_9 = session_7_8
            session_8_9_label = session_7_8_label or "Grand Rounds Conference"
        if session_8_9 and not session_7_8:
            session_7_8 = session_8_9
            session_7_8_label = session_7_8_label or "Grand Rounds"

        has_two = bool(session_7_8 and session_8_9)
        agenda = """
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px;margin-bottom:16px">
<tr><td style="padding:12px 16px;font-size:11px;color:#6b7280;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;border-bottom:1px solid #e5e7eb;text-align:center">Agenda</td></tr>"""
        if session_7_8:
            label_7 = session_7_8_label or ""
            if label_7:
                label_html_7 = f"""
  <p style="margin:0;font-size:11px;color:#6b7280;font-weight:600;text-transform:uppercase;letter-spacing:0.5px">{label_7}</p>"""
            else:
                label_html_7 = ""
            agenda += f"""
<tr><td style="padding:14px 20px;{'border-bottom:1px solid #e5e7eb;' if has_two else ''}text-align:center">{label_html_7}
  <p style="margin:{'2px' if label_html_7 else '0'};font-size:12px;color:#9ca3af">7:00 – 8:00 AM</p>
  <p style="margin:6px 0 0 0;font-size:14px;color:#111827;font-weight:500">{session_7_8}</p>
</td></tr>"""
        if session_8_9:
            label_8 = session_8_9_label or ""
            if label_8:
                label_html_8 = f"""
  <p style="margin:0;font-size:11px;color:#6b7280;font-weight:600;text-transform:uppercase;letter-spacing:0.5px">{label_8}</p>"""
            else:
                label_html_8 = ""
            agenda += f"""
<tr><td style="padding:14px 20px;text-align:center">{label_html_8}
  <p style="margin:{'2px' if label_html_8 else '0'};font-size:12px;color:#9ca3af">8:00 – 9:00 AM</p>
  <p style="margin:6px 0 0 0;font-size:14px;color:#111827;font-weight:500">{session_8_9}</p>
</td></tr>"""
        agenda += "</table>"

    # Resident/Attending info (visible in email body)
    people_section = ""
    if resident or attending:
        people_section = """
<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:16px">
<tr><td style="text-align:center">"""
        if resident:
            people_section += f"""<p style="margin:0;font-size:14px;color:#374151"><strong>Resident:</strong> {resident}</p>"""
        if attending:
            people_section += f"""<p style="margin:4px 0 0 0;font-size:14px;color:#374151"><strong>Attending:</strong> {attending}</p>"""
        people_section += """
</td></tr>
</table>"""

    dt = datetime.strptime(date_str, "%Y-%m-%d")
    formatted_date = dt.strftime("%A, %B %d, %Y")

    inner = f"""{zoom_section}{location_section}{agenda}{people_section}
<table width="100%" cellpadding="0" cellspacing="0">
<tr><td style="padding:8px 0;text-align:center">
<p style="margin:0;font-size:14px;color:#374151"><strong>Date:</strong> {formatted_date}</p>
<p style="margin:6px 0 0 0;font-size:14px;color:#374151"><strong>Time:</strong> {start_time} – {end_time} ({_get_tz_abbrev(date_str)})</p>
</td></tr>
</table>"""

    html_body = _html_wrap(summary, inner)
    
    # Build .ics — pass recipient email so ATTENDEE;RSVP=TRUE is included
    ics_content = _build_ics(summary, description, location, date_str, start_time, end_time,
                             attendee_email=to)
    
    # Send
    return _send_mime_message(to, subject, html_body, ics_content,
                              filename=f"{date_str}-invite.ics")


def send_reminder_email(to: str, subject: str, html_body: str) -> str:
    """Send an HTML-only reminder email (no .ics attachment)."""
    return _send_mime_message(to, subject, html_body)


def _send_mime_message(to: str, subject: str, html_body: str,
                       ics_content: str = "", filename: str = "") -> str:
    """Low-level MIME message sender. Returns message ID.
    Uses SMTP if configured; falls back to Gmail API with calendar invite support."""
    
    if not SMTP_USER or not SMTP_PASS:
        # Fall back to Gmail API with proper calendar MIME
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            from modules.google_workspace import GoogleWorkspace
            
            if ics_content:
                # Build full MIME message with calendar invite for Accept/Reject
                msg = _build_mime_message(to, subject, html_body, ics_content, filename or "invite.ics")
                raw_bytes = msg.as_bytes()
                raw_b64 = base64.urlsafe_b64encode(raw_bytes).decode()
                
                gw = GoogleWorkspace()
                creds = gw._get_credentials()
                if creds:
                    from googleapiclient.discovery import build
                    service = build("gmail", "v1", credentials=creds)
                    result = service.users().messages().send(
                        userId="me",
                        body={"raw": raw_b64}
                    ).execute()
                    return result.get("id", "gmail-sent")
            else:
                # No .ics — use simpler send_email path
                gw = GoogleWorkspace()
                if gw._get_credentials():
                    result = gw.send_email(
                        user_id="default",
                        to=to,
                        subject=subject,
                        body=html_body,
                        is_html=True,
                    )
                    if result.get("successful"):
                        return result.get("data", {}).get("id", "gmail-sent")
                    print(f"[GMAIL ERROR] {result.get('error', 'unknown')}")
                    return "gmail-failed"
        except Exception as e:
            print(f"[GMAIL FALLBACK ERROR] {e}")
        
        # Dry-run mode — log instead of send
        print(f"[DRY RUN] Would send to: {to}")
        print(f"[DRY RUN] Subject: {subject}")
        return "dry-run"
    
    # Build MIME message for SMTP
    msg = _build_mime_message(to, subject, html_body, ics_content, filename or "invite.ics")
    
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
    
    return msg.get("Message-ID", "sent")
