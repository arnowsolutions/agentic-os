#!/usr/bin/env python3
"""CLI helper for sending a quick email via the Gmail API.

Usage:
    echo "body" | python email_helper.py --to user@example.com --subject "Hello"
"""
import argparse
import sys
from pathlib import Path

# Ensure project modules are importable
sys.path.insert(0, str(Path(__file__).parent))

from modules.google_workspace import GoogleWorkspace
from modules.smtp_sender import send_email_smart


def _html_wrap(text: str, subject: str) -> str:
    lines = "<br>".join(text.strip().split("\n"))
    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:24px;background:#f4f6f8;font-family:'Segoe UI',Arial,sans-serif">
  <div style="max-width:600px;margin:0 auto;background:#fff;border-radius:12px;padding:32px;box-shadow:0 2px 8px rgba(0,0,0,0.08)">
    <h2 style="color:#1a3a5c;margin-top:0">{subject}</h2>
    <div style="color:#374151;line-height:1.6">{lines}</div>
  </div>
</body></html>"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--to", required=True)
    parser.add_argument("--subject", required=True)
    args = parser.parse_args()
    body_text = sys.stdin.read()
    html = _html_wrap(body_text, args.subject)
    try:
        result = send_email_smart(
            to=args.to,
            subject=args.subject,
            body=html,
            is_html=True,
        )
        if result["successful"]:
            print(f"email sent: {result['data']['id']}")
        else:
            print(f"email failed: {result.get('error')}", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"email failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
