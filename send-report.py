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

# Data source: the UNIFIED reimbursement DB (authoritative). Legacy SQLite
# reader is no longer used.
from unified_reimbursement_data import get_resident_data as _unified_get_resident_data

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

def get_resident_data(resident_name, year=None):
    """Get all transactions and summary for a resident from the UNIFIED DB."""
    data = _unified_get_resident_data(resident_name, year)
    if data is None:
        return None
    # Front-end expects 'academic_year' label via data['academic_year_label'];
    # keep the legacy keys the HTML/PDF builders use.
    data.setdefault("by_account", {})
    data.setdefault("txns", [])
    return data


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
    # Header reflects the requested scope (specific AY or "All Years")
    pdf_req = data.get('requested_year')
    pdf_header = pdf_req if pdf_req else ("All Years" if data.get('years') else f"{ay_start}&ndash;{ay_end}")
    elements.append(Paragraph(f"Academic Year {pdf_header}", s_sub))
    
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
    
    # Transaction table — grouped by academic year (newest first) with a
    # per-year header row, so multi-year summaries are clearly separated.
    grouped_pdf = data.get('grouped_txns') or {}
    years_pdf = data.get('years') or []
    if not grouped_pdf and data.get('txns'):
        grouped_pdf = {'': data['txns']}
        years_pdf = ['']
    per_year_totals = data.get('per_year_totals') or {}

    txn_header = [[
        Paragraph("<b>Date</b>", s_acct),
        Paragraph("<b>Description</b>", s_acct),
        Paragraph("<b>Account</b>", s_acct),
        Paragraph("<b>Amount</b>", ParagraphStyle('AmtHdr', parent=s_acct, alignment=TA_RIGHT)),
    ]]
    txn_rows = []
    for ay in years_pdf:
        rows = grouped_pdf.get(ay, [])
        if not rows:
            continue
        ay_label = ay or 'NO DATE'
        ay_total = per_year_totals.get(ay, sum(r['amount'] for r in rows))
        # Year header row (spanning all 4 columns)
        txn_rows.append([
            Paragraph(f"<b>{ay_label}</b>", ParagraphStyle('AYHdr', parent=s_acct, fontSize=10, textColor=HexColor('#1a3a5c'))),
            Paragraph("", s_acct),
            Paragraph("", s_acct),
            Paragraph(f"<b>${ay_total:,.2f}</b>", ParagraphStyle('AYTot', parent=s_right, fontSize=10, textColor=HexColor('#1a3a5c'))),
        ])
        for t in rows:
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
            ('BACKGROUND', (0, 1), (-1, -1), HexColor('#ffffff')),
            ('GRID', (0, 0), (-1, -1), 0.25, HexColor('#e0e4e8')),
            ('LINEBEFORE', (0, 0), (0, -1), 0, HexColor('#ffffff')),
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


def send_individual(resident_name, recipient, year=None):
    """Send individual resident reimbursement email with PDF attachment (SMTP).

    `year` optionally filters to a single academic year (e.g. '2025-26');
    None/'all' returns all years grouped by AY.
    """
    from modules.smtp_sender import send_email_smart
    
    greeting = get_greeting()
    data = get_resident_data(resident_name, year)
    
    if not data:
        return f"❌ Resident '{resident_name}' not found"
    
    remaining_color = '#2e7d32' if data['gme_pct'] < 50 else '#e65100' if data['gme_pct'] < 80 else '#c62828'
    
    now = datetime.now()
    ay_start = now.year if now.month >= 7 else now.year - 1
    ay_end = now.year + 1 if now.month >= 7 else now.year

    # Header AY label: specific requested year, else "All Years" (grouped).
    req_year = data.get('requested_year')
    ay_header = req_year if req_year else "All Years"
    # For the subject/body we also keep the full-year form when requested.
    ay_label_full = f"{int(req_year[:4])}-{int(req_year[:4])+1}" if req_year and '-' in req_year else req_year
    
    # Transaction table — grouped by academic year (newest first) for clarity,
    # with a per-year total line. If a specific year was requested, only one
    # group shows.
    grouped = data.get('grouped_txns') or {}
    years = data.get('years') or []
    if not grouped and data.get('txns'):
        # fallback to flat
        grouped = {'': data['txns']}
        years = ['']
    per_year_totals = data.get('per_year_totals') or {}

    table_rows = ""
    for ay in years:
        rows = grouped.get(ay, [])
        if not rows:
            continue
        ay_label = ay or 'NO DATE'
        table_rows += (f"<tr><td colspan=\"4\" style=\"padding:8px 6px 4px 6px;"
                       f"font-family:Georgia,'Times New Roman',serif;font-size:10pt;font-weight:bold;"
                       f"color:#1a3a5c;border-bottom:1px solid #d0d4d8\">"
                       f"{ay_label} &mdash; ${per_year_totals.get(ay, sum(r['amount'] for r in rows)):,.2f}</td></tr>")
        for t in rows:
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
        <td style="padding:0 28px 6px 28px;font-family:Georgia,'Times New Roman',serif;font-size:10pt;color:#888">Academic Year {ay_header}</td>
      </tr>
      <tr><td style="padding:0 28px"><hr style="border:none;border-top:1px solid #d0d4d8;margin:0"></td></tr>
      <tr>
        <td style="padding:14px 28px 0 28px">
          <p style="margin:0 0 4px 0;font-family:Times New Roman,Georgia,serif;font-size:12pt;color:#333;line-height:1.5">{greeting} {data['name'].split()[0]},</p>
          <p style="margin:0 0 12px 0;font-family:Times New Roman,Georgia,serif;font-size:11pt;color:#333;line-height:1.5">Below is your reimbursement summary{(' for the ' + ay_header + ' academic year') if req_year else ' across all academic years'}.</p>
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

    # Subject reflects the requested scope: specific AY or all years.
    subj_year = req_year if req_year else ("All Years" if data.get('years') else data.get('academic_year_label', ''))
    result = send_email_smart(
        to=recipient,
        subject=f"Montefiore Urology — Reimbursement Summary ({data['name']}) — AY {subj_year}",
        body=html,
        attachments=[pdf_path],
        is_html=True,
    )

    # Clean up temp PDF
    try:
        os.unlink(pdf_path)
    except Exception:
        pass

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
