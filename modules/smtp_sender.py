#!/usr/bin/env python3
"""
SMTP email sender — drop-in replacement for GoogleWorkspace.send_email()

Uses Gmail App Password + SMTP instead of OAuth tokens.
App passwords never expire, eliminating the re-auth-every-few-days problem.

Configuration (env vars or .env file):
  SMTP_USER     — Gmail address to send from (e.g. shareef@gmail.com)
  SMTP_APP_PASSWORD — 16-char Gmail App Password (generated at myaccount.google.com)
  SMTP_HOST     — SMTP server (default: smtp.gmail.com)
  SMTP_PORT     — SMTP port (default: 587)

If SMTP_USER or SMTP_APP_PASSWORD is not set, send_email() returns
{"successful": False, "error": "SMTP not configured"} so callers can
fall back to the OAuth path.
"""
import os
import base64
import mimetypes
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import List, Optional, Dict

# Load .env if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def _get_smtp_config() -> Dict[str, str]:
    """Read SMTP configuration from environment variables."""
    return {
        "user": os.environ.get("SMTP_USER", ""),
        "password": os.environ.get("SMTP_APP_PASSWORD", ""),
        "host": os.environ.get("SMTP_HOST", "smtp.gmail.com"),
        "port": int(os.environ.get("SMTP_PORT", "587")),
    }


def is_smtp_configured() -> bool:
    """Check if SMTP credentials are configured."""
    cfg = _get_smtp_config()
    return bool(cfg["user"] and cfg["password"])


def send_email(
    to: str,
    subject: str,
    body: str,
    attachments: Optional[List[str]] = None,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
    from_email: Optional[str] = None,
    is_html: bool = False,
    **kwargs,  # absorb user_id and other OAuth-specific params
) -> Dict:
    """
    Send email via Gmail SMTP with App Password.

    Returns dict matching GoogleWorkspace.send_email format:
        {"successful": True/False, "data": {...}, "error": "..."}
    """
    cfg = _get_smtp_config()

    if not cfg["user"] or not cfg["password"]:
        return {
            "successful": False,
            "error": "SMTP not configured (SMTP_USER / SMTP_APP_PASSWORD missing)",
            "data": None,
        }

    sender = from_email or cfg["user"]

    # Use display name "Urology Residency Program" for the From header
    from email.utils import formataddr
    display_name = os.environ.get("SMTP_FROM_NAME", "Urology Residency Program")
    msg_from = formataddr((display_name, sender))

    # Build MIME message
    is_html = is_html or ("<" in body and ">" in body)
    msg = MIMEMultipart()
    msg["From"] = msg_from
    msg["To"] = to
    msg["Subject"] = subject
    if cc:
        msg["Cc"] = ", ".join(cc)
    if bcc:
        msg["Bcc"] = ", ".join(bcc)

    msg.attach(MIMEText(body, "html" if is_html else "plain"))

    # Handle attachments
    if attachments:
        for file_path in attachments:
            fp = Path(file_path)
            if not fp.exists():
                continue
            mime_type, _ = mimetypes.guess_type(str(fp))
            if mime_type is None:
                mime_type = "application/octet-stream"
            main_type, sub_type = mime_type.split("/", 1)

            part = MIMEBase(main_type, sub_type)
            part.set_payload(fp.read_bytes())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f'attachment; filename="{fp.name}"',
            )
            msg.attach(part)

    # Build recipient list (to + cc + bcc)
    recipients = [to]
    if cc:
        recipients.extend(cc)
    if bcc:
        recipients.extend(bcc)

    # Send via SMTP
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(cfg["host"], cfg["port"], timeout=30) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(cfg["user"], cfg["password"])
            server.sendmail(sender, recipients, msg.as_string())
            server.quit()

        return {"successful": True, "data": {"id": "smtp_sent", "method": "smtp"}}
    except smtplib.SMTPAuthenticationError as e:
        return {"successful": False, "error": f"SMTP auth failed: {str(e)}", "data": None}
    except Exception as e:
        return {"successful": False, "error": f"SMTP error: {str(e)}", "data": None}


def send_email_smart(
    to: str,
    subject: str,
    body: str,
    attachments: Optional[List[str]] = None,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
    from_email: Optional[str] = None,
    is_html: bool = False,
    **kwargs,
) -> Dict:
    """
    Smart email sender: tries SMTP first, falls back to Google OAuth if SMTP fails.

    This is the main entry point for all email sending in the Vapi system.
    """
    # Try SMTP first if configured
    if is_smtp_configured():
        result = send_email(
            to=to, subject=subject, body=body,
            attachments=attachments, cc=cc, bcc=bcc,
            from_email=from_email, is_html=is_html, **kwargs,
        )
        if result.get("successful"):
            return result
        # If SMTP was configured but failed (auth error etc), try OAuth fallback
        # Log the SMTP failure but don't block — try OAuth
        smtp_error = result.get("error", "unknown")
        # Fall through to OAuth
    else:
        smtp_error = "SMTP not configured"

    # Fall back to Google OAuth (GoogleWorkspace)
    try:
        try:
            from modules.google_workspace import GoogleWorkspace
        except ImportError:
            from google_workspace import GoogleWorkspace

        ws = GoogleWorkspace()
        result = ws.send_email(
            user_id="default",
            to=to,
            subject=subject,
            body=body,
            attachments=attachments,
            cc=cc,
            bcc=bcc,
            from_email=from_email,
            is_html=is_html,
        )
        return result
    except Exception as e:
        return {
            "successful": False,
            "error": f"SMTP failed ({smtp_error}); OAuth also failed: {str(e)}",
            "data": None,
        }