#!/usr/bin/env python3
"""Update Kelly Bottger's CRM/PIN entry with personal data + special Vapi greeting"""
import json, os, urllib.request, re, hashlib

# ── 1. Update PIN DB ─────────────────────────────────────────
with open('/workspace/agentic-os/data/user_pins.json') as f:
    pins = json.load(f)

pins["contact-kelly-bottger"] = {
    "name": "Kelly Bottger",
    "display_name": "Kellz",
    "pin_hash": hashlib.sha256("6368".encode()).hexdigest(),
    "role": "manager",
    "department": "Urology",
    "email": "KBottger@montefiore.org",
    "phone": "",
    "default_pin": "6368",
    "ez_id": "36368",
    "notes": "Loves shopping at Zales for diamonds. Manager. Initiate small talk — ask about her weekend or if she's been to Zales lately."
}

with open('/workspace/agentic-os/data/user_pins.json', 'w') as f:
    json.dump(pins, f, indent=2)

print("✅ PIN DB updated for Kelly")

# ── 2. Update CRM ────────────────────────────────────────────
with open('/workspace/agentic-os/data/crm_contacts.json') as f:
    crm = json.load(f)

for c in crm:
    if c.get('id') == 'contact-kelly-bottger':
        c['category'] = 'Manager'
        c['ezId'] = '36368'
        print(f"✅ CRM updated for Kelly: {c['firstName']} {c['lastName']} → Manager")
        break

with open('/workspace/agentic-os/data/crm_contacts.json', 'w') as f:
    json.dump(crm, f, indent=2)

# ── 3. Update Vapi assistant system prompt ──────────────────
with open('/home/hermeswebui/.hermes/.env') as f:
    env = f.read()

api_key = ""
for line in env.split('\n'):
    if line.startswith('VAPI_API_KEY=***        parts = line.split('=', 1)
        if len(parts) > 1:
            api_key = parts[1].strip().strip("'\"")

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

# Add Kelly's special greeting to the personalized section
kelly_greeting = """
SPECIAL GREETING — KELLY BOTTGER (Manager, EZ ID 36368):
When Kelly Bottger (Kellz) calls, this is the MOST IMPORTANT caller after Shareef.
  Greeting: "Hey Kellz! What's good? How's your week going?"
  THEN: Make natural small talk before business. Ask about:
    - Her weekend plans
    - If she's been shopping lately (she loves Zales diamonds)
  THEN: Ask what she needs help with.
  She's the manager. Be warm, familiar, and treat her like a friend.
"""

# Insert before the admin section
admin_tag = "=== ADMIN FEATURES (Shareef only"
kelly_block = "\n" + kelly_greeting + "\n"
system = system.replace(admin_tag, kelly_block + admin_tag)

# Also check if PHASE 3 greeting section has special entries, add Kelly there
phase3_tag = "PHASE 3: PERSONALIZED GREETINGS"
if phase3_tag in system:
    # Add manager section
    manager_section = """
FOR MANAGER (Kelly Bottger / Kellz):
  Use "Kellz" — warm and familiar.
  Say: "Hey Kellz! What's good? How's your week going?"
  Make small talk before business — ask about shopping, weekend plans, Zales.
  She's your manager — be respectful but friendly, like a coworker you actually like.
"""
    for_tag = "FOR ADMIN (Shareef):"
    system = system.replace(for_tag, manager_section + "\n" + for_tag)
    print("✅ Manager greeting section added to PHASE 3")
else:
    print("❌ Could not find PHASE 3 section")

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
        "tools": tools
    }
}

server = d.get("server", {})
if server.get("url"):
    payload["server"] = server

print(f"\nSystem prompt: {len(system)} chars")
print(f"Deploying with Kelly's special greeting...")

data = json.dumps(payload).encode()
req = urllib.request.Request(f"https://api.vapi.ai/assistant/{ASSISTANT_ID}", data=data, headers=headers, method="PATCH")
with urllib.request.urlopen(req, timeout=20) as r:
    result = json.loads(r.read())
    msgs = result.get('model', {}).get('messages', [])
    for m in msgs:
        if m.get('role') == 'system':
            c = m.get('content', '')
            if 'Kellz' in c:
                print(f"\n✅ Kelly's greeting found in deployed system prompt!")
                break
    print(f"✅ Deployed! Tools: {len(result.get('model', {}).get('tools', []))}")
    print(f"   Kelly's PIN: 6368")
    print(f"   Kelly's EZ ID: 36368")
