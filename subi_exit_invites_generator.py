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


def esc(s):
    """HTML-escape for embedding values in data attributes."""
    return str(s).replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")


def find_cv(interviewee, email):
    """Locate a student's CV in data/subi-cvs/ from name/email tokens.

    Directory-driven on purpose (2026-09-13): the previous version keyed off
    hardcoded student IDs, so a CV added for anyone else never surfaced.
    """
    import re as _re
    if not CV_DIR.exists():
        return None
    tokens = set()
    for tok in _re.split(r"[._\-0-9]+", (email or "").split("@")[0].lower()):
        if len(tok) >= 4:
            tokens.add(tok)
    for part in (interviewee or "").lower().split():
        if len(part) >= 4:
            tokens.add(part)
    for f in sorted(CV_DIR.iterdir()):
        flat = _re.sub(r"[^a-z0-9]", "", f.name.lower())
        if f.is_file() and any(_re.sub(r"[^a-z0-9]", "", t) in flat for t in tokens):
            return f
    return None

# ── Fixed Sub-I Exit Interview Zoom template (does NOT change per row) ──────
ZOOM_JOIN_URL = "https://us02web.zoom.us/j/5172907646?pwd=SVRqbElnTHRUNGxLL3B3bVZFVFYzUT09&omn=81977282270"
ZOOM_MEETING_ID = "517 290 7646"
ZOOM_PASSCODE = "197277"
CC_EMAIL = "mschoenb@montefiore.org"  # Dr. Schoenberg attends every Sub-I Exit Interview
DEFAULT_DURATION_MINUTES = 10


# ── DB connection (identical to server.py _get_db_conn) ─────────────────────
def _get_db_conn():
    """psycopg2 connection to the CANONICAL store: postgres DB, unified schema.

    2026-09-13: urology_qgenda no longer exists (renamed urology_roster) and the
    Sub-I interviews now live in unified.subi_exit_interviews — the same store
    server.py's API reads. A retired dbname connects as None and yields an empty
    list, which silently blanked the mass-email page; never point this back at a
    DB name that is not in pg_database.
    """
    import psycopg2
    pw = os.environ.get("POSTGRES_PASSWORD", "")
    if not pw:
        for env_path in ("/workspace/agentic-os/.env",
                         "/workspace/projects/unified/app/.env"):
            try:
                if os.path.exists(env_path):
                    with open(env_path) as ef:
                        for line in ef:
                            if line.strip().startswith("POSTGRES_PASSWORD="):
                                pw = line.strip().split("=", 1)[1].strip()
                                break
            except Exception:
                continue
            if pw:
                break
    for host in ("172.16.3.1", "127.0.0.1"):
        try:
            kwargs = dict(host=host, port=5432, dbname="postgres", user="postgres", connect_timeout=3)
            if pw:
                kwargs["password"] = pw
            return psycopg2.connect(**kwargs)
        except Exception:
            continue
    return None


def get_interviews():
    conn = _get_db_conn()
    if not conn:
        print("WARNING: no DB connection — cannot read unified.subi_exit_interviews",
              file=sys.stderr)
        return []
    try:
        cur = conn.cursor()
        cur.execute('''
            SELECT id, interviewee, recipient_email, interview_date::text, interview_time,
                   duration_minutes, notes, created_at::text, sent_status
            FROM unified.subi_exit_interviews ORDER BY interview_date, interview_time
        ''')
        rows = []
        for r in cur.fetchall():
            rows.append({
                "id": r[0], "interviewee": r[1] or "", "recipient_email": r[2] or "",
                "date": r[3] or "", "time": r[4] or "12:00 PM",
                "duration_minutes": r[5] if r[5] else DEFAULT_DURATION_MINUTES,
                "notes": r[6] or "", "created_at": r[7] or "",
                "sent_status": r[8] if r[8] is not None else False,
            })
        cur.close()
        conn.close()
        return rows
    except Exception as e:
        print(f"WARNING: subi exit interview read failed: {e}", file=sys.stderr)
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





# ── Schoenberg scheduling request (DB-driven, NEVER hardcoded student names) ──
def parse_rotation_end(notes):
    """Extract the rotation END date (2nd m/d/yy in notes) -> datetime or None."""
    import re as _re
    m = _re.search(r"(\d{1,2})/(\d{1,2})/(\d{2,4})\s*[-\u2013]\s*(\d{1,2})/(\d{1,2})/(\d{2,4})", notes or "")
    if not m:
        return None
    try:
        y = int(m.group(6))
        y = 2000 + y if y < 100 else y
        return datetime(y, int(m.group(4)), int(m.group(5)))
    except Exception:
        return None


def _ordinal(n):
    if 10 <= n % 100 <= 20:
        suf = "th"
    else:
        suf = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


def _pick_next_cohort(rows, window_days=35):
    """Students still needing interviews whose rotation end is soonest (>= today,
    within window_days), so Dr. Schoenberg is asked cohort by cohort."""
    from datetime import date as _date
    now = _date.today()
    cands = []
    for r in rows:
        if r.get("date"):  # already has a scheduled interview
            continue
        end = parse_rotation_end(r.get("notes", ""))
        if end and end.date() >= now and (end.date() - now).days <= window_days:
            cands.append((end.date(), r))
    if not cands:
        return None, None
    min_end = min(e for e, _ in cands)
    return [r for e, r in cands if e == min_end], min_end


def build_schoenberg_request(rows):
    """Build (anchor_html, storage_key) for the 'Request Dates' button.

    Auto-scopes to the soonest-ending cohort of students who still need an exit
    interview — replaces the old hardcoded Juliana/Ashley email (2026-09-09)."""
    import urllib.parse as _up
    group, end = _pick_next_cohort(rows)
    if not group:
        return ('<a id="reqDatesBtn" style="display:inline-block;background:#e4e4e7;color:#71717a;padding:8px 16px;border-radius:6px;text-decoration:none;font-size:13px;font-weight:600;cursor:not-allowed">No upcoming cohorts to schedule</a>', "none")

    names = [str(r.get("interviewee") or "").strip() for r in group if str(r.get("interviewee") or "").strip()]
    subject = "Sub-I Exit Interviews: " + " & ".join(names)

    end_label = f"{end.strftime('%B')} {_ordinal(end.day)}, {end.year}"
    monday = end - timedelta(days=end.weekday())
    week = []
    d = monday
    while d < end:
        week.append(d)
        d += timedelta(days=1)
    if not week:
        week = [end - timedelta(days=1)]
    window_label = f"{monday.strftime('%B')} {monday.day}–{week[-1].day}"
    if len(week) > 1:
        days_label = (f"{monday.strftime('%B')} " + ", ".join(str(x.day) for x in week[:-1]) + f", or {week[-1].day}")
    else:
        days_label = f"{monday.strftime('%B')} {week[0].day}"

    if len(names) == 1:
        who = f"{names[0]} is currently rotating with us through {end_label}."
    elif len(names) == 2:
        who = f"{names[0]} and {names[1]} are currently rotating with us through {end_label}."
    else:
        who = ", ".join(names[:-1]) + f", and {names[-1]} are currently rotating with us through {end_label}."

    body = (
        "Good afternoon,\n\n"
        + who +
        f"\n\nI'd like to schedule their Sub-I Exit Interviews with you during the last week of their rotation ({window_label}), before their end date on {end_label}. "
        f"Would a 10-minute time slot on {days_label} work for you? A midday slot around 12:30 PM worked well previously.\n\n"
        "Please let me know your availability.\n\nThank you,\nShareef Frasier"
    )
    params = _up.urlencode({"to": CC_EMAIL, "subject": subject, "body": body}, quote_via=_up.quote)
    url = "https://outlook.cloud.microsoft/mail/deeplink/compose?" + params
    anchor = (f'<a id="reqDatesBtn" href="{url}" target="_blank" '
              'style="display:inline-block;background:#f59e0b;color:#0f172a;padding:8px 16px;border-radius:6px;text-decoration:none;font-size:13px;font-weight:600">'
              'Request Dates from Dr. Schoenberg</a>')
    key = "schoenberg_dates_requested_" + end.strftime("%Y%m%d")
    return anchor, key



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
    return f"https://outlook.cloud.microsoft/calendar/deeplink/compose?{params}"


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

    today_iso = datetime.now().strftime("%Y-%m-%d")
    req_anchor_html, req_key = build_schoenberg_request(rows)
    req_button_block = (
        '<div style="display:flex;align-items:center;gap:12px;margin-bottom:16px">\n'
        f'  {req_anchor_html}\n'
        '  <span id="reqStatus" style="font-size:12px;color:#71717a"></span>\n'
        '  <button id="resetReqBtn" style="background:transparent;border:1px solid #d4d4d8;color:#71717a;padding:3px 8px;border-radius:4px;font-size:11px;cursor:pointer;display:none" title="Reset status">\u21ba Reset</button>\n'
        '</div>'
    )
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
        # CV presence is resolved from data/subi-cvs/ (no hardcoded student IDs)
        has_cv = bool(find_cv(r.get("interviewee", ""), r.get("recipient_email", "")))
        eml_label = "⬇ .eml (CV)" if has_cv else "⬇ .eml"
        eml_link = f'<a href="/api/subi-exit/eml?id={r["id"]}" style="display:inline-block;color:#71717a;font-size:11px;margin-left:8px;text-decoration:none;border:1px solid #d4d4d8;padding:3px 10px;border-radius:4px" title="Download .eml file — double-click in Outlook to open with CV attached">{eml_label}</a>' if has_date else ''
        action_cell = f'{outlook_btn}{eml_link}' if has_date else '<span style="color:#71717a;font-size:12px">TBD — date not set</span>'
        edit_btn = (f'<a href="#" data-edit-id="{r["id"]}" class="edit-btn" '
                    f'data-interviewee="{esc(r["interviewee"])}" data-email="{esc(r["recipient_email"])}" '
                    f'data-date="{esc(r["date"])}" data-time="{esc(r["time"])}" '
                    f'data-duration="{r["duration_minutes"]}" data-notes="{esc(r["notes"])}" '
                    f'style="display:inline-block;color:#b45309;font-size:12px;margin-left:8px;text-decoration:none;border:1px solid #f59e0b;padding:3px 10px;border-radius:4px;cursor:pointer">✎ Edit</a>')
        action_cell += edit_btn
        if has_date and r["date"] < today_iso:
            action_cell = f'<span style="color:#047857;font-size:12px;font-weight:600">\u2713 Interviewed {format_date(r["date"])}</span>'
        time_display = r["time"] if r["time"] != "TBD" else "TBD"
        # Show rotation dates as subtitle under interviewee name (from notes)
        rot_dates = ""
        notes = r.get("notes", "")
        import re as _re
        rot_match = _re.search(r"(\d{1,2}/\d{1,2}/?\d{2,4})\s*[-–]\s*(\d{1,2}/\d{1,2}/?\d{2,4})", notes)
        if rot_match:
            rot_dates = f'<br><span style="color:#71717a;font-size:11px">{rot_match.group(1)} – {rot_match.group(2)}</span>'
        to_display = ", ".join([r["recipient_email"], CC_EMAIL]) if r["recipient_email"] else CC_EMAIL
        rows_html += f'''<tr id="row-{r['event_id']}" style="border-bottom:1px solid #e4e4e7">
  <td style="padding:10px 14px;white-space:nowrap;font-size:13px"><strong>{date_display}</strong><br><span style="color:#71717a;font-size:11px">{date_dow}</span></td>
  <td style="padding:10px 14px;white-space:nowrap;font-size:13px"><strong>{time_display}</strong></td>
  <td style="padding:10px 14px;font-size:13px;max-width:280px;overflow:hidden;text-overflow:ellipsis"><strong>{r['interviewee']}</strong>{rot_dates}</td>
  <td style="padding:10px 14px;font-size:12px;color:#71717a;max-width:260px;overflow:hidden;text-overflow:ellipsis">{to_display}</td>
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
  body {{ background:#ffffff; color:#18181b; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif; padding:20px; max-width:1000px; margin:0 auto }}
  h1 {{ font-size:22px; margin-bottom:4px }}
  .subtitle {{ color:#71717a; font-size:14px; margin-bottom:20px }}
  .info {{ background:#ffffff; border:1px solid #e4e4e7; border-radius:8px; padding:14px 18px; margin-bottom:20px; font-size:13px; line-height:1.6 }}
  .info strong {{ color:#b45309 }}
  .info .test {{ color:#ef4444 }}
  .toggle-bar {{ display:flex; align-items:center; gap:16px; background:#ffffff; border:1px solid #e4e4e7; border-radius:8px; padding:12px 18px; margin-bottom:20px; font-size:13px }}
  .toggle-bar label {{ font-weight:600; color:#18181b }}
  .switch {{ position:relative; display:inline-block; width:44px; height:24px }}
  .switch input {{ opacity:0; width:0; height:0 }}
  .slider {{ position:absolute; cursor:pointer; top:0; left:0; right:0; bottom:0; background:#e4e4e7; border-radius:24px; transition:0.2s }}
  .slider:before {{ content:''; position:absolute; height:18px; width:18px; left:3px; bottom:3px; background:#94a3b8; border-radius:50%; transition:0.2s }}
  input:checked + .slider {{ background:#f59e0b }}
  input:checked + .slider:before {{ transform:translateX(20px); background:#fff }}
  .toggle-bar .hint {{ color:#71717a; font-size:12px }}
  .sent-badge {{ display:inline-flex; align-items:center; gap:4px; background:#d1fae5; color:#047857; padding:3px 10px; border-radius:999px; font-size:11px; font-weight:600 }}
  .sent-badge:before {{ content:'\\2713' }}
  .row-sent {{ opacity:0.5 }}
  .row-sent .invite-btn {{ background:#e4e4e7 !important; cursor:default }}
  .sent-badge /* sent tracking */ .invite-btn /*primary*/ .row-sent /*dim*/ .footer {{ }} .edit-badge {{ }}
  a:hover {{ opacity:0.85 }}
  .count {{ color:#71717a; font-size:13px; margin:14px 0 }}
  table {{ width:100%; border-collapse:collapse; font-size:13px }}
  th {{ text-align:left; padding:8px 14px; color:#71717a; font-size:11px; text-transform:uppercase; letter-spacing:0.5px; border-bottom:2px solid #e4e4e7 }}
  .footer {{ margin-top:24px; padding-top:16px; border-top:1px solid #334155; font-size:12px; color:#71717a; line-height:1.5 }}
</style>
</head>
<body>
  <h1>Sub-I Exit Interviews</h1>

    {req_button_block}
  <script type="text/javascript">
    (function() {{
      const btn = document.getElementById('reqDatesBtn');
      const statusSpan = document.getElementById('reqStatus');
      const resetBtn = document.getElementById('resetReqBtn');
      const storageKey = '{req_key}';
      
      function updateState(sent) {{
        if (sent) {{
          btn.style.background = '#064e3b';
          btn.style.color = '#047857';
          btn.textContent = '✓ Dates Requested from Dr. Schoenberg';
          statusSpan.innerHTML = '<span style="color:#047857">Already sent</span>';
          resetBtn.style.display = 'inline-block';
        }} else {{
          btn.style.background = '#fbbf24';
          btn.style.color = '#0f172a';
          btn.textContent = 'Request Dates from Dr. Schoenberg';
          statusSpan.innerHTML = '';
          resetBtn.style.display = 'none';
        }}
      }}
      
      if (localStorage.getItem(storageKey) === 'true') {{
        updateState(true);
      }}
      
      btn.addEventListener('click', function() {{
        localStorage.setItem(storageKey, 'true');
        setTimeout(() => {{ updateState(true); }}, 200);
      }});
      
      resetBtn.addEventListener('click', function(e) {{
        e.preventDefault();
        localStorage.removeItem(storageKey);
        updateState(false);
      }});
    }})();
  </script>

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
    <th style="width:250px">To</th>
    <th style="width:250px">Action</th>
  </tr></thead>
  <tbody>
  {rows_html}    </tbody>
  </table>

  <!-- ✎ Inline Edit Modal -->
  <div id="editModal" style="display:none;position:fixed;inset:0;z-index:1000;background:rgba(0,0,0,0.6);align-items:center;justify-content:center">
  <div style="background:#ffffff;border:1px solid #e4e4e7;border-radius:12px;padding:22px;max-width:500px;width:92%;max-height:90vh;overflow:auto">
    <h3 style="margin:0 0 4px;color:#b45309">✎ Edit Interview</h3>
    <p style="color:#71717a;font-size:12px;margin:0 0 16px" id="editSubtitle">Update the row — changes save to the database and reflect on this page.</p>
    <label style="display:block;font-size:12px;color:#71717a;margin:8px 0 3px">Interviewee</label>
    <input id="eInterviewee" style="width:100%;background:#ffffff;color:#18181b;border:1px solid #e4e4e7;border-radius:6px;padding:8px 10px;font-size:13px">
    <label style="display:block;font-size:12px;color:#71717a;margin:8px 0 3px">Recipient Email</label>
    <input id="eEmail" style="width:100%;background:#ffffff;color:#18181b;border:1px solid #e4e4e7;border-radius:6px;padding:8px 10px;font-size:13px">
    <div style="display:flex;gap:10px">
      <div style="flex:1">
        <label style="display:block;font-size:12px;color:#71717a;margin:8px 0 3px">Date</label>
        <input id="eDate" type="date" style="width:100%;background:#ffffff;color:#18181b;border:1px solid #e4e4e7;border-radius:6px;padding:8px 10px;font-size:13px">
      </div>
      <div style="flex:1">
        <label style="display:block;font-size:12px;color:#71717a;margin:8px 0 3px">Time</label>
        <input id="eTime" placeholder="e.g. 12:00 PM" style="width:100%;background:#ffffff;color:#18181b;border:1px solid #e4e4e7;border-radius:6px;padding:8px 10px;font-size:13px">
      </div>
      <div style="width:90px">
        <label style="display:block;font-size:12px;color:#71717a;margin:8px 0 3px">Min</label>
        <input id="eDuration" type="number" min="5" max="120" style="width:100%;background:#ffffff;color:#18181b;border:1px solid #e4e4e7;border-radius:6px;padding:8px 10px;font-size:13px">
      </div>
    </div>
    <label style="display:block;font-size:12px;color:#71717a;margin:8px 0 3px">Notes</label>
    <textarea id="eNotes" rows="3" style="width:100%;background:#ffffff;color:#18181b;border:1px solid #e4e4e7;border-radius:6px;padding:8px 10px;font-size:13px;resize:vertical"></textarea>
    <div style="display:flex;justify-content:flex-end;gap:10px;margin-top:18px">
      <button id="editCancel" style="background:#ffffff;color:#71717a;border:1px solid #e4e4e7;border-radius:6px;padding:8px 16px;font-size:13px;cursor:pointer">Cancel</button>
      <button id="editDelete" style="background:#7f1d1d;color:#fca5a5;border:1px solid #991b1b;border-radius:6px;padding:8px 16px;font-size:13px;cursor:pointer">Delete</button>
      <button id="editSave" style="background:#f59e0b;color:#0f172a;border:none;border-radius:6px;padding:8px 20px;font-size:13px;font-weight:600;cursor:pointer">Save</button>
    </div>
    <p id="editMsg" style="font-size:12px;margin-top:10px;color:#047857"></p>
  </div>
  </div>

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

    // ── ✎ Inline Edit (uses existing PUT/DELETE /api/subi-exit-interviews/{id}) ──
    const modal = document.getElementById('editModal');
    let editingId = null;
    modal.style.display = 'none';

    document.querySelectorAll('.edit-btn').forEach(btn => {{
      btn.addEventListener('click', function(e) {{
        e.preventDefault(); e.stopPropagation();
        editingId = this.dataset.editId;
        document.getElementById('eInterviewee').value = this.dataset.interviewee || '';
        document.getElementById('eEmail').value = this.dataset.email || '';
        const d = this.dataset.date || '';
        document.getElementById('eDate').value = (d.match(/^\d{{4}}-\d{{2}}-\d{{2}}$/)) ? d : '';
        document.getElementById('eTime').value = (this.dataset.time || '').toLowerCase() === 'tbd' ? '12:00 PM' : (this.dataset.time || '');
        document.getElementById('eDuration').value = this.dataset.duration || 10;
        document.getElementById('eNotes').value = this.dataset.notes || '';
        document.getElementById('editMsg').textContent = '';
        modal.style.display = 'flex';
      }});
    }});

    document.getElementById('editCancel').addEventListener('click', function(){{
      modal.style.display = 'none'; editingId = null;
    }});
    modal.addEventListener('click', function(e){{
      if (e.target === modal) {{ modal.style.display = 'none'; editingId = null; }}
    }});

    document.getElementById('editSave').addEventListener('click', async function(){{
      const payload = {{
        interviewee: document.getElementById('eInterviewee').value,
        recipient_email: document.getElementById('eEmail').value,
        interview_date: document.getElementById('eDate').value || null,
        interview_time: document.getElementById('eTime').value || '12:00 PM',
        duration_minutes: parseInt(document.getElementById('eDuration').value || '10', 10),
        notes: document.getElementById('eNotes').value,
      }};
      const msg = document.getElementById('editMsg');
      try {{
        const resp = await fetch('/api/subi-exit-interviews/' + editingId, {{
          method: 'PUT',
          headers: {{'Content-Type': 'application/json'}},
          body: JSON.stringify(payload),
        }});
        const res = await resp.json();
        if (res.success) {{
          msg.style.color = '#047857';
          msg.textContent = '✓ Saved. Reloading…';
          setTimeout(() => location.reload(), 600);
        }} else {{
          msg.style.color = '#f87171';
          msg.textContent = 'Save failed: ' + (res.error || 'unknown');
        }}
      }} catch (err) {{
        msg.style.color = '#f87171';
        msg.textContent = 'Save error: ' + err;
      }}
    }});

    document.getElementById('editDelete').addEventListener('click', async function(){{
      if (!confirm('Delete this interview row? This cannot be undone.')) return;
      const msg = document.getElementById('editMsg');
      try {{
        const resp = await fetch('/api/subi-exit-interviews/' + editingId, {{ method: 'DELETE' }});
        const res = await resp.json();
        if (res.success) {{
          msg.style.color = '#047857';
          msg.textContent = '✓ Deleted. Reloading…';
          setTimeout(() => location.reload(), 500);
        }} else {{
          msg.style.color = '#f87171';
          msg.textContent = 'Delete failed: ' + (res.error || 'unknown');
        }}
      }} catch (err) {{
        msg.style.color = '#f87171';
        msg.textContent = 'Delete error: ' + err;
      }}
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
