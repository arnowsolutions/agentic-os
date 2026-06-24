"""Vapi email module — generate and email professional schedule PDFs."""
import io
import os
import re
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from modules import vapi_unified
from modules.config import get_settings

NAVY = colors.HexColor("#1a3a5c")
LIGHT_GRAY = colors.HexColor("#f4f6f9")
WHITE = colors.white
DARK_TEXT = colors.HexColor("#333333")

SCHEDULE_PATH = "/workspace/Call_Schedule_Q3_Q4_2026.xlsx"


def _fetch_schedule_data(
    date_str: Optional[str] = None,
    period: Optional[str] = None,
    person_name: Optional[str] = None,
) -> dict:
    """Fetch schedule data based on query parameters."""
    if person_name:
        return vapi_unified.call_month(person_name)
    if period == "month" or period == "30days":
        start = date.today()
        end = start + timedelta(days=30)
        return {"date_range": f"{start} - {end}", "data": "full month"}

    by_date = vapi_unified.schedule_by_date(date_str or date.today().strftime("%Y-%m-%d"))
    return by_date


def _format_date(dt) -> str:
    if hasattr(dt, "strftime"):
        return dt.strftime("%Y-%m-%d")
    return str(dt)[:10]


def _normalize_entries(schedule_data: dict) -> list:
    """Convert various schedule_data shapes into a flat list of entries."""
    entries = []

    # Single date with campuses
    if "campuses" in schedule_data:
        for campus_name, coverage in schedule_data["campuses"].items():
            entries.append({
                "date": schedule_data.get("date", ""),
                "day": schedule_data.get("day", ""),
                "campus": campus_name,
                "primary": coverage.get("primary", "—") or "—",
                "backup": coverage.get("backup", "—") or "—",
                "peds": coverage.get("peds", "—") or "—",
            })
        return entries

    # Person schedule results
    if "results" in schedule_data:
        for r in schedule_data["results"]:
            entries.append({
                "date": r.get("date", ""),
                "day": r.get("day", ""),
                "campus": r.get("campus", ""),
                "primary": r.get("primary", r.get("role", "—")) or "—",
                "backup": r.get("backup", "—") or "—",
                "peds": r.get("peds", "—") or "—",
            })
        return entries

    # Weekend / multi-date per campus
    if "dates" in schedule_data:
        for campus, rows in schedule_data.items():
            if campus == "dates":
                continue
            if isinstance(rows, list):
                for r in rows:
                    entries.append({
                        "date": r.get("date", ""),
                        "day": r.get("day", ""),
                        "campus": campus.title() if campus else "",
                        "primary": r.get("primary", "—") or "—",
                        "backup": r.get("backup", "—") or "—",
                        "peds": r.get("peds", "—") or "—",
                    })
        return entries

    return entries


def build_schedule_pdf(
    schedule_data: dict,
    title: str = "Call Schedule",
    subtitle: str = "",
) -> str:
    """Build a professional PDF of schedule data. Returns file path."""
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    pdf_path = tmp.name
    tmp.close()

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=landscape(letter),
        topMargin=0.5 * inch,
        bottomMargin=0.4 * inch,
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
    )

    styles = getSampleStyleSheet()
    body_style = ParagraphStyle("Body", parent=styles["Normal"], fontSize=8, leading=10, textColor=DARK_TEXT)
    header_style = ParagraphStyle("Header", parent=styles["Normal"], fontSize=18, leading=22, textColor=colors.white, alignment=TA_LEFT)
    sub_style = ParagraphStyle("Sub", parent=styles["Normal"], fontSize=10, leading=14, textColor=colors.white)
    cell_style = ParagraphStyle("Cell", parent=styles["Normal"], fontSize=7.5, leading=9, textColor=DARK_TEXT)
    title_style = ParagraphStyle("Title", parent=styles["Normal"], fontSize=14, leading=18, textColor=colors.black)

    elements = []

    # Navy header
    header_data = [[Paragraph(f"Montefiore Einstein Urology", header_style)]]
    if subtitle:
        header_data[0].append(Paragraph(subtitle, sub_style))
    else:
        header_data[0].append(Paragraph(datetime.now().strftime("%B %d, %Y"), sub_style))

    header_table = Table(header_data, colWidths=[6 * inch, 3.5 * inch])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, -1), WHITE),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.15 * inch))

    # Title
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 0.1 * inch))

    entries = _normalize_entries(schedule_data)

    if entries:
        # If all entries share the same date, show one row per campus
        same_date = len(set(e.get("date", "") for e in entries)) == 1
        if same_date:
            rows = [[
                Paragraph("<b>Campus</b>", cell_style),
                Paragraph("<b>Primary Attending</b>", cell_style),
                Paragraph("<b>Backup Attending</b>", cell_style),
                Paragraph("<b>PEDS Attending</b>", cell_style),
            ]]
            for e in entries:
                rows.append([
                    Paragraph(e.get("campus", ""), cell_style),
                    Paragraph(e.get("primary", "—"), cell_style),
                    Paragraph(e.get("backup", "—"), cell_style),
                    Paragraph(e.get("peds", "—"), cell_style),
                ])
            table = Table(rows, colWidths=[1.2 * inch, 2.5 * inch, 2.5 * inch, 2.5 * inch])
        else:
            rows = [[
                Paragraph("<b>Date</b>", cell_style),
                Paragraph("<b>Day</b>", cell_style),
                Paragraph("<b>Campus</b>", cell_style),
                Paragraph("<b>Primary</b>", cell_style),
                Paragraph("<b>Backup</b>", cell_style),
                Paragraph("<b>PEDS</b>", cell_style),
            ]]
            for e in entries:
                rows.append([
                    Paragraph(e.get("date", ""), cell_style),
                    Paragraph(e.get("day", ""), cell_style),
                    Paragraph(e.get("campus", ""), cell_style),
                    Paragraph(e.get("primary", "—"), cell_style),
                    Paragraph(e.get("backup", "—"), cell_style),
                    Paragraph(e.get("peds", "—"), cell_style),
                ])
            table = Table(rows, colWidths=[1.0 * inch, 0.8 * inch, 1.0 * inch, 2.0 * inch, 2.0 * inch, 2.0 * inch])

        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("BACKGROUND", (0, 1), (-1, -1), WHITE),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d0d4d8")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(table)
    elif "note" in schedule_data:
        elements.append(Paragraph(schedule_data["note"], body_style))
    else:
        elements.append(Paragraph("No coverage data available for the requested date.", body_style))

    # Footer note
    elements.append(Spacer(1, 0.2 * inch))
    elements.append(Paragraph(
        "Montefiore Urology &bull; Call Schedule &bull; Generated automatically",
        ParagraphStyle("Footer", parent=styles["Normal"], fontSize=7, textColor=colors.HexColor("#999999"), alignment=TA_CENTER),
    ))

    doc.build(elements)
    return pdf_path


def _build_email_schedule_table(entries: list) -> str:
    """Build an HTML table string from schedule entries for the email body."""
    if not entries:
        return "<p>No schedule data available.</p>"

    same_date = len(set(e.get("date", "") for e in entries)) == 1
    if same_date:
        rows = "".join(f"""
            <tr style="border-bottom:1px solid #d0d4d8">
                <td style="padding:8px 6px">{e.get('campus', '')}</td>
                <td style="padding:8px 6px">{e.get('primary', '—')}</td>
                <td style="padding:8px 6px">{e.get('backup', '—')}</td>
                <td style="padding:8px 6px">{e.get('peds', '—')}</td>
            </tr>""" for e in entries)
        return f"""
        <table cellpadding="0" cellspacing="0" width="100%" style="border-collapse:collapse;font-family:Arial,Helvetica,sans-serif;font-size:10pt;color:#333">
            <tr style="background-color:#1a3a5c;color:#ffffff">
                <th style="padding:8px 6px;text-align:left">Campus</th>
                <th style="padding:8px 6px;text-align:left">Primary Attending</th>
                <th style="padding:8px 6px;text-align:left">Backup Attending</th>
                <th style="padding:8px 6px;text-align:left">PEDS Attending</th>
            </tr>
            {rows}
        </table>
        """
    else:
        rows = "".join(f"""
            <tr style="border-bottom:1px solid #d0d4d8">
                <td style="padding:8px 6px">{e.get('date', '')}</td>
                <td style="padding:8px 6px">{e.get('day', '')}</td>
                <td style="padding:8px 6px">{e.get('campus', '')}</td>
                <td style="padding:8px 6px">{e.get('primary', '—')}</td>
                <td style="padding:8px 6px">{e.get('backup', '—')}</td>
                <td style="padding:8px 6px">{e.get('peds', '—')}</td>
            </tr>""" for e in entries)
        return f"""
        <table cellpadding="0" cellspacing="0" width="100%" style="border-collapse:collapse;font-family:Arial,Helvetica,sans-serif;font-size:10pt;color:#333">
            <tr style="background-color:#1a3a5c;color:#ffffff">
                <th style="padding:8px 6px;text-align:left">Date</th>
                <th style="padding:8px 6px;text-align:left">Day</th>
                <th style="padding:8px 6px;text-align:left">Campus</th>
                <th style="padding:8px 6px;text-align:left">Primary</th>
                <th style="padding:8px 6px;text-align:left">Backup</th>
                <th style="padding:8px 6px;text-align:left">PEDS</th>
            </tr>
            {rows}
        </table>
        """


def build_email_html(
    recipient_name: str,
    schedule_title: str,
    schedule_data: dict = None,
    note: str = "",
) -> str:
    """Build a professional HTML email body with Montefiore navy header and optional schedule table."""
    now = datetime.now().strftime("%B %d, %Y")
    greeting = "Good Morning" if datetime.now().hour < 12 else "Good Afternoon" if datetime.now().hour < 17 else "Good Evening"

    entries = _normalize_entries(schedule_data or {})
    schedule_table = _build_email_schedule_table(entries)
    note_html = f'<p style="margin:0 0 12px 0;font-family:Times New Roman,Georgia,serif;font-size:10pt;color:#666;font-style:italic">{note}</p>' if note else ""

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background-color:#f0f2f5;font-family:'Times New Roman',Georgia,serif">
<table cellpadding="0" cellspacing="0" width="100%" style="background-color:#f0f2f5">
  <tr><td style="padding:30px 10px" align="center">
    <table cellpadding="0" cellspacing="0" style="max-width:620px;width:100%;background-color:#ffffff;border-radius:4px;box-shadow:0 1px 3px rgba(0,0,0,0.08)">
      <tr>
        <td style="background-color:#1a3a5c;border-radius:4px 4px 0 0;padding:18px 28px">
          <table cellpadding="0" cellspacing="0" width="100%">
            <tr>
              <td style="font-family:Georgia,'Times New Roman',serif;font-size:16pt;font-weight:bold;color:#ffffff">Montefiore Einstein Urology</td>
              <td style="font-family:Georgia,'Times New Roman',serif;font-size:9pt;color:#ffffff;text-align:right;vertical-align:bottom">{now}</td>
            </tr>
          </table>
        </td>
      </tr>
      <tr>
        <td style="padding:24px 28px 12px 28px">
          <p style="margin:0 0 4px 0;font-family:Times New Roman,Georgia,serif;font-size:13pt;color:#000000;font-weight:bold">{schedule_title}</p>
          <p style="margin:0 0 16px 0;font-family:Times New Roman,Georgia,serif;font-size:11pt;color:#333;line-height:1.5">{greeting} {recipient_name},</p>
          <p style="margin:0 0 12px 0;font-family:Times New Roman,Georgia,serif;font-size:11pt;color:#333;line-height:1.5">Please find the requested call schedule below and attached as a PDF.</p>
          {note_html}
        </td>
      </tr>
      <tr>
        <td style="padding:0 28px 24px 28px">
          {schedule_table}
        </td>
      </tr>
      <tr>
        <td style="padding:12px 28px 24px 28px"><hr style="border:none;border-top:1px solid #d0d4d8"></td>
      </tr>
    </table>
    <table cellpadding="0" cellspacing="0" style="max-width:620px;width:100%;padding-top:10px">
      <tr><td style="font-family:Arial,Helvetica,sans-serif;font-size:8pt;color:#aaa;text-align:center">Montefiore Urology &bull; 1250 Waters Place &bull; Bronx, NY 10461</td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>"""


def email_schedule(
    email: str,
    schedule_data: list,
    date_range_text: str = "",
    campuses: list = None,
    person_name: str = None,
) -> dict:
    """Called from Vapi bridge. Takes pre-fetched schedule entries, generates PDF, emails it."""
    try:
        from google_workspace import GoogleWorkspace
    except ImportError:
        return {"success": False, "message": "Email sending not configured"}

    if not schedule_data:
        return {"success": False, "message": "No schedule data provided"}

    # schedule_data from the bridge is already a flat list of entries
    display_data = {"results": schedule_data}

    title = f"Call Schedule — {date_range_text}" if date_range_text else "Call Schedule"
    if person_name:
        title = f"Call Schedule: {person_name}"
    subtitle = ", ".join(campuses or [])

    try:
        pdf_path = build_schedule_pdf(
            display_data,
            title=title,
            subtitle=subtitle,
        )
    except Exception as e:
        return {"success": False, "message": f"PDF generation failed: {str(e)}"}

    recipient_name = person_name or "Colleague"
    try:
        html_body = build_email_html(recipient_name, title, schedule_data=display_data)
        ws = GoogleWorkspace()
        result = ws.send_email(
            user_id="default",
            to=email,
            subject=f"Montefiore Urology — {title}",
            body=html_body,
            attachments=[pdf_path],
            is_html=True,
        )
    except Exception as e:
        try:
            os.unlink(pdf_path)
        except Exception:
            pass
        return {"success": False, "message": f"Email failed: {str(e)}"}

    try:
        os.unlink(pdf_path)
    except Exception:
        pass

    if result.get("successful"):
        return {"success": True, "message": f"Schedule emailed to {email}."}
    return {"success": False, "message": f"Email failed: {result.get('error', 'unknown')}"}


def _build_roster_email_table(staff: list) -> str:
    """Build an HTML table string from staff roster entries for the email body."""
    if not staff:
        return "<p>No staff roster data available.</p>"

    rows = "".join(f"""
        <tr style="border-bottom:1px solid #d0d4d8">
            <td style="padding:8px 6px">{s.get('name', '')}</td>
            <td style="padding:8px 6px">{s.get('role', '—') or '—'}</td>
            <td style="padding:8px 6px">{s.get('status', '—') or '—'}</td>
        </tr>""" for s in staff)

    return f"""
    <table cellpadding="0" cellspacing="0" width="100%" style="border-collapse:collapse;font-family:Arial,Helvetica,sans-serif;font-size:10pt;color:#333">
        <tr style="background-color:#1a3a5c;color:#ffffff">
            <th style="padding:8px 6px;text-align:left">Name</th>
            <th style="padding:8px 6px;text-align:left">Role</th>
            <th style="padding:8px 6px;text-align:left">Status</th>
        </tr>
        {rows}
    </table>
    """


def build_roster_pdf(roster_data: dict, location: str, date_str: str) -> str:
    """Build a professional PDF of location staff roster. Returns file path."""
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    pdf_path = tmp.name
    tmp.close()

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=landscape(letter),
        topMargin=0.5 * inch,
        bottomMargin=0.4 * inch,
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
    )

    styles = getSampleStyleSheet()
    body_style = ParagraphStyle("Body", parent=styles["Normal"], fontSize=8, leading=10, textColor=DARK_TEXT)
    header_style = ParagraphStyle("Header", parent=styles["Normal"], fontSize=18, leading=22, textColor=colors.white, alignment=TA_LEFT)
    sub_style = ParagraphStyle("Sub", parent=styles["Normal"], fontSize=10, leading=14, textColor=colors.white)
    cell_style = ParagraphStyle("Cell", parent=styles["Normal"], fontSize=9, leading=11, textColor=DARK_TEXT)
    title_style = ParagraphStyle("Title", parent=styles["Normal"], fontSize=14, leading=18, textColor=colors.black)

    elements = []

    # Navy header
    header_data = [[Paragraph("Montefiore Einstein Urology", header_style)]]
    header_data[0].append(Paragraph(datetime.now().strftime("%B %d, %Y"), sub_style))

    header_table = Table(header_data, colWidths=[6 * inch, 3.5 * inch])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, -1), WHITE),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.15 * inch))

    # Title
    title = f"Staff Roster — {location}"
    if date_str:
        title += f" — {date_str}"
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 0.1 * inch))

    staff = roster_data.get("records", [])

    if staff:
        rows = [[
            Paragraph("<b>Name</b>", cell_style),
            Paragraph("<b>Role</b>", cell_style),
            Paragraph("<b>Status</b>", cell_style),
        ]]
        for s in staff:
            rows.append([
                Paragraph(s.get("name", ""), cell_style),
                Paragraph(s.get("role", "—") or "—", cell_style),
                Paragraph(s.get("status", "—") or "—", cell_style),
            ])

        table = Table(rows, colWidths=[2.5 * inch, 2.0 * inch, 2.0 * inch])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("BACKGROUND", (0, 1), (-1, -1), WHITE),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d0d4d8")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph("No staff roster data available.", body_style))

    # Footer
    elements.append(Spacer(1, 0.2 * inch))
    elements.append(Paragraph(
        "Montefiore Urology &bull; Staff Roster &bull; Generated automatically",
        ParagraphStyle("Footer", parent=styles["Normal"], fontSize=7, textColor=colors.HexColor("#999999"), alignment=TA_CENTER),
    ))

    doc.build(elements)
    return pdf_path


def email_staff_roster(
    email: str,
    location: str,
    date_str: str = None,
    period: str = "day",
) -> dict:
    """Fetch location staff roster, generate PDF, and email it. Called from Vapi bridge."""
    try:
        from google_workspace import GoogleWorkspace
    except ImportError:
        return {"success": False, "message": "Email sending is not configured."}

    from modules import roster_parser

    if not date_str:
        date_str = date.today().strftime("%Y-%m-%d")

    roster_data = roster_parser.staff_at_location(location, date_str)

    data_status = roster_data.get("data_status", "")
    if data_status != "ok":
        status_messages = {
            "no_assignments": f"Nobody is scheduled at {location} on {date_str}.",
            "no_data_for_date": f"I don't have a roster loaded for that week yet — the latest one I have covers {roster_data.get('period_end', 'N/A')}.",
            "unknown_location": f"I don't recognize {location} as one of our sites — the ones I know are {roster_data.get('known_locations', [])}.",
            "rosters_not_synced": "The location rosters haven't been synced from Drive yet — let me flag that for Shareef.",
        }
        return {
            "success": False,
            "message": status_messages.get(data_status, f"Could not retrieve roster data: {data_status}"),
        }

    try:
        pdf_path = build_roster_pdf(roster_data, location, date_str)
    except Exception as e:
        return {"success": False, "message": f"PDF generation failed: {str(e)}"}

    staff = roster_data.get("records", [])
    title = f"Staff Roster — {location} — {date_str}"

    try:
        staff_table = _build_roster_email_table(staff)
        now_str = datetime.now().strftime("%B %d, %Y")
        html_body = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background-color:#f0f2f5;font-family:'Times New Roman',Georgia,serif">
<table cellpadding="0" cellspacing="0" width="100%" style="background-color:#f0f2f5">
  <tr><td style="padding:30px 10px" align="center">
    <table cellpadding="0" cellspacing="0" style="max-width:620px;width:100%;background-color:#ffffff;border-radius:4px;box-shadow:0 1px 3px rgba(0,0,0,0.08)">
      <tr>
        <td style="background-color:#1a3a5c;border-radius:4px 4px 0 0;padding:18px 28px">
          <table cellpadding="0" cellspacing="0" width="100%">
            <tr>
              <td style="font-family:Georgia,'Times New Roman',serif;font-size:16pt;font-weight:bold;color:#ffffff">Montefiore Einstein Urology</td>
              <td style="font-family:Georgia,'Times New Roman',serif;font-size:9pt;color:#ffffff;text-align:right;vertical-align:bottom">{now_str}</td>
            </tr>
          </table>
        </td>
      </tr>
      <tr>
        <td style="padding:24px 28px 12px 28px">
          <p style="margin:0 0 4px 0;font-family:Times New Roman,Georgia,serif;font-size:13pt;color:#000000;font-weight:bold">{title}</p>
          <p style="margin:0 0 12px 0;font-family:Times New Roman,Georgia,serif;font-size:11pt;color:#333;line-height:1.5">Please find the requested staff roster below and attached as a PDF.</p>
        </td>
      </tr>
      <tr>
        <td style="padding:0 28px 24px 28px">
          {staff_table}
        </td>
      </tr>
      <tr>
        <td style="padding:12px 28px 24px 28px"><hr style="border:none;border-top:1px solid #d0d4d8"></td>
      </tr>
    </table>
    <table cellpadding="0" cellspacing="0" style="max-width:620px;width:100%;padding-top:10px">
      <tr><td style="font-family:Arial,Helvetica,sans-serif;font-size:8pt;color:#aaa;text-align:center">Montefiore Urology &bull; 1250 Waters Place &bull; Bronx, NY 10461</td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>"""

        ws = GoogleWorkspace()
        result = ws.send_email(
            user_id="default",
            to=email,
            subject=f"Montefiore Urology — {location} Staff Roster — {date_str}",
            body=html_body,
            attachments=[pdf_path],
            is_html=True,
        )
    except Exception as e:
        try:
            os.unlink(pdf_path)
        except Exception:
            pass
        return {"success": False, "message": f"Email failed: {str(e)}"}

    try:
        os.unlink(pdf_path)
    except Exception:
        pass

    if result.get("successful"):
        return {"success": True, "message": f"Staff roster emailed to {email}."}
    return {"success": False, "message": f"Email failed: {result.get('error', 'unknown')}"}


def email_schedule_pdf(
    recipient_email: str,
    recipient_name: str = "",
    date_str: Optional[str] = None,
    period: Optional[str] = None,
    person_name: Optional[str] = None,
) -> dict:
    """Generate and email a professional schedule PDF. Called from Vapi bridge."""
    try:
        from google_workspace import GoogleWorkspace
    except ImportError:
        return {"success": False, "message": "Email sending is not configured."}

    # Determine what data to fetch
    schedule_data = {}
    title = "Call Schedule"
    subtitle = ""

    if person_name:
        sched = vapi_unified.call_month(person_name)
        if sched.get("results"):
            title = f"Call Schedule — {person_name}"
            subtitle = f"Next 60 days"
        else:
            # Try person schedule
            sched = vapi_unified.schedule_by_date(date_str or date.today().strftime("%Y-%m-%d"))
            title = f"Call Schedule for {person_name}"
        schedule_data = sched

    elif date_str:
        sched = vapi_unified.schedule_by_date(date_str)
        title = f"Call Schedule — {date_str}"
        schedule_data = sched

    elif period == "weekend":
        sched = vapi_unified.call_weekend()
        dates = sched.get("dates", [])
        title = "Weekend Call Schedule"
        subtitle = f"{' - '.join(dates)}" if dates else ""
        schedule_data = sched

    elif period in ("month", "30days"):
        sched = vapi_unified._load_schedule()
        today = date.today()
        cutoff = today + timedelta(days=30)
        today_str = today.strftime("%Y-%m-%d")
        cutoff_str = cutoff.strftime("%Y-%m-%d")
        title = f"Call Schedule — Next 30 Days"
        subtitle = f"{today_str} to {cutoff_str}"
        # Build aggregated data
        campus_entries = {}
        for campus, rows in sched.items():
            for row in rows:
                if row["date"] >= today_str and row["date"] <= cutoff_str:
                    campus_entries.setdefault(campus, []).append(row)
        # Create a flat list
        all_entries = []
        for campus, rows in campus_entries.items():
            for r in rows:
                all_entries.append({
                    "campus": campus.title(),
                    "date": r["date"],
                    "day": r.get("day", ""),
                    "primary": r.get("primary", "") or "—",
                    "backup": r.get("backup", "") or "—",
                    "peds": r.get("peds", "") or "—",
                })
        all_entries.sort(key=lambda x: x["date"])
        schedule_data = {"results": all_entries, "total": len(all_entries)}

    else:
        # Default to today
        sched = vapi_unified.schedule_by_date(date.today().strftime("%Y-%m-%d"))
        schedule_data = sched
        title = "Today's Call Schedule"

    if not schedule_data or (isinstance(schedule_data, dict) and schedule_data.get("total") == 0 and not schedule_data.get("campuses")):
        return {"success": False, "message": "No schedule data available for the requested period."}

    # Generate PDF
    try:
        pdf_path = build_schedule_pdf(schedule_data, title=title, subtitle=subtitle)
    except Exception as e:
        return {"success": False, "message": f"Failed to generate PDF: {str(e)}"}

    # Build email
    try:
        html_body = build_email_html(recipient_name or "Colleague", title, schedule_data=schedule_data)
        ws = GoogleWorkspace()
        result = ws.send_email(
            user_id="default",
            to=recipient_email,
            subject=f"Montefiore Urology — {title}",
            body=html_body,
            attachments=[pdf_path],
            is_html=True,
        )
    except Exception as e:
        os.unlink(pdf_path)
        return {"success": False, "message": f"Failed to send email: {str(e)}"}

    # Cleanup
    try:
        os.unlink(pdf_path)
    except Exception:
        pass

    if result.get("successful"):
        return {"success": True, "message": f"Schedule PDF emailed to {recipient_email}."}
    else:
        return {"success": False, "message": f"Email failed: {result.get('error', 'unknown error')}"}
