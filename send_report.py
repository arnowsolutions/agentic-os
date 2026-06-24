#!/usr/bin/env python3
"""
Send Montefiore Urology reports via Gmail OAuth with PDF attachment.

This module is the engine behind send-report.py. It can render emails from:
  1. A structured report_data dict (preferred, uses the templates in
     email_templates/).
  2. A legacy free-text summary (kept for one-off CLI use).

Usage from another script:
    from send_report import send
    send('gme', report_data, pdf_path, 'sfrasier@montefiore.org',
         recipient_name='Shareef')

CLI wrapper:
    python3 send-report.py --pdf /path/to/report.pdf --type gme \
        --data /path/to/report_data.json --email sfrasier@montefiore.org
"""

import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# Add /workspace so we can import google_workspace
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from google_workspace import GoogleWorkspace

DEFAULT_RECIPIENT = "sfrasier@montefiore.org"

REPORT_NAMES = {
    'gme': 'GME Reimbursement Report',
    'coverage': 'Coverage Gap Analysis',
    'absences': 'Absence Summary Report',
    'full': 'Consolidated Operations Report',
}

TEMPLATE_FILES = {
    'gme': 'gme_reimbursement_email.html',
    'coverage': 'coverage_gap_email.html',
    'absences': 'absence_summary_email.html',
    'full': 'consolidated_operations_email.html',
}

TEMPLATE_DIR = Path(__file__).resolve().parent / 'email_templates'

SIG_BLOCK: str = ""

# Load signature from email config
_CONFIG_PATH = Path.home() / ".hermes" / "email_accounts.yaml"
if _CONFIG_PATH.exists():
    try:
        import yaml
        _config = yaml.safe_load(_CONFIG_PATH.read_text())
        _accts = (_config or {}).get('accounts', {})
        _sigs = [v.get('signature_html', '') for v in _accts.values() if v.get('signature_html')]
        if _sigs:
            SIG_BLOCK = _sigs[0]
    except Exception:
        pass

if not SIG_BLOCK:
    SIG_BLOCK = """<br><br>"""


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_greeting():
    """Time-based greeting for ET."""
    et = datetime.now(timezone.utc).astimezone()
    h = et.hour
    if h < 12:
        return "Good Morning"
    elif h < 17:
        return "Good Afternoon"
    return "Good Evening"


def _fmt_currency(value, decimals=True):
    try:
        v = float(value)
    except (TypeError, ValueError):
        return str(value)
    if decimals:
        return f"${v:,.2f}"
    return f"${v:,.0f}"


def _status_for_pct(pct):
    """Return (label, text_color, bg_color) for a GME usage percentage."""
    pct = float(pct or 0)
    if pct >= 100:
        return "Cap Exhausted", "#991b1b", "#fee2e2"
    if pct >= 80:
        return "High Usage", "#991b1b", "#fee2e2"
    if pct >= 50:
        return "Moderate", "#b45309", "#fef3c7"
    return "On Track", "#065f46", "#d1fae5"


def _remaining_color(pct):
    pct = float(pct or 0)
    if pct >= 80:
        return "#991b1b"
    if pct >= 50:
        return "#b45309"
    return "#065f46"


def _academic_year_str(d=None):
    d = d or datetime.now()
    start = d.year if d.month >= 7 else d.year - 1
    return f"{start}-{start + 1}"


def _render_template(template_path, context):
    """Simple placeholder renderer. Removes any unused {{placeholders}}."""
    html = Path(template_path).read_text(encoding='utf-8')
    for key, val in context.items():
        if val is None:
            val = ""
        html = html.replace('{{' + key + '}}', str(val))
    # Strip anything left behind
    html = re.sub(r'\{\{[^{}]+\}\}', '', html)
    return html


def _build_metrics_html(metrics):
    """Build the four-cell metrics row from a list of {label, value} dicts."""
    if not metrics:
        return ""
    cells = ""
    for m in metrics[:4]:
        cells += f'''
          <td width="25%" align="center" style="padding:12px 6px;font-family:Georgia,Times New Roman,serif;">
            <div style="font-size:8px;color:#888888;text-transform:uppercase;letter-spacing:0.5px;">{m['label']}</div>
            <div style="font-size:14px;font-weight:bold;color:#1a3a5c;padding-top:2px;">{m['value']}</div>
          </td>
        '''
    return f'''
      <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="border:1px solid #e0e4e8;background-color:#fafbfc;">
        <tr>{cells}</tr>
      </table>
    '''


def _build_attachment_callout(attachment_name):
    return f'''
      <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="border:1px solid #bbf7d0;background-color:#f0fdf4;">
        <tr>
          <td style="padding:10px 14px;font-family:Helvetica,Arial,sans-serif;font-size:11px;color:#065f46;">
            <strong>&#128206; {attachment_name}</strong> attached &mdash; see the PDF for charts and full details.
          </td>
        </tr>
      </table>
    '''


def _build_resident_rows(residents):
    """Build HTML rows for the resident breakdown table."""
    if not residents:
        return ""
    rows = ""
    for r in sorted(residents, key=lambda x: float(x.get('pct', 0) or 0), reverse=True):
        name = r.get('name', 'Unknown')
        cls = r.get('class', '')
        used = _fmt_currency(r.get('used', 0))
        remaining = _fmt_currency(r.get('remaining', 0))
        pct = int(float(r.get('pct', 0) or 0))
        label, status_color, status_bg = _status_for_pct(pct)
        rem_color = _remaining_color(pct)
        rows += f'''
          <tr>
            <td style="padding:7px 0;border-bottom:1px solid #f1f5f9;font-family:Times New Roman,Georgia,serif;font-size:12px;color:#333333;">
              <strong>{name}</strong> <span style="color:#888888;font-size:10px;">({cls})</span>
            </td>
            <td style="padding:7px 0;border-bottom:1px solid #f1f5f9;">
              <table role="presentation" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td bgcolor="{status_bg}" style="background-color:{status_bg};padding:2px 8px;font-family:Helvetica,Arial,sans-serif;font-size:10px;font-weight:bold;color:{status_color};">
                    {label}
                  </td>
                </tr>
              </table>
            </td>
            <td align="right" style="padding:7px 0;border-bottom:1px solid #f1f5f9;font-family:Helvetica,Arial,sans-serif;font-size:11px;color:#555555;">
              {used}
            </td>
            <td align="right" style="padding:7px 0;border-bottom:1px solid #f1f5f9;font-family:Helvetica,Arial,sans-serif;font-size:11px;font-weight:bold;color:{rem_color};">
              {remaining}
            </td>
          </tr>
        '''
    return rows


def _build_transaction_table(transactions, max_rows=75):
    """Build a combined transaction table from a {resident: [txns]} dict."""
    if not transactions:
        return ""

    # Flatten and sort by date desc
    flat = []
    for resident, txns in transactions.items():
        for t in txns:
            flat.append({
                'resident': resident,
                'date': t.get('date', ''),
                'description': t.get('description', ''),
                'amount': float(t.get('amount', 0) or 0),
            })
    flat.sort(key=lambda x: x['date'] or '', reverse=True)

    total_flat = len(flat)
    truncated = False
    if len(flat) > max_rows:
        flat = flat[:max_rows]
        truncated = True

    rows = ""
    for t in flat:
        rows += f'''
          <tr>
            <td style="padding:6px 10px;border-bottom:1px solid #f1f5f9;font-family:Helvetica,Arial,sans-serif;font-size:11px;color:#555555;">{t['date']}</td>
            <td style="padding:6px 10px;border-bottom:1px solid #f1f5f9;font-family:Helvetica,Arial,sans-serif;font-size:11px;color:#555555;">{t['resident']}</td>
            <td style="padding:6px 10px;border-bottom:1px solid #f1f5f9;font-family:Helvetica,Arial,sans-serif;font-size:11px;color:#555555;">{t['description']}</td>
            <td align="right" style="padding:6px 10px;border-bottom:1px solid #f1f5f9;font-family:Helvetica,Arial,sans-serif;font-size:11px;color:#1a3a5c;font-weight:bold;">${t['amount']:,.2f}</td>
          </tr>
        '''

    note = ""
    if truncated:
        note = (
            f'<tr><td colspan="4" style="padding:8px 10px;font-family:Helvetica,Arial,sans-serif;font-size:10px;color:#888888;">'
            f'Showing {max_rows} of {total_flat} transactions. See the PDF for the full list.</td></tr>'
        )

    return f'''
      <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="border-collapse:collapse;margin-top:8px;">
        <tr>
          <td style="padding:6px 10px;border-bottom:1px solid #d0d4d8;font-family:Helvetica,Arial,sans-serif;font-size:9px;color:#888888;text-transform:uppercase;letter-spacing:0.5px;width:85px;">Date</td>
          <td style="padding:6px 10px;border-bottom:1px solid #d0d4d8;font-family:Helvetica,Arial,sans-serif;font-size:9px;color:#888888;text-transform:uppercase;letter-spacing:0.5px;width:120px;">Resident</td>
          <td style="padding:6px 10px;border-bottom:1px solid #d0d4d8;font-family:Helvetica,Arial,sans-serif;font-size:9px;color:#888888;text-transform:uppercase;letter-spacing:0.5px;">Description</td>
          <td align="right" style="padding:6px 10px;border-bottom:1px solid #d0d4d8;font-family:Helvetica,Arial,sans-serif;font-size:9px;color:#888888;text-transform:uppercase;letter-spacing:0.5px;width:80px;">Amount</td>
        </tr>
        {rows}
        {note}
      </table>
    '''


def _build_absence_rows(absences):
    if not absences:
        return ""
    rows = ""
    for a in absences:
        late = " <span style='font-size:10px;color:#dc2626;'>(&#128276; late)</span>" if a.get('late') else ""
        rows += f'''
          <tr>
            <td style="padding:7px 0;border-bottom:1px solid #f1f5f9;font-family:Times New Roman,Georgia,serif;font-size:12px;color:#333333;">{a['name']}{late}</td>
            <td style="padding:7px 0;border-bottom:1px solid #f1f5f9;font-family:Helvetica,Arial,sans-serif;font-size:11px;color:#555555;">{a['dates']}</td>
            <td style="padding:7px 0;border-bottom:1px solid #f1f5f9;font-family:Helvetica,Arial,sans-serif;font-size:11px;color:#555555;">{a.get('reason', '')}</td>
            <td style="padding:7px 0;border-bottom:1px solid #f1f5f9;font-family:Helvetica,Arial,sans-serif;font-size:11px;color:{a.get('status_color', '#555555')};">{a['status']}</td>
          </tr>
        '''
    return rows


def _build_department_section(departments):
    if not departments:
        return ""
    rows = ""
    for d in departments:
        rows += f'''
          <tr>
            <td style="padding:5px 0;border-bottom:1px solid #f1f5f9;font-family:Times New Roman,Georgia,serif;font-size:12px;color:#333333;width:70%;">{d['name']}</td>
            <td align="right" style="padding:5px 0;border-bottom:1px solid #f1f5f9;font-family:Helvetica,Arial,sans-serif;font-size:11px;color:#555555;width:30%;">{d['count']}</td>
          </tr>
        '''
    return f'''
      <tr>
        <td style="padding:18px 28px 0 28px;font-family:Georgia,Times New Roman,serif;font-size:13px;font-weight:bold;color:#1a3a5c;">
          By Department
        </td>
      </tr>
      <tr>
        <td style="padding:6px 28px 10px 28px;">
          <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="border-collapse:collapse;">
            {rows}
          </table>
        </td>
      </tr>
    '''


def _build_coverage_alert(coverage):
    if not coverage:
        return ""
    return f'''
      <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="border:1px solid {coverage.get('border', '#bbf7d0')};background-color:{coverage.get('bg', '#f0fdf4')};">
        <tr>
          <td style="padding:10px 14px;font-family:Helvetica,Arial,sans-serif;font-size:12px;color:{coverage.get('color', '#065f46')};">
            <strong>{coverage.get('headline', '')}</strong> {coverage.get('detail', '')}
          </td>
        </tr>
      </table>
    '''


# ─────────────────────────────────────────────────────────────────────────────
# Context builders
# ─────────────────────────────────────────────────────────────────────────────

def _common_context(report_type, data, recipient_name):
    now = datetime.now()
    report_name = data.get('report_name') or REPORT_NAMES.get(report_type, 'Urology Operations Report')
    attachment_name = data.get('attachment_name') or f"{report_type}_report.pdf"
    date_str = data.get('date_str') or now.strftime("%B %d, %Y")

    preheader = data.get('preheader') or f"{report_name} for {date_str} — PDF attached."

    return {
        'report_name': report_name,
        'date_str': date_str,
        'greeting': get_greeting(),
        'recipient_first_name': recipient_name or 'Team',
        'preheader': preheader,
        'academic_year': data.get('academic_year') or _academic_year_str(),
        'date_range': data.get('date_range') or date_str,
        'week_start': data.get('week_start') or date_str,
        'signature_html': SIG_BLOCK,
        'attachment_callout': _build_attachment_callout(attachment_name),
        'metrics_cards': _build_metrics_html(data.get('metrics', [])),
    }


def build_email_html(report_type, report_data, recipient_name="Team"):
    """Render a professional HTML email from structured report data."""
    template_name = TEMPLATE_FILES.get(report_type, TEMPLATE_FILES['full'])
    template_path = TEMPLATE_DIR / template_name
    if not template_path.exists():
        raise FileNotFoundError(f"Email template not found: {template_path}")

    ctx = _common_context(report_type, report_data, recipient_name)

    if report_type == 'gme':
        ctx['resident_rows'] = _build_resident_rows(report_data.get('residents', []))
        ctx['transaction_table'] = _build_transaction_table(report_data.get('transactions', {}))
        ctx['academic_year'] = report_data.get('academic_year') or _academic_year_str()

    elif report_type == 'coverage':
        ctx['date_range'] = report_data.get('date_range') or ctx['date_str']
        ctx['coverage_status'] = _build_coverage_alert(report_data.get('coverage_status'))
        ctx['absence_rows'] = _build_absence_rows(report_data.get('absences', []))

    elif report_type == 'absences':
        ctx['week_start'] = report_data.get('week_start') or ctx['date_str']
        ctx['department_section'] = _build_department_section(report_data.get('departments'))
        ctx['absence_rows'] = _build_absence_rows(report_data.get('absences', []))

    elif report_type == 'full':
        ctx['date_range'] = report_data.get('date_range') or ctx['date_str']
        # GME summary line
        gme = report_data.get('gme', {})
        ctx['gme_summary_line'] = (
            f"<strong>{gme.get('resident_count', 0)}</strong> residents tracked. "
            f"Total used: <strong>{_fmt_currency(gme.get('total_used', 0))}</strong>; "
            f"remaining: <strong>{_fmt_currency(gme.get('total_remaining', 0))}</strong>."
        )
        alert = gme.get('alert')
        ctx['gme_alert'] = (
            f'<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" '
            f'style="border:1px solid {alert["border"]};background-color:{alert["bg"]};">'
            f'<tr><td style="padding:8px 12px;font-family:Helvetica,Arial,sans-serif;font-size:11px;color:{alert["color"]};">'
            f'<strong>&#9888; Attention:</strong> {alert["text"]}</td></tr></table>'
            if alert else ""
        )
        # Coverage summary line
        cov = report_data.get('coverage', {})
        ctx['coverage_summary_line'] = (
            f"<strong>{cov.get('future_shifts', 'N/A')}</strong> future shifts on file. "
            f"{cov.get('status_text', '')}"
        )
        # Absence section
        absences = report_data.get('absences', [])
        if absences:
            top = absences[:5]
            rows = _build_absence_rows(top)
            more = f"<p style='margin:6px 0 0 0;font-family:Helvetica,Arial,sans-serif;font-size:10px;color:#888888;'>+ {len(absences) - len(top)} more in the PDF.</p>" if len(absences) > 5 else ""
            ctx['absence_section'] = (
                f'<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="border-collapse:collapse;">'
                f'<tr><td style="padding:6px 0;border-bottom:1px solid #d0d4d8;font-family:Helvetica,Arial,sans-serif;font-size:9px;color:#888888;text-transform:uppercase;letter-spacing:0.5px;width:35%;">Name</td>'
                f'<td style="padding:6px 0;border-bottom:1px solid #d0d4d8;font-family:Helvetica,Arial,sans-serif;font-size:9px;color:#888888;text-transform:uppercase;letter-spacing:0.5px;width:30%;">Dates</td>'
                f'<td style="padding:6px 0;border-bottom:1px solid #d0d4d8;font-family:Helvetica,Arial,sans-serif;font-size:9px;color:#888888;text-transform:uppercase;letter-spacing:0.5px;width:35%;">Status</td></tr>'
                f'{rows}</table>{more}'
            )
        else:
            ctx['absence_section'] = "<p style='margin:0;font-family:Times New Roman,Georgia,serif;font-size:12px;color:#16a34a;'>&#10004; No absences recorded this week.</p>"

    return _render_template(template_path, ctx)


# ─────────────────────────────────────────────────────────────────────────────
# Sending
# ─────────────────────────────────────────────────────────────────────────────

def _subject(report_type, data):
    report_name = data.get('report_name') or REPORT_NAMES.get(report_type, 'Report')
    if report_type == 'gme':
        return f"Montefiore Urology - {report_name} (AY {data.get('academic_year', _academic_year_str())})"
    if data.get('date_range'):
        return f"Montefiore Urology - {report_name} ({data['date_range']})"
    return f"Montefiore Urology - {report_name} ({data.get('date_str', datetime.now().strftime('%B %d, %Y'))})"


def send(report_type, report_data, pdf_path, recipient, recipient_name="Team"):
    """Send the email with PDF attachment via Gmail OAuth."""
    html_body = build_email_html(report_type, report_data, recipient_name)

    ws = GoogleWorkspace()
    result = ws.send_email(
        user_id="urologyresidency",
        to=recipient,
        subject=_subject(report_type, report_data),
        body=html_body,
        attachments=[pdf_path],
        from_email="sfrasier@montefiore.org",
        is_html=True,
    )

    if result.get("successful"):
        print(f"  📬 Sent to {recipient}")
        return True
    else:
        print(f"  ❌ Email failed: {json.dumps(result, indent=2, default=str)[:300]}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Legacy CLI support (free-text summary)
# ─────────────────────────────────────────────────────────────────────────────

def _parse_summary_text(report_summary):
    """Parse the structured text report into metrics, sections, and residents."""
    metrics = {}
    sections = {}
    residents = []
    transactions = {}
    current_section = ""

    lines = report_summary.strip().split('\n')
    for line in lines:
        ls = line.strip()
        if not ls or ls.startswith('='):
            continue
        if ls.startswith('# '):
            current_section = ls[2:].strip()
            sections[current_section] = []
        elif current_section:
            sections.setdefault(current_section, []).append(ls)
        else:
            if ':' in ls and not ls.startswith('  '):
                parts = ls.split(':', 1)
                metrics[parts[0].strip()] = parts[1].strip()

    if "Resident Breakdown" in sections:
        for entry in sections["Resident Breakdown"]:
            m = re.match(r'[✅⚠️❗]?\s*(.+?)\s*\((.+?)\):\s*\$?([\d,]+)\s*used,\s*\$?([\d,]+)\s*remaining\s*\((\d+)%\)', entry)
            if m:
                residents.append({
                    'name': m.group(1).strip(),
                    'class': m.group(2).strip(),
                    'used': float(m.group(3).replace(',', '')),
                    'remaining': float(m.group(4).replace(',', '')),
                    'pct': int(m.group(5)),
                })

    if "Approved GME Transactions" in sections:
        txn_lines = sections["Approved GME Transactions"]
        current_resident = None
        for entry in txn_lines:
            m = re.match(r'^\s*(.+?):\s*(\d+)\s*transactions?,\s*\$?([\d,]+\.?\d*)\s*total', entry)
            if m:
                current_resident = m.group(1).strip()
                count = int(m.group(2))
                total = float(m.group(3).replace(',', ''))
                transactions[current_resident] = {'count': count, 'total': total}

    return metrics, sections, residents, transactions


def _legacy_build_email_html(report_type, report_summary, greeting):
    """Old inline email builder for one-off CLI use with --summary."""
    now = datetime.now()
    date_str = now.strftime("%B %d, %Y")
    report_name = REPORT_NAMES.get(report_type, "Urology Operations Report")

    metrics, sections, residents, transactions = _parse_summary_text(report_summary)

    # Derive annual cap from metrics if possible, else default
    annual_cap = 1250.0
    cap_str = metrics.get('Annual Cap per Resident') or metrics.get('Cap/Resident')
    if cap_str:
        cap_clean = re.sub(r'[^\d.]', '', cap_str)
        try:
            annual_cap = float(cap_clean)
        except ValueError:
            pass

    resident_rows = _build_resident_rows([
        {
            'name': r['name'],
            'class': r.get('class', ''),
            'used': r['used'],
            'remaining': r['remaining'],
            'pct': r['pct'],
        }
        for r in sorted(residents, key=lambda x: x.get('pct', 0), reverse=True)
    ])

    # Reconstruct transactions into grouped format for the new table builder
    grouped = {}
    for resident, t in transactions.items():
        grouped[resident] = [{'date': '', 'description': f"{t['count']} transactions, ${_fmt_currency(t['total'])} total", 'amount': t['total']}]
    transaction_table = _build_transaction_table(grouped, max_rows=50)

    data = {
        'report_name': report_name,
        'date_str': date_str,
        'academic_year': _academic_year_str(),
        'metrics': [{'label': k, 'value': v} for k, v in list(metrics.items())[:4]],
        'residents': [
            {'name': r['name'], 'class': r.get('class', ''), 'used': r['used'], 'remaining': r['remaining'], 'pct': r['pct'], 'annual_cap': annual_cap}
            for r in residents
        ],
        'transactions': transactions,
    }

    ctx = _common_context(report_type, data, 'Shareef')
    ctx['greeting'] = greeting
    ctx['resident_rows'] = resident_rows
    ctx['transaction_table'] = transaction_table
    ctx['academic_year'] = data['academic_year']

    template_name = TEMPLATE_FILES.get(report_type, TEMPLATE_FILES['full'])
    template_path = TEMPLATE_DIR / template_name
    if not template_path.exists():
        return "<html><body>Template missing.</body></html>"
    return _render_template(template_path, ctx)


def _legacy_send(report_type, report_summary, pdf_path, recipient):
    """Send using the legacy free-text summary path."""
    greeting = get_greeting()
    html_body = _legacy_build_email_html(report_type, report_summary, greeting)
    report_name = REPORT_NAMES.get(report_type, "Urology Operations Report")
    date_str = datetime.now().strftime("%B %d, %Y")

    ws = GoogleWorkspace()
    result = ws.send_email(
        user_id="urologyresidency",
        to=recipient,
        subject=f"Montefiore Urology - {report_name} ({date_str})",
        body=html_body,
        attachments=[pdf_path],
        from_email="sfrasier@montefiore.org",
        is_html=True,
    )

    if result.get("successful"):
        print(f"  📬 Sent to {recipient}")
        return True
    else:
        print(f"  ❌ Email failed: {json.dumps(result, indent=2, default=str)[:300]}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", required=True)
    parser.add_argument("--type", default="full", choices=REPORT_NAMES.keys())
    parser.add_argument("--data", help="Path to JSON report_data file")
    parser.add_argument("--summary", help="Legacy report summary text for email body")
    parser.add_argument("--email", default=DEFAULT_RECIPIENT)
    parser.add_argument("--recipient-name", default="Team",
                        help="First name to use in greeting")
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"❌ PDF not found: {args.pdf}")
        sys.exit(1)

    print(f"\n📧 Sending {REPORT_NAMES.get(args.type, 'Report')} to {args.email}...")

    if args.data:
        data = json.loads(Path(args.data).read_text(encoding='utf-8'))
        ok = send(args.type, data, str(pdf_path), args.email, recipient_name=args.recipient_name)
    elif args.summary:
        ok = _legacy_send(args.type, args.summary, str(pdf_path), args.email)
    else:
        print("❌ Either --data or --summary is required.")
        sys.exit(1)

    print(f"✅ Done\n" if ok else f"❌ Failed\n")


if __name__ == "__main__":
    main()
