#!/usr/bin/env python3
"""Deploy Vapi V8 — Live Data Awareness

The schedule/staff/call tools behind the voice assistant now serve LIVE
data from the unified platform databases (ADR 0001 m2m bridge) instead of
flat-file snapshots. This deploy:
  1. Appends a LIVE DATA section so the assistant uses the new fields
     (chief / first_call / second_call resident roles in call coverage).
  2. Replaces the stale "schedule only covers July 2026 through January
     2027" guidance with generic no-data phrasing.
Idempotent: skips if the V8 marker is already present.
"""
import json
import urllib.request

with open('/home/hermeswebui/.hermes/.env') as f:
    env = f.read()

api_key = ""
for line in env.split('\n'):
    if line.startswith('VAPI_API_KEY='):
        api_key = line.split('=', 1)[1].strip().strip("'\"")

if not api_key:
    raise SystemExit("VAPI_API_KEY not found in ~/.hermes/.env")

ASSISTANT_ID = "9b00342e-1951-4bd0-b4a5-5ca4c9827bd0"
headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}

req = urllib.request.Request(f"https://api.vapi.ai/assistant/{ASSISTANT_ID}", headers=headers)
with urllib.request.urlopen(req, timeout=15) as r:
    d = json.loads(r.read())

model = d.get("model", {})
messages = model.get("messages", [])
tools = model.get("tools", d.get("tools", []))

system = ""
for m in messages:
    if m.get("role") == "system":
        system = m["content"]
        break

MARKER = "=== LIVE DATA (V8) ==="
if MARKER in system:
    print("V8 live-data section already present — nothing to do.")
    raise SystemExit(0)

print(f"System prompt length before: {len(system)} chars")

# 1. Replace stale coverage-window guidance (conditional phrasing kept generic)
stale = 'tell the caller: "The schedule I have loaded only goes from July 2026 through January 2027, so I don\'t have coverage details for that date."'
fresh = 'tell the caller: "I don\'t have coverage details for that date yet."'
if stale in system:
    system = system.replace(stale, fresh)
    print("Replaced stale coverage-window guidance.")

live_section = """

=== LIVE DATA (V8) ===
Your schedule, call-coverage, and staff tools now return LIVE data straight
from the department's databases — the same data the Unified Platform portal
edits. When a result includes "source": "live", it is real-time. If a result
mentions a file snapshot or limited coverage, that is the backup copy and may
be slightly out of date; answer from it but do not promise it is current.

NEW FIELDS IN CALL COVERAGE ANSWERS:
scheduleByDate / weekend / monthly call results now include resident roles in
addition to attendings:
  - "chief" — chief resident on call
  - "first_call" — 1st call resident
  - "second_call" — 2nd call resident
  - "primary" / "backup" / "peds" — attendings (as before)
When callers ask "who's the chief tonight", "who's on first call at Moses",
or similar, answer directly from those fields.

STAFF LOOKUPS:
Staff results now come from the department CRM (the source of truth) and can
include category (Faculty / Resident / Staff / Admin), title, and PGY level.
Prefer these values over anything you remember from earlier in the call.
"""

system = system + live_section

new_messages = []
for m in messages:
    if m.get("role") == "system":
        new_messages.append({"role": "system", "content": system})
    else:
        new_messages.append(m)

payload = {
    "model": {
        "provider": model.get("provider", "openai"),
        "model": model.get("model", "gpt-4o"),
        "temperature": model.get("temperature", 0.7),
        "messages": new_messages,
        "tools": tools,
    }
}

server = d.get("server", {})
if server.get("url"):
    payload["server"] = server

print(f"System prompt length after: {len(system)} chars")
print("Deploying V8 live-data awareness...")

data = json.dumps(payload).encode()
req = urllib.request.Request(f"https://api.vapi.ai/assistant/{ASSISTANT_ID}", data=data, headers=headers, method="PATCH")
with urllib.request.urlopen(req, timeout=20) as r:
    result = json.loads(r.read())
    print("✅ Deployed V8!")
    print(f"   Tools: {len(result.get('model', {}).get('tools', []))}")
    print(f"   Model: {result.get('model', {}).get('model', 'unknown')}")
    sys_msgs = [m for m in result.get('model', {}).get('messages', []) if m.get('role') == 'system']
    print(f"   V8 marker present: {MARKER in (sys_msgs[0]['content'] if sys_msgs else '')}")
