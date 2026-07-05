#!/usr/bin/env python3
"""Deliver undelivered voice messages to sfrasier@montefiore.org.
   Runs daily at 7am ET. Sends any messages that haven't been delivered yet.
"""
import sys
sys.path.insert(0, "/workspace/agentic-os/modules")
import voice_messages
import json, os

msgs = voice_messages.get_undelivered()
if not msgs:
    print("No undelivered messages.")
    sys.exit(0)

# Build email body
html = voice_messages.format_for_email()

# Try to send via email_assistant.py
try:
    sys.path.insert(0, "/home/hermeswebui/.hermes")
    import email_assistant as ea
    result = ea.send_email(
        "urology",
        "sfrasier@montefiore.org",
        f"Voice Messages - {len(msgs)} pending",
        html,
        prefer_composio=False,
    )
    if result.get("successful"):
        for m in msgs:
            voice_messages.mark_delivered(m["id"])
        print(f"Sent {len(msgs)} messages to sfrasier@montefiore.org")
    else:
        print(f"Email failed: {result.get('error', 'unknown')}")
except ImportError:
    # Fallback: just print them
    print(f"=== {len(msgs)} Undelivered Voice Messages ===")
    for m in msgs:
        print(f"  {m['id']}: {m.get('caller_name')} - {m.get('message')[:80]}")
except Exception as e:
    print(f"Error: {e}")
