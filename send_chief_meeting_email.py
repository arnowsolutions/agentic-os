#!/usr/bin/env python3
"""Generate Chief Residents' Meeting .eml files for Outlook.

Produces pre-filled .eml files so Shareef can double-click each one
in Outlook, review, and hit Send. Also supports SMTP send mode for
when we go live.

Usage:
  # Generate .eml files for all meetings → data/chief_meeting_eml/
  python3 send_chief_meeting_email.py

  # Generate for a single date
  python3 send_chief_meeting_email.py --date 2026-09-04

  # SMTP send mode (go-live only — requires env vars)
  python3 send_chief_meeting_email.py --send
  python3 send_chief_meeting_email.py --date 2026-09-04 --send
"""

import json
import os
import sys
from datetime import datetime
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calendar_mailer import _build_ics, _build_mime_message, _html_wrap

# ── Config ────────────────────────────────────────────────
PROGRESS_FILE = "/workspace/agentic-os/data/chief_meeting_progress.json"
EML_DIR = "/workspace/agentic-os/data/chief_meeting_eml/"

TEST_MODE = True
TEST_EMAIL = "sfrasier@montefiore.org"
FROM_EMAIL = "urologyresidencyprogram@gmail.com"
FROM_NAME = "Shareef Frasier"

PROD_RECIPIENTS = [
    "sfrasier@montefiore.org",   # Admin
    "asankin@montefiore.org",    # Dr. Sankin
    "alesmall@montefiore.org",   # Dr. Small
    "mschoenb@montefiore.org",   # Dr. Schoenberg
    # Chief Residents:
    "johill@montefiore.org",     # John Hill
    "johordines@montefiore.org", # John Hordines
    "sopak@montefiore.org",      # So Yeon (Jen) Pak
]

# ── Meeting Dates ─────────────────────────────────────────
CHIEF_MEETINGS = [
    {"date": "2026-09-04", "label": "Kick Off"},
    {"date": "2026-10-16", "label": ""},
    {"date": "2026-12-04", "label": ""},
    {"date": "2027-01-14", "label": ""},
    {"date": "2027-02-26", "label": ""},
    {"date": "2027-04-09", "label": ""},
    {"date": "2027-06-04", "label": ""},
]


def build_summary(meeting):
    """Build summary string for the meeting."""
    base = "Chief Residents' Meeting"
    if meeting.get("label"):
        return f"{base} \u2014 {meeting['label']}"
    dt = datetime.strptime(meeting["date"], "%Y-%m-%d")
    return f"{base} \u2014 {dt.strftime('%b %d, %Y')}"


def build_html_body(meeting):
    """Build the premium HTML email body for a Chief Meeting invite."""
    date_str = meeting["date"]
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    day_name = dt.strftime("%A")
    formatted = dt.strftime("%B %d, %Y")

    summary = build_summary(meeting)

    inner = f"""
<table width="100%" cellpadding="0" cellspacing="0" style="font-family:'Segoe UI',Arial,sans-serif;color:#333;max-width:600px;margin:0 auto">
  <tr>
    <td style="background:#1a3a5c;padding:20px 24px;text-align:center;border-radius:8px 8px 0 0">
      <h1 style="color:#ffffff;margin:0;font-size:22px;font-weight:600;letter-spacing:0.5px">CHIEF RESIDENTS' MEETING</h1>
    </td>
  </tr>
  <tr>
    <td style="background:#ffffff;padding:24px;border-left:1px solid #e5e7eb;border-right:1px solid #e5e7eb">

      <table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;margin-bottom:16px">
        <tr>
          <td style="padding:16px 20px">
            <table cellpadding="0" cellspacing="0" width="100%">
              <tr>
                <td style="font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:0.5px;padding-bottom:4px">Date</td>
              </tr>
              <tr>
                <td style="font-size:15px;color:#111827;font-weight:600;padding-bottom:10px">{day_name}, {formatted}</td>
              </tr>
              <tr>
                <td style="font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:0.5px;padding-bottom:4px">Time</td>
              </tr>
              <tr>
                <td style="font-size:15px;color:#111827;font-weight:600;padding-bottom:10px">12:00 PM \u2013 1:00 PM (ET)</td>
              </tr>
              <tr>
                <td style="font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:0.5px;padding-bottom:4px">Location</td>
              </tr>
              <tr>
                <td style="font-size:15px;color:#111827;font-weight:600">Penthouse</td>
              </tr>
            </table>
          </td>
        </tr>
      </table>

      <table width="100%" cellpadding="0" cellspacing="0" style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;margin-bottom:16px">
        <tr>
          <td style="padding:14px 20px;text-align:center">
            <p style="margin:0;font-size:12px;color:#166534;font-weight:600">Attendees</p>
            <p style="margin:6px 0 0 0;font-size:13px;color:#111827">Dr. Schoenberg, Dr. Sankin, Dr. Small, Chief Residents</p>
          </td>
        </tr>
      </table>

      <table width="100%" cellpadding="0" cellspacing="0" style="background:#fefce8;border:1px solid #fde68a;border-radius:8px">
        <tr>
          <td style="padding:12px 16px;text-align:center">
            <p style="margin:0;font-size:11px;color:#92400e">
              <strong>Note:</strong> This calendar invite will be added to your Outlook calendar automatically.
              You can Accept, Tentative, or Decline below.
            </p>
          </td>
        </tr>
      </table>

    </td>
  </tr>
</table>"""

    return _html_wrap(summary, inner)


def build_eml(meeting, to_email):
    """Build a .eml file for a single Chief Meeting invite."""
    date_str = meeting["date"]
    summary = build_summary(meeting)
    description = "Chief Residents' Meeting with Dr. Schoenberg, Dr. Sankin, Dr. Small"
    subject = f"Invitation: {summary}"

    # Build HTML body
    html_body = build_html_body(meeting)

    # Build .ics calendar data
    ics_content = _build_ics(
        summary=summary,
        description=description,
        location="Penthouse",
        date_str=date_str,
        start_time="12:00",
        end_time="13:00",
    )

    # Build full MIME message
    msg = _build_mime_message(to_email, subject, html_body, ics_content)

    # Set From header
    msg.replace_header("From", f"{FROM_NAME} <{FROM_EMAIL}>")

    return msg


def generate_eml_files():
    """Generate .eml files for all meetings into the EML_DIR."""
    os.makedirs(EML_DIR, exist_ok=True)

    to_email = TEST_EMAIL if TEST_MODE else ", ".join(PROD_RECIPIENTS)
    mode_label = "TEST_MODE" if TEST_MODE else "PRODUCTION"
    print(f"Mode: {mode_label}")
    print(f"To: {to_email}")
    print(f"\nGenerating .eml files to {EML_DIR}...")

    generated = []
    for meeting in CHIEF_MEETINGS:
        try:
            msg = build_eml(meeting, to_email)
            date_str = meeting["date"]
            label = f"_{meeting['label'].replace(' ','_')}" if meeting.get("label") else ""
            filename = f"chief_meeting_{date_str}{label}.eml"
            filepath = os.path.join(EML_DIR, filename)

            with open(filepath, "wb") as f:
                f.write(msg.as_bytes())

            generated.append((date_str, filepath))
            print(f"  ✓ {date_str} -> {filename}")

        except Exception as e:
            print(f"  ✗ {meeting['date']}: FAILED - {e}")

    print(f"\nDone. {len(generated)} .eml files saved to {EML_DIR}")
    print("\nTo open in Outlook: double-click the .eml file, review, and press Send.")
    return generated


def generate_single_eml(target_date):
    """Generate .eml file for a single date."""
    for meeting in CHIEF_MEETINGS:
        if meeting["date"] == target_date:
            os.makedirs(EML_DIR, exist_ok=True)
            to_email = TEST_EMAIL if TEST_MODE else ", ".join(PROD_RECIPIENTS)
            msg = build_eml(meeting, to_email)
            label = f"_{meeting['label'].replace(' ','_')}" if meeting.get("label") else ""
            filename = f"chief_meeting_{target_date}{label}.eml"
            filepath = os.path.join(EML_DIR, filename)
            with open(filepath, "wb") as f:
                f.write(msg.as_bytes())
            print(f"Saved: {filepath}")
            return filepath
    print(f"No meeting found for {target_date}")
    return None


def send_via_smtp(target_date=None):
    """Send invites via SMTP for all meetings or a specific date.
    Used by cron wrapper when going live.
    """
    meetings = [m for m in CHIEF_MEETINGS if not target_date or m["date"] == target_date]
    if not meetings:
        print(f"No meetings found for date {target_date}" if target_date else "No meetings defined")
        return

    to_email = TEST_EMAIL if TEST_MODE else ", ".join(PROD_RECIPIENTS)
    mode = "TEST_MODE" if TEST_MODE else "PRODUCTION"
    print(f"Mode: {mode}")
    print(f"Sending {len(meetings)} invite(s) to: {to_email}")

    # Re-import with SMTP env
    import importlib
    import calendar_mailer
    importlib.reload(calendar_mailer)

    sent = 0
    for meeting in meetings:
        try:
            msg = build_eml(meeting, to_email)
            ics_content = _build_ics(
                summary=build_summary(meeting),
                description="Chief Residents' Meeting with Dr. Schoenberg, Dr. Sankin, Dr. Small",
                location="Penthouse",
                date_str=meeting["date"],
                start_time="12:00",
                end_time="13:00",
            )
            subject = f"Invitation: {build_summary(meeting)}"
            html_body = build_html_body(meeting)

            mid = calendar_mailer.send_calendar_invite(
                to=to_email,
                subject=subject,
                summary=build_summary(meeting),
                description="Chief Residents' Meeting with Dr. Schoenberg, Dr. Sankin, Dr. Small",
                location="Penthouse",
                date_str=meeting["date"],
                start_time="12:00",
                end_time="13:00",
                duration_minutes=60,
                physical_location="Penthouse",
            )
            print(f"  ✓ {meeting['date']}: {mid}")
            sent += 1

            # Update progress
            progress = load_progress()
            if meeting["date"] not in progress.get("ics_sent_dates", []):
                progress.setdefault("ics_sent_dates", []).append(meeting["date"])
            progress["last_run"] = datetime.now().isoformat()
            save_progress(progress)

        except Exception as e:
            print(f"  ✗ {meeting['date']}: FAILED - {e}")

    print(f"\nSent {sent}/{len(meetings)} invites via SMTP ({mode})")


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Generate Chief Residents' Meeting .eml files or send via SMTP"
    )
    parser.add_argument("--date", type=str, default="",
                        help="Single date to generate/send for (YYYY-MM-DD)")
    parser.add_argument("--send", action="store_true",
                        help="Send via SMTP instead of generating .eml (go-live only)")
    args = parser.parse_args()

    if args.send:
        send_via_smtp(target_date=args.date if args.date else None)

    if args.date:
        generate_single_eml(args.date)
    else:
        generate_eml_files()


if __name__ == "__main__":
    main()
