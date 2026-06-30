#!/usr/bin/env python3
"""Deploy Vapi Assistant V6 — Add Admin Tools"""
import json, os, urllib.request

# Read API key
with open('/home/hermeswebui/.hermes/.env') as f:
    env = f.read()
api_key = ""
for line in env.split('\n'):
    if line.startswith('VAPI_API_KEY='):
        api_key = line.split('=', 1)[1].strip().strip("'\"")
        break

ASSISTANT_ID = "9b00342e-1951-4bd0-b4a5-5ca4c9827bd0"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0"
}

# Get current assistant config
req = urllib.request.Request(f"https://api.vapi.ai/assistant/{ASSISTANT_ID}", headers=headers)
with urllib.request.urlopen(req, timeout=15) as r:
    assistant = json.loads(r.read())

# Get current model config and tools
model = assistant.get("model", {})
tools = model.get("tools", assistant.get("tools", []))
messages = model.get("messages", [])

# Get current system prompt
system_msg = ""
for m in messages:
    if m.get("role") == "system":
        system_msg = m["content"]
        break

# Add admin-only section to system prompt
admin_section = """

=== ADMIN FEATURES (Shareef only — verified by ez_id=504615) ===

When Shareef Frasier (EZ ID 504615) is verified, these ADMIN tools are available:

## ADMIN TOOL 1: resetUserPin
Reset anyone's PIN to a new 4-digit number.
Example: "Reset Jasmin's PIN to 1234" → call resetUserPin(name="Jasmin Capellan", new_pin="1234")
Only Shareef can use this. If a non-admin caller asks, say "Only Shareef can reset PINs."

## ADMIN TOOL 2: unlockUser
Unlock a user who's been locked out from too many failed PIN attempts.
Example: "Unlock Dr. Aboumohamed" → call unlockUser(name="Alex Aboumohamed")
Only Shareef can use this.

## ADMIN TOOL 3: addUser
Add a new user to the system with name, role, phone, and EZ ID.
Example: "Add Dr. Kim to the system, EZ ID 77812, phone 555-1234" → call addUser(name="Joseph Kim", role="resident", phone="555-1234", ez_id="77812")
Only Shareef can use this.

## ADMIN TOOL 4: departmentStatus
Get a quick department dashboard overview — today's open sick calls, coverage gaps, grand rounds status.
Example: "What's going on in the department today?" → call departmentStatus()
Only Shareef can use this.

## ADMIN TOOL 5: broadcastMessage
Send a message to all residents or all faculty.
Example: "Text all residents about Friday's grand rounds at 8am" → call broadcastMessage(group="residents", message="Reminder: Grand rounds Friday at 8am in the conference room.")
Only Shareef can use this.

CRITICAL: Only show admin tools to Shareef. If someone who isn't Shareef asks about these, say "That's something only Shareef can do."
"""

# Admin tool definitions
admin_tools = [
    {
        "type": "function",
        "function": {
            "name": "resetUserPin",
            "description": "Reset any user's PIN to a new 4-digit number. Admin only — verified by caller's identity.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name of the user whose PIN to reset"},
                    "new_pin": {"type": "string", "description": "New 4-digit PIN"}
                },
                "required": ["name", "new_pin"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "unlockUser",
            "description": "Unlock a user who has been locked out due to too many failed PIN attempts. Admin only.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name of the user to unlock"}
                },
                "required": ["name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "addUser",
            "description": "Add a new user to the system with name, role, phone, and EZ ID. Admin only.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Full name of the new user"},
                    "role": {"type": "string", "description": "Role: resident, faculty, staff, nurse"},
                    "phone": {"type": "string", "description": "Phone number"},
                    "ez_id": {"type": "string", "description": "EZ ID number for the user"}
                },
                "required": ["name", "role", "phone"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "departmentStatus",
            "description": "Get a quick department status overview — today's sick calls, coverage gaps, call schedule for today. Admin only.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "broadcastMessage",
            "description": "Send a message to all residents or all faculty. Admin only.",
            "parameters": {
                "type": "object",
                "properties": {
                    "group": {"type": "string", "enum": ["residents", "faculty", "all"], "description": "Who to send the message to"},
                    "message": {"type": "string", "description": "The message to send"}
                },
                "required": ["group", "message"]
            }
        }
    }
]

# Add admin tools to existing tools
all_tools = tools + admin_tools

# Update system prompt
updated_system = system_msg + admin_section

# Update messages
new_messages = []
for m in messages:
    if m.get("role") == "system":
        new_messages.append({"role": "system", "content": updated_system})
    else:
        new_messages.append(m)

# Build update payload
payload = {
    "model": {
        "provider": model.get("provider", "openai"),
        "model": model.get("model", "gpt-4o"),
        "temperature": model.get("temperature", 0.7),
        "messages": new_messages,
        "tools": all_tools
    }
}

# Check if server URL is set
server = assistant.get("server", {})
if server.get("url"):
    payload["server"] = server

# Dry run
print(f"Tools: {len(tools)} existing + {len(admin_tools)} new = {len(all_tools)} total")
print(f"System prompt: {len(system_msg)} chars → {len(updated_system)} chars (+{len(admin_section)} chars)")
print(f"\nNew admin tools:")
for t in admin_tools:
    fn = t["function"]
    print(f"  ✅ {fn['name']}: {fn['description'][:60]}")

# Deploy
print(f"\n--- PATCHING ASSISTANT {ASSISTANT_ID} ---")
data = json.dumps(payload).encode()
req = urllib.request.Request(
    f"https://api.vapi.ai/assistant/{ASSISTANT_ID}",
    data=data, headers=headers, method="PATCH"
)
with urllib.request.urlopen(req, timeout=20) as r:
    result = json.loads(r.read())
    print(f"✅ Deployed! Tools: {len(result.get('model', {}).get('tools', []))}")
    print(f"   Model: {result.get('model', {}).get('model', 'unknown')}")
    print(f"   FirstMessage: {result.get('firstMessage', 'N/A')[:80]}")
