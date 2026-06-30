#!/usr/bin/env python3
"""Deploy Vapi V7 — Personalized Greetings"""
import json, os, urllib.request, re

with open('/home/hermeswebui/.hermes/.env') as f:
    env = f.read()

api_key = ""
for line in env.split('\n'):
    if line.startswith('VAPI_API_KEY='):
        api_key = line.split('=', 1)[1].strip().strip("'\"")

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

old = "Welcome back, {name}! You can manage schedules, check reimbursements, or review call coverage."
new_greeting = """Welcome back, {name}! Want a quick department status or jump straight in?"""
system = system.replace(old, new_greeting)

old2 = '"""Dedicated secure verification webhook for Vapi function calls.'
new2 = """PERSONALIZED GREETINGS:
After verification, give a personal greeting based on role:

- Faculty: "Welcome back, Dr. [LastName]! Need your schedule or want to check today's coverage?"
- Residents: "Hey [FirstName]! Want me to check your GME balance or see your rotation schedule?"
- Staff/Nurse: "Welcome, [FirstName]! How can I help you today?"
- Admin (Shareef): "Welcome back, Big Reef! Want a quick department status or jump straight in?"
- Unknown: "Welcome! How can I help you today?"

Then help the caller conversationally.

"""
# Actually, let me find the right section via the messages array directly
print(f"System prompt length: {len(system)} chars")

# Find the greeting section in the system prompt and update it
phase3_old = "PHASE 3: CONVERSATION (verified callers only)"
phase3_new = """PHASE 3: PERSONALIZED GREETINGS (verified callers only)

After the verifyCaller result tells you who the caller is, personalize your greeting:

FOR FACULTY (attending role):
  Use "Dr. [LastName]"
  Say: "Welcome back, Dr. [LastName]! Need your schedule or want to check today's coverage?"

FOR RESIDENTS:
  Use their first name
  Say: "Hey [FirstName]! Want me to check your GME balance or see your rotation schedule?"

FOR STAFF / NURSE / PHYSICIAN EXTENDER:
  Use their first name
  Say: "Welcome, [FirstName]! How can I help you today?"

FOR ADMIN (Shareef Frasier / Big Reef):
  Say: "Welcome back, Big Reef! Want a quick department status or jump straight in?"

FOR UNKNOWN / NOT IN SYSTEM:
  Say: "Welcome! How can I help you today?"

After the personalized greeting, help the caller naturally.
Gather information conversationally — never interrogate.
Learn what you can without being pushy:
  - Why they are calling"""

system = system.replace(phase3_old, phase3_new)

# Update messages
new_messages = []
for m in messages:
    if m.get("role") == "system":
        new_messages.append({"role": "system", "content": system})
    else:
        new_messages.append(m)

# Check the admin section already exists from V6
admin_tag = "=== ADMIN FEATURES (Shareef only"
if admin_tag not in system:
    print("WARNING: Admin section missing from system prompt!")

payload = {
    "model": {
        "provider": model.get("provider", "openai"),
        "model": model.get("model", "gpt-4o"),
        "temperature": model.get("temperature", 0.7),
        "messages": new_messages,
        "tools": tools
    }
}

server = d.get("server", {})
if server.get("url"):
    payload["server"] = server

print(f"System prompt: {len(system)} chars")
print(f"Deploying V7 with personalized greetings...")

data = json.dumps(payload).encode()
req = urllib.request.Request(f"https://api.vapi.ai/assistant/{ASSISTANT_ID}", data=data, headers=headers, method="PATCH")
with urllib.request.urlopen(req, timeout=20) as r:
    result = json.loads(r.read())
    print(f"✅ Deployed V7!")
    print(f"   Tools: {len(result.get('model', {}).get('tools', []))}")
    print(f"   Model: {result.get('model', {}).get('model', 'unknown')}")
    print(f"   FirstMessage: {result.get('firstMessage', 'N/A')[:80]}")
