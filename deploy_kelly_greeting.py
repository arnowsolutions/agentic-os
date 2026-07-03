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

# ── 2. Update CRM (Supabase Postgres + JSON fallback) ────────
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from modules.crm_db import get_contacts

crm = get_contacts()
if not crm:
    # Fallback to JSON
    json_path = '/workspace/agentic-os/data/crm_contacts.fallback.json'
    if os.path.exists(json_path):
        with open(json_path) as f:
            crm = json.load(f)

for c in crm:
    if c.get('id') == 'contact-kelly-bottger' or (c.get('ezId') == '36368'):
        c['category'] = 'Manager'
        c['ezId'] = '36368'
        print(f"✅ CRM updated for Kelly: {c.get('firstName')} {c.get('lastName')} → Manager")
        break

# Write back to JSON fallback
json_path = '/workspace/agentic-os/data/crm_contacts.fallback.json'
with open(json_path, 'w') as f:
    json.dump(crm, f, indent=2)

# Write to Supabase Postgres
try:
    import subprocess as _sp
    pw = os.environ.get("POSTGRES_PASSWORD", "")
    if not pw:
        r = _sp.run(['grep', 'POSTGRES_PASSWORD', '/workspace/projects/unified/app/.env'],
            capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            pw = r.stdout.strip().split('=', 1)[1].strip()
    if pw:
        import psycopg2
        conn = psycopg2.connect(host="127.0.0.1", port=5432, dbname="postgres", user="postgres", password=pw, connect_timeout=3)
        cur = conn.cursor()
        cur.execute("UPDATE public.contacts SET category = %s, ez_id = %s WHERE id = %s OR ez_id = %s",
            ('Manager', '36368', 'contact-kelly-bottger', '36368'))
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Supabase PG updated for Kelly")
except Exception as e:
    print(f"⚠️ Could not update Supabase PG: {e}")

# ── 3. Update Vapi assistant system prompt ──────────────────
api_key = os.environ.get('VAPI_API_KEY', '')
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
