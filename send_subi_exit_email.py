#!/usr/bin/env python3
"""Generate Sub-I Exit Interview .eml files for Outlook.

Produces pre-filled .eml files (premium branded HTML + .ics calendar invite)
so Shareef can double-click each one in Outlook, review, and hit Send.
This is the SAME flow as Chief Meetings / Grand Rounds (.eml generation) —
NOT deeplinks, which hit Outlook's URL length limit (AADSTS90015).

Reads interview rows from the subi_exit_interviews table (urology_qgenda DB).
Each email: To = <student>, <Dr. Schoenberg>; subject "Invitation: Sub-I Exit
Interview: <Name>"; rich HTML body matching the Grand Rounds look; .ics with
RSVP so the event lands on the calendar.

Usage:
  python3 send_subi_exit_email.py                       # generate all rows
  python3 send_subi_exit_email.py --date 2026-08-10     # one date
  python3 send_subi_exit_email.py --id 3                # one row id
  python3 send_subi_exit_email.py --send                # SMTP (go-live only)
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calendar_mailer import _build_ics, _build_mime_message, _html_wrap

# ── Config ────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
EML_DIR = BASE_DIR / "data" / "subi_eml"
PROGRESS_FILE = BASE_DIR / "data" / "subi_exit_progress.json"

TEST_MODE = True
TEST_EMAIL = "sfrasier@montefiore.org"
FROM_EMAIL = "urologyresidencyprogram@gmail.com"
FROM_NAME = "Shareef Frasier"

# Dr. Schoenberg attends every Sub-I Exit Interview — added to the To line
CC_ATTENDEE = "mschoenb@montefiore.org"

# Fixed Sub-I Zoom details
ZOOM_JOIN_URL = "https://us02web.zoom.us/j/5172907646?pwd=SVRqbElnTHRUNGxLL3B3bVZFVFYzUT09&omn=81977282270"
ZOOM_MEETING_ID = "517 290 7646"
ZOOM_PASSCODE = "197277"
ZOOM_DIAL_IN = [
    "+1 646-931-3860 (New York)",
    "+1 929-205-6099 (New York)",
]
DEFAULT_DURATION_MINUTES = 10
CV_DIR = BASE_DIR / "data" / "subi-cvs"

# ── CV lookup (maps student email → CV file in data/subi-cvs/) ─────────────
def get_cv_path(recipient_email: str) -> Path | None:
    """Find a CV file for a student based on their email address.
    
    Looks in CV_DIR for files containing the student's name or email.
    Returns Path if found, None otherwise.
    """
    if not recipient_email or not CV_DIR.exists():
        return None
    # Student name snippets derived from email (e.g. may32@case.edu → Yang)
    email_map = {
        "may32@case.edu":                "Yang_Matthew_CV.docx",
        "matthew.yang@hmhn.org":         "Yang_Matthew_CV.docx",
        "olivermenken98@gmail.com":      "OLIVER_MENKEN_CV_07_26.pdf",
        "spanpaliya2@gmail.com":         None,  # CV not yet available
        "yakovklu@buffalo.edu":          None,
        "cabbrian@student.nymc.edu":     None,
        "awang495@gmail.com":            None,
        "juliana.e.viola@gmail.com":     None,
    }
    fname = email_map.get(recipient_email.lower().strip())
    if fname:
        p = CV_DIR / fname
        if p.exists():
            return p
    return None


# ── DB read (same pattern as server.py _get_db_conn) ─────────────────────────
def _get_db_conn():
    import psycopg2
    pw = os.environ.get("POSTGRES_PASSWORD", "")
    if not pw:
        import subprocess as _sp
        r = _sp.run(['grep', 'POSTGRES_PASSWORD', '/workspace/projects/unified/app/.env'],
            capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            pw = r.stdout.strip().split('=', 1)[1].strip()
    for host in ("127.0.0.1", "172.16.3.1"):
        try:
            kwargs = dict(host=host, port=5432, dbname="urology_qgenda", user="postgres", connect_timeout=3)
            if pw:
                kwargs["password"] = pw
            return psycopg2.connect(**kwargs)
        except Exception:
            continue
    return None


def get_interviews(target_date=None, target_id=None):
    """Read interview rows from the DB (all, or filtered by date/id)."""
    conn = _get_db_conn()
    if not conn:
        print("ERROR: no DB connection")
        return []
    try:
        cur = conn.cursor()
        sql = '''SELECT id, interviewee, recipient_email, interview_date::text, interview_time,
                        duration_minutes, notes
                 FROM subi_exit_interviews WHERE 1=1'''
        params = []
        if target_id:
            sql += " AND id = %s"
            params.append(target_id)
        elif target_date:
            sql += " AND interview_date = %s"
            params.append(target_date)
        sql += " ORDER BY interview_date, interview_time"
        cur.execute(sql, params)
        rows = []
        for r in cur.fetchall():
            rows.append({
                "id": r[0], "interviewee": r[1] or "", "recipient_email": r[2] or "",
                "date": r[3] or "", "time": r[4] or "12:00 PM",
                "duration_minutes": r[5] if r[5] else DEFAULT_DURATION_MINUTES,
                "notes": r[6] or "",
            })
        cur.close()
        conn.close()
        return rows
    except Exception as e:
        print(f"DB error: {e}")
        return []


def parse_time_24h(tstr):
    import re
    m = re.match(r"(\d{1,2}):(\d{2})\s*(AM|PM)?", (tstr or "").strip().upper())
    if not m:
        return None
    hour, minute, ampm = int(m.group(1)), int(m.group(2)), m.group(3)
    if ampm == "PM" and hour != 12:
        hour += 12
    elif ampm == "AM" and hour == 12:
        hour = 0
    return f"{hour:02d}:{minute:02d}"


def format_12h(hhmm):
    h, m = map(int, hhmm.split(":"))
    ampm = "AM" if h < 12 else "PM"
    h12 = h % 12 or 12
    return f"{h12}:{m:02d} {ampm}"


# ── Builders ───────────────────────────────────────────────
def build_summary(iv):
    return f"Sub-I Exit Interview: {iv['interviewee']}" if iv.get("interviewee") else "Sub-I Exit Interview"


def build_subject(iv):
    return f"Invitation: {build_summary(iv)}"


def build_html_body(iv):
    """Premium branded HTML body — same look as the Grand Rounds emails."""
    try:
        d = datetime.strptime(iv["date"], "%Y-%m-%d")
        day_name = d.strftime("%A")
        formatted = d.strftime("%B %d, %Y")
    except Exception:
        day_name, formatted = "", iv.get("date", "TBD")
    timestr = iv.get("time", "12:00 PM")
    dur = int(iv.get("duration_minutes") or DEFAULT_DURATION_MINUTES)
    start_24 = parse_time_24h(timestr) or "12:00"
    end_24 = (datetime.strptime(start_24, "%H:%M") + timedelta(minutes=dur)).strftime("%H:%M")
    time_range = f"{timestr} – {format_12h(end_24)} (ET)"
    name = iv.get("interviewee") or "TBD"
    location = f"Zoom Meeting ID {ZOOM_MEETING_ID}"

    dial_rows = "".join(
        f'<tr><td style="font-size:12px;color:#6b7280;padding:2px 8px 2px 0">•</td>'
        f'<td style="font-size:13px;color:#111827">{line}</td></tr>'
        for line in ZOOM_DIAL_IN
    )

    inner = f"""
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f0f7ff;border:1px solid #bfdbfe;border-radius:8px;margin-bottom:16px">
  <tr><td style="padding:16px 20px;text-align:center">
    <p style="margin:0 0 12px 0;font-size:11px;color:#1d4ed8;font-weight:600;text-transform:uppercase;letter-spacing:0.5px">Sub-I Exit Interview</p>
    <a href="{ZOOM_JOIN_URL}" style="display:inline-block;background-color:#1a3a5c;color:#ffffff;font-size:13px;font-weight:600;text-decoration:none;padding:10px 24px;border-radius:6px;margin-bottom:8px">Click Here to Join Zoom Meeting</a>
    <table cellpadding="0" cellspacing="0" style="margin:0 auto">
      <tr><td style="font-size:12px;color:#6b7280;padding:2px 8px 2px 0">Meeting ID:</td><td style="font-size:13px;color:#111827;font-weight:600">{ZOOM_MEETING_ID}</td></tr>
      <tr><td style="font-size:12px;color:#6b7280;padding:2px 8px 2px 0">Passcode:</td><td style="font-size:13px;color:#111827;font-weight:600">{ZOOM_PASSCODE}</td></tr>
    </table>
  </td></tr>
</table>
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px;margin-bottom:16px">
  <tr><td style="padding:12px 16px;font-size:11px;color:#6b7280;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;border-bottom:1px solid #e5e7eb;text-align:center">Interview Details</td></tr>
  <tr><td style="padding:14px 20px;border-bottom:1px solid #e5e7eb;text-align:center">
    <p style="margin:0;font-size:11px;color:#6b7280;font-weight:600;text-transform:uppercase;letter-spacing:0.5px">Interviewee</p>
    <p style="margin:2px 0 0 0;font-size:14px;color:#111827;font-weight:500">{name}</p>
  </td></tr>
  <tr><td style="padding:14px 20px;text-align:center">
    <p style="margin:0;font-size:11px;color:#6b7280;font-weight:600;text-transform:uppercase;letter-spacing:0.5px">Scheduled</p>
    <p style="margin:2px 0 0 0;font-size:12px;color:#9ca3af">{day_name}, {formatted}</p>
    <p style="margin:2px 0 0 0;font-size:13px;color:#111827;font-weight:500">{time_range}</p>
  </td></tr>
</table>
<table width="100%" cellpadding="0" cellspacing="0">
  <tr><td style="padding:8px 0;text-align:center">
    <p style="margin:0;font-size:14px;color:#374151"><strong>Date:</strong> {day_name}, {formatted}</p>
    <p style="margin:6px 0 0 0;font-size:14px;color:#374151"><strong>Time:</strong> {time_range}</p>
    <p style="margin:6px 0 0 0;font-size:14px;color:#374151"><strong>Location:</strong> {location}</p>
  </td></tr>
</table>
<table width="100%" cellpadding="0" cellspacing="0" style="margin-top:16px">
  <tr><td style="padding:12px 16px;font-size:11px;color:#6b7280;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;border-top:1px solid #e5e7eb">Phone Dial-In</td></tr>
  <tr><td style="padding:8px 16px">{dial_rows}
    <p style="margin:8px 0 0 0;font-size:11px;color:#9ca3af;font-style:italic">Enter Meeting ID, then Passcode when prompted.</p>
  </td></tr>
</table>"""

    return _html_wrap("Sub-I Exit Interview", inner)


def build_eml(iv, to_email):
    """Build a .eml for one interview (rich HTML + .ics with RSVP + CV attachment)."""
    date_str = iv["date"]
    summary = build_summary(iv)
    subject = build_subject(iv)
    html_body = build_html_body(iv)
    start_24 = parse_time_24h(iv.get("time", "12:00 PM")) or "12:00"
    dur = int(iv.get("duration_minutes") or DEFAULT_DURATION_MINUTES)
    end_24 = (datetime.strptime(start_24, "%H:%M") + timedelta(minutes=dur)).strftime("%H:%M")
    description = f"Sub-I Exit Interview with {iv.get('interviewee', 'student')}"

    ics_content = _build_ics(
        summary=summary,
        description=description,
        location=ZOOM_JOIN_URL,
        date_str=date_str,
        start_time=start_24,
        end_time=end_24,
        attendee_email=iv.get("recipient_email", ""),
    )

    msg = _build_mime_message(to_email, subject, html_body, ics_content)
    msg.replace_header("From", f"{FROM_NAME} <{FROM_EMAIL}>")

    # Attach CV if available for this student.
    # When CVs are present, wrap the existing multipart/alternative (HTML+.ics)
    # inside a multipart/mixed so the attachment is a peer MIME part.
    cv_path = get_cv_path(iv.get("recipient_email", "").lower().strip())
    if cv_path and cv_path.exists():
        from email.mime.base import MIMEBase
        from email.mime.multipart import MIMEMultipart
        from email import encoders
        # Create multipart/mixed wrapper, move msg into it, then attach CV
        outer = MIMEMultipart("mixed")
        outer["From"] = msg["From"]
        outer["To"] = msg["To"]
        outer["Subject"] = msg["Subject"]
        # Transfer all headers from msg to outer
        for key in list(msg.keys()):
            if key not in ("From", "To", "Subject", "MIME-Version", "Content-Type"):
                outer[key] = msg[key]
        outer.attach(msg)
        # Attach the CV
        with open(cv_path, "rb") as f:
            cv_data = f.read()
        cv_part = MIMEBase("application", "octet-stream")
        cv_part.set_payload(cv_data)
        encoders.encode_base64(cv_part)
        cv_part.add_header("Content-Disposition", f"attachment; filename=\"{cv_path.name}\"")
        outer.attach(cv_part)
        msg = outer
        print(f"    📎 CV attached: {cv_path.name}")

    return msg


# ── Generation ─────────────────────────────────────────────
def generate_eml_files(target_date=None, target_id=None):
    interviews = get_interviews(target_date=target_date, target_id=target_id)
    if not interviews:
        print("No interviews found" + (f" for date {target_date}" if target_date else f" for id {target_id}" if target_id else ""))
        return []

    EML_DIR.mkdir(parents=True, exist_ok=True)
    to_email = TEST_EMAIL if TEST_MODE else None  # resolved per row below
    mode_label = "TEST_MODE" if TEST_MODE else "PRODUCTION"
    print(f"Mode: {mode_label}")
    print(f"Generating .eml files to {EML_DIR}...")

    generated = []
    for iv in interviews:
        try:
            # Live mode: To = student + Dr. Schoenberg. Test mode: test email only.
            if TEST_MODE:
                to_email = TEST_EMAIL
            else:
                recipients = [iv.get("recipient_email", "").strip(), CC_ATTENDEE]
                to_email = ", ".join(r for r in recipients if r)
            msg = build_eml(iv, to_email)
            fname = f"subi_exit_{iv['date']}_{iv['id']:02d}.eml"
            fpath = EML_DIR / fname
            with open(fpath, "wb") as f:
                f.write(msg.as_bytes())
            generated.append((iv["date"], str(fpath), to_email, iv.get("interviewee", "")))
            print(f"  ✓ {iv['date']} [{iv['id']}] {iv.get('interviewee','?')} -> {fname} (To: {to_email})")
        except Exception as e:
            print(f"  ✗ {iv.get('date')} [{iv.get('id')}]: FAILED - {e}")

    # Progress tracking
    try:
        progress = {"generated": [g[0] for g in generated], "last_run": datetime.now().isoformat()}
        PROGRESS_FILE.write_text(json.dumps(progress, indent=2))
    except Exception:
        pass

    print(f"\nDone. {len(generated)} .eml files saved to {EML_DIR}")
    print("Open each .eml in Outlook, review, and press Send.")
    return generated


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate Sub-I Exit Interview .eml files")
    parser.add_argument("--date", type=str, default="", help="Filter by date (YYYY-MM-DD)")
    parser.add_argument("--id", type=int, default=0, help="Filter by row id")
    parser.add_argument("--output-dir", type=str, default="", help="Override output dir")
    args = parser.parse_args()

    global EML_DIR
    if args.output_dir:
        EML_DIR = Path(args.output_dir)

    generate_eml_files(target_date=args.date or None, target_id=args.id or None)


if __name__ == "__main__":
    main()
