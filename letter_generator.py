#!/usr/bin/env python3
"""
Resident Letter Generator — Good Standing & Income Verification
Pulls resident data from CRM, fills HTML templates, outputs PDF-ready letters.

Usage:
  python3 letter_generator.py --type good-standing --resident-id <id> --recipient "Dr. Smith" --institution "MSK"
  python3 letter_generator.py --type income --resident-id <id>
  python3 letter_generator.py --list-residents
"""

import os, sys, json, argparse
from datetime import datetime, date

# ── PGY Salary Table (2025-2026 academic year) ─────────────
PGY_SALARY = {
    "PG-1": 82000,
    "PG-2": 85000,
    "PG-3": 88000,
    "PG-4": 92000,
    "PG-5": 96000,
    "PG-6": 100000,
    "PG-7": 104000,
}

# ── Letterhead HTML ────────────────────────────────────────
LETTERHEAD = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><style>
  body { font-family: 'Times New Roman', Georgia, serif; color: #111; max-width: 700px; margin: 40px auto; padding: 0 20px; line-height: 1.5; }
  .letterhead { text-align: center; border-bottom: 2px solid #1a3a5c; padding-bottom: 16px; margin-bottom: 28px; }
  .letterhead h1 { font-size: 18px; color: #1a3a5c; margin: 0 0 2px 0; letter-spacing: 1px; }
  .letterhead h2 { font-size: 13px; color: #1a3a5c; margin: 0 0 4px 0; font-weight: normal; }
  .letterhead p { font-size: 11px; color: #555; margin: 2px 0; }
  .letterhead .contact { font-size: 11px; color: #555; margin-top: 6px; }
  .date { margin-bottom: 20px; font-size: 12px; }
  .re { font-weight: bold; margin-bottom: 16px; font-size: 12px; }
  .body { font-size: 12px; }
  .body p { margin: 10px 0; }
  .signature { margin-top: 40px; }
  .signature .name { font-weight: bold; }
  .signature .title { font-size: 11px; color: #444; }
  .footer { margin-top: 30px; border-top: 1px solid #ccc; padding-top: 8px; font-size: 9px; color: #888; }
</style></head>
<body>
<div class="letterhead">
  <h1>Department of Urology Residency Program</h1>
  <h2>Montefiore Medical Center</h2>
  <p>The University Hospital for Albert Einstein College of Medicine</p>
  <p>1250 Waters Place, Tower I, Penthouse &bull; Bronx, N.Y. 10461</p>
  <p class="contact">347.842.1724 &bull; 917.962.5410 fax</p>
  <p class="contact">Alex Sankin, M.D., Program Director &bull; asankin@montefiore.org</p>
  <p class="contact">Shareef Frasier, Program Administrator &bull; sfrasier@montefiore.org</p>
</div>
"""

FOOTER_HTML = """
<div class="footer">
  Montefiore Medical Center &bull; The University Hospital for Albert Einstein College of Medicine<br>
  1250 Waters Place, Tower One, PH-2, Bronx, NY 10461 &bull; 347-842-1724 Office &bull; 917-962-5410 Fax
</div>
</body></html>
"""


def load_resident(resident_id=None, email=None):
    """Load resident data from CRM via API or fallback JSON."""
    # Try API first
    try:
        import urllib.request
        if resident_id:
            url = f"http://127.0.0.1:8090/api/crm/contacts/{resident_id}"
        else:
            url = "http://127.0.0.1:8090/api/crm/contacts"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            contacts = data.get("contacts", [data] if isinstance(data, dict) else [])
            if email:
                contacts = [c for c in contacts if c.get("email", "").lower() == email.lower()]
            return contacts if not resident_id else (contacts[0] if contacts else None)
    except Exception as e:
        print(f"CRM API unavailable: {e}", file=sys.stderr)

    # Fallback: try JSON file
    fallback_paths = [
        "/workspace/agentic-os/data/crm_contacts.json",
        "/workspace/agentic-os/data/crm_contacts.fallback.json",
    ]
    for fp in fallback_paths:
        if os.path.exists(fp):
            with open(fp) as f:
                contacts = json.load(f)
                if isinstance(contacts, list):
                    if email:
                        contacts = [c for c in contacts if c.get("email", "").lower() == email.lower()]
                    if resident_id:
                        contacts = [c for c in contacts if c.get("id") == resident_id]
                    return contacts
    return []


def list_residents():
    """List all active residents with PGY info."""
    contacts = load_resident()
    residents = [c for c in contacts if c.get("category") == "Resident" and not c.get("archived")]
    print(f"\n{'Name':<30} {'PGY':<8} {'Start':<12} {'Grad':<8} {'Email'}")
    print("-" * 90)
    for r in sorted(residents, key=lambda x: (x.get("lastName", ""), x.get("firstName", ""))):
        name = f"{r.get('firstName','')} {r.get('lastName','')}"
        pgy = r.get("pgy", "?")
        start = r.get("programStart", "?")
        grad = r.get("graduationYear", "?")
        email = r.get("email", "")
        print(f"{name:<30} {pgy:<8} {start:<12} {grad:<8} {email}")
    print(f"\n{len(residents)} active residents")
    return residents


def get_salary(pgy):
    """Get annual salary for a PGY level."""
    return PGY_SALARY.get(pgy, 0)


def format_currency(amount):
    return f"${amount:,}"


def format_date(d):
    """Format date as 'July 1, 2024'"""
    if isinstance(d, str):
        for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%B %d, %Y"]:
            try:
                d = datetime.strptime(d, fmt)
                break
            except ValueError:
                continue
    if isinstance(d, datetime):
        return d.strftime("%B %d, %Y")
    return str(d)


def pgy_to_text(pgy):
    """Convert 'PG-2' to 'Post-Graduate Year 2 (PGY-2)'"""
    if not pgy:
        return "a resident physician"
    num = pgy.replace("PG-", "").replace("PGY-", "").strip()
    return f"Post-Graduate Year {num} (PGY-{num})"


def build_good_standing_letter(resident, recipient_name, recipient_title="Dr.", institution=""):
    """Build Letter of Good Standing HTML."""
    first = resident.get("firstName", "")
    last = resident.get("lastName", "")
    full_name = f"{first} {last}, MD"
    pgy = resident.get("pgy", "")
    pgy_text = pgy_to_text(pgy)
    start_raw = resident.get("programStart", resident.get("urologyStart", "July 1, 2024"))
    start_date = format_date(start_raw)
    grad_year = resident.get("graduationYear", "2029")
    grad_date = f"June 30, {grad_year}"

    today = date.today().strftime("%B %d, %Y")

    body = f"""
<div class="date">{today}</div>
<div class="re">RE: {first} {last}, MD</div>
<div class="body">
<p>Dear {recipient_title} {recipient_name},</p>
<p>Please be advised that {full_name}, {pgy_text} is currently in the Urology
Residency Training Program at Montefiore Medical Center. He was credentialed by
the Montefiore House Staff office prior to joining residency on {start_date}. {last}'s
anticipated graduation date from the program is {grad_date}.</p>
<p>Please let me know if any further information is needed to complete credentialing for
{institution}.</p>
<p>Thank you,</p>
</div>
"""

    if institution:
        body = body.replace("{institution}", institution)
    else:
        body = body.replace("to complete credentialing for\n{institution}.", "to complete the credentialing process.")

    sig = """
<div class="signature">
<p class="name">Alex Sankin, MD</p>
<p class="title">Department of Urology<br>
Residency Program Director<br>
Department of Urology<br>
Residency Program</p>
</div>
"""
    return LETTERHEAD + body + sig + FOOTER_HTML


def build_income_verification_letter(resident):
    """Build Employment & Income Verification Letter HTML."""
    first = resident.get("firstName", "")
    last = resident.get("lastName", "")
    full_name = f"{first} {last}"
    pgy = resident.get("pgy", "")
    pgy_text = pgy_to_text(pgy)
    start_raw = resident.get("programStart", resident.get("urologyStart", "July 1, 2024"))
    start_date = format_date(start_raw)
    grad_year = resident.get("graduationYear", "2029")
    grad_date = f"June 30, {grad_year}"
    salary = get_salary(pgy)
    salary_text = format_currency(salary) if salary else "[salary not available]"

    today = date.today().strftime("%B %d, %Y")

    body = f"""
<div class="date">Date: {today}</div>
<div class="re">Re: Employment and Income Verification for {full_name}</div>
<div class="body">
<p>To Whom It May Concern,</p>
<p>This letter is to verify the employment and income of Mr. {full_name}, who is currently a resident
physician in the Urology Residency Program at Montefiore Hospital.</p>
<p>Mr. {last} holds the position of {pgy_text} Urology Resident in our ACGME-
accredited Urology Residency Program. His residency training in this program began on {start_date},
and is scheduled to continue through {grad_date}.</p>
<p>Mr. {last} is employed on a full-time basis and receives an annual salary of {salary_text}. This position
is a structured graduate medical education role with ongoing funding administered through
Montefiore's Graduate Medical Education (GME) system.</p>
<p>If you require any additional information or wish to verify the details in this letter, please feel
free to contact our office:</p>
<p>Thank You</p>
</div>
"""

    sig = """
<div class="signature">
<p class="name">Alex Sankin, M.D.</p>
<p class="title">Program Director, Urology Residency<br>
Director, Clinical Trials Program<br>
Professor and Attending Physician<br>
Department of Urology<br>
Montefiore Medical Center</p>
</div>
"""
    return LETTERHEAD + body + sig + FOOTER_HTML


def main():
    parser = argparse.ArgumentParser(description="Generate resident letters")
    parser.add_argument("--type", choices=["good-standing", "income"], help="Letter type")
    parser.add_argument("--resident-id", help="CRM contact ID")
    parser.add_argument("--email", help="Find resident by email")
    parser.add_argument("--name", help="Find resident by name (partial match)")
    parser.add_argument("--recipient", help="Recipient name (for good-standing letter)")
    parser.add_argument("--recipient-title", default="Dr.", help="Recipient title")
    parser.add_argument("--institution", default="", help="Institution name (for good-standing letter)")
    parser.add_argument("--output", help="Output HTML file path")
    parser.add_argument("--list-residents", action="store_true", help="List all residents")
    parser.add_argument("--salary-table", action="store_true", help="Show PGY salary table")
    args = parser.parse_args()

    if args.salary_table:
        print("\nPGY Salary Table (2025-2026):")
        for pgy, sal in sorted(PGY_SALARY.items()):
            print(f"  {pgy}: ${sal:,}")
        return

    if args.list_residents:
        list_residents()
        return

    if not args.type:
        parser.error("--type required (good-standing or income)")

    # Find resident
    contacts = load_resident(resident_id=args.resident_id, email=args.email)
    if args.name:
        contacts = [c for c in contacts if args.name.lower() in
                    f"{c.get('firstName','')} {c.get('lastName','')}".lower()]
    if not contacts:
        print("No resident found. Use --list-residents to see available residents.")
        sys.exit(1)
    if len(contacts) > 1:
        print(f"Multiple matches ({len(contacts)}). Use --resident-id or --email to narrow down:")
        for c in contacts[:10]:
            print(f"  {c.get('id','?')}: {c.get('firstName','')} {c.get('lastName','')} ({c.get('pgy','?')})")
        sys.exit(1)

    resident = contacts[0] if isinstance(contacts, list) else contacts

    # Generate letter
    if args.type == "good-standing":
        if not args.recipient:
            parser.error("--recipient required for good-standing letter")
        html = build_good_standing_letter(
            resident, args.recipient, args.recipient_title, args.institution)
        filename = f"good_standing_{resident.get('lastName','')}_{resident.get('firstName','')}.html"
    else:
        html = build_income_verification_letter(resident)
        filename = f"income_verification_{resident.get('lastName','')}_{resident.get('firstName','')}.html"

    outpath = args.output or os.path.join("/workspace/agentic-os/data/letters", filename)
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    with open(outpath, "w") as f:
        f.write(html)

    print(f"✅ Letter saved to: {outpath}")
    print(f"   Resident: {resident.get('firstName','')} {resident.get('lastName','')}, {resident.get('pgy','?')}")
    if args.type == "good-standing":
        print(f"   Recipient: {args.recipient_title}. {args.recipient}")
    else:
        print(f"   Salary: {format_currency(get_salary(resident.get('pgy','')))}")


if __name__ == "__main__":
    main()
