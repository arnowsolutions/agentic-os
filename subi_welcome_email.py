#!/usr/bin/env python3
"""
subi_welcome_email.py — Personalized Sub-I Welcome Email generator.

Builds the standard Montefiore Urology Sub-I welcome email for one student,
with these fields filled from per-student config + the standard template:
  - first name, rotation dates
  - weekly site schedule (Hutch / Peds / Moses / Weiler by week)
  - Grand Rounds presentation date
  - chief resident contact at the student's sites

The two FILLABLE onboarding forms (MMC Access Form + ID Badge Info) are included
as LINKS (public FormForge URLs), NOT attachments. The other 6 reference docs
(welcome letter, meet the residents, meet the faculty, parking, shuttle, reading
list) are attached.

Sends go through the REVIEW GATE (review_gate.py) — the email is drafted to
Shareef's inbox for approval and only delivered after --approve. This enforces
the review-before-send rule and lets Shareef review before any student is emailed.

Usage:
  python3 subi_welcome_email.py --draft --student juliana.viola
      -> drafts the welcome email via review_gate (preview to Shareef). NOT sent.
  python3 subi_welcome_email.py --student juliana.viola
      -> alias for --draft
  python3 subi_welcome_email.py --list
      -> list students configured for welcome emails
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
CFG = DATA / "subi_welcome_config.json"
DOCS = DATA / "subi-welcome-docs"
FORMS = DATA / "subi_online_forms.json"
GATE = BASE / "review_gate.py"
FROM_FMT = "Dr. Beth Edelblute\nSubinternship Clerkship Director"
CC_EMAIL = "sfrasier@montefiore.org"

# 6 documents to attach (fillable forms are links, not attachments)
ATTACH = [
    ("Welcome_Letter_Updated_2026.docx", "Welcome Letter"),
    ("Meet_The_Residents_Updated.docx", "Meet the Residents"),
    ("Meet_the_Faculty_2026.docx", "Meet the Faculty"),
    ("Montefiore_Parking_Info_for_Sub-Interns.pdf", "Parking Info"),
    ("Montefiore_Einstein_Shuttle_Schedule_2024.pdf", "Shuttle Schedule"),
    ("Sub-Intern_Reading_Material_List.pdf", "Reading Material List"),
]


def load():
    return json.loads(CFG.read_text())


def load_forms():
    """Return the online-forms dict {key: url} from subi_online_forms.json."""
    if FORMS.exists():
        try:
            return json.loads(FORMS.read_text())
        except Exception:
            pass
    return {}


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_html(first_name, cfg, st, forms):
    weeks = st.get("weekly_schedule") or []
    # Site schedule rows
    if weeks:
        rows = "".join(
            f"<tr><td style='padding:4px 10px;border:1px solid #ddd'>{esc(w.get('dates',''))}</td>"
            f"<td style='padding:4px 10px;border:1px solid #ddd'>{esc(w.get('site',''))}</td></tr>"
            for w in weeks
        )
        schedule = f"<table style='border-collapse:collapse;font-size:13px'>{rows}</table>"
    else:
        schedule = "<em>Site schedule to be provided.</em>"
    gr = esc(st.get("gr_date") or "TBD")
    chiefs = st.get("chief_contacts") or {}
    chief_lines = "".join(f"<li>{esc(v)}</li>" for v in chiefs.values()) or "<li>Chief contacts to be provided.</li>"

    # Fillable forms included as LINKS (from subi_online_forms.json)
    f = forms if isinstance(forms, dict) else {}
    mmc = f.get("mmc_access_form", "")
    epic = f.get("epic_access_form", "")
    scrub = f.get("scrub_access_form", "")
    badge = f.get("id_badge_info", "")
    form_items = []
    if mmc:
        form_items.append(
            f"<li><a href='{esc(mmc)}'>MMC Access Form (fillable online)</a> — complete and email to Shareef for Epic access</li>")
    if epic:
        form_items.append(
            f"<li><a href='{esc(epic)}'>Epic Access Request Form (fillable online)</a> — complete and email to Shareef</li>")
    if scrub:
        form_items.append(
            f"<li><a href='{esc(scrub)}'>Scrub Access Form (fillable online)</a> — complete and email to Shareef</li>")
    if badge:
        form_items.append(
            f"<li><a href='{esc(badge)}'>Montefiore ID Badge Info</a> — reference for getting your Monte ID / badge</li>")
    if form_items:
        form_links = f"""
<p style='font-size:14px'><strong>Online forms (please complete as soon as possible):</strong></p>
<ul>{''.join(form_items)}</ul>"""
    else:
        form_links = ""

    return f"""<html><body style="font-family:'Segoe UI',Arial,sans-serif;font-size:14px;line-height:1.55;color:#111827">
<p>Dear {first_name},</p>
<p>Welcome to the Montefiore Department of Urology! We are all so excited to have you for your
sub-internship rotation from <strong>{esc(st.get('rotation_start'))} - {esc(st.get('rotation_end'))}</strong>.</p>
<p>These documents are designed to give you a more in-depth overview of our department for your reference.
Before your rotation, as soon as you conveniently can, please fill out the <strong>online forms below</strong>
and email them to Shareef ({CC_EMAIL}, cc'd) so we can work on getting your Epic access as soon as possible.</p>
{form_links}
<p>At the House Staff office, you will receive an <strong>ID memo</strong> which you can then take to a
Monte Security location in order to receive your Monte ID.</p>
<p><strong>House Staff Information:</strong><br>Moses Campus (Main office)<br>150 East 210th Street<br>
Bronx, NY 10467<br>3rd Floor (4th doorbell)<br>Phone: 718-920-2345<br>Fax: 718-920-8403</p>
<p><strong>Logistics and First Day</strong><br>Our chief residents' contact info are listed below. Before your
first day on rotation, please reach out to the chief at your designated site for first day instructions.</p>
<ul>{chief_lines}</ul>
<p><strong>Your 4-week rotation schedule:</strong></p>
{schedule}
<p><strong>Expectations</strong> — During your 4 weeks on service, you will be expected to complete the following milestones:</p>
<ul>
<li>[ ] 1 evening night call until 10pm with junior resident. Coordinate with your chiefs on service.</li>
<li>[ ] 10 minute Grand Rounds presentation (+5 min Q+A) based on a clinical case you saw on service.
Your GR date will be on <strong>{gr}</strong>. Run your topic ideas by me or an attending.</li>
<li>[ ] Mid rotation feedback with me. You can text me at 603-548-2658 to arrange a brief chat roughly halfway.</li>
<li>[ ] Subintern Curriculum — mini lecture series held by our faculty. Schedule sent out shortly after this email.</li>
<li>[ ] Meeting with Dr. Schoenberg. I will arrange with his secretary for a one-on-one.
Please email me your CV upon receipt of this email so I can set up your meeting.</li>
</ul>
<p><strong>General Tips for Subintern Success</strong><br>Treat a subinternship exactly as it sounds — a role
right below an intern, meaning act as a supporting team member, not just an observer. Anticipate helpful tasks:
grabbing stirrups for a cysto case, being prepared for supplies during rounds, or knowing where to grab blankets.
Think of yourself as a good waiter — always one step ahead of what people need, but not so eager you get in the way.</p>
<p>Preparing for your cases will be key to showcasing your knowledge about urology. Understand the anatomy of a
case first, then the general steps and disease process. Ask questions about interesting cases, but show you came prepared.</p>
<p>Finally, take time to reflect. Trying to match into a competitive specialty is stressful, but the success of
matching into urology is well worth the effort. Your subinternship is your time to gain confidence that this
specialty (and hopefully this program!) is the right fit for you.</p>
<p>Looking forward to seeing you soon!</p>
<p>Dr. Beth Edelblute<br>Subinternship Clerkship Director</p>
</body></html>"""


def run_gate_draft(to, subject, html, attachments):
    cmd = [sys.executable, str(GATE), "--draft", "--to", to, "--cc", CC_EMAIL,
           "--subject", subject, "--body", html, "--html"]
    for a in attachments:
        cmd += ["--attach", a]
    # The review gate uses smtp_send's plain-text body; for a full HTML email we pass HTML.
    print("Queueing welcome email for review (NOT sent):")
    print("  To:", to, "| Cc:", CC_EMAIL)
    print("  Subject:", subject)
    print("  Attachments:", len(attachments))
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
    out = (r.stdout + r.stderr).strip()
    print(out)
    if r.returncode != 0:
        sys.exit(r.returncode)


def do_student(key, cfg):
    st = (cfg.get("students") or {}).get(key)
    if not st:
        raise SystemExit(f"Student '{key}' not in {CFG}")
    first = st.get("first_name", key)
    email = st.get("email", "")
    if not email:
        raise SystemExit(f"No email for {key}")
    forms = load_forms()
    subject = f"Welcome to Montefiore Urology!"
    html = build_html(first, cfg, st, forms)
    # Build attachment paths (only the 6 non-form docs)
    attach_paths = []
    for fname, label in ATTACH:
        p = DOCS / fname
        if p.exists():
            attach_paths.append(str(p))
    run_gate_draft(email, subject, html, attach_paths)


def do_list(cfg):
    for k, st in (cfg.get("students") or {}).items():
        print(f"{k:24} {st.get('first_name',''):12} {st.get('email',''):35} "
              f"rot {st.get('rotation_start')} - {st.get('rotation_end')}  "
              f"{'WELCOME-ON' if st.get('welcome') else 'no'}")
    print(f"\n{len((cfg.get('students') or {}))} students configured")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--student")
    ap.add_argument("--draft", action="store_true")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    cfg = load()
    if a.list:
        do_list(cfg)
    elif a.student:
        do_student(a.student, cfg)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
