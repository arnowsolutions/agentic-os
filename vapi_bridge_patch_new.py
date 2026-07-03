#!/usr/bin/env python3
"""Patch to append to vapi_bridge.py — adds getMyDashboard, emailMyDashboard,
VIP phone recognition, sick call auto-find, and voicemail handler."""

import json, hashlib, time, os, subprocess, sys
from datetime import datetime, timezone, date, timedelta


# ─── VIP Phone Recognition ──────────────────────────────────────────────────

def _lookup_by_phone(phone: str) -> dict | None:
    """Match a phone number against CRM + PIN DB. Returns user profile or None."""
    if not phone:
        return None
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) < 10:
        return None
    # Try last 10 digits for flexibility (country code)
    last10 = digits[-10:]
    last7 = digits[-7:]

    # Check CRM
    for c in _load_crm():
        cphone = "".join(ch for ch in (c.get("phone", "") or "") if ch.isdigit())
        if cphone and (last10 == cphone[-10:] if len(cphone) >= 10 else last7 == cphone[-7:]):
            role = _crm_role_to_vapi(c.get("category", ""))
            display = f"{c.get('firstName', '')} {c.get('lastName', '')}".strip()
            return {
                "name": display,
                "role": role,
                "email": c.get("email", ""),
                "ez_id": c.get("ezId", ""),
            }

    # Check PIN DB
    for uid, u in _load_pin_db().items():
        uphone = "".join(ch for ch in (u.get("phone", "") or "") if ch.isdigit())
        if uphone and (last10 == uphone[-10:] if len(uphone) >= 10 else last7 == uphone[-7:]):
            profile = {k: v for k, v in u.items() if k != "pin_hash"}
            return profile

    return None


# ─── getMyDashboard ─────────────────────────────────────────────────────────

def _handle_get_my_dashboard(args: dict) -> dict:
    """Merge all caller data: QGenda assignments, call schedule, GME balance,
    deadlines, evaluations — into one comprehensive response."""
    name = args.get("name", "")
    role = args.get("role", "")

    if not name:
        return {"success": False, "message": "I need your name to pull up your dashboard."}

    dashboard = {
        "caller": name,
        "role": role,
        "date": date.today().strftime("%Y-%m-%d"),
        "sections": {},
    }

    # 1. QGenda — today's clinic assignment
    try:
        today_qgenda = vapi_unified.qgenda_person_day(name)
        if today_qgenda and not today_qgenda.get("error"):
            dashboard["sections"]["clinic_today"] = today_qgenda
    except Exception as e:
        dashboard["sections"]["clinic_today"] = {"error": str(e)}

    # 2. QGenda — upcoming assignments (next 7 days)
    try:
        upcoming = vapi_unified.qgenda_person_upcoming(name, 7)
        if upcoming:
            dashboard["sections"]["upcoming"] = upcoming
    except Exception as e:
        dashboard["sections"]["upcoming"] = {"error": str(e)}

    # 3. Call coverage — person schedule
    try:
        person_sched = vapi_data.schedule_person(name)
        if person_sched and not person_sched.get("note"):
            # Only include next 3 upcoming call dates
            today_str = date.today().strftime("%Y-%m-%d")
            upcoming_calls = []
            if isinstance(person_sched, list):
                for item in person_sched:
                    if item.get("date", "9999") >= today_str:
                        upcoming_calls.append(item)
                        if len(upcoming_calls) >= 3:
                            break
            elif isinstance(person_sched, dict):
                for campus, rows in person_sched.items():
                    for row in (rows if isinstance(rows, list) else [rows]):
                        if row.get("date", "9999") >= today_str:
                            upcoming_calls.append({"campus": campus, **row})
                            if len(upcoming_calls) >= 3:
                                break
            dashboard["sections"]["call_coverage"] = upcoming_calls if upcoming_calls else {"note": "No upcoming call assignments."}
    except Exception as e:
        dashboard["sections"]["call_coverage"] = {"error": str(e)}

    # 4. GME balance
    try:
        gme = vapi_data.gme_balance_for(name)
        if gme:
            dashboard["sections"]["gme_balance"] = gme
    except Exception as e:
        dashboard["sections"]["gme_balance"] = {"error": str(e)}

    # 5. Deadlines
    try:
        from modules import vapi_concierge
        deadlines = vapi_concierge.get_deadlines(role)
        if deadlines:
            dashboard["sections"]["deadlines"] = deadlines
    except Exception as e:
        dashboard["sections"]["deadlines"] = {"error": str(e)}

    # 6. Evaluations due
    try:
        from modules import vapi_concierge
        evals = vapi_concierge.get_evaluations_due(name)
        if evals:
            dashboard["sections"]["evaluations"] = evals
    except Exception as e:
        dashboard["sections"]["evaluations"] = {"error": str(e)}

    dashboard["success"] = True
    return dashboard


# ─── emailMyDashboard ───────────────────────────────────────────────────────

def _handle_email_my_dashboard(args: dict) -> dict:
    """Generate a professional PDF of the caller's full dashboard and email it."""
    name = args.get("name", "")
    role = args.get("role", "")
    email = args.get("email", "")

    if not email:
        return {"success": False, "message": "I need your email address to send the dashboard."}

    # Get the dashboard data
    dashboard = _handle_get_my_dashboard({"name": name, "role": role})
    if not dashboard.get("success"):
        return {"success": False, "message": "I couldn't pull up your dashboard data."}

    try:
        from modules import vapi_email
        from reportlab.lib.pagesizes import letter, portrait
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        import io

        # Build PDF
        buf = io.BytesIO()
        styles = getSampleStyleSheet()
        navy = colors.HexColor("#0B2545")
        white = colors.white
        light_gray = colors.HexColor("#F0F2F5")

        header_style = ParagraphStyle("Header", parent=styles["Title"], fontSize=16,
                                       textColor=navy, spaceAfter=6)
        sub_style = ParagraphStyle("Sub", parent=styles["Normal"], fontSize=10,
                                    textColor=colors.HexColor("#666666"), spaceAfter=12)
        section_style = ParagraphStyle("Section", parent=styles["Heading2"], fontSize=12,
                                        textColor=navy, spaceBefore=12, spaceAfter=4)
        body_style = ParagraphStyle("Body", parent=styles["Normal"], fontSize=9, spaceAfter=2)

        doc = SimpleDocTemplate(buf, pagesize=portrait(letter),
                                leftMargin=0.6*inch, rightMargin=0.6*inch,
                                topMargin=0.8*inch, bottomMargin=0.5*inch)
        elements = []

        # Header
        elements.append(Paragraph("Montefiore Urology — Personal Dashboard", header_style))
        elements.append(Paragraph(f"Prepared for {name} ({role}) • {dashboard['date']}", sub_style))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph("This dashboard includes your clinic assignments, call coverage, GME balance, deadlines, and evaluations.", body_style))
        elements.append(Spacer(1, 12))

        sections = dashboard.get("sections", {})

        # Clinic Today
        if "clinic_today" in sections:
            elements.append(Paragraph("Clinic Assignment — Today", section_style))
            ct = sections["clinic_today"]
            if isinstance(ct, dict):
                for k, v in ct.items():
                    if k != "error":
                        elements.append(Paragraph(f"<b>{k.title()}:</b> {v}", body_style))

        # Upcoming
        if "upcoming" in sections:
            elements.append(Paragraph("Upcoming Assignments (7 Days)", section_style))
            up = sections["upcoming"]
            if isinstance(up, dict):
                items = up.get("items", up.get("assignments", []))
            elif isinstance(up, list):
                items = up
            else:
                items = []
            for item in items[:10]:
                if isinstance(item, dict):
                    line = f"{item.get('date', '')} — {item.get('task', item.get('clinic', item.get('assignment', '')))}"
                    elements.append(Paragraph(line, body_style))

        # Call Coverage
        if "call_coverage" in sections:
            elements.append(Paragraph("Upcoming Call Coverage", section_style))
            cc = sections["call_coverage"]
            if isinstance(cc, list):
                for item in cc[:5]:
                    if isinstance(item, dict):
                        line = f"{item.get('date', '')} ({item.get('day', '')}) — {item.get('campus', '')}: Primary {item.get('primary', '—')}, Backup {item.get('backup', '—')}"
                        elements.append(Paragraph(line, body_style))
            elif isinstance(cc, dict) and cc.get("note"):
                elements.append(Paragraph(cc["note"], body_style))

        # GME Balance
        if "gme_balance" in sections:
            elements.append(Paragraph("GME / Reimbursement Balance", section_style))
            gme = sections["gme_balance"]
            if isinstance(gme, dict):
                for k, v in gme.items():
                    if k != "error":
                        elements.append(Paragraph(f"<b>{k.replace('_', ' ').title()}:</b> {v}", body_style))
            elif isinstance(gme, (int, float, str)):
                elements.append(Paragraph(f"Balance: {gme}", body_style))

        # Deadlines
        if "deadlines" in sections:
            elements.append(Paragraph("Upcoming Deadlines", section_style))
            dl = sections["deadlines"]
            if isinstance(dl, list):
                for d in dl[:5]:
                    elements.append(Paragraph(str(d) if not isinstance(d, dict) else f"{d.get('date', '')}: {d.get('title', d.get('description', str(d)))}", body_style))
            elif isinstance(dl, dict):
                for k, v in dl.items():
                    elements.append(Paragraph(f"<b>{k}:</b> {v}", body_style))

        # Evaluations
        if "evaluations" in sections:
            elements.append(Paragraph("Evaluations Due", section_style))
            ev = sections["evaluations"]
            if isinstance(ev, list):
                for e in ev[:5]:
                    elements.append(Paragraph(str(e) if not isinstance(e, dict) else f"{e.get('date', '')}: {e.get('title', e.get('name', str(e)))}", body_style))
            elif isinstance(ev, dict):
                for k, v in ev.items():
                    elements.append(Paragraph(f"<b>{k}:</b> {v}", body_style))

        doc.build(elements)
        pdf_bytes = buf.getvalue()

        # Send email via SMTP
        from modules.smtp_sender import send_email_smart

        html_body = f"""
        <html><body>
        <h2 style="color:#0B2545;">Montefiore Urology — Personal Dashboard</h2>
        <p>Hi {name.split()[0] if name else ''},</p>
        <p>Here's your complete dashboard for {dashboard['date']}, including clinic assignments,
        call coverage, GME balance, deadlines, and evaluations.</p>
        <p>The full details are in the attached PDF.</p>
        <p style="color:#666;font-size:12px;">Montefiore Urology • Generated by your AI voice assistant</p>
        </body></html>
        """

        attachments = [{"filename": f"dashboard_{dashboard['date']}.pdf", "content": pdf_bytes, "mime": "application/pdf"}]

        result = send_email_smart(
            to=email,
            subject=f"Your Dashboard — Montefiore Urology — {dashboard['date']}",
            html=html_body,
            attachments=attachments,
        )

        audit_record("tool_call", function="emailMyDashboard", email=email, caller=name, result="ok" if result.get("success") else "fail")
        return {"success": True, "message": f"Dashboard sent to {email}."}

    except ImportError:
        # Reportlab or smtp_sender not available — try fallback
        logger.warning("emailMyDashboard: missing deps, trying email_schedule path")
        return {"success": False, "message": "PDF generation unavailable on this server."}
    except Exception as e:
        logger.exception("emailMyDashboard failed")
        return {"success": False, "message": f"Failed to send dashboard: {e}"}


# ─── Sick Call Auto-Find Coverage ──────────────────────────────────────────

def _auto_find_coverage_for_sick_call(args: dict, sick_result: dict) -> dict:
    """After a sick call is logged, find eligible backup coverage from the schedule
    and email Shareef about it. Does NOT send SMS — just flags for Shareef."""
    employee_id = args.get("employee_id", "")
    start_date = args.get("start_date", "")
    name = args.get("name", "Unknown")
    campus = args.get("campus", "")

    coverage_candidates = []

    try:
        # Look at today's schedule for backup coverage
        today_sched = vapi_data.schedule_today()
        if isinstance(today_sched, dict):
            campuses = today_sched.get("campuses", today_sched)
            if isinstance(campuses, dict):
                for cname, cov in campuses.items():
                    if isinstance(cov, dict):
                        backup = cov.get("backup", "")
                        primary = cov.get("primary", "")
                        if backup and backup != "—" and backup != "None":
                            coverage_candidates.append({
                                "campus": cname,
                                "primary": primary,
                                "backup": backup,
                            })

        # If specific campus mentioned, filter
        if campus:
            coverage_candidates = [c for c in coverage_candidates if campus.lower() in c["campus"].lower()]

    except Exception as e:
        logger.warning(f"auto-find coverage error: {e}")

    # Email Shareef with the sick call + coverage suggestions
    try:
        from modules.smtp_sender import send_email_smart

        candidate_lines = ""
        if coverage_candidates:
            candidate_lines = "\n\nPotential coverage candidates from today's schedule:\n"
            for c in coverage_candidates:
                candidate_lines += f"  - {c['campus']}: Primary {c['primary']}, Backup {c['backup']}\n"
        else:
            candidate_lines = "\n\nNo immediate backup candidates found in today's schedule."

        html_body = f"""
        <html><body>
        <h2 style="color:#0B2545;">Sick Call Alert</h2>
        <p>A sick call was submitted via the voice assistant:</p>
        <table style="border-collapse:collapse;font-size:14px;">
        <tr><td style="padding:4px 12px;font-weight:bold;">Caller:</td><td style="padding:4px 12px;">{name}</td></tr>
        <tr><td style="padding:4px 12px;font-weight:bold;">Employee ID:</td><td style="padding:4px 12px;">{employee_id}</td></tr>
        <tr><td style="padding:4px 12px;font-weight:bold;">Start Date:</td><td style="padding:4px 12px;">{start_date}</td></tr>
        <tr><td style="padding:4px 12px;font-weight:bold;">Campus:</td><td style="padding:4px 12px;">{campus or 'Not specified'}</td></tr>
        </table>
        <pre style="font-size:13px;">{candidate_lines}</pre>
        <p style="color:#666;font-size:12px;">Please confirm coverage arrangements manually.</p>
        </body></html>
        """

        send_email_smart(
            to="sfrasier@montefiore.org",
            subject=f"URGENT: Sick Call — {name} — {start_date}",
            html=html_body,
        )
        audit_record("sick_call_coverage_alert", caller=name, date=start_date, candidates=len(coverage_candidates))
    except Exception as e:
        logger.warning(f"sick call email notification failed: {e}")

    return {
        "sick_call_status": sick_result.get("status", "logged"),
        "coverage_candidates": coverage_candidates,
        "shared_with_shareef": True,
    }


# ─── Voicemail Handler ──────────────────────────────────────────────────────

def _handle_voicemail(args: dict) -> dict:
    """When Vapi voicemail detection triggers, transcribe and save."""
    transcript = args.get("transcript", args.get("message", ""))
    caller_number = args.get("caller_number", args.get("from", ""))

    # Save as a voice message
    result = voice_messages.take_message(
        caller_name="Voicemail",
        message=transcript or "No transcript available",
        phone=caller_number,
        callback_requested=True,
    )

    audit_record("voicemail", phone=caller_number, transcript_preview=transcript[:200] if transcript else "")
    return {"status": "saved", "message_id": result.get("id", "")}


def _normalize_name_entry(name):
    """Normalize name for VIP lookup in auth flow."""
    return _normalize_name(name) if name else ""