#!/usr/bin/env python3
"""
Telegram Voice Command Handler for Montefiore Urology Reports.
Strips debug noise — only sends clean, formatted output to Telegram.

Usage:
  python3 voice-report-handler.py --type gme
  python3 voice-report-handler.py --type full --email sfrasier@montefiore.org

Cron jobs call this with no_agent=true — stdout becomes the delivery message.
"""

import argparse
import json
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

import gme_transactions

REPORT_GENERATOR = Path(__file__).parent / "report-generator.py"
SEND_SCRIPT = Path(__file__).parent / "send-report.py"
REPORTS_DIR = Path("/workspace/agentic-os/reports")
LATEST_DIR = REPORTS_DIR / "latest"

VERBOSE_NAMES = {
    'gme': 'GME Reimbursement',
    'coverage': 'Coverage Gap Analysis',
    'absences': 'Absence Summary',
    'full': 'Consolidated Operations',
}


def resolve_pdf_path(report_type, generated_pdf=None):
    """Return the best PDF path: prefer reports/latest/, then the generated path."""
    expected_name = f"{report_type}_report.pdf"

    # 1. Prefer reports/latest/ top-level file/symlink
    latest_pdf = LATEST_DIR / expected_name
    if latest_pdf.exists():
        return str(latest_pdf)

    # 2. Use the path reported by report-generator.py
    if generated_pdf and Path(generated_pdf).exists():
        return generated_pdf

    return generated_pdf


def generate_report(report_type):
    """Run the report generator and capture output."""
    cmd = [sys.executable, str(REPORT_GENERATOR), "--type", report_type, "--quiet", "--json"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)

    full = (result.stdout or '') + (result.stderr or '')
    pdf_path = None
    summary = ""
    txn_data = {}

    # Parse structured JSON output
    if result.returncode == 0:
        import re
        m = re.search(r'---JSON_OUTPUT---\n(.*?)\n---END_JSON---', result.stdout or '', re.DOTALL)
        if m:
            try:
                data = json.loads(m.group(1))
                pdf_path = str(REPORTS_DIR / "latest" / f"{report_type}_report.pdf")
                if not Path(pdf_path).exists():
                    pdf_path = data.get('pdf_path')
                summary = data.get('text_content', '')
                txn_data = data.get('transactions', {})
            except (json.JSONDecodeError, KeyError):
                pass

    # Fallback: extract from stdout if JSON parsing failed
    if not pdf_path:
        for line in full.split('\n'):
            if 'PDF:' in line:
                pdf_path = line.split('PDF:')[-1].strip()
        # Prefer reports/latest/ symlinks
        pdf_path = resolve_pdf_path(report_type, pdf_path)

    if not summary:
        in_summary = False
        for line in full.split('\n'):
            s = line.strip()
            if 'REPORT SUMMARY' in s:
                in_summary = True
                continue
            if not in_summary:
                continue
            if '📎 Charts' in s or '📄 PDF' in s or 'Report saved' in s:
                continue
            if s and not s.startswith('==='):
                summary += s + '\n'

    return {
        'type': report_type,
        'success': result.returncode == 0,
        'full_output': full,
        'summary': summary.strip(),
        'pdf_path': pdf_path or '',
        'name': VERBOSE_NAMES.get(report_type, report_type),
        'transactions': txn_data,
    }


def format_transactions_telegram(grouped_transactions):
    """Format per-resident transactions for Telegram; concise but complete."""
    if not grouped_transactions:
        return []

    summary = gme_transactions.transaction_summary(grouped_transactions)
    lines = [
        "",
        f"📋 *Approved GME Transactions*",
        f"`Residents: {summary['resident_count']} | "
        f"Transactions: {summary['transaction_count']} | "
        f"Total: ${summary['total_amount']:,.2f}`",
        "",
    ]

    for resident_name in sorted(grouped_transactions.keys()):
        txns = grouped_transactions[resident_name]
        resident_total = sum(float(t.get('amount', 0) or 0) for t in txns)
        lines.append(f"*{resident_name}* — ${resident_total:,.2f}")
        for t in txns:
            date = t.get('date', '')
            desc = t.get('description', '')
            amount = float(t.get('amount', 0) or 0)
            lines.append(f"  `{date}` {desc}  ${amount:,.2f}")
        lines.append("")

    return lines


def format_telegram(result):
    """Clean Telegram message — key stats, per-resident transactions, no debug lines."""
    now = datetime.now().strftime('%b %d, %Y at %H:%M')
    name = result['name']

    if not result['success']:
        return (
            f"❌ *{name} Report Failed*\n"
            f"Try again or check data service health"
        )

    # Parse summary into structured sections
    summary = result.get('summary', '')
    pdf_path = result.get('pdf_path')

    lines = [
        f"📊 *{name} Report*",
        f"_{now}_",
        "",
    ]

    # Extract top-level stats from the top of the summary
    top_stats = []
    breakdown_lines = []
    in_breakdown = False
    for line in summary.split('\n'):
        s = line.strip()
        if not s:
            continue
        if s.startswith('# '):
            in_breakdown = True
        if in_breakdown:
            breakdown_lines.append(s)
        else:
            top_stats.append(s)

    # Top stats — cleanly formatted
    for stat in top_stats:
        if stat and not stat.startswith('='):
            lines.append(f"▸ {stat}")

    # Resident breakdown — condensed (top 5 only if GME report)
    if breakdown_lines:
        lines.append("")
        shown = 0
        for line in breakdown_lines:
            if line.startswith('# '):
                lines.append(f"\n*{line[2:]}*")
            elif shown < 5 and (line.startswith('❗') or line.startswith('✅') or line.startswith('⚠')):
                lines.append(f"`{line}`")
                shown += 1
            elif line.startswith('❗') or line.startswith('✅') or line.startswith('⚠'):
                break  # Stop after top 5

    # Per-resident transaction lists (concise but complete)
    grouped = gme_transactions.transactions_by_resident(
        status='complete', account_filter='GME'
    )
    lines.extend(format_transactions_telegram(grouped))

    # PDF link
    if pdf_path:
        lines.append("")
        lines.append(f"📄 `{Path(pdf_path).name}`")
        lines.append(f"`{pdf_path}`")

    lines.append("")
    lines.append("Say *'email the report'* to send it with charts")

    return '\n'.join(lines)


def send_email(report_type, pdf_path, summary_text, recipient):
    """Send the PDF + summary as an email via send-report.py."""
    if not pdf_path or not Path(pdf_path).exists():
        return "❌ No PDF to send"
    cmd = [
        sys.executable, str(SEND_SCRIPT),
        "--pdf", pdf_path,
        "--type", report_type,
        "--summary", summary_text,
        "--email", recipient,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode == 0:
        out = (result.stdout or '') + (result.stderr or '')
        return f"✅ Emailed to {recipient}\n{out.strip()}"
    else:
        return f"❌ Email failed: {(result.stderr or result.stdout)[:200]}"


def main():
    parser = argparse.ArgumentParser(description="Voice Report Handler")
    parser.add_argument('--type', choices=['gme', 'coverage', 'absences', 'full'],
                        default='full', help='Report type')
    parser.add_argument('--email', type=str, help='Email PDF to this address')
    parser.add_argument('--mode', choices=['telegram', 'cli', 'json'],
                        default='telegram', help='Output mode')
    args = parser.parse_args()

    result = generate_report(args.type)

    if args.email and result['pdf_path']:
        # Generate report + email it
        email_result = send_email(args.type, result['pdf_path'],
                                  result.get('summary', ''), args.email)
        if args.mode == 'telegram':
            # Show Telegram message + email result
            tg = format_telegram(result)
            print(tg)
            print(f"\n{email_result}")
        else:
            print(email_result)
    elif args.mode == 'json':
        print(json.dumps(result))
    elif args.mode == 'cli':
        print(result.get('full_output', ''))
    else:
        msg = format_telegram(result)
        print(msg)


if __name__ == "__main__":
    main()
