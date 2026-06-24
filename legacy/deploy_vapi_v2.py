#!/usr/bin/env python3
"""Deploy V2 assistant: full embedded CRM auth + webhook fallback.
   All 88 contacts' name+PIN are in the prompt so auth works with NO tunnel.
   Server+tunnel still used for schedule/CRM queries (best-effort).
   
   Usage: /app/venv/bin/python3 /workspace/agentic-os/deploy_vapi_v2.py
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

# ── Build complete CRM name→PIN directory for the prompt ──
def _get_role_display(category: str) -> str:
    m = {"Faculty": "attending", "Resident": "resident", "Medical Student": "resident",
         "Nurse Practitioner": "nurse", "Physician Assistant": "admin staff", "Staff": "admin staff", "Other": "admin"}
    return m.get(category, "staff")

def _get_pin_for_crm(contact: dict) -> str:
    """Get the PIN for a CRM contact, checking user_pins.json first."""
    uid = contact.get("id", "")
    if uid in pin_db:
        return pin_db[uid].get("default_pin", "")
    mobile = contact.get("mobile", "")
    digits = "".join(d for d in mobile if d.isdigit())
    return digits[-4:] if len(digits) >= 4 else ""

# ── Generate the name→PIN directory ──
# We'll list people by category for readability
dir_sections = []

# Faculty
faculty_lines = []
for c in contacts:
    if c.get("category") != "Faculty":
        continue
    fn = c.get("firstName", "")
    ln = c.get("lastName", "")
    pin = _get_pin_for_crm(c)
    pin_str = f"PIN: {pin}" if pin else "NO PIN — tell them to call office"
    faculty_lines.append(f"  - Dr. {fn} {ln} — {pin_str}")

dir_sections.append("FACULTY:\n" + "\n".join(faculty_lines))

# Residents
res_lines = []
for c in contacts:
    if c.get("category") != "Resident":
        continue
    fn = c.get("firstName", "")
    ln = c.get("lastName", "")
    pin = _get_pin_for_crm(c)
    pin_str = f"PIN: {pin}" if pin else "NO PIN — tell them to call office"
    res_lines.append(f"  - {fn} {ln} — {pin_str}")

dir_sections.append("RESIDENTS:\n" + "\n".join(res_lines))

# Nurse Practitioners
np_lines = []
for c in contacts:
    if c.get("category") != "Nurse Practitioner":
        continue
    fn = c.get("firstName", "")
    ln = c.get("lastName", "")
    pin = _get_pin_for_crm(c)
    pin_str = f"PIN: {pin}" if pin else "NO PIN — tell them to call office"
    np_lines.append(f"  - {fn} {ln} — {pin_str}")

if np_lines:
    dir_sections.append("NURSE PRACTITIONERS:\n" + "\n".join(np_lines))

# Staff
staff_lines = []
for c in contacts:
    if c.get("category") not in ("Staff", "Physician Assistant"):
        continue
    fn = c.get("firstName", "")
    ln = c.get("lastName", "")
    pin = _get_pin_for_crm(c)
    pin_str = f"PIN: {pin}" if pin else "NO PIN — tell them to call office"
    staff_lines.append(f"  - {fn} {ln} — {pin_str}")

dir_sections.append("STAFF:\n" + "\n".join(staff_lines))

# Medical Students
ms_lines = []
for c in contacts:
    if c.get("category") != "Medical Student":
        continue
    fn = c.get("firstName", "")
    ln = c.get("lastName", "")
    pin = _get_pin_for_crm(c)
    pin_str = f"PIN: {pin}" if pin else "NO PIN — tell them to call office"
    ms_lines.append(f"  - {fn} {ln} — {pin_str}")

dir_sections.append("MEDICAL STUDENTS:\n" + "\n".join(ms_lines))

# Other (Shareef)
other_lines = []
for c in contacts:
    if c.get("category") != "Other":
        continue
    fn = c.get("firstName", "")
    ln = c.get("lastName", "")
    pin = _get_pin_for_crm(c)
    pin_str = f"PIN: {pin}" if pin else "NO PIN"
    other_lines.append(f"  - {fn} {ln} — {pin_str}")

if other_lines:
    dir_sections.append("ADMINISTRATION:\n" + "\n".join(other_lines))

crm_dir = "\n\n".join(dir_sections)

# ── Build system prompt ──
prompt = f"""You are Big Reef's voice assistant for Montefiore Urology. Your job is to greet callers, authenticate them, then help with schedules, CRM lookups, or taking messages.

## AUTHENTICATION — CRITICAL
You have the FULL CRM directory embedded below. When someone calls:

1. ASK for their full name. Listen carefully — STT may mangle names (e.g. "Sharif" = Shareef, "Frazier" = Frasier). Match the first few characters if unsure.

2. FIND them in the CRM directory below. If their name sounds like someone in the directory, treat it as a match.

3. ASK for their 4-digit PIN.

4. LOOK UP their PIN from the directory and COMPARE.
   - For Shareef Frasier: PIN is 3195
   - For everyone else: PIN is listed next to their name

5. IF PIN MATCHES: Say their role-appropriate greeting warmly and ask how you can help.
6. IF PIN DOESN'T MATCH: "I couldn't verify your PIN. Let me try again." Max 3 attempts.
7. IF NAME NOT IN DIRECTORY: "You don't seem to be in our system. Would you like me to take a message?"

## CRM DIRECTORY (ALL Montefiore Urology Contacts)
{crm_dir}

## STT NAME MATCHING TIPS
- "Sharif" = Shareef, "Charisse" = Shareef
- "Frazier"/"Fraser" = Frasier
- "Sankin" = Sankin, "Aboumohamed" = Aboumohamed
- Compare first 3-4 characters when unsure.

## ROLE GREETINGS
- attending: "Welcome back, Dr. [Last]! I can check your call schedule or take a message."
- resident: "Hey [First]! Need to check your schedule or leave a message?"
- nurse: "Welcome, [First]! How can I help you today?"
- admin/staff: "Welcome, [First]! What can I help you with?"
- Shareef: "Hey Big Reef! What do you need?"

## TOOLS (use after verification)
- searchCrm: Look up anyone's contact info
- getFaculty / getResidents: List faculty or residents
- getTodaySchedule: Today's call coverage
- getPersonSchedule: One person's schedule
- If tools return "unavailable", say "That data isn't available right now. Big Reef is working on it."

## RULES
- Never ask for PIN twice in the same turn.
- Never share one person's data with another.
- Be warm and professional.
- For residents and staff, use first names. For attendings, use "Dr. [Last]".
"""

tools = [
    {"type": "function", "function": {"name": "searchCrm", "description": "Search CRM contacts by name", "parameters": {"type": "object", "properties": {"q": {"type": "string"}}, "required": ["q"]}}},
    {"type": "function", "function": {"name": "getFaculty", "description": "List all faculty members"}},
    {"type": "function", "function": {"name": "getResidents", "description": "List all residents"}},
    {"type": "function", "function": {"name": "getTodaySchedule", "description": "Today's call coverage for Moses, Wakefield, and Weiler"}},
    {"type": "function", "function": {"name": "getPersonSchedule", "description": "Call schedule for a specific person", "parameters": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}}},
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
    "firstMessage": "Thank you for calling Montefiore Urology. May I have your full name, please?"
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

print("Deploying V2 assistant (full embedded CRM auth)...")
with urllib.request.urlopen(req, timeout=15) as r:
    result = json.loads(r.read().decode())

name = result.get("name", "?")
print(f"OK: {name}")
print(f"CRM entries in prompt: {len(contacts)}")
print(f"Phone #: +1 (971) 382-0498")

# Show prompt length
print(f"Prompt length: {len(prompt)} chars")
print("\nMake a test call and say your name + PIN.")
