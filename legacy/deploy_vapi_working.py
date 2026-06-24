#!/usr/bin/env python3
"""Deploy working Vapi assistant: embedded auth + tunnel for schedule queries.
   Run this to restore the config after any changes.
   Usage: /app/venv/bin/python3 /workspace/agentic-os/deploy_vapi_working.py
"""
import json, urllib.request

k = "9ebf667a-ae3c-4b60-823f-d8045d77b939"
AID = "9b00342e-1951-4bd0-b4a5-5ca4c9827bd0"
TUNNEL = "https://membrane-distributors-rebel-globe.trycloudflare.com"

prompt = (
    "You are Big Reef's voice assistant for Montefiore Urology.\n\n"
    "AUTHENTICATION:\n"
    "1. Ask for full name and 4-digit PIN.\n"
    "2. If name sounds like Shareef/Sharif/Shariff AND PIN is 1279: VERIFIED - greet warmly as Big Reef.\n"
    "3. Any other name or PIN: 'I could not verify you. Please contact the office.' Max 3 tries.\n\n"
    "AFTER VERIFICATION:\n"
    "- To check call schedules: use getTodaySchedule or getPersonSchedule tools\n"
    "- To look up people: use searchCrm or getFaculty or getResidents tools\n"
    "- If a tool returns unavailable data, say 'Schedule data isn't available right now. Big Reef is working on restoring the connection.'\n\n"
    "Never ask PIN twice."
)

tools = [
    {"type": "function", "function": {"name": "searchCrm", "description": "Search CRM contacts by name", "parameters": {"type": "object", "properties": {"q": {"type": "string"}}, "required": ["q"]}}},
    {"type": "function", "function": {"name": "getFaculty", "description": "List all faculty members"}},
    {"type": "function", "function": {"name": "getResidents", "description": "List all residents"}},
    {"type": "function", "function": {"name": "getTodaySchedule", "description": "Today's call coverage for Moses, Wakefield, Weiler"}},
    {"type": "function", "function": {"name": "getPersonSchedule", "description": "Call schedule for one person", "parameters": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}}},
]

payload = {
    "server": {"url": TUNNEL + "/api/vapi", "timeoutSeconds": 30},
    "model": {
        "provider": "openai",
        "model": "gpt-4o",
        "temperature": 0.3,
        "messages": [{"role": "system", "content": prompt}],
        "tools": tools
    },
    "firstMessage": "Thank you for calling Montefiore Urology. Before I help you, I need your full name and 4-digit PIN."
}

headers = {"Authorization": "Bearer " + k, "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
body = json.dumps(payload).encode()
req = urllib.request.Request(f"https://api.vapi.ai/assistant/{AID}", data=body, headers=headers, method="PATCH")

with urllib.request.urlopen(req, timeout=15) as r:
    result = json.loads(r.read().decode())
print("OK: " + result.get("name", "?"))
print("Auth: embedded (PIN 1279)")
print("Schedule: tunnel via " + TUNNEL)
print("Call +1 (971) 382-0498 - say 'Shareef, 1279'")
