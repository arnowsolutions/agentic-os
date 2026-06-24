#!/usr/bin/env python3
"""Update Vapi assistant config: server URL + V5 system prompt."""
import os
import re
import json
import requests

# --- Config ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TUNNEL_URL_FILE = os.path.join(BASE_DIR, "tunnel_url.txt")

# Load system prompt from single source of truth
PROMPT_PATH = os.path.join(BASE_DIR, "prompts", "vapi_assistant_v5.md")
with open(PROMPT_PATH) as _f:
    SYSTEM_PROMPT = _f.read().strip()
print(f"Loaded system prompt from {PROMPT_PATH} ({len(SYSTEM_PROMPT)} chars)")

# Read VAPI_API_KEY from .env
env_path = os.path.join(os.path.dirname(__file__), '.env')
api_key = None
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line.startswith('VAPI_API_KEY='):
            api_key = line.split('=', 1)[1]
            break

if not api_key:
    print("ERROR: VAPI_API_KEY not found in .env")
    exit(1)

# Read tunnel URL
with open(TUNNEL_URL_FILE) as f:
    tunnel_url = f.read().strip()
print(f"Tunnel URL: {tunnel_url}")

SERVER_URL = f"{tunnel_url}/vapi"

# --- Fetch current assistant config ---
print("Fetching current assistant config...")
r = requests.get(f"https://api.vapi.ai/assistant/{ASSISTANT_ID}", 
                 headers={"Authorization": f"Bearer {api_key}"}, timeout=30)
if r.status_code != 200:
    print(f"ERROR fetching config: {r.status_code} {r.text}")
    exit(1)

config = r.json()
print(f"Current name: {config.get('name')}")
print(f"Current server URL: {config.get('server', {}).get('url')}")
print(f"Prompt length before: {len(config.get('model', {}).get('messages', [{}])[0].get('content', '')) if config.get('model', {}).get('messages') else 0}")

# --- Update server URL ---
if 'server' not in config:
    config['server'] = {}
config['server']['url'] = SERVER_URL
config['server']['timeoutSeconds'] = 20

# --- Update system prompt ---
# The Vapi API uses model.messages for the system prompt
messages = [{"role": "system", "content": SYSTEM_PROMPT}]

# Preserve existing model settings
if 'model' not in config:
    config['model'] = {}
config['model']['messages'] = messages
config['model']['temperature'] = 0.7
config['model']['provider'] = config.get('model', {}).get('provider', 'openai')
config['model']['model'] = config.get('model', {}).get('model', 'gpt-4o')

# Remove tools from model level (they're defined at top level)
# Actually keep tools in model if they were there - Vapi seems to use both levels
# Let's not touch tools at all

# --- Update assistant ---
print(f"\nUpdating server URL to: {SERVER_URL}")
print(f"Updating system prompt ({len(SYSTEM_PROMPT)} chars)...")

# --- Register staffAtLocation tool if not already registered ---
staff_at_location_tool = {
    "type": "function",
    "function": {
        "name": "staffAtLocation",
        "description": "Use this for 'who is working/scheduled at [location] on [date]' questions about secretaries, extenders, and support staff. This queries the location roster data (not the CRM directory).",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The location or department name (e.g. 'Nursing', 'Clerical')"
                },
                "date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format (optional, defaults to today)"
                }
            },
            "required": ["location"]
        }
    }
}

# Check existing tools from config
existing_tools = config.get("model", {}).get("tools", [])
tool_names = [t.get("function", {}).get("name") for t in existing_tools if isinstance(t, dict)]
if "staffAtLocation" not in tool_names:
    existing_tools.append(staff_at_location_tool)
    print(f"📝 Added staffAtLocation tool (was not in existing {len(tool_names)} tools)")
else:
    print(f"✓ staffAtLocation tool already registered")

# --- Register emailStaffRoster tool if not already registered ---
email_staff_roster_tool = {
    "type": "function",
    "function": {
        "name": "emailStaffRoster",
        "description": "Email the staff roster for a specific location on a given date. Use for 'email me the [location] roster' or 'send me who's at [location]' requests.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The location or department name (e.g. 'Nursing', 'Clerical')"
                },
                "date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format (optional, defaults to today)"
                },
                "email": {
                    "type": "string",
                    "description": "Recipient email address (optional, defaults to configured recipient)"
                }
            },
            "required": ["location"]
        }
    }
}

if "emailStaffRoster" not in tool_names:
    existing_tools.append(email_staff_roster_tool)
    print(f"📝 Added emailStaffRoster tool (was not in existing {len(tool_names)} tools)")
else:
    print(f"✓ emailStaffRoster tool already registered")

# PUT update
payload = {
    "name": config.get("name"),
    "voice": config.get("voice"),
    "firstMessage": config.get("firstMessage"),
    "server": config["server"],
    "model": {
        **config.get("model", {}),
        "messages": messages,
        "tools": existing_tools,
    },
}

r = requests.patch(f"https://api.vapi.ai/assistant/{ASSISTANT_ID}",
                   headers={"Authorization": f"Bearer {api_key}"},
                   json=payload,
                   timeout=30)

if r.status_code == 200:
    result = r.json()
    new_url = result.get('server', {}).get('url')
    msg_len = len(result.get('model', {}).get('messages', [{}])[0].get('content', '')) if result.get('model', {}).get('messages') else 0
    print(f"✅ Update successful!")
    print(f"   Server URL: {new_url}")
    print(f"   Prompt length: {msg_len}")
    print(f"   Tools: {len(result.get('model', {}).get('tools', []))}")
else:
    print(f"❌ Update failed: {r.status_code}")
    print(r.text[:500])
