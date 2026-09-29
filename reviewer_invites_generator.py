#!/usr/bin/env python3
"""Reviewer invite page for the Agentic OS dashboard.

Reads data/reviewer_invites.json (written by scripts/interview-2026-27/11-build-reviewer-emails.py
from the live roster + the credential sheet) and renders one row per reviewer with an
Outlook compose deeplink — plus a sent / not-sent state the owner controls.

TWO KINDS OF STATUS, kept distinct on purpose:
  * "Sent" is the owner's own mark. The deeplink only opens a draft; nothing in this stack can
    see whether the human pressed Send, so it is recorded by hand (POST /api/reviewer-invites/mark)
    into data/reviewer_invite_status.json — never guessed, never inferred from "the button was clicked".
  * "Portal sign-in" is EVIDENCE, from auth.users.last_sign_in_at in the live DB. A sign-in after
    the send mark is proof the credential arrived and worked. A sign-in that PREDATES the mark is
    a test login, and is labelled as such instead of being counted as progress.

Deeplink rules (see the outlook-compose-deeplinks skill):
  - host is outlook.cloud.microsoft
  - MAIL drafts take a PLAIN-TEXT body and NO bodyType (HTML in a mail deeplink is ignored
    and renders as literal tags)
  - percent-encode with quote_via=quote, never quote_plus
"""
import json
import html
import re
import datetime
from pathlib import Path
from urllib.parse import urlencode, quote

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "reviewer_invites.json"
STATUS_FILE = BASE_DIR / "data" / "reviewer_invite_status.json"
OUTLOOK_MAIL = "https://outlook.cloud.microsoft/mail/deeplink/compose"
OUTLOOK_CAL = "https://outlook.cloud.microsoft/calendar/deeplink/compose"

# Where the formatting probes point. Kept on the owner's own address so a mis-click can
# never reach a reviewer.
PROBE_TO = "sfrasier@montefiore.org"

# Calendar-invite slot for every reviewer draft. A calendar deeplink must carry a window;
# there is no "all day" parameter, so it's expressed the way Outlook itself does it — the
# full date, midnight to 23:59. Location is intentionally blank (owner, 2026-09-28).
CAL_START = "2026-10-11T00:00:00"
CAL_END = "2026-10-11T23:59:59"
CAL_LOCATION = ""
CAL_LABEL = "all day, Sunday 11 October 2026 — the due date"

# ── House signature ──────────────────────────────────────────────────────────────
# The same block the platform mailer appends to every send, with one change: the logo and
# social strip are referenced as hosted URLs under /dashboard/ (a public static mount)
# because a deeplink body cannot carry nodemailer's inline CID attachments.
# Markup is kept lean on purpose — every character here is percent-encoded in the URL.
SIG_ASSET = "https://os.srv1738752.hstgr.cloud/dashboard/assets/email"
# Blank line between blocks. A trailing <br>&nbsp; inside the paragraph is the cheapest
# spacing that every Outlook renderer honours — a stray <br> between blocks gets dropped,
# and a margin style costs roughly twice as many encoded characters.
GAP = "<br>&nbsp;"

SIG_HTML = (
    "<hr>"
    f"<p><strong>Thank You</strong>{GAP}</p>"
    f"<p><strong>Shareef Frasier</strong><br>"
    f"Residency Program Administrator<br>"
    f"Department of Urology{GAP}</p>"
    f"<p><strong>Montefiore Medical Center</strong><br>"
    f"The University Hospital for Albert Einstein College of Medicine<br>"
    f"1250 Waters Place, Tower One, PH-2, Bronx, NY 10461<br>"
    f"929-696-3195 Cell<br>347-842-1724 Office<br>917-962-5410 Fax{GAP}</p>"
    f"<p><strong>Follow Us @montefioreuro</strong><br>"
    f'<img src="{SIG_ASSET}/mfu-social.png" width="52" height="17" alt="Instagram, TikTok, X">{GAP}</p>'
    f'<p><a href="mailto:sfrasier@montefiore.org">sfrasier@montefiore.org</a><br>'
    f'<a href="https://www.montefiore.org/urology">www.montefiore.org/urology</a>{GAP}</p>'
    f'<p><img src="{SIG_ASSET}/mfu-logo.png" width="230" height="49" alt="Montefiore Einstein Urology"></p>'
    '<p style="font-size:10px;line-height:1.5;color:#133667;"><u>CONFIDENTIALITY NOTICE:</u> '
    "This e-mail message, including any attachments, is for the sole use of the intended "
    "recipient(s). The information contained in this message may be private and confidential. "
    "Any unauthorized review, use, disclosure or distribution is prohibited. If you are not the "
    "intended recipient, please contact the sender by reply e-mail and destroy all copies of the "
    "original message. Thank you.</p>"
)
SIG_TEXT = """
Thank You

Shareef Frasier
Residency Program Administrator
Department of Urology

Montefiore Medical Center
The University Hospital for Albert Einstein College of Medicine
1250 Waters Place, Tower One, PH-2, Bronx, NY 10461
929-696-3195 Cell
347-842-1724 Office
917-962-5410 Fax

Follow Us @montefioreuro
sfrasier@montefiore.org
www.montefiore.org/urology

CONFIDENTIALITY NOTICE: This e-mail message, including any attachments, is for the sole use
of the intended recipient(s). The information contained in this message may be private and
confidential. Any unauthorized review, use, disclosure or distribution is prohibited. If you
are not the intended recipient, please contact the sender by reply e-mail and destroy all
copies of the original message. Thank you.
"""


def build_deeplink(subject: str, body: str, to: str) -> str:
    params = {"to": to, "subject": subject, "body": body}
    return OUTLOOK_MAIL + "?" + urlencode(params, quote_via=quote)


def build_mail_html_deeplink(subject: str, html_body: str, to: str) -> str:
    """MAIL deeplink carrying HTML. Microsoft ignores bodyType on the mail handler — this
    exists so the owner can see that for himself in his own Outlook rather than take it
    on faith (the last hard evidence was a September case)."""
    params = {"to": to, "subject": subject, "body": html_body, "bodyType": "HTML"}
    return OUTLOOK_MAIL + "?" + urlencode(params, quote_via=quote)


def build_calendar_deeplink(subject: str, html_body: str, to: str, start: str, end: str,
                            location: str = "") -> str:
    """CALENDAR deeplink — the handler that DOES render HTML (see the screenshot's
    Resident AM Conference invite). Body must be HTML tags only: <br>, <strong>, <hr>, <a>."""
    params = {"to": to, "subject": subject, "body": html_body, "bodyType": "HTML",
              "startdt": start, "enddt": end}
    if location:
        params["location"] = location
    return OUTLOOK_CAL + "?" + urlencode(params, quote_via=quote)


def body_to_html(body: str, signature: bool = True) -> str:
    """Plain-text canonical body → the HTML the deeplink body carries.

    Derived from the same text the plain deeplinks use, so the two cannot drift.
    Markup is deliberately lean (bare <p>, bare <hr>, <strong>, <a>): the calendar handler
    renders default paragraph spacing anyway, and every character spent on inline styles is
    percent-encoded into the URL. Bullets keep an explicit gap — Outlook collapses adjacent
    paragraph margins in some clients and the owner asked for a clear break between them.
    """
    parts = ['<div style="line-height:1.6">']
    for line in body.split("\n"):
        line = line.rstrip()
        if not line.strip():
            continue
        if _RULE_RE.match(line.strip()):
            parts.append("<hr>")
            continue
        caps = re.match(r"^[A-Z][A-Z0-9& ]+$", line.strip())
        if caps:
            parts.append(f"<p><strong>{html.escape(line.strip())}</strong>{GAP}</p>")
            continue
        bullet = re.match(r"^•\s+(.*)$", line.strip())
        if bullet:
            parts.append(f"<p>&bull;&nbsp;&nbsp;{_html_inline(bullet.group(1))}{GAP}</p>")
            continue
        label = re.match(r"^([A-Za-z][A-Za-z /]+?):\s+(\S.*)$", line.strip())
        if label:
            parts.append(f"<p><strong>{html.escape(label.group(1))}:</strong> "
                         f"{_html_inline(label.group(2))}{GAP}</p>")
            continue
        parts.append(f"<p>{_html_inline(line.strip())}{GAP}</p>")
    if signature:
        parts.append(SIG_HTML)
    parts.append("</div>")
    return "".join(parts)


def _html_inline(text: str) -> str:
    esc = html.escape(text)
    esc = re.sub(r"\b([A-Z][A-Z0-9&]{1,})\b", r"<strong>\1</strong>", esc)
    return re.sub(r"(https?://[^\s<]+)",
                  r'<a href="\1" style="color:#0b4f9e;text-decoration:underline;">\1</a>', esc)


def load_invites() -> dict:
    if not DATA_FILE.exists():
        return {"generated_at": None, "subject": "", "invites": []}
    return json.loads(DATA_FILE.read_text())


def load_status() -> dict:
    if not STATUS_FILE.exists():
        return {}
    try:
        return json.loads(STATUS_FILE.read_text())
    except Exception:
        return {}


def save_status(email: str, sent: bool, by: str = "owner") -> dict:
    """Record (or clear) a send mark. Atomic write: tmp + replace."""
    status = load_status()
    key = email.strip().lower()
    if sent:
        status[key] = {
            "sent_at": datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "marked_by": by,
        }
    else:
        status.pop(key, None)
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATUS_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
    tmp.replace(STATUS_FILE)
    return status


_URL_RE = re.compile(r"(https?://[^\s<]+)")
_CAPS_RE = re.compile(r"\b[A-Z][A-Z0-9&]{1,}\b")
_RULE_RE = re.compile(r"^-{6,}$")


def render_body(body: str) -> str:
    """Preview decoration for the page ONLY.

    The Outlook draft body is plain text (Microsoft ignores HTML in a mail deeplink — HTML
    shows up as literal tags), so bold text and clickable links can exist HERE, where the
    owner reads it, but cannot travel through the link. In the draft the caps words carry
    emphasis by themselves and the URL is followed by whitespace so Outlook auto-links it.
    """
    out = []
    for line in body.split("\n"):
        esc = html.escape(line)
        if _RULE_RE.match(esc.strip()):
            out.append(f'<span class="rule">{esc}</span>')
            continue
        esc = _CAPS_RE.sub(lambda m: f"<strong>{m.group(0)}</strong>", esc)
        esc = _URL_RE.sub(
            lambda m: f'<a href="{m.group(1)}" target="_blank" rel="noopener">{m.group(1)}</a>', esc)
        out.append(esc)
    return "\n".join(out)


def _parse(ts):
    if not ts or ts == "never":
        return None
    try:
        return datetime.datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except Exception:
        return None


def _fmt(ts) -> str:
    dt = _parse(ts)
    if dt is None:
        return ""
    return dt.astimezone(datetime.UTC).strftime("%b %-d, %H:%M UTC")


def generate_html_page(signins: dict | None = None) -> str:
    data = load_invites()
    invites = data.get("invites", [])
    status = load_status()
    signins = signins or {}
    subject = data.get("subject", "")
    total_files = sum(i.get("files", 0) for i in invites)
    sent_count = sum(1 for i in invites if i["email"].strip().lower() in status)

    # ── The dry run ────────────────────────────────────────────────────────────
    # A reviewer's EXACT draft with the attendee swapped to the owner: same subject, body,
    # credentials and signature, same calendar deeplink + HTML, same all-day Oct 11 window,
    # same blank location. It can only ever open in his Outlook, so a mis-click is harmless,
    # and nothing leaves until he presses Send.
    probe_html = ""
    if invites:
        sample = next((i for i in invites if i["last"] == "Harel"), invites[0])
        dry_body = body_to_html(sample["body"])
        dry_url = build_calendar_deeplink(subject, dry_body, PROBE_TO, CAL_START, CAL_END, CAL_LOCATION)
        probe_html = f"""
  <section class="probe">
    <h2>Your dry run &mdash; the real draft, delivered to you</h2>
    <p class="meta">Dr. {html.escape(sample['last'])}&rsquo;s exact draft &mdash; same subject, queue count,
       credentials and signature &mdash; with the attendee changed to you. Click it, Outlook opens the
       draft, and nothing leaves until you press Send. <span class="len">{len(dry_url):,} chars</span></p>
    <div class="probe-actions">
      <a class="btn alt" href="{html.escape(dry_url, quote=True)}" target="_blank" rel="noopener">Open my dry-run draft in Outlook</a>
    </div>
  </section>"""

    rows = []
    for inv in invites:
        key = inv["email"].strip().lower()
        html_body = body_to_html(inv["body"])
        # Primary button = CALENDAR deeplink + HTML: the only handler that renders bold,
        # rules and live links (verified by the owner in his own Outlook, 2026-09-28).
        # The plain MAIL deeplink stays as a discreet fallback, since it is the only route
        # that arrives as an ordinary email rather than an invite.
        cal_url = build_calendar_deeplink(subject, html_body, inv["email"],
                                          CAL_START, CAL_END, CAL_LOCATION)
        plain_url = build_deeplink(subject, inv["body"] + SIG_TEXT, inv["email"])
        length = len(cal_url)
        # 5,600 is the practical ceiling for the cloud.microsoft handler (the old
        # outlook.office.com host failed outright on long links; ~5.5K is known-good here).
        budget = "ok" if length < 5600 else "over"

        mark = status.get(key)
        if mark:
            chip = f'<span class="chip sent">Sent &middot; {html.escape(_fmt(mark.get("sent_at")))}</span>'
            buttons = (f'<button class="ghost" onclick="mark(\'{html.escape(inv["email"], quote=True)}\', false)">'
                       f'Undo</button>')
        else:
            chip = '<span class="chip unsent">Not sent</span>'
            buttons = (f'<button class="mark" onclick="mark(\'{html.escape(inv["email"], quote=True)}\', true)">'
                       f'Mark sent</button>')

        # evidence, never a guess
        signin = signins.get(key)
        if _parse(signin):
            if mark and _parse(mark.get("sent_at")) and _parse(signin) > _parse(mark["sent_at"]):
                evidence = (f'<span class="ev good">&#10003; signed in after send &middot; '
                            f'{html.escape(_fmt(signin))}</span>')
            elif mark:
                evidence = (f'<span class="ev">portal sign-in {html.escape(_fmt(signin))} '
                            f'(before this send)</span>')
            else:
                evidence = (f'<span class="ev">portal sign-in {html.escape(_fmt(signin))} '
                            f'&mdash; test login, nothing sent yet</span>')
        else:
            evidence = '<span class="ev">no portal sign-in yet</span>'

        rows.append(f"""
    <section class="card{' done' if mark else ''}">
      <header>
        <div>
          <h2>{html.escape(inv['name'])}</h2>
          <p class="meta">{html.escape(inv['email'])} &middot; {inv['files']} applicants &middot; temp password
             <code>{html.escape(inv['password'])}</code></p>
          <p class="status">{chip} {evidence}</p>
        </div>
        <div class="actions">
          <a class="btn" href="{html.escape(cal_url, quote=True)}" target="_blank" rel="noopener">Open in Outlook</a>
          {buttons}
          <span class="len {budget}">{length:,} chars</span>
        </div>
      </header>
      <details>
        <summary>Preview the message</summary>
        <pre class="body">{render_body(inv['body'] + SIG_TEXT)}</pre>
      </details>
      <p class="fallback"><a href="{html.escape(plain_url, quote=True)}" target="_blank" rel="noopener">Send the plain-text email version instead</a></p>
    </section>""")

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Reviewer invites — 2026-2027</title>
<style>
  :root {{ --ink:#101418; --mut:#5c6672; --line:#e3e7ec; --accent:#0d6b5f; --bg:#f7f8fa;
           --good:#0f7b4f; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; padding:22px; background:var(--bg); color:var(--ink);
         font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; }}
  h1 {{ font-size:19px; margin:0 0 4px; letter-spacing:-.01em; }}
  .lede {{ color:var(--mut); margin:0 0 18px; }}
  .card {{ background:#fff; border:1px solid var(--line); border-radius:10px; padding:14px 16px; margin-bottom:12px; }}
  .card.done {{ border-left:3px solid var(--good); }}
  .card header {{ display:flex; justify-content:space-between; gap:16px; align-items:flex-start; }}
  .card h2 {{ font-size:15px; margin:0 0 2px; }}
  .meta {{ margin:0; color:var(--mut); font-size:12.5px; }}
  .status {{ margin:6px 0 0; display:flex; gap:10px; flex-wrap:wrap; align-items:center; }}
  code {{ background:#eef1f4; padding:1px 5px; border-radius:4px; }}
  .chip {{ font-size:11.5px; font-weight:700; padding:2px 8px; border-radius:99px; border:1px solid transparent; }}
  .chip.sent {{ background:#e7f5ee; color:var(--good); border-color:#bfe3d0; }}
  .chip.unsent {{ background:#f1f3f5; color:var(--mut); border-color:#e0e5ea; }}
  .ev {{ font-size:11.5px; color:var(--mut); }}
  .ev.good {{ color:var(--good); }}
  .actions {{ display:flex; align-items:center; gap:8px; white-space:nowrap; }}
  .btn {{ background:var(--accent); color:#fff; text-decoration:none; padding:7px 13px;
          border-radius:7px; font-weight:600; font-size:13px; }}
  .mark, .ghost {{ border-radius:7px; padding:6px 11px; font-size:12.5px; font-weight:600; cursor:pointer;
                   font-family:inherit; background:#fff; }}
  .mark {{ border:1px solid var(--accent); color:var(--accent); }}
  .ghost {{ border:1px solid var(--line); color:var(--mut); }}
  .len {{ color:var(--mut); font-size:11.5px; }}
  .len.over {{ color:#b3261e; font-weight:600; }}
  details {{ margin-top:10px; }}
  summary {{ cursor:pointer; color:var(--mut); font-size:12.5px; }}
  pre {{ white-space:pre-wrap; background:#fafbfc; border:1px solid var(--line); border-radius:8px;
         padding:12px; margin:10px 0 0; font:12.5px/1.55 ui-monospace,SFMono-Regular,Menlo,monospace; }}
  pre.body strong {{ font-weight:700; color:#0b1117; }}
  pre.body a {{ color:var(--accent); text-decoration:underline; }}
  pre.body .rule {{ color:#c4ccd4; }}
  .probe {{ background:#fff; border:1px solid #cfe0dc; border-left:3px solid var(--accent);
            border-radius:10px; padding:14px 16px; margin-bottom:16px; }}
  .probe h2 {{ font-size:14.5px; margin:0 0 6px; }}
  .probe-actions {{ display:flex; align-items:center; gap:10px; margin-top:10px; flex-wrap:wrap; }}
  .btn.alt {{ background:#fff; color:var(--accent); border:1px solid var(--accent); }}
  .fallback {{ margin:10px 0 0; font-size:12px; }}
  .fallback a {{ color:var(--mut); text-decoration:underline; }}
  .foot {{ color:var(--mut); font-size:12px; margin-top:18px; }}
</style></head>
<body>
  <h1>2026-2027 application review — reviewer invites</h1>
  <p class="lede"><strong>{sent_count} of {len(invites)} sent</strong> &middot; {len(invites)} reviewers &middot;
     {total_files} applicants &middot; one Outlook draft per reviewer, each carrying their own temporary password.
     <strong>Open in Outlook</strong> opens a <em>calendar invite</em> ({html.escape(CAL_LABEL)},
     no location) whose body is the formatted message &mdash;
     bold labels, a live portal link &mdash; you hit Send, then <strong>Mark sent</strong>.</p>
  {probe_html}
  {''.join(rows) if rows else '<p class="lede">No invite data file yet &mdash; run scripts/interview-2026-27/11-build-reviewer-emails.py, then reload.</p>'}
  <p class="foot">Generated {html.escape(str(data.get('generated_at') or 'unknown'))} from the live roster and
     the committee credential sheet. Subject: {html.escape(subject)}</p>
<script>
async function mark(email, sent) {{
  const r = await fetch('/api/reviewer-invites/mark', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{email: email, sent: sent}})
  }});
  if (!r.ok) {{ alert('Could not save the mark (' + r.status + ')'); return; }}
  location.reload();
}}
</script>
</body></html>"""


if __name__ == "__main__":
    inv = load_invites().get("invites", [])
    demo = {i["email"]: "2026-09-28T19:15:37Z" for i in inv[:2]}
    Path("/tmp/reviewer_invites_preview.html").write_text(generate_html_page(demo))
    print("wrote /tmp/reviewer_invites_preview.html",
          "| sent marks:", len(load_status()), "of", len(inv))
