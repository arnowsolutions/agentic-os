#!/usr/bin/env python3
"""Sub-I Exit Interview invites — DB-backed Outlook deeplink generator.

EXACT same pattern as outlook_deeplink_generator.py (Grand Rounds / Monday
SASP) —  quote_via=urllib.parse.quote encoding, bodyType=HTML, anchor links.
The body format mirrors build_grand_rounds_body precisely.

Usage:
  python3 subi_exit_invites_generator.py              # write static HTML (test)
  python3 subi_exit_invites_generator.py --no-test    # live mode
"""

import json
import os
import sys
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "data" / "subi_exit_deeplinks"
PROGRESS_FILE = BASE_DIR / "data" / "subi_exit_progress.json"
CV_DIR = BASE_DIR / "data" / "subi-cvs"

TEST_EMAIL = "sfrasier@montefiore.org"

# ── Fixed Sub-I Exit Interview Zoom template (does NOT change per row) ──────
ZOOM_JOIN_URL = "https://us02web.zoom.us/j/5172907646?pwd=SVRqbElnTHRUNGxLL3B3bVZFVFYzUT09&omn=81977282270"
ZOOM_MEETING_ID = "517 290 7646"
ZOOM_PASSCODE = "197277"
CC_EMAIL = "mschoenb@montefiore.org"  # Dr. Schoenberg attends every Sub-I Exit Interview
DEFAULT_DURATION_MINUTES = 10


# ── DB connection (identical to server.py _get_db_conn) ─────────────────────
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


def get_interviews():
    conn = _get_db_conn()
    if not conn:
        return []
    try:
        cur = conn.cursor()
        cur.execute('''
            SELECT id, interviewee, recipient_email, interview_date::text, interview_time,
                   duration_minutes, notes, created_at::text
            FROM subi_exit_interviews ORDER BY interview_date, interview_time
        ''')
        rows = []
        for r in cur.fetchall():
            rows.append({
                "id": r[0], "interviewee": r[1] or "", "recipient_email": r[2] or "",
                "date": r[3] or "", "time": r[4] or "12:00 PM",
                "duration_minutes": r[5] if r[5] else DEFAULT_DURATION_MINUTES,
                "notes": r[6] or "", "created_at": r[7] or "",
            })
        cur.close()
        conn.close()
        return rows
    except Exception:
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


def format_date(datestr):
    try:
        return datetime.strptime(datestr, "%Y-%m-%d").strftime("%b %d, %Y")
    except Exception:
        return datestr or ""


def format_12h(hhmm):
    h, m = map(int, hhmm.split(":"))
    ampm = "AM" if h < 12 else "PM"
    h12 = h % 12 or 12
    return f"{h12}:{m:02d} {ampm}"


# ── Subject & body builders (mirroring build_monday_body / build_grand_rounds_body) ──
def build_subject(iv, update=False):
    name = (iv.get("interviewee") or "").strip()
    base = f"Sub-I Exit Interview: {name}" if name else "Sub-I Exit Interview"
    subject = f"Invitation: {base}"
    if update:
        subject = f"**UPDATE** {subject}"
    return subject


def build_body(iv):
    """Build the Sub-I Exit Interview body — EXACT Grand Rounds format.

    Mirrors build_grand_rounds_body(): bold title, <hr> separators, two-column
    detail table, uppercase section headers, gray-highlighted Meeting ID/Passcode,
    phone dial-in bullets, italic instruction, Montefiore footer.
    """
    datestr = iv.get("date", "")
    try:
        d = datetime.strptime(datestr, "%Y-%m-%d")
        formatted = d.strftime("%A, %B %d, %Y")
    except Exception:
        formatted = datestr or "TBD"
    name = (iv.get("interviewee") or "").strip()
    timestr = iv.get("time", "12:00 PM")
    dur = int(iv.get("duration_minutes") or DEFAULT_DURATION_MINUTES)
    start_24 = parse_time_24h(timestr) or "12:00"
    end_24 = (datetime.strptime(start_24, "%H:%M") + timedelta(minutes=dur)).strftime("%H:%M")
    time_range = f"{timestr} - {format_12h(end_24)} (Eastern)"

    def esc(s):
        return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    return (
        f"<strong>Montefiore Urology - Sub-I Exit Interview</strong>"
        f"<hr>"
        f"<table cellpadding='4' style='border-collapse:collapse;'>"
        f"<tr><td><strong>Date</strong></td><td>{esc(formatted)}</td></tr>"
        f"<tr><td><strong>Time</strong></td><td>{esc(time_range)}</td></tr>"
        f"<tr><td><strong>Location</strong></td><td><a href='{esc(ZOOM_JOIN_URL)}'>Zoom Meeting</a></td></tr>"
        f"<tr><td><strong>Interviewee</strong></td><td>{esc(name) if name else 'TBD'}</td></tr>"
        f"</table>"
        f"<hr>"
        f"<strong>ZOOM MEETING DETAILS</strong>"
        f"<table cellpadding='4' style='border-collapse:collapse;'>"
        f"<tr><td><strong>Join</strong></td><td><a href='{esc(ZOOM_JOIN_URL)}'>Click here to join Zoom</a></td></tr>"
        f"<tr><td><strong>Meeting ID</strong></td><td style='background:#f0f0f0; padding:4px 10px; font-size:15px;'><strong>{esc(ZOOM_MEETING_ID)}</strong></td></tr>"
        f"<tr><td><strong>Passcode</strong></td><td style='background:#f0f0f0; padding:4px 10px; font-size:15px;'><strong>{esc(ZOOM_PASSCODE)}</strong></td></tr>"
        f"</table>"
        f"<hr>"
        f"<strong>PHONE DIAL-IN</strong>"
        f"<table cellpadding='4' style='border-collapse:collapse;'>"
        f"<tr><td valign='top'>&bull;</td><td>+1 646-931-3860 (New York)</td></tr>"
        f"<tr><td valign='top'>&bull;</td><td>+1 929-205-6099 (New York)</td></tr>"
        f"</table>"
        f"<em>Enter Meeting ID, then Passcode when prompted.</em>"
        f"<hr>"
        f"<strong>Montefiore Medical Center &nbsp;|&nbsp; Department of Urology</strong><br>"
        f"1250 Waters Place, Tower One, PH-2, Bronx, NY 10461"
    )


# ── Deeplink builder (IDENTICAL to outlook_deeplink_generator.py) ───────────
def build_deeplink(subject, body, to_param, start_dt, end_dt, location="Zoom"):
    # EXACT match: quote_via=urllib.parse.quote — same as the working GR generator
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


# ── Event building ──────────────────────────────────────────────────────────
def build_event_data(test_mode=True):
    interviews = get_interviews()
    rows = []
    event_data = {}
    for iv in interviews:
        datestr = iv.get("date", "")
        timestr = iv.get("time", "12:00 PM")
        dur = int(iv.get("duration_minutes") or DEFAULT_DURATION_MINUTES)

        to_param = TEST_EMAIL if test_mode else ", ".join(
            filter(None, [iv.get("recipient_email", "").strip(), CC_EMAIL]))
        subject = build_subject(iv)
        update_subject = build_subject(iv, update=True)
        body = build_body(iv)

        has_date = bool(datestr)

        start_24 = parse_time_24h(timestr) or "12:00"
        start_dt = f"{datestr}T{start_24}:00"
        end_24 = (datetime.strptime(start_24, "%H:%M") + timedelta(minutes=dur)).strftime("%H:%M")
        end_dt = f"{datestr}T{end_24}:00"
        location = ZOOM_JOIN_URL

        url = build_deeplink(subject, body, to_param, start_dt, end_dt, location) if has_date else ""
        update_url = build_deeplink(update_subject, body, to_param, start_dt, end_dt, location) if has_date else ""

        eid = f"subi_{iv['id']}"
        rows.append({
            "id": iv["id"], "event_id": eid, "date": datestr, "time": timestr,
            "interviewee": iv.get("interviewee") or "TBD",
            "recipient_email": iv.get("recipient_email", ""),
            "duration_minutes": dur, "notes": iv.get("notes", ""),
            "url": url, "update_url": update_url,
        })
        event_data[eid] = {
            "subject": subject, "body": body, "to": to_param,
            "startdt": start_dt, "enddt": end_dt, "location": location,
            "id": iv["id"],
        }
    rows.sort(key=lambda r: (r["date"], r["time"]))
    return rows, event_data


# ── HTML page generator (mirrors generate_html_page) ────────────────────────
def generate_html_page(test_mode=True):
    rows, event_data = build_event_data(test_mode=test_mode)
    event_data_json = json.dumps(event_data)
    test_html = (f'<span class="test"><strong>TEST MODE</strong> — all invites go to {TEST_EMAIL} only</span>'
                 if test_mode else '<strong>LIVE MODE</strong> — invites go to each row\'s recipient + Dr. Schoenberg')

    rows_html = ""
    for r in rows:
        date_display = format_date(r["date"]) if r["date"] else "TBD"
        date_dow = ""
        try:
            date_dow = datetime.strptime(r["date"], "%Y-%m-%d").strftime("%a")
        except Exception:
            pass
        has_date = bool(r["date"])
        outlook_btn = f'<a href="{r["url"]}" target="_blank" data-event-id="{r["event_id"]}" data-normal-url="{r["url"]}" data-update-url="{r["update_url"]}" class="invite-btn" style="display:inline-block;background:#1a3a5c;color:#fff;padding:6px 14px;border-radius:6px;text-decoration:none;font-size:12px;font-weight:600">Open in Outlook</a>'
        # Check if CV exists for this student
        has_cv = os.path.exists(CV_DIR / f"Yang_Matthew_CV.docx") if r["id"] in (3,) else \
                 os.path.exists(CV_DIR / "OLIVER_MENKEN_CV_07_26.pdf") if r["id"] in (4,) else False
        eml_label = "⬇ .eml (CV)" if has_cv else "⬇ .eml"
        eml_link = f'<a href="/api/subi-exit/eml?id={r["id"]}" style="display:inline-block;color:#94a3b8;font-size:11px;margin-left:8px;text-decoration:none;border:1px solid #475569;padding:3px 10px;border-radius:4px" title="Download .eml file — double-click in Outlook to open with CV attached">{eml_label}</a>' if has_date else ''
        action_cell = f'{outlook_btn}{eml_link}' if has_date else '<span style="color:#64748b;font-size:12px">TBD — date not set</span>'
        time_display = r["time"] if r["time"] != "TBD" else "TBD"
        # Show rotation dates as subtitle under interviewee name (from notes)
        rot_dates = ""
        notes = r.get("notes", "")
        import re as _re
        rot_match = _re.search(r"(\d{1,2}/\d{1,2}/?\d{2,4})\s*[-–]\s*(\d{1,2}/\d{1,2}/?\d{2,4})", notes)
        if rot_match:
            rot_dates = f'<br><span style="color:#64748b;font-size:11px">{rot_match.group(1)} – {rot_match.group(2)}</span>'
        to_display = ", ".join([r["recipient_email"], CC_EMAIL]) if r["recipient_email"] else CC_EMAIL
        rows_html += f'''<tr id="row-{r['event_id']}" style="border-bottom:1px solid #1e293b">
  <td style="padding:10px 14px;white-space:nowrap;font-size:13px"><strong>{date_display}</strong><br><span style="color:#64748b;font-size:11px">{date_dow}</span></td>
  <td style="padding:10px 14px;white-space:nowrap;font-size:13px"><strong>{time_display}</strong></td>
  <td style="padding:10px 14px;font-size:13px;max-width:280px;overflow:hidden;text-overflow:ellipsis"><strong>{r['interviewee']}</strong>{rot_dates}</td>
  <td style="padding:10px 14px;font-size:12px;color:#94a3b8;max-width:260px;overflow:hidden;text-overflow:ellipsis">{to_display}</td>
  <td style="padding:10px 14px;white-space:nowrap">
    {action_cell}
  </td>
</tr>
'''

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Montefiore Urology - Sub-I Exit Interviews</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box }}
  body {{ background:#0f172a; color:#e2e8f0; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif; padding:20px; max-width:1000px; margin:0 auto }}
  h1 {{ font-size:22px; margin-bottom:4px }}
  .subtitle {{ color:#94a3b8; font-size:14px; margin-bottom:20px }}
  .info {{ background:#1e293b; border:1px solid #334155; border-radius:8px; padding:14px 18px; margin-bottom:20px; font-size:13px; line-height:1.6 }}
  .info strong {{ color:#fbbf24 }}
  .info .test {{ color:#ef4444 }}
  .toggle-bar {{ display:flex; align-items:center; gap:16px; background:#1e293b; border:1px solid #334155; border-radius:8px; padding:12px 18px; margin-bottom:20px; font-size:13px }}
  .toggle-bar label {{ font-weight:600; color:#e2e8f0 }}
  .switch {{ position:relative; display:inline-block; width:44px; height:24px }}
  .switch input {{ opacity:0; width:0; height:0 }}
  .slider {{ position:absolute; cursor:pointer; top:0; left:0; right:0; bottom:0; background:#334155; border-radius:24px; transition:0.2s }}
  .slider:before {{ content:''; position:absolute; height:18px; width:18px; left:3px; bottom:3px; background:#94a3b8; border-radius:50%; transition:0.2s }}
  input:checked + .slider {{ background:#f59e0b }}
  input:checked + .slider:before {{ transform:translateX(20px); background:#fff }}
  .toggle-bar .hint {{ color:#64748b; font-size:12px }}
  .sent-badge {{ display:inline-flex; align-items:center; gap:4px; background:#064e3b; color:#34d399; padding:3px 10px; border-radius:999px; font-size:11px; font-weight:600 }}
  .sent-badge:before {{ content:'\\2713' }}
  .row-sent {{ opacity:0.5 }}
  .row-sent .invite-btn {{ background:#334155 !important; cursor:default }}
  .sent-badge /* sent tracking */ .invite-btn /*primary*/ .row-sent /*dim*/ .footer {{ }} .edit-badge {{ }}
  a:hover {{ opacity:0.85 }}
  .count {{ color:#94a3b8; font-size:13px; margin:14px 0 }}
  table {{ width:100%; border-collapse:collapse; font-size:13px }}
  th {{ text-align:left; padding:8px 14px; color:#64748b; font-size:11px; text-transform:uppercase; letter-spacing:0.5px; border-bottom:2px solid #334155 }}
  .footer {{ margin-top:24px; padding-top:16px; border-top:1px solid #334155; font-size:12px; color:#64748b; line-height:1.5 }}
</style>
</head>
<body>
  <h1>Sub-I Exit Interviews</h1>
  <p class="subtitle">Click any button to open a pre-filled Outlook compose form — then click Send</p>

  <div class="info">
    <strong>How it works:</strong> Each button opens Outlook Web with everything pre-filled
    (subject, formatted Zoom invite body, date/time, location, recipients).<br>
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
  </div>

  <div class="count">{len(rows)} interviews · Zoom Meeting ID {ZOOM_MEETING_ID} · {TEST_EMAIL if test_mode else 'live recipients + Dr. Schoenberg'}</div>
  <table>
    <thead><tr>
      <th style="width:110px">Date</th>
      <th style="width:90px">Time</th>
      <th>Interviewee</th>
      <th style="width:260px">To</th>
      <th style="width:140px">Action</th>
    </tr></thead>
    <tbody>
{rows_html}    </tbody>
  </table>

  <div class="footer">
    {len(rows)} total interviews · Location field auto-filled with Zoom Meeting ID · Generated by subi_exit_invites_generator.py
  </div>

  <script>
    const eventData = {event_data_json};
    // UPDATE toggle — switch href between normal and update URLs
    document.querySelectorAll('a[data-event-id]').forEach(a => {{
      a.addEventListener('click', function() {{
        const upd = document.getElementById('updateToggle').checked;
        if (upd) this.href = this.dataset.updateUrl;
        const eid = this.dataset.eventId;
        document.getElementById('status-' + eid).innerHTML = '<span class="sent-badge">Sent</span>';
        document.getElementById('row-' + eid).classList.add('row-sent');
      }});
    }});
  </script>
</body>
</html>'''
    return html


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate Sub-I Exit Interview deeplink page")
    parser.add_argument("--no-test", action="store_true", help="Live mode (real recipient emails)")
    parser.add_argument("--output", type=str, default="", help="Write HTML to file (default: stdout)")
    args = parser.parse_args()

    html = generate_html_page(test_mode=not args.no_test)
    if args.output:
        p = Path(args.output)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(html)
        print(f"Written: {p} ({len(html)} bytes)")
    else:
        print(html)


if __name__ == "__main__":
    main()
