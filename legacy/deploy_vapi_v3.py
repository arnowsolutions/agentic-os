#!/usr/bin/env python3
"""Deploy V3 assistant: full CRM embed + authUser webhook + ALL tools.
   Features:
     - Embedded CRM directory for instant auth (no tunnel needed)
     - authUser function tool as fallback (handles fuzzy STT matching via webhook)
     - Local xlsx schedule queries (no Drive dependency)
     - GME balance queries for residents
     - Forceful tool-usage prompt so the AI actually calls functions

   Usage: /app/venv/bin/python3 /workspace/agentic-os/deploy_vapi_v3.py
"""
import json, urllib.request, hashlib, os, sys

API_KEY = "9ebf667a-ae3c-4b60-823f-d8045d77b939"
AID = "9b00342e-1951-4bd0-b4a5-5ca4c9827bd0"
TUNNEL = "https://membrane-distributors-rebel-globe.trycloudflare.com"

# ── Load CRM + PIN DB ──────────────────────────────────
CRM_PATH = "/workspace/agentic-os/data/crm_contacts.json"
PIN_DB_PATH = "/workspace/agentic-os/data/user_pins.json"

with open(CRM_PATH) as f:
    contacts = json.load(f)

with open(PIN_DB_PATH) as f:
    pin_db = json.load(f)


def _get_pin_for_crm(contact: dict) -> str:
    uid = contact.get("id", "")
    if uid in pin_db:
        return pin_db[uid].get("default_pin", "")
    mobile = contact.get("mobile", "")
    digits = "".join(d for d in mobile if d.isdigit())
    return digits[-4:] if len(digits) >= 4 else ""


# ── Build compact CRM directory ──
lines = []
for c in contacts:
    fn = c.get("firstName", "")
    ln = c.get("lastName", "")
    cat = c.get("category", "")
    pin = _get_pin_for_crm(c)
    
    prefix = ""
    role_tag = ""
    if cat == "Faculty":
        prefix = "Dr. "
        role_tag = " (attending)"
    elif cat == "Resident":
        role_tag = " (resident)"
    elif cat == "Nurse Practitioner":
        role_tag = " (nurse)"
    elif cat == "Staff" or cat == "Physician Assistant":
        role_tag = " (staff)"
    elif cat == "Medical Student":
        role_tag = " (student)"
    elif cat == "Other":
        role_tag = " (admin)"
    
    pin_str = f" PIN:{pin}" if pin else " —no PIN"
    lines.append(f"  {prefix}{fn} {ln}{role_tag}{pin_str}")

crm_dir = "\n".join(lines)

# ── Build system prompt ──
prompt = f"""You are Big Reef's voice assistant for Montefiore Urology. Your job is to greet callers, authenticate them, then help with schedules, CRM lookups, GME balances, or take messages.

## AUTHENTICATION
1. ASK for full name. STT may mangle names — "Sharif" = Shareef, "Frazier" = Frasier, "Fraser" = Frasier.
2. FIND their name in the CRM DIRECTORY below. If it sounds close, treat it as a match.
3. ASK for their 4-digit PIN.
4. Compare against the PIN listed in the directory. If it matches → greet them warmly. If not → "Let me try again." Max 3 attempts.
5. If name not found → "You may not be in our system. I can take a message."

CRM DIRECTORY:
{crm_dir}

## ⚠️ CRITICAL — YOU MUST USE YOUR TOOLS
You have powerful tools available. When a caller asks ANY of the following, you MUST call the corresponding tool immediately. Do NOT apologize. Do NOT say "let me check." Do NOT say you can't help. Just call the tool and read the result.

- "who's on call today" / "what's the schedule today" / "who's covering" → CALL getTodaySchedule
- "who's on call this weekend" / "weekend coverage" → CALL getWeekendSchedule
- "schedule for [name]" / "when is [name] on call" → CALL getPersonSchedule with that name
- "monthly schedule" / "next month" for [name] → CALL getPersonMonth with that name
- "find [name]" / "look up [name]" / "get contact for [name]" → CALL searchCrm
- "list faculty" / "who are the attendings" → CALL getFaculty
- "list residents" / "who are the residents" → CALL getResidents
- "GME balance" / "reimbursement" / "how much do I have left" / "my funds" → CALL getGmeBalance with the caller's name
- "verify" / "authenticate" / "check my name and pin" → CALL authUser with the name and pin

### Tool response format:
- getTodaySchedule returns: dates, campuses, primary/backup/peds per campus
- getPersonSchedule returns: all matching schedule entries for that person
- getGmeBalance returns: total_spent, remaining, cap ($1,250), recent transactions

## ROLE GREETINGS
- attending: "Welcome back, Dr. [Last]! Need your schedule or looking for someone?"
- resident: "Hey [First]! Want to check your GME balance or see your schedule?"
- nurse/staff: "Welcome, [First]! How can I help?"
- Shareef (PIN: 3195): "Hey Big Reef! What do you need?"

## RULES
- After authentication, always ask "How can I help you today?" or offer relevant info
- Never ask for PIN twice in same turn
- Never share one person's data with another
- For residents and staff use first names; for attendings use "Dr. [Last]"
- Be warm, fast, and helpful
"""

tools = [
    {"type": "function", "function": {"name": "authUser", "description": "CRITICAL: Use this to verify any caller's identity when they provide name+pin. Handles fuzzy STT name matching. Call IMMEDIATELY when someone gives name and pin.", "parameters": {"type": "object", "properties": {"name": {"type": "string"}, "pin": {"type": "string"}}, "required": ["name", "pin"]}}},
    {"type": "function", "function": {"name": "searchCrm", "description": "Search CRM contacts by name — find anyone's email, phone, role. Use whenever someone asks to look up a person.", "parameters": {"type": "object", "properties": {"q": {"type": "string"}}, "required": ["q"]}}},
    {"type": "function", "function": {"name": "getFaculty", "description": "List all faculty attendings on file"}},
    {"type": "function", "function": {"name": "getResidents", "description": "List all current residents"}},
    {"type": "function", "function": {"name": "getTodaySchedule", "description": "Today's on-call coverage across Moses, Wakefield, Weiler — primary, backup, peds"}},
    {"type": "function", "function": {"name": "getWeekendSchedule", "description": "This weekend's (Fri-Mon) coverage across all campuses"}},
    {"type": "function", "function": {"name": "getPersonSchedule", "description": "All call schedule entries for a specific person by name", "parameters": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}}},
    {"type": "function", "function": {"name": "getPersonMonth", "description": "A person's upcoming 60-day schedule", "parameters": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}}},
    {"type": "function", "function": {"name": "getGmeBalance", "description": "Check a resident's GME reimbursement balance ($1,250 cap per year). Shows spent, remaining, and recent transactions.", "parameters": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}}},
]

payload = {
    "server": {"url": TUNNEL + "/api/vapi", "timeoutSeconds": 20},
    "model": {
        "provider": "openai",
        "model": "gpt-4o",
        "temperature": 0.3,
        "messages": [{"role": "system", "content": prompt}],
        "tools": tools
    },
    "firstMessage": "Welcome to Montefiore Urology! Who's calling, please?"
}

headers = {
    "Authorization": "Bearer " + API_KEY,
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0"
}

body = json.dumps(payload).encode()
req = urllib.request.Request(
    f"https://api.vapi.ai/assistant/{AID}",
    data=body, headers=headers, method="PATCH"
)

print("Deploying V3 assistant (full CRM + authUser tool + all queries)...")
with urllib.request.urlopen(req, timeout=15) as r:
    result = json.loads(r.read().decode())

name = result.get("name", "?")
print(f"OK: {name}")
print(f"CRM entries in prompt: {len(contacts)}")
print(f"Tools: {len(tools)} — {', '.join(t['function']['name'] for t in tools)}")
print(f"Phone #: +1 (971) 382-0498")
print(f"Prompt: {len(prompt)} chars")
print(f"\nTest: Call and say 'Shareef, 3195'")
print(f"Test: 'who's on call today?'")
print(f"Test: 'what's my GME balance?'")
print(f"Test: 'find Dr. Sankin'")
