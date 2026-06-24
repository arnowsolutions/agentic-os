#!/usr/bin/env python3
"""
Montefiore Urology — Multi-Report Generator
Voice-activated Telegram command → report with charts + PDF + email delivery.

Usage:
  python3 report-generator.py                # CLI interactive mode
  python3 report-generator.py --type gme     # Generate GME report only
  python3 report-generator.py --type full --email sfrasier@montefiore.org

Reports output to /workspace/agentic-os/reports/ (PNG charts + PDF)
"""

import argparse
import fcntl
import json
import os
import shutil
import sys
import io
from datetime import datetime, date, timedelta
from pathlib import Path
from collections import Counter, defaultdict

import httpx
import gme_transactions
import send_report

# ─── Matplotlib Setup (module-level, called once) ─────────────────────
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.dates as mdates

MPL_RCPARAMS = {
    'figure.facecolor': '#ffffff',
    'axes.facecolor': '#ffffff',
    'axes.edgecolor': '#d0d7de',
    'axes.labelcolor': '#24292f',
    'text.color': '#24292f',
    'xtick.color': '#656d76',
    'ytick.color': '#656d76',
    'grid.color': '#d0d7de',
    'grid.alpha': 0.4,
    'font.size': 10,
    'font.family': 'sans-serif',
}
plt.rcParams.update(MPL_RCPARAMS)

# ─── Config ─────────────────────────────────────────────────────────
DATA_SERVICE_URL = "http://localhost:8086"
OUTPUT_DIR = Path("/workspace/agentic-os/reports")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REIMBURSEMENT_DB = Path("/workspace/repos/reimbursement/reimbursement.db")
LOCK_FILE = OUTPUT_DIR / ".report-generator.lock"
LATEST_DIR = OUTPUT_DIR / "latest"
LATEST_DIR.mkdir(parents=True, exist_ok=True)


def acquire_lock():
    """Acquire an advisory file lock; exit cleanly if another instance holds it."""
    try:
        fd = os.open(str(LOCK_FILE), os.O_RDWR | os.O_CREAT)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd
    except (OSError, IOError):
        print("Another report generation is already running. Exiting.")
        sys.exit(0)


def release_lock(fd):
    """Release the advisory lock and close the file descriptor."""
    if fd is None:
        return
    try:
        fcntl.flock(fd, fcntl.LOCK_UN)
    except OSError as e:
        print(f"  ⚠️  Failed to unlock lock file: {e}")
    try:
        os.close(fd)
    except OSError as e:
        print(f"  ⚠️  Failed to close lock file descriptor: {e}")


def update_latest_symlink(report_dir, report_type):
    """Clear prior contents of reports/latest/, copy the new report in, and
    create top-level symlinks for the common PDF files."""
    if not report_dir.exists():
        return

    for item in LATEST_DIR.iterdir():
        try:
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
        except Exception as e:
            print(f"  ⚠️  Could not remove old latest item {item}: {e}")

    shutil.copytree(report_dir, LATEST_DIR / report_dir.name, dirs_exist_ok=True)

    pdf_name = f"{report_type}_report.pdf"
    src_pdf = LATEST_DIR / report_dir.name / pdf_name
    if src_pdf.exists():
        link_names = [pdf_name]
        if report_type == "gme":
            link_names.append("gme_report.pdf")
        elif report_type == "full":
            link_names.append("full_report.pdf")
        for link_name in link_names:
            link_path = LATEST_DIR / link_name
            if link_path.exists() or link_path.is_symlink():
                link_path.unlink()
            try:
                os.symlink(src_pdf, link_path)
            except Exception as e:
                print(f"  ⚠️  Could not create symlink {link_path}: {e}")

    print(f"  ✅ latest/ updated: {LATEST_DIR}")


# ─── Data Fetching ──────────────────────────────────────────────────

def fetch_json(endpoint):
    """Fetch JSON from the data service. Returns None on transient failure."""
    url = f"{DATA_SERVICE_URL}{endpoint}"
    try:
        r = httpx.get(url, timeout=15)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError as e:
        print(f"  ⚠️  Failed to fetch {url}: {e}")
        return None
    except (OSError, IOError, ValueError) as e:
        print(f"  ⚠️  Connection/parse error for {url}: {e}")
        return None


def get_gme_data():
    return fetch_json("/api/reimbursement/gme-summary")


def get_residents():
    data = fetch_json("/api/unified/residents")
    return data.get("items", []) if data else []


def get_today():
    return fetch_json("/api/unified/today")


def get_allocations(account=None, limit=200):
    params = f"?limit={limit}"
    if account:
        params += f"&account={account}"
    return fetch_json(f"/api/reimbursement/allocations{params}") or {"items": []}


def get_submissions(status=None, limit=100):
    params = f"?limit={limit}"
    if status:
        params += f"&status={status}"
    return fetch_json(f"/api/reimbursement/submissions{params}")


# ─── Date Helpers ─────────────────────────────────────────────────────

def _academic_year_str(d=None):
    d = d or date.today()
    start = d.year if d.month >= 7 else d.year - 1
    return f"{start}-{start + 1}"


def _week_start_str(d=None):
    d = d or date.today()
    monday = d - timedelta(days=d.weekday())
    return monday.strftime("%B %d, %Y")


def _date_range_str(d=None, days=6):
    d = d or date.today()
    end = d + timedelta(days=days)
    if d.year == end.year:
        return f"{d.strftime('%B %d')} – {end.strftime('%B %d, %Y')}"
    return f"{d.strftime('%B %d, %Y')} – {end.strftime('%B %d, %Y')}"


# ─── Chart Generation ───────────────────────────────────────────────

def _save_fig(fig, dpi=200):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight',
                facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close(fig)
    buf.seek(0)
    return buf


def make_fallback_chart(message):
    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_facecolor('#ffffff')
    ax.set_facecolor('#fafbfc')
    ax.text(0.5, 0.5, message, ha='center', va='center',
            fontsize=14, color='#656d76', transform=ax.transAxes)
    ax.set_title('No Data Available', fontsize=12, color='#656d76')
    ax.axis('off')
    return _save_fig(fig, dpi=100)


def generate_gme_bar_chart(residents):
    """Generate a GME usage bar chart. Returns PNG bytes."""
    if not residents:
        return make_fallback_chart("No resident data available")

    residents_sorted = sorted(residents, key=lambda r: r.get('pct', 0), reverse=True)
    names = [r.get('name', 'Unknown') for r in residents_sorted]
    used = [r.get('gme_used', 0) for r in residents_sorted]
    cap = residents_sorted[0].get('annual_cap', 1250)
    pcts = [r.get('pct', 0) for r in residents_sorted]

    n = len(names)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, max(4.5, n * 0.45)),
                                    gridspec_kw={'width_ratios': [2, 1]})

    bars = ax1.barh(names, used, height=0.55, color='#1a3a5c', alpha=0.9, label='Used')
    ax1.axvline(x=cap, color='#c0392b', linestyle='--', linewidth=1.5, alpha=0.8, label=f'Cap (${cap:,.0f})')
    ax1.set_xlabel('Amount ($)', color='#24292f')
    ax1.set_title('GME Usage by Resident', fontsize=13, fontweight='bold', color='#1a3a5c', pad=12)

    for bar, val in zip(bars, used):
        if val > 0:
            ax1.text(val + 10, bar.get_y() + bar.get_height()/2,
                     f'${val:,.0f}', va='center', fontsize=8, color='#24292f')

    ax1.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    ax1.legend(loc='lower right', fontsize=8, framealpha=0.9)
    ax1.invert_yaxis()
    ax1.grid(axis='x', alpha=0.3)

    max_pct = max(pcts) if pcts else 100
    x_upper = max(105, max_pct + 15)
    colors = ['#27ae60' if p < 50 else '#f39c12' if p < 80 else '#e74c3c' for p in pcts]
    bars2 = ax2.barh(names, [min(p, x_upper) for p in pcts], height=0.55, color=colors, alpha=0.9)
    ax2.set_xlabel('Usage (%)', color='#24292f')
    ax2.set_title('Cap Utilization', fontsize=13, fontweight='bold', color='#1a3a5c', pad=12)

    for bar, pct in zip(bars2, pcts):
        label_x = min(pct, x_upper - 5) + 1
        color = '#c0392b' if pct > 100 else '#24292f'
        ax2.text(label_x, bar.get_y() + bar.get_height()/2,
                 f'{pct:.0f}%', va='center', fontsize=8, color=color)

    ax2.axvline(x=50, color='#27ae60', linestyle=':', linewidth=1, alpha=0.5)
    ax2.axvline(x=80, color='#e74c3c', linestyle=':', linewidth=1, alpha=0.5)
    ax2.invert_yaxis()
    ax2.set_xlim(0, x_upper)
    ax2.grid(axis='x', alpha=0.3)

    plt.tight_layout(pad=2)
    return _save_fig(fig)


def generate_gme_category_chart(allocations_data):
    """Horizontal bar chart (or KPI card for one category) of GME spending by category."""
    if not allocations_data or not allocations_data.get('items'):
        return make_fallback_chart("No allocation data available")

    cat_totals = defaultdict(float)
    for item in allocations_data['items']:
        acct = item.get('account', 'Unknown')
        if 'GME' in acct.upper():
            short = acct.replace('GME - ', '').replace('GME ', '')
        else:
            short = acct
        cat_totals[short] += float(item.get('amount', 0))

    if not cat_totals:
        return make_fallback_chart("No allocations with GME data")

    categories = list(cat_totals.keys())
    amounts = [cat_totals[c] for c in categories]

    if len(categories) == 1:
        fig, ax = plt.subplots(figsize=(7, 3.5))
        fig.patch.set_facecolor('#ffffff')
        ax.axis('off')
        from matplotlib.patches import FancyBboxPatch
        ax.add_patch(FancyBboxPatch((0.05, 0.12), 0.9, 0.76,
                                     boxstyle="round,pad=0.04",
                                     facecolor='#f0f4f8', edgecolor='#d0d7de',
                                     linewidth=1.5, transform=ax.transAxes))
        ax.text(0.5, 0.72, categories[0], ha='center', va='center',
                fontsize=14, fontweight='bold', color='#1a3a5c', transform=ax.transAxes)
        ax.text(0.5, 0.45, f'${amounts[0]:,.0f}', ha='center', va='center',
                fontsize=32, fontweight='bold', color='#1a3a5c', transform=ax.transAxes)
        ax.text(0.5, 0.25, 'Total GME Spending', ha='center', va='center',
                fontsize=10, color='#656d76', transform=ax.transAxes)
        return _save_fig(fig)

    # Sort descending, use horizontal bars
    sorted_pairs = sorted(zip(categories, amounts), key=lambda x: x[1], reverse=True)
    categories, amounts = zip(*sorted_pairs)

    fig, ax = plt.subplots(figsize=(8, max(4, len(categories) * 0.55)))
    y_pos = range(len(categories))
    bars = ax.barh(y_pos, amounts, color='#1a3a5c', alpha=0.85, height=0.6)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(categories)
    ax.invert_yaxis()
    ax.set_xlabel('Amount ($)', color='#24292f')
    ax.set_title('GME Spending by Category', fontsize=13, fontweight='bold', color='#1a3a5c', pad=12)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    ax.grid(axis='x', alpha=0.3)

    for bar, val in zip(bars, amounts):
        ax.text(val + max(amounts) * 0.01, bar.get_y() + bar.get_height()/2,
                f'${val:,.0f}', va='center', fontsize=9, color='#24292f')

    plt.tight_layout()
    return _save_fig(fig)


def generate_absence_trend_chart(today_data):
    """Generate an absence trend chart from sick call data."""
    if not today_data or not today_data.get('sick_call', {}).get('absences'):
        return make_fallback_chart("No absence data available")

    absences = today_data['sick_call']['absences']
    if not absences:
        return make_fallback_chart("No absences found this week")

    date_counts = Counter()
    for a in absences:
        start = a.get('start_date', '')
        if start:
            try:
                d = datetime.strptime(start[:10], '%Y-%m-%d').date()
                date_counts[d] += 1
            except ValueError:
                pass

    if not date_counts:
        return make_fallback_chart("No date data in absences")

    dates_sorted = sorted(date_counts.keys())
    counts = [date_counts[d] for d in dates_sorted]

    fig, ax = plt.subplots(figsize=(10, 5))
    max_count = max(counts) if counts else 0
    line_color = '#e74c3c' if max_count >= 3 else '#1a3a5c'

    ax.fill_between(dates_sorted, counts, alpha=0.15, color=line_color)
    ax.plot(dates_sorted, counts, color=line_color, linewidth=2.5, marker='o', markersize=8, markerfacecolor=line_color)

    ax.set_title('Absences This Week', fontsize=14, fontweight='bold', color='#1a3a5c', pad=12)
    ax.set_ylabel('Number of Absences', fontsize=11)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%a\n%b %d'))
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    return _save_fig(fig)


# ─── PDF Generation ─────────────────────────────────────────────────

def _make_reportlab_styles():
    from reportlab.lib.colors import HexColor
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

    styles = getSampleStyleSheet()
    return {
        'title': ParagraphStyle('Title', parent=styles['Title'],
            textColor=HexColor('#1a3a5c'), fontSize=22, spaceAfter=4, alignment=TA_CENTER,
            fontName='Helvetica-Bold'),
        'subtitle': ParagraphStyle('Subtitle', parent=styles['Normal'],
            textColor=HexColor('#666666'), fontSize=11, spaceAfter=20, alignment=TA_CENTER),
        'h2': ParagraphStyle('H2', parent=styles['Heading2'],
            textColor=HexColor('#1a3a5c'), fontSize=14, spaceBefore=16, spaceAfter=8,
            fontName='Helvetica-Bold'),
        'h3': ParagraphStyle('H3', parent=styles['Heading3'],
            textColor=HexColor('#333333'), fontSize=11, spaceBefore=10, spaceAfter=4,
            fontName='Helvetica-Bold'),
        'body': ParagraphStyle('Body', parent=styles['Normal'],
            textColor=HexColor('#333333'), fontSize=9.5, leading=13, spaceAfter=3),
        'highlight': ParagraphStyle('Highlight', parent=styles['Normal'],
            textColor=HexColor('#1a7d36'), fontSize=9.5),
        'warning': ParagraphStyle('Warning', parent=styles['Normal'],
            textColor=HexColor('#b85a00'), fontSize=9.5),
    }


def _status_color_for_pct(pct):
    pct = float(pct or 0)
    if pct >= 80:
        return '#e74c3c'
    if pct >= 50:
        return '#f39c12'
    return '#27ae60'


def _first_page_header_footer(canvas, doc, report_name, date_str):
    canvas.saveState()
    canvas.setFont('Helvetica', 8)
    canvas.setFillColorRGB(0.61, 0.64, 0.67)
    canvas.drawCentredString(
        4.25 * 72, 0.5 * 72,
        f"Montefiore Einstein Urology  |  {report_name}  |  Page {doc.page}  |  {date_str}"
    )
    canvas.restoreState()


def _later_pages_header_footer(canvas, doc, report_name, date_str):
    canvas.saveState()
    canvas.setFont('Helvetica-Bold', 8)
    canvas.setFillColorRGB(0.10, 0.23, 0.36)
    canvas.drawString(0.7 * 72, 10.6 * 72, "Montefiore Einstein Urology")
    canvas.setFont('Helvetica', 8)
    canvas.setFillColorRGB(0.40, 0.44, 0.48)
    canvas.drawRightString(7.8 * 72, 10.6 * 72, report_name)
    canvas.line(0.7 * 72, 10.45 * 72, 7.8 * 72, 10.45 * 72)
    canvas.setFont('Helvetica', 8)
    canvas.setFillColorRGB(0.61, 0.64, 0.67)
    canvas.drawCentredString(
        4.25 * 72, 0.5 * 72,
        f"Page {doc.page}  |  {date_str}"
    )
    canvas.restoreState()


def _png_size(path):
    try:
        from PIL import Image as PILImage
        with PILImage.open(path) as im:
            w, h = im.size
            return w, h
    except Exception:
        return None


def generate_pdf(report_data, output_path):
    """Generate a clean professional PDF report from structured report data."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, KeepTogether
    )
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

    report_name = report_data.get('report_name', 'Urology Operations Report')
    date_str = report_data.get('date_str', datetime.now().strftime("%B %d, %Y"))

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        topMargin=0.65*inch, bottomMargin=0.75*inch,
        leftMargin=0.7*inch, rightMargin=0.7*inch,
    )

    s = _make_reportlab_styles()
    styles = _make_reportlab_styles()
    ss = _make_reportlab_styles()
    cell_style = ParagraphStyle('Cell', parent=ss['body'],
        textColor=HexColor('#333333'), fontSize=8.5, leading=11, spaceAfter=0)
    right_cell = ParagraphStyle('RightCell', parent=cell_style, alignment=TA_RIGHT)
    header_cell = ParagraphStyle('HeaderCell', parent=cell_style,
        textColor=HexColor('#ffffff'), fontSize=9, fontName='Helvetica-Bold')

    elements = []

    # Header bar
    header_table = Table(
        [[Paragraph("<b>Montefiore Einstein Urology</b>",
            ParagraphStyle('HeaderTitle', parent=s['title'], fontSize=16, spaceAfter=0, alignment=TA_LEFT)),
          Paragraph(f"<i>{date_str}</i>",
            ParagraphStyle('HeaderDate', parent=s['subtitle'], fontSize=9, spaceAfter=0, alignment=TA_RIGHT))]],
        colWidths=[4.3*inch, 3*inch]
    )
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#1a3a5c')),
        ('TEXTCOLOR', (0, 0), (-1, -1), HexColor('#ffffff')),
        ('LEFTPADDING', (0, 0), (0, 0), 14),
        ('RIGHTPADDING', (-1, -1), (-1, -1), 14),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 14))

    # Title
    elements.append(Paragraph(f"<b>{report_name}</b>",
        ParagraphStyle('ReportTitle', parent=s['h2'], fontSize=15, spaceAfter=2)))
    elements.append(Spacer(1, 8))

    # Metrics
    metrics = report_data.get('metrics', [])
    if metrics:
        kpi_data = []
        row = []
        for i, m in enumerate(metrics[:4]):
            cell_text = f"<b>{m['label']}</b><br/>{m['value']}"
            row.append(Paragraph(cell_text, ParagraphStyle('KPICell',
                parent=ss['body'], textColor=HexColor('#1a3a5c'),
                fontSize=10, leading=14, alignment=TA_CENTER)))
            if len(row) == 2 or i == len(metrics) - 1:
                while len(row) < 2:
                    row.append(Paragraph("", cell_style))
                kpi_data.append(row)
                row = []
        if kpi_data:
            kpi_table = Table(kpi_data, colWidths=[3.2*inch, 3.2*inch])
            kpi_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f0f4f8')),
                ('BOX', (0, 0), (-1, -1), 0.5, HexColor('#d0d7de')),
                ('INNERGRID', (0, 0), (-1, -1), 0.25, HexColor('#d0d7de')),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            elements.append(kpi_table)
            elements.append(Spacer(1, 14))

    # Sections
    for section in report_data.get('sections', []):
        heading = section.get('heading', '')
        kind = section.get('kind', '')
        elements.append(Paragraph(f"<b>{heading}</b>", s['h3']))

        if kind == 'resident_table':
            rows = [[
                Paragraph("<b>Resident</b>", header_cell),
                Paragraph("<b>Class</b>", header_cell),
                Paragraph("<b>Used</b>", header_cell),
                Paragraph("<b>Remaining</b>", header_cell),
                Paragraph("<b>%</b>", header_cell),
            ]]
            for r in section.get('residents', []):
                color = _status_color_for_pct(r.get('pct', 0))
                rows.append([
                    Paragraph(f"<font color='{color}'>&#9679;</font> {r['name']}", cell_style),
                    Paragraph(r.get('class', ''), cell_style),
                    Paragraph(f"${r.get('gme_used', 0):,.0f}", right_cell),
                    Paragraph(f"${r.get('gme_remaining', r.get('remaining', 0)):,.0f}", right_cell),
                    Paragraph(f"{r.get('pct', 0):.0f}%", right_cell),
                ])
            table = Table(rows, colWidths=[2.4*inch, 0.8*inch, 1.1*inch, 1.2*inch, 0.8*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1a3a5c')),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 7),
                ('TOPPADDING', (0, 0), (-1, 0), 7),
                ('BACKGROUND', (0, 1), (-1, -1), HexColor('#f6f8fa')),
                ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#d0d7de')),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(table)

        elif kind == 'category_table':
            cats = section.get('categories', [])
            total = sum(c['amount'] for c in cats)
            rows = [[
                Paragraph("<b>Category</b>", header_cell),
                Paragraph("<b>Amount</b>", header_cell),
                Paragraph("<b>%</b>", header_cell),
            ]]
            for c in cats:
                pct = (c['amount'] / total * 100) if total else 0
                rows.append([
                    Paragraph(c['name'], cell_style),
                    Paragraph(f"${c['amount']:,.2f}", right_cell),
                    Paragraph(f"{pct:.1f}%", right_cell),
                ])
            rows.append([
                Paragraph("<b>Total</b>", ParagraphStyle('TotalLabel', parent=cell_style, textColor=HexColor('#1a3a5c'), fontName='Helvetica-Bold')),
                Paragraph(f"<b>${total:,.2f}</b>", ParagraphStyle('TotalVal', parent=right_cell, textColor=HexColor('#1a3a5c'), fontName='Helvetica-Bold')),
                Paragraph("", right_cell),
            ])
            table = Table(rows, colWidths=[4.2*inch, 1.4*inch, 0.8*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1a3a5c')),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BACKGROUND', (0, 1), (-1, -2), HexColor('#f6f8fa')),
                ('BACKGROUND', (0, -1), (-1, -1), HexColor('#e8eef5')),
                ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#d0d7de')),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(table)

        elif kind == 'transaction_summary':
            summary = section.get('summary', {})
            elements.append(Paragraph(
                f"Residents: {summary.get('resident_count', 0)} | "
                f"Transactions: {summary.get('transaction_count', 0)} | "
                f"Total: ${summary.get('total_amount', 0):,.2f}",
                s['body']
            ))
            elements.append(Paragraph("Full per-resident transaction tables are included at the end of this PDF.",
                ParagraphStyle('Note', parent=s['body'], textColor=HexColor('#656d76'), fontSize=8.5)))

        elif kind == 'coverage_alert':
            cov = section.get('coverage', {})
            if cov:
                alert = Table([[Paragraph(f"<b>{cov.get('headline', '')}</b> {cov.get('detail', '')}", s['body'])]],
                              colWidths=[6.4*inch])
                alert.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor(cov.get('bg', '#f0fdf4'))),
                    ('BOX', (0, 0), (-1, -1), 0.5, HexColor(cov.get('border', '#bbf7d0'))),
                    ('LEFTPADDING', (0, 0), (-1, -1), 10),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ]))
                elements.append(alert)

        elif kind == 'absence_table':
            rows = [[
                Paragraph("<b>Name</b>", header_cell),
                Paragraph("<b>Dates</b>", header_cell),
                Paragraph("<b>Reason</b>", header_cell),
                Paragraph("<b>Status</b>", header_cell),
            ]]
            for a in section.get('absences', []):
                late = " 🔔 late" if a.get('late') else ""
                rows.append([
                    Paragraph(f"{a['name']}{late}", cell_style),
                    Paragraph(a.get('dates', ''), cell_style),
                    Paragraph(a.get('reason', ''), cell_style),
                    Paragraph(a.get('status', ''), ParagraphStyle('StatusCell', parent=cell_style, textColor=HexColor(a.get('status_color', '#333333')))),
                ])
            if not rows[1:]:
                rows.append([
                    Paragraph("No absences recorded.", cell_style),
                    Paragraph("", cell_style), Paragraph("", cell_style), Paragraph("", cell_style)
                ])
            table = Table(rows, colWidths=[1.8*inch, 1.4*inch, 2.0*inch, 1.0*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1a3a5c')),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BACKGROUND', (0, 1), (-1, -1), HexColor('#f6f8fa')),
                ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#d0d7de')),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(table)

        elif kind == 'department_table':
            rows = [[Paragraph("<b>Department</b>", header_cell),
                     Paragraph("<b>Absences</b>", header_cell)]]
            for d in section.get('departments', []):
                rows.append([Paragraph(d['name'], cell_style),
                             Paragraph(str(d['count']), right_cell)])
            table = Table(rows, colWidths=[4.6*inch, 1.6*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1a3a5c')),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('BACKGROUND', (0, 1), (-1, -1), HexColor('#f6f8fa')),
                ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#d0d7de')),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(table)

        elif kind == 'gme_summary':
            gme = section.get('gme', {})
            elements.append(Paragraph(
                f"<b>{gme.get('resident_count', 0)}</b> residents tracked. "
                f"Total used: <b>${gme.get('total_used', 0):,.2f}</b>; "
                f"remaining: <b>${gme.get('total_remaining', 0):,.2f}</b>.",
                s['body']
            ))
            if gme.get('alert'):
                elements.append(Paragraph(
                    f"&#9888; <b>Attention:</b> {gme['alert']['text']}", s['warning']
                ))

        elif kind == 'coverage_summary':
            cov = section.get('coverage', {})
            elements.append(Paragraph(
                f"<b>{cov.get('future_shifts', 'N/A')}</b> future shifts on file. "
                f"{cov.get('status_text', '')}",
                s['body']
            ))

        elif kind == 'absence_summary':
            absences = section.get('absences', [])
            if absences:
                for a in absences[:5]:
                    late = " (late call-out)" if a.get('late') else ""
                    elements.append(Paragraph(
                        f"&bull; {a['name']}: {a.get('dates', '')} — {a['status']}{late}", s['body']
                    ))
                if len(absences) > 5:
                    elements.append(Paragraph(f"... and {len(absences) - 5} more in the PDF.", s['body']))
            else:
                elements.append(Paragraph("No absences recorded this week.", s['highlight']))

        elements.append(Spacer(1, 8))

        # Chart placement near relevant section
        chart_path = section.get('chart_path')
        if chart_path and Path(chart_path).exists():
            try:
                img_size = _png_size(chart_path)
                if img_size:
                    w_px, h_px = img_size
                    aspect = w_px / h_px
                else:
                    aspect = 2.4
                max_width = 6.5 * inch
                img = Image(str(chart_path), width=max_width, height=max_width/aspect)
                elements.append(KeepTogether([Spacer(1, 6), img, Spacer(1, 10)]))
            except Exception as e:
                elements.append(Paragraph(f"Chart unavailable: {e}", s['body']))

        # Support a second chart for the same section (e.g. full report GME)
        chart_path2 = section.get('chart_path2')
        if chart_path2 and Path(chart_path2).exists():
            try:
                img_size = _png_size(chart_path2)
                if img_size:
                    w_px, h_px = img_size
                    aspect = w_px / h_px
                else:
                    aspect = 2.4
                max_width = 6.5 * inch
                img = Image(str(chart_path2), width=max_width, height=max_width/aspect)
                elements.append(KeepTogether([Spacer(1, 6), img, Spacer(1, 10)]))
            except Exception as e:
                elements.append(Paragraph(f"Chart unavailable: {e}", s['body']))

    # Footer generation timestamp
    elements.append(Spacer(1, 18))
    elements.append(Paragraph(
        f"<i>Generated by Hermes Agent — {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}</i>",
        ParagraphStyle('Footer', parent=s['body'], textColor=HexColor('#484f58'), fontSize=8, alignment=TA_CENTER)
    ))

    first_cb = lambda canvas, doc: _first_page_header_footer(canvas, doc, report_name, date_str)
    later_cb = lambda canvas, doc: _later_pages_header_footer(canvas, doc, report_name, date_str)

    try:
        doc.build(elements, onFirstPage=first_cb, onLaterPages=later_cb)
    except Exception as e:
        print(f"  ⚠️  PDF build failed: {e}")
        fallback = [Paragraph(report_name, s['title']), Spacer(1, 12)]
        for m in report_data.get('metrics', []):
            fallback.append(Paragraph(f"{m['label']}: {m['value']}", s['body']))
        doc.build(fallback, onFirstPage=first_cb, onLaterPages=later_cb)

    return output_path


def generate_transactions_pdf(grouped_transactions, output_path):
    """Generate a separate PDF containing per-resident transaction tables."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

    report_name = "GME Transactions by Resident"
    date_str = datetime.now().strftime("%B %d, %Y")

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TxnTitle', parent=styles['Title'],
        textColor=HexColor('#1a3a5c'),
        fontSize=18, spaceAfter=14, alignment=TA_CENTER,
    )
    resident_style = ParagraphStyle(
        'TxnResident', parent=styles['Heading2'],
        textColor=HexColor('#1a3a5c'),
        fontSize=13, spaceBefore=16, spaceAfter=6, alignment=TA_LEFT,
    )
    body_style = ParagraphStyle(
        'TxnBody', parent=styles['Normal'],
        textColor=HexColor('#333333'),
        fontSize=9, leading=12,
    )
    right_style = ParagraphStyle('TxnRight', parent=body_style, alignment=TA_RIGHT)

    elements = []
    elements.append(Paragraph(report_name, title_style))
    elements.append(Paragraph(
        f"Montefiore Urology Department — {date_str}",
        ParagraphStyle('TxnSub', parent=body_style, textColor=HexColor('#656d76'),
                       alignment=TA_CENTER, spaceAfter=16)
    ))

    if not grouped_transactions:
        elements.append(Spacer(1, 30))
        elements.append(Paragraph(
            "No approved GME transactions were found in the reimbursement database.",
            body_style
        ))
        doc.build(elements)
        return output_path

    for resident_name in sorted(grouped_transactions.keys()):
        transactions = grouped_transactions[resident_name]
        resident_block = [Paragraph(resident_name, resident_style)]

        table_data = [[
            Paragraph("<b>Date</b>", body_style),
            Paragraph("<b>Description</b>", body_style),
            Paragraph("<b>Amount</b>", right_style),
        ]]

        total = 0.0
        for txn in transactions:
            amount = float(txn.get('amount', 0) or 0)
            total += amount
            table_data.append([
                Paragraph(str(txn.get('date', '')), body_style),
                Paragraph(str(txn.get('description', '')), body_style),
                Paragraph(f"${amount:,.2f}", right_style),
            ])

        table_data.append([
            Paragraph("", body_style),
            Paragraph("<b>Total</b>", ParagraphStyle('TxnTotalLabel', parent=right_style, textColor=HexColor('#1a3a5c'))),
            Paragraph(f"<b>${total:,.2f}</b>", ParagraphStyle('TxnTotal', parent=right_style, textColor=HexColor('#1a3a5c'))),
        ])

        table = Table(
            table_data,
            colWidths=[1.1 * inch, 4.8 * inch, 1.1 * inch],
            repeatRows=1,
        )
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1a3a5c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -2), HexColor('#f6f8fa')),
            ('BACKGROUND', (0, -1), (-1, -1), HexColor('#e8eef5')),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#d0d7de')),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
        ]))

        resident_block.append(table)
        resident_block.append(Spacer(1, 10))
        elements.extend(resident_block)

    def _txn_header_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica-Bold', 8)
        canvas.setFillColorRGB(0.10, 0.23, 0.36)
        canvas.drawString(0.6 * 72, 10.6 * 72, "Montefiore Einstein Urology")
        canvas.setFont('Helvetica', 8)
        canvas.setFillColorRGB(0.40, 0.44, 0.48)
        canvas.drawRightString(7.9 * 72, 10.6 * 72, report_name)
        canvas.line(0.6 * 72, 10.45 * 72, 7.9 * 72, 10.45 * 72)
        canvas.setFont('Helvetica', 8)
        canvas.setFillColorRGB(0.61, 0.64, 0.67)
        canvas.drawCentredString(4.25 * 72, 0.5 * 72, f"Page {doc.page}  |  {date_str}")
        canvas.restoreState()

    doc.build(elements, onFirstPage=_txn_header_footer, onLaterPages=_txn_header_footer)
    return output_path


def merge_pdfs(source_paths, output_path):
    from pypdf import PdfWriter, PdfReader
    writer = PdfWriter()
    for path in source_paths:
        reader = PdfReader(str(path))
        for page in reader.pages:
            writer.add_page(page)
    with open(output_path, 'wb') as f:
        writer.write(f)
    return output_path


# ─── Report Data Builders ───────────────────────────────────────────

def _fmt_money(value):
    try:
        return f"${float(value):,.2f}"
    except (TypeError, ValueError):
        return str(value)


def generate_gme_report_data(residents, allocations_data, gme_summary, grouped_transactions=None):
    data = {
        'report_type': 'gme',
        'report_name': 'GME Reimbursement Report',
        'date_str': datetime.now().strftime("%B %d, %Y"),
        'academic_year': _academic_year_str(),
        'transactions': grouped_transactions or {},
    }

    # Prefer cached resident data from the Drive spreadsheet
    resident_list = []
    if gme_summary:
        resident_list = gme_summary.get('residents', [])
    if not resident_list:
        resident_list = residents
    annual_cap = 1250.0
    total_used = 0.0
    total_remaining = 0.0

    enriched = []
    for r in resident_list:
        pct = r.get('usage_pct', r.get('gme_pct', 0))
        used = r.get('gme_used', 0)
        remaining = r.get('remaining', r.get('gme_remaining', 0))
        cap = r.get('annual_cap', 1250.0)
        annual_cap = cap if cap else annual_cap
        total_used += float(used or 0)
        total_remaining += float(remaining or 0)
        enriched.append({
            'name': r.get('name', 'Unknown'),
            'class': r.get('cls', ''),
            'gme_used': used,
            'gme_remaining': remaining,
            'pct': pct,
            'annual_cap': cap,
        })

    enriched.sort(key=lambda x: float(x['pct'] or 0), reverse=True)

    data['metrics'] = [
        {'label': 'Total Residents', 'value': len(enriched)},
        {'label': 'GME Used', 'value': _fmt_money(total_used)},
        {'label': 'GME Remaining', 'value': _fmt_money(total_remaining)},
        {'label': 'Cap/Resident', 'value': _fmt_money(annual_cap)},
    ]

    data['residents'] = enriched

    categories = []
    if allocations_data and allocations_data.get('items'):
        cat_totals = defaultdict(float)
        for item in allocations_data['items']:
            acct = item.get('account', 'Unknown')
            cat_totals[acct] += float(item.get('amount', 0))
        for cat, amt in sorted(cat_totals.items(), key=lambda x: -x[1]):
            categories.append({'name': cat, 'amount': amt})

    txn_summary = gme_transactions.transaction_summary(grouped_transactions or {})

    data['sections'] = [
        {'heading': 'Resident Breakdown', 'kind': 'resident_table', 'residents': enriched},
        {'heading': 'Spending by Category', 'kind': 'category_table', 'categories': categories},
        {'heading': 'Approved GME Transactions', 'kind': 'transaction_summary', 'summary': txn_summary},
    ]

    data['gme'] = {
        'resident_count': len(enriched),
        'total_used': total_used,
        'total_remaining': total_remaining,
        'annual_cap': annual_cap,
        'alert': None,
    }
    if enriched and any(r['pct'] >= 100 for r in enriched):
        exhausted = [r['name'] for r in enriched if r['pct'] >= 100]
        data['gme']['alert'] = {
            'text': f"Cap exhausted for: {', '.join(exhausted[:5])}{'...' if len(exhausted) > 5 else ''}",
            'color': '#991b1b', 'bg': '#fef2f2', 'border': '#fecaca',
        }

    return data


def generate_coverage_report_data(today_data, residents):
    data = {
        'report_type': 'coverage',
        'report_name': 'Coverage Gap Analysis',
        'date_str': datetime.now().strftime("%B %d, %Y"),
        'date_range': _date_range_str(),
    }

    if not today_data:
        data['metrics'] = [{'label': 'Status', 'value': 'Unavailable'}]
        data['coverage_status'] = {'headline': 'Data unavailable', 'detail': 'Could not retrieve coverage data.', 'color': '#991b1b', 'bg': '#fef2f2', 'border': '#fecaca'}
        data['absences'] = []
        data['sections'] = [
            {'heading': 'Coverage Status', 'kind': 'coverage_alert', 'coverage': data['coverage_status']},
        ]
        return data

    urosched = today_data.get('urosched', {})
    sick = today_data.get('sick_call', {})

    locations = urosched.get('locations', [])
    loc_names = [l.get('name', '?') for l in locations]

    today_shifts = urosched.get('today_shifts', 0)
    total_shifts = urosched.get('total_shifts', 0)
    future_shifts = urosched.get('future_shifts', 0)
    absences = sick.get('absences', [])

    data['metrics'] = [
        {'label': 'Locations', 'value': ', '.join(loc_names) if loc_names else 'N/A'},
        {'label': 'Total Shifts', 'value': total_shifts},
        {'label': "Today's Shifts", 'value': today_shifts},
        {'label': 'Future Shifts', 'value': future_shifts},
    ]

    if future_shifts == 0 and total_shifts == 0:
        coverage = {'headline': 'No future shifts scheduled.', 'detail': 'Coverage may be incomplete.', 'color': '#991b1b', 'bg': '#fef2f2', 'border': '#fecaca'}
    elif future_shifts < 10:
        coverage = {'headline': 'Low future shift count.', 'detail': 'Verify coverage is complete.', 'color': '#b45309', 'bg': '#fef3c7', 'border': '#fde68a'}
    else:
        coverage = {'headline': 'All shifts covered.', 'detail': f'{future_shifts} future shifts on file.', 'color': '#065f46', 'bg': '#f0fdf4', 'border': '#bbf7d0'}
    data['coverage_status'] = coverage

    absence_rows = []
    for a in absences:
        start = a.get('start_date', '')[:10]
        end = a.get('end_date', '')[:10]
        dates = f"{start}" + (f" → {end}" if end and end != start else "")
        status = a.get('status', '')
        absence_rows.append({
            'name': a.get('employee_name', 'Unknown'),
            'dates': dates,
            'reason': a.get('reason', ''),
            'status': status,
            'status_color': '#16a34a' if status == 'approved' else '#f59e0b' if status == 'pending' else '#dc2626',
            'late': bool(a.get('is_late_callout')),
        })
    data['absences'] = absence_rows

    data['sections'] = [
        {'heading': 'Coverage Status', 'kind': 'coverage_alert', 'coverage': coverage},
        {'heading': 'Absences This Week', 'kind': 'absence_table', 'absences': absence_rows},
    ]

    data['coverage'] = {
        'future_shifts': future_shifts,
        'status_text': coverage['detail'],
    }

    return data


def generate_absence_report_data(today_data):
    data = {
        'report_type': 'absences',
        'report_name': 'Absence Summary Report',
        'date_str': datetime.now().strftime("%B %d, %Y"),
        'week_start': _week_start_str(),
    }

    if not today_data:
        data['metrics'] = [{'label': 'Status', 'value': 'Unavailable'}]
        data['absences'] = []
        data['departments'] = []
        data['sections'] = [
            {'heading': 'Detailed List', 'kind': 'absence_table', 'absences': []},
        ]
        return data

    sick = today_data.get('sick_call', {})
    absences = sick.get('absences', [])
    depts = sick.get('employees_by_dept', {})

    data['metrics'] = [
        {'label': 'Total Absences', 'value': len(absences)},
        {'label': 'Pending', 'value': sick.get('pending', 0)},
        {'label': 'Approved', 'value': sick.get('approved', 0)},
        {'label': 'Departments', 'value': len(depts)},
    ]

    departments = [{'name': k, 'count': v} for k, v in sorted(depts.items(), key=lambda x: -x[1])]
    data['departments'] = departments

    absence_rows = []
    for a in absences:
        start = a.get('start_date', '')[:10]
        end = a.get('end_date', '')[:10]
        dates = f"{start}" + (f" → {end}" if end and end != start else "")
        status = a.get('status', '')
        absence_rows.append({
            'name': a.get('employee_name', 'Unknown'),
            'dates': dates,
            'reason': a.get('reason', 'Personal'),
            'status': status,
            'status_color': '#16a34a' if status == 'approved' else '#f59e0b' if status == 'pending' else '#dc2626',
            'late': bool(a.get('is_late_callout')),
        })
    data['absences'] = absence_rows

    sections = []
    if departments:
        sections.append({'heading': 'By Department', 'kind': 'department_table', 'departments': departments})
    sections.append({'heading': 'Detailed List', 'kind': 'absence_table', 'absences': absence_rows})
    data['sections'] = sections

    return data


def generate_full_report_data(gme_data, coverage_data, absence_data):
    data = {
        'report_type': 'full',
        'report_name': 'Consolidated Operations Report',
        'date_str': datetime.now().strftime("%B %d, %Y"),
        'date_range': coverage_data.get('date_range') or _date_range_str(),
        'transactions': gme_data.get('transactions', {}),
    }

    gme = gme_data.get('gme', {})
    cov = coverage_data.get('coverage', {})

    data['metrics'] = [
        {'label': 'GME Used', 'value': _fmt_money(gme.get('total_used', 0))},
        {'label': 'GME Remaining', 'value': _fmt_money(gme.get('total_remaining', 0))},
        {'label': 'Future Shifts', 'value': cov.get('future_shifts', 'N/A')},
        {'label': 'Absences', 'value': len(absence_data.get('absences', []))},
    ]

    data['sections'] = [
        {'heading': '1. GME Reimbursement', 'kind': 'gme_summary', 'gme': gme},
        {'heading': '2. Coverage', 'kind': 'coverage_summary', 'coverage': cov},
        {'heading': '3. Absences', 'kind': 'absence_summary', 'absences': absence_data.get('absences', [])},
    ]

    data['gme'] = gme
    data['coverage'] = cov
    data['absences'] = absence_data.get('absences', [])

    return data


def render_report_text(report_data):
    """Render a plain-text summary from report data for stdout/JSON."""
    lines = []
    lines.append(report_data.get('report_name', 'Report'))
    lines.append(report_data.get('date_str', ''))
    lines.append("")
    for m in report_data.get('metrics', []):
        lines.append(f"{m['label']}: {m['value']}")
    lines.append("")

    for section in report_data.get('sections', []):
        heading = section.get('heading', '')
        lines.append(f"# {heading}")
        kind = section.get('kind', '')

        if kind == 'resident_table':
            for r in section.get('residents', []):
                icon = '❗' if r['pct'] >= 80 else '⚠️' if r['pct'] >= 50 else '✅'
                lines.append(f"{icon} {r['name']} ({r['class']}): {_fmt_money(r['gme_used'])} used, {_fmt_money(r['gme_remaining'])} remaining ({r['pct']:.0f}%)")

        elif kind == 'category_table':
            for c in section.get('categories', []):
                lines.append(f"  {c['name']}: {_fmt_money(c['amount'])}")

        elif kind == 'transaction_summary':
            s = section.get('summary', {})
            lines.append(f"  Residents: {s.get('resident_count', 0)} | Transactions: {s.get('transaction_count', 0)} | Total: {_fmt_money(s.get('total_amount', 0))}")

        elif kind == 'coverage_alert':
            cov = section.get('coverage', {})
            lines.append(f"  {cov.get('headline', '')} {cov.get('detail', '')}")

        elif kind == 'absence_table':
            for a in section.get('absences', []):
                late = " [late]" if a.get('late') else ""
                lines.append(f"  • {a['name']}: {a['dates']} — {a['reason']} ({a['status']}){late}")

        elif kind == 'department_table':
            for d in section.get('departments', []):
                lines.append(f"  • {d['name']}: {d['count']}")

        elif kind == 'gme_summary':
            gme = section.get('gme', {})
            lines.append(f"  {gme.get('resident_count', 0)} residents, {_fmt_money(gme.get('total_used', 0))} used, {_fmt_money(gme.get('total_remaining', 0))} remaining")
            if gme.get('alert'):
                lines.append(f"  ⚠️ {gme['alert']['text']}")

        elif kind == 'coverage_summary':
            cov = section.get('coverage', {})
            lines.append(f"  {cov.get('future_shifts', 'N/A')} future shifts. {cov.get('status_text', '')}")

        elif kind == 'absence_summary':
            absences = section.get('absences', [])
            if absences:
                for a in absences[:5]:
                    late = " [late]" if a.get('late') else ""
                    lines.append(f"  • {a['name']}: {a['dates']} ({a['status']}){late}")
                if len(absences) > 5:
                    lines.append(f"  ... and {len(absences) - 5} more")
            else:
                lines.append("  No absences recorded.")

        lines.append("")

    return '\n'.join(lines)


# ─── Main Report Pipeline ───────────────────────────────────────────

def generate_report(report_type='full', email_to=None, recipient_name="Team"):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_dir = OUTPUT_DIR / f"{report_type}_{timestamp}"
    report_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  Montefiore Urology — Report Generator")
    print(f"  Type: {report_type.upper()}")
    print(f"  Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}")
    print(f"{'='*60}\n")

    print("Fetching data...")
    residents = get_residents()
    today_data = get_today()
    gme_summary = get_gme_data()
    allocations = get_allocations(account='GME', limit=500)

    print(f"  Residents: {len(residents)}")
    if today_data:
        print(f"  Absences this week: {today_data.get('sick_call', {}).get('absences_this_week', 'N/A')}")
        print(f"  UroSched shifts: {today_data.get('urosched', {}).get('total_shifts', 'N/A')}")

    grouped_transactions = {}
    chart_paths = []
    report_data = None

    # Build data objects
    if report_type == 'gme':
        grouped_transactions = gme_transactions.transactions_by_resident(
            status='complete', account_filter='GME', db_path=REIMBURSEMENT_DB
        )
        report_data = generate_gme_report_data(residents, allocations, gme_summary, grouped_transactions)

        bar_chart = generate_gme_bar_chart(report_data['residents'])
        bar_path = report_dir / "gme_bar.png"
        with open(bar_path, 'wb') as f:
            f.write(bar_chart.read())
        chart_paths.append(bar_path)
        report_data['sections'][0]['chart_path'] = bar_path
        print(f"  ✅ GME bar chart: {bar_path}")

        cat_chart = generate_gme_category_chart(allocations)
        cat_path = report_dir / "gme_category.png"
        with open(cat_path, 'wb') as f:
            f.write(cat_chart.read())
        chart_paths.append(cat_path)
        report_data['sections'][1]['chart_path'] = cat_path
        print(f"  ✅ GME category chart: {cat_path}")

    elif report_type == 'coverage':
        report_data = generate_coverage_report_data(today_data, residents)

    elif report_type == 'absences':
        report_data = generate_absence_report_data(today_data)
        trend_chart = generate_absence_trend_chart(today_data)
        trend_path = report_dir / "absence_trend.png"
        with open(trend_path, 'wb') as f:
            f.write(trend_chart.read())
        chart_paths.append(trend_path)
        # attach chart to the last absence section
        if report_data['sections']:
            report_data['sections'][-1]['chart_path'] = trend_path
        print(f"  ✅ Absence trend chart: {trend_path}")

    elif report_type == 'full':
        grouped_transactions = gme_transactions.transactions_by_resident(
            status='complete', account_filter='GME', db_path=REIMBURSEMENT_DB
        )
        gme_data = generate_gme_report_data(residents, allocations, gme_summary, grouped_transactions)
        coverage_data = generate_coverage_report_data(today_data, residents)
        absence_data = generate_absence_report_data(today_data)
        report_data = generate_full_report_data(gme_data, coverage_data, absence_data)
        report_data['transactions'] = grouped_transactions

        bar_chart = generate_gme_bar_chart(gme_data['residents'])
        bar_path = report_dir / "gme_bar.png"
        with open(bar_path, 'wb') as f:
            f.write(bar_chart.read())
        chart_paths.append(bar_path)
        # attach to GME section
        report_data['sections'][0]['chart_path'] = bar_path
        print(f"  ✅ GME bar chart: {bar_path}")

        cat_chart = generate_gme_category_chart(allocations)
        cat_path = report_dir / "gme_category.png"
        with open(cat_path, 'wb') as f:
            f.write(cat_chart.read())
        chart_paths.append(cat_path)
        # full report doesn't have a category section, so place after GME
        report_data['sections'][0]['chart_path2'] = cat_path
        print(f"  ✅ GME category chart: {cat_path}")

        if today_data and today_data.get('sick_call', {}).get('absences'):
            trend_chart = generate_absence_trend_chart(today_data)
            trend_path = report_dir / "absence_trend.png"
            with open(trend_path, 'wb') as f:
                f.write(trend_chart.read())
            chart_paths.append(trend_path)
            report_data['sections'][2]['chart_path'] = trend_path
            print(f"  ✅ Absence trend chart: {trend_path}")

    text_content = render_report_text(report_data)

    # Generate PDF
    print("\n📄 Generating PDF...")
    pdf_path = report_dir / f"{report_type}_report.pdf"
    generate_pdf(report_data, pdf_path)

    # For GME reports, append per-resident transaction pages and merge
    if report_type in ('gme', 'full') and grouped_transactions:
        try:
            transactions_pdf_path = report_dir / "gme_transactions.pdf"
            generate_transactions_pdf(grouped_transactions, transactions_pdf_path)
            merged_path = report_dir / f"{report_type}_report_merged.pdf"
            merge_pdfs([pdf_path, transactions_pdf_path], merged_path)
            merged_path.replace(pdf_path)
            print(f"  ✅ Transaction pages appended ({transactions_pdf_path.name})")
        except Exception as e:
            print(f"  ⚠️  Could not append transaction PDF pages: {e}")

    print(f"  ✅ PDF: {pdf_path}")

    # Email delivery
    if email_to:
        print(f"\n📧 Sending email to {email_to}...")
        try:
            send_report.send(report_type, report_data, str(pdf_path), email_to, recipient_name=recipient_name)
        except Exception as e:
            print(f"  ❌ Email failed: {e}")

    # Summary to stdout
    if not args.quiet:
        print(f"\n{'='*60}")
        print(f"  REPORT SUMMARY")
        print(f"{'='*60}")
        lines = text_content.split('\n')
        for line in lines[:55]:
            if line.strip():
                print(f"  {line.strip()}")
        if len(lines) > 55:
            print(f"  ... (+{len(lines)-55} more lines in PDF)")
        print(f"\n  📎 Charts: {len(chart_paths)} generated")
        print(f"  📄 PDF: {pdf_path}")
        if email_to:
            print(f"  📧 Email: {email_to}")
        print(f"{'='*60}\n")

    return {
        'type': report_type,
        'timestamp': timestamp,
        'text_content': text_content,
        'chart_paths': [str(p) for p in chart_paths],
        'pdf_path': str(pdf_path),
        'report_dir': str(report_dir),
        'report_data': report_data,
        'gme_summary': gme_summary,
        'today_data': today_data,
        'grouped_transactions': grouped_transactions,
        'transaction_summary': gme_transactions.transaction_summary(grouped_transactions or {}),
    }


# ─── Retention ──────────────────────────────────────────────────────

def print_json_result(result):
    output = {
        'status': 'ok',
        'type': result['type'],
        'report_name': result.get('report_data', {}).get('report_name', ''),
        'pdf_path': str(result['pdf_path']),
        'text_content': result['text_content'][:2000],
        'charts': len(result['chart_paths']),
        'transactions': result['transaction_summary'],
    }
    print(f"\n---JSON_OUTPUT---\n{json.dumps(output)}\n---END_JSON---")


def enforce_report_retention(max_days=30):
    cutoff = datetime.now() - timedelta(days=max_days)
    for item in OUTPUT_DIR.iterdir():
        if item.is_dir() and item.name != "latest":
            try:
                mtime = datetime.fromtimestamp(item.stat().st_mtime)
                if mtime < cutoff:
                    shutil.rmtree(item)
                    print(f"  🗑️  Removed stale report: {item.name}")
            except Exception as e:
                print(f"  ⚠️  Could not remove stale report {item.name}: {e}")


# ─── CLI Entry Point ────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Montefiore Urology Report Generator")
    parser.add_argument('--type', choices=['gme', 'coverage', 'absences', 'full'],
                        default='full', help='Report type to generate')
    parser.add_argument('--email', type=str, default=None,
                        help='Email address to send the PDF to')
    parser.add_argument('--recipient-name', type=str, default="Team",
                        help='First name to use in email greeting')
    parser.add_argument('--quiet', action='store_true',
                        help='Minimal output (for cron/script mode)')
    parser.add_argument('--json', action='store_true',
                        help='Output structured JSON for programmatic consumers')

    global args
    args = parser.parse_args()

    lock_fd = acquire_lock()
    try:
        result = generate_report(report_type=args.type, email_to=args.email,
                                 recipient_name=args.recipient_name)
    except Exception as e:
        print(f"  ❌ Report generation failed: {e}")
        import traceback
        traceback.print_exc()
        release_lock(lock_fd)
        sys.exit(1)

    try:
        update_latest_symlink(Path(result['report_dir']), args.type)
    except Exception as e:
        print(f"  ⚠️  Could not update latest/ directory: {e}")

    release_lock(lock_fd)

    try:
        enforce_report_retention()
    except Exception as e:
        print(f"  ⚠️  Retention cleanup failed: {e}")

    if not args.quiet:
        print(f"\nReport saved to: {result['report_dir']}/")
        print(f"PDF: {result['pdf_path']}")

    if args.json:
        print_json_result(result)
