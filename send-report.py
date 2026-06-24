#!/usr/bin/env python3
"""
Send Montefiore Urology reimbursement emails via Gmail OAuth.
Pulls data from reimbursement.db (synced from xlsx twice daily).
Shows all transactions across all funding accounts. Donation → MISC.

Usage:
  python3 send-report.py --resident "Ariel Allen" --email sfrasier@montefiore.org
"""
import os, sys, json, yaml, sqlite3
from datetime import datetime, timezone
from pathlib import Path
from collections import OrderedDict, defaultdict
import openpyxl
import re

sys.path.insert(0, os.path.expanduser("~/.hermes/home/.local/lib/python3.12/site-packages"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

DEFAULT_RECIPIENT = "sfrasier@montefiore.org"

# Database path
DB_PATH = Path("/workspace/repos/reimbursement/reimbursement.db")

SIG_BLOCK = ""
_CONFIG_PATH = Path.home() / ".hermes" / "email_accounts.yaml"
if _CONFIG_PATH.exists():
    try:
        _config = yaml.safe_load(_CONFIG_PATH.read_text())
        _accts = (_config or {}).get('accounts', {})
        _sigs = [v.get('signature_html', '') for v in _accts.values() if v.get('signature_html')]
        if _sigs:
            SIG_BLOCK = _sigs[0]
    except Exception:
        pass

ACCT_MAP = {
    'GME Funds': 'GME Funds',
    'Teaching Funds': 'Teaching Funds',
    'Dept Funds': 'Dept Funds',
    'Donation Funds': 'MISC',
    'Sleep Deprivation': 'Sleep Deprivation',
}

def get_greeting():
    et = datetime.now(timezone.utc).astimezone()
    h = et.hour
    return "Good Morning" if h < 12 else "Good Afternoon" if h < 17 else "Good Evening"

def get_resident_data(resident_name):
    """Get all transactions and summary for a resident from the DB."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    
    # Find person
    name_lower = resident_name.lower().replace(' ', '').replace(',', '')
    cur = conn.execute("SELECT id, name, cls FROM persons")
    person = None
    for row in cur.fetchall():
        rn = str(row['name']).lower().replace(' ', '').replace(',', '')
        if rn == name_lower or name_lower in rn or rn in name_lower:
            person = dict(row)
            break
        # Double letter normalization
        if rn.replace('ll', 'l') == name_lower.replace('ll', 'l'):
            person = dict(row)
            break
    
    if not person:
        conn.close()
        return None
    
    # Get all approved allocations for this person — prefer sync'd data
    # Sync creates entries with al_xlsx_ prefix; old seed data uses al_r_ or al_k_ prefix
    cur = conn.execute("""
        SELECT amount, account, description, created_at
        FROM allocations
        WHERE beneficiary_id = ?
          AND status = 'approved'
          AND id LIKE 'al_xlsx_%'
        ORDER BY created_at
    """, (person['id'],))
    
    raw_allocations = [dict(r) for r in cur.fetchall()]
    
    # Fallback: if no sync'd data, read everything
    if not raw_allocations:
        cur = conn.execute("""
            SELECT amount, account, description, created_at
            FROM allocations
            WHERE beneficiary_id = ?
              AND status = 'approved'
            ORDER BY created_at
        """, (person['id'],))
        raw_allocations = [dict(r) for r in cur.fetchall()]
    
    conn.close()
    
    # Map accounts and build transactions
    txns = []
    gme_total = 0
    by_account = defaultdict(float)
    
    for a in raw_allocations:
        acct = ACCT_MAP.get(a['account'], a['account'])
        amt = float(a['amount'] or 0)
        if amt <= 0:
            continue
        
        date_str = str(a['created_at'])[:10] if a['created_at'] else ''
        desc = str(a['description'] or '').strip()
        
        txns.append({
            'date': date_str,
            'description': desc,
            'amount': amt,
            'account': acct,
        })
        by_account[acct] += amt
        if acct == 'GME Funds':
            gme_total += amt
    
    # Sort by date
    txns.sort(key=lambda t: t['date'])
    
    gme_remaining = max(0, 1250 - gme_total)
    gme_pct = min(100, round((gme_total / 1250) * 100, 1))
    
    return {
        'name': person['name'],
        'cls': person.get('cls', ''),
        'txns': txns,
        'by_account': dict(by_account),
        'grand_total': sum(t['amount'] for t in txns),
        'gme_used': gme_total,
        'gme_remaining': gme_remaining,
        'gme_pct': gme_pct,
    }


def generate_pdf(data):
    """Generate a matching PDF for the reimbursement summary."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    import tempfile
    
    remaining_color = '#2e7d32' if data['gme_pct'] < 50 else '#e65100' if data['gme_pct'] < 80 else '#c62828'
    
    pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
    pdf_path = pdf.name
    pdf.close()
    
    doc = SimpleDocTemplate(
        pdf_path, pagesize=letter,
        topMargin=0.6*inch, bottomMargin=0.6*inch,
        leftMargin=0.6*inch, rightMargin=0.6*inch,
    )
    
    styles = getSampleStyleSheet()
    s_title = ParagraphStyle('Title', parent=styles['Title'],
        textColor=HexColor('#1a3a5c'), fontSize=18, spaceAfter=2,
        fontName='Helvetica-Bold')
    s_sub = ParagraphStyle('Sub', parent=styles['Normal'],
        textColor=HexColor('#666666'), fontSize=10, spaceAfter=16)
    s_h2 = ParagraphStyle('H2', parent=styles['Heading2'],
        textColor=HexColor('#1a3a5c'), fontSize=13, spaceBefore=12, spaceAfter=6,
        fontName='Helvetica-Bold')
    s_body = ParagraphStyle('Body', parent=styles['Normal'],
        textColor=HexColor('#333333'), fontSize=9, leading=13, spaceAfter=4)
    s_green = ParagraphStyle('Green', parent=s_body,
        textColor=HexColor('#2e7d32'), fontSize=9, fontName='Helvetica-Bold')
    s_right = ParagraphStyle('Right', parent=s_body,
        alignment=TA_RIGHT, fontSize=9)
    s_acct = ParagraphStyle('Acct', parent=s_body,
        textColor=HexColor('#888888'), fontSize=8)
    
    elements = []
    
    # Header bar
    hdr = Table(
        [[Paragraph("<b>Montefiore Einstein Urology</b>", ParagraphStyle('Hdr', parent=s_title, fontSize=14, alignment=TA_LEFT)),
          Paragraph(data['name'], ParagraphStyle('HdrDate', parent=s_sub, fontSize=12, textColor=HexColor('#ffffff'), alignment=TA_RIGHT))]],
        colWidths=[4.3*inch, 3*inch]
    )
    hdr.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#1a3a5c')),
        ('TEXTCOLOR', (0, 0), (-1, -1), HexColor('#ffffff')),
        ('LEFTPADDING', (0, 0), (0, 0), 14),
        ('RIGHTPADDING', (-1, -1), (-1, -1), 14),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(hdr)
    elements.append(Spacer(1, 12))
    
    elements.append(Paragraph("<b>Reimbursement Summary</b>", s_h2))
    now = datetime.now()
    ay_start = now.year if now.month >= 7 else now.year - 1
    ay_end = now.year + 1 if now.month >= 7 else now.year
    elements.append(Paragraph(f"Academic Year {ay_start}&ndash;{ay_end}", s_sub))
    
    # GME Status card
    gme_data = [[
        Paragraph(f"<b>GME Status</b><br/>{'${:,.2f}'.format(data['gme_remaining'])} remaining of $1,250<br/>{data['gme_pct']:.0f}% used",
            ParagraphStyle('GMECell', parent=s_body, fontSize=9, alignment=TA_CENTER, textColor=HexColor('#333'))),
        Paragraph(f"<b>Account Totals</b><br/>" + "<br/>".join(
            f"{acct}: ${total:,.2f}" for acct, total in sorted(data['by_account'].items())
        ) + f"<br/><b>Total: ${data['grand_total']:,.2f}</b>",
            ParagraphStyle('AcctCell', parent=s_body, fontSize=9, alignment=TA_RIGHT, textColor=HexColor('#333'))),
    ]]
    gme_table = Table(gme_data, colWidths=[3.2*inch, 3.2*inch])
    gme_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f4f6f9')),
        ('BOX', (0, 0), (-1, -1), 0.5, HexColor('#d0d7de')),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, HexColor('#d0d7de')),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(gme_table)
    elements.append(Spacer(1, 12))
    
    # Transaction table
    txn_header = [[
        Paragraph("<b>Date</b>", s_acct),
        Paragraph("<b>Description</b>", s_acct),
        Paragraph("<b>Account</b>", s_acct),
        Paragraph("<b>Amount</b>", ParagraphStyle('AmtHdr', parent=s_acct, alignment=TA_RIGHT)),
    ]]
    txn_rows = []
    for t in data['txns']:
        txn_rows.append([
            Paragraph(t['date'][:10], s_body),
            Paragraph(t['description'][:50], s_body),
            Paragraph(t['account'], s_acct),
            Paragraph(f"${t['amount']:,.2f}", s_right),
        ])
    
    if txn_rows:
        txn_table = Table(txn_header + txn_rows, colWidths=[0.9*inch, 3.3*inch, 1.0*inch, 1.0*inch])
        txn_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#f4f6f9')),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#555555')),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, -1), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.25, HexColor('#e0e4e8')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(txn_table)
    
    # Footer
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(
        "<i>Reimbursements tracked in USD per academic year (July 1 &ndash; June 30). Generated by Hermes Agent.</i>",
        ParagraphStyle('Footer', parent=s_body, textColor=HexColor('#999999'), fontSize=7, alignment=TA_CENTER)
    ))
    
    doc.build(elements)
    return pdf_path


def send_individual(resident_name, recipient):
    """Send individual resident reimbursement email with PDF attachment."""
    from google_workspace import GoogleWorkspace
    
    greeting = get_greeting()
    data = get_resident_data(resident_name)
    
    if not data:
        return f"❌ Resident '{resident_name}' not found"
    
    remaining_color = '#2e7d32' if data['gme_pct'] < 50 else '#e65100' if data['gme_pct'] < 80 else '#c62828'
    
    now = datetime.now()
    ay_start = now.year if now.month >= 7 else now.year - 1
    ay_end = now.year + 1 if now.month >= 7 else now.year
    
    # Transaction table
    table_rows = ""
    for t in data['txns']:
        table_rows += f"""
    <tr>
      <td style="padding:4px 6px;border-bottom:1px solid #e8e8e8;font-family:Georgia,'Times New Roman',serif;font-size:9pt;color:#555;width:75px">{t['date']}</td>
      <td style="padding:4px 6px;border-bottom:1px solid #e8e8e8;font-family:Georgia,'Times New Roman',serif;font-size:9pt;color:#555">{t['description'][:50]}</td>
      <td style="padding:4px 6px;border-bottom:1px solid #e8e8e8;font-family:Georgia,'Times New Roman',serif;font-size:9pt;color:#888;width:80px">{t['account']}</td>
      <td style="padding:4px 6px;border-bottom:1px solid #e8e8e8;font-family:Georgia,'Times New Roman',serif;font-size:9pt;color:#555;text-align:right;width:75px">${t['amount']:,.2f}</td>
    </tr>"""
    
    # Account totals
    acct_rows = ""
    for acct, total in sorted(data['by_account'].items()):
        acct_rows += f"""
    <tr>
      <td style="padding:3px 6px;font-family:Georgia,'Times New Roman',serif;font-size:9pt;color:#555;text-align:right">{acct}:</td>
      <td style="padding:3px 6px;font-family:Georgia,'Times New Roman',serif;font-size:9pt;color:#1a3a5c;text-align:right;font-weight:bold">${total:,.2f}</td>
    </tr>"""
    
    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background-color:#f0f2f5;font-family:'Times New Roman',Georgia,serif">
<table cellpadding="0" cellspacing="0" width="100%" style="background-color:#f0f2f5">
  <tr><td style="padding:30px 10px" align="center">
    <table cellpadding="0" cellspacing="0" style="max-width:620px;width:100%;background-color:#ffffff;border-radius:4px;box-shadow:0 1px 3px rgba(0,0,0,0.08)">
      <tr>
        <td style="background-color:#1a3a5c;border-radius:4px 4px 0 0;padding:18px 28px">
          <table cellpadding="0" cellspacing="0" width="100%">
            <tr>
              <td style="font-family:Georgia,'Times New Roman',serif;font-size:16pt;font-weight:bold;color:#ffffff">Montefiore Einstein Urology</td>
              <td style="font-family:Georgia,'Times New Roman',serif;font-size:9pt;color:#b0c4de;text-align:right;vertical-align:bottom">{now.strftime('%B %d, %Y')}</td>
            </tr>
          </table>
        </td>
      </tr>
      <tr>
        <td style="padding:16px 28px 0 28px">
          <table cellpadding="0" cellspacing="0" width="100%">
            <tr>
              <td style="font-family:Georgia,'Times New Roman',serif;font-size:16pt;font-weight:bold;color:#1a3a5c">Reimbursement Summary</td>
              <td style="font-family:Georgia,'Times New Roman',serif;font-size:10pt;color:#888;text-align:right;vertical-align:bottom">{data['name']}</td>
            </tr>
          </table>
        </td>
      </tr>
      <tr>
        <td style="padding:0 28px 6px 28px;font-family:Georgia,'Times New Roman',serif;font-size:10pt;color:#888">Academic Year {ay_start}&ndash;{ay_end}</td>
      </tr>
      <tr><td style="padding:0 28px"><hr style="border:none;border-top:1px solid #d0d4d8;margin:0"></td></tr>
      <tr>
        <td style="padding:14px 28px 0 28px">
          <p style="margin:0 0 4px 0;font-family:Times New Roman,Georgia,serif;font-size:12pt;color:#333;line-height:1.5">{greeting} {data['name'].split()[0]},</p>
          <p style="margin:0 0 12px 0;font-family:Times New Roman,Georgia,serif;font-size:11pt;color:#333;line-height:1.5">Below is your full reimbursement summary for the {ay_start}&ndash;{ay_end} academic year.</p>
        </td>
      </tr>
      <tr>
        <td style="padding:0 28px">
          <table cellpadding="0" cellspacing="0" width="100%">
            <tr>
              <td style="width:50%;padding-right:6px;vertical-align:top">
                <table cellpadding="0" cellspacing="0" width="100%" style="background-color:#f4f6f9;border:1px solid #e0e4e8;border-radius:4px">
                  <tr>
                    <td style="padding:10px 12px;text-align:center;font-family:Georgia,'Times New Roman',serif;font-size:9pt;color:#555">
                      <div style="font-size:8pt;color:#888;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px">GME Status</div>
                      <div style="font-size:16pt;font-weight:bold;color:{remaining_color}">${data['gme_remaining']:,.2f}</div>
                      <div style="font-size:8pt;color:#888">remaining of $1,250</div>
                      <div style="height:4px;background:#e8e8e8;border-radius:2px;margin:6px 0 2px"><div style="height:4px;width:{data['gme_pct']:.0f}%;background:{'#2e7d32' if data['gme_pct'] < 50 else '#e65100' if data['gme_pct'] < 80 else '#c62828'};border-radius:2px"></div></div>
                      <div style="font-size:7pt;color:#999">{data['gme_pct']:.0f}% used</div>
                    </td>
                  </tr>
                </table>
              </td>
              <td style="width:50%;padding-left:6px;vertical-align:top">
                <table cellpadding="0" cellspacing="0" width="100%" style="background-color:#f4f6f9;border:1px solid #e0e4e8;border-radius:4px">
                  <tr>
                    <td style="padding:8px 12px">
                      <table cellpadding="0" cellspacing="0" width="100%">
                        {acct_rows}
                        <tr>
                          <td style="padding:4px 6px 0 6px;border-top:2px solid #1a3a5c;font-family:Georgia,'Times New Roman',serif;font-size:9pt;color:#1a3a5c;text-align:right;font-weight:bold">Total:</td>
                          <td style="padding:4px 6px 0 6px;border-top:2px solid #1a3a5c;font-family:Georgia,'Times New Roman',serif;font-size:9pt;color:#1a3a5c;text-align:right;font-weight:bold">${data['grand_total']:,.2f}</td>
                        </tr>
                      </table>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
          </table>
        </td>
      </tr>
      <tr>
        <td style="padding:12px 28px 0 28px">
          <table cellpadding="0" cellspacing="0" width="100%" style="border-collapse:collapse">
            <tr style="color:#888;font-size:8pt;font-family:Georgia,'Times New Roman',serif">
              <td style="padding:4px 6px;border-bottom:2px solid #d0d4d8;width:75px;font-weight:bold">Date</td>
              <td style="padding:4px 6px;border-bottom:2px solid #d0d4d8;font-weight:bold">Description</td>
              <td style="padding:4px 6px;border-bottom:2px solid #d0d4d8;width:80px;font-weight:bold">Account</td>
              <td style="padding:4px 6px;border-bottom:2px solid #d0d4d8;text-align:right;width:75px;font-weight:bold">Amount</td>
            </tr>
            {table_rows}
          </table>
        </td>
      </tr>
      <tr>
        <td style="padding:8px 28px 4px 28px">
          <p style="margin:10px 0 0;font-family:Times New Roman,Georgia,serif;font-size:9pt;color:#999;line-height:1.4">Reimbursements tracked in USD per academic year (July 1 &ndash; June 30). Account names may be abbreviated.</p>
        </td>
      </tr>
      <tr>
        <td style="padding:10px 28px 24px 28px">
          <hr style="border:none;border-top:1px solid #ddd;margin:0 0 10px 0">
          {SIG_BLOCK}
        </td>
      </tr>
    </table>
    <table cellpadding="0" cellspacing="0" style="max-width:620px;width:100%;padding-top:10px">
      <tr><td style="font-family:Arial,Helvetica,sans-serif;font-size:8pt;color:#aaa;text-align:center">Montefiore Urology &bull; 1250 Waters Place &bull; Bronx, NY 10461</td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>"""

    # Generate PDF
    pdf_path = generate_pdf(data)

    ws = GoogleWorkspace()
    result = ws.send_email(
        user_id="urologyresidency",
        to=recipient,
        subject=f"Montefiore Urology — Reimbursement Summary ({data['name']}) — AY {ay_start}-{ay_end}",
        body=html,
        attachments=[pdf_path],
        from_email="sfrasier@montefiore.org",
        is_html=True,
    )

    if result.get("successful"):
        return f"✅ Sent to {recipient}"
    else:
        return f"❌ Failed: {json.dumps(result, indent=2, default=str)[:300]}"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--resident", required=True)
    parser.add_argument("--email", default=DEFAULT_RECIPIENT)
    args = parser.parse_args()
    
    print(f"\n📧 Sending reimbursement summary for {args.resident} to {args.email}...")
    result = send_individual(args.resident, args.email)
    print(f"  {result}")
