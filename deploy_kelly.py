#!/usr/bin/env python3
"""Update Vapi assistant with Kelly's special greeting"""
import json, os, urllib.request

# Read API key from env
with open('/home/hermeswebui/.hermes/.env') as f:
    env_lines = [l.strip() for l in f.readlines()]

api_key = ""
for line in env_lines:
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

# Add Kelly's greeting section
kelly_greeting = """

SPECIAL — KELLY BOTTGER (Manager, EZ ID 36368):
When Kelly Bottger (nickname Kellz) calls, she is the second most important caller after Shareef.
  Greeting: "Hey Kellz! What's good? How's your week going?"
  Make small talk BEFORE business. Ask about:
    - Her weekend plans
    - If she's been shopping lately (she loves Zales diamonds)
  Keep it warm and familiar. She's your manager — treat her like a friend.
  THEN ask what she needs help with.
"""

admin_tag = "=== ADMIN FEATURES (Shareef only"
if admin_tag in system:
    system = system.replace(admin_tag, kelly_greeting + "\n" + admin_tag)
    print("Kelly greeting inserted before admin section")
else:
    print("Admin tag not found, appending instead")
    system += kelly_greeting

# Add manager to PHASE 3 greetings
phase3_tag = "FOR ADMIN (Shareef):"
manager_section = """FOR MANAGER (Kelly Bottger / Kellz):
  Use "Kellz" — warm and familiar.
  Say: "Hey Kellz! What's good? How's your week going?"
  Make small talk before business — ask about shopping, weekend plans, Zales.
  She's your manager — be respectful but friendly, like a coworker you actually like.

"""
if phase3_tag in system:
    system = system.replace(phase3_tag, manager_section + "\n" + phase3_tag)
    print("Manager section added to PHASE 3")

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
data = json.dumps(payload).encode()
req = urllib.request.Request(f"https://api.vapi.ai/assistant/{ASSISTANT_ID}", data=data, headers=headers, method="PATCH")
with urllib.request.urlopen(req, timeout=20) as r:
    result = json.loads(r.read())
    # Verify Kelly's greeting made it
    msgs = result.get('model', {}).get('messages', [])
    for m in msgs:
        if m.get('role') == 'system':
            c = m.get('content', '')
            if 'Kellz' in c and 'Zales' in c:
                print("✅ Kelly's special greeting verified in deployed system prompt!")
            elif 'Kellz' in c:
                print("⚠️ Kellz found but Zales reference missing")
            break
    print(f"✅ Deployed! Tools: {len(result.get('model', {}).get('tools', []))}")
