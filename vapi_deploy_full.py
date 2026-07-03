#!/usr/bin/env python3
"""Full Vapi assistant upgrade — V6.
Registers all 35 tools, updates system prompt, voice settings, and
patches the bridge with new handlers (getMyDashboard, emailMyDashboard,
VIP phone recognition, sick call auto-find, voicemail).
"""
import base64, json, os, sys, subprocess, requests

ASSISTANT_ID = "9b00342e-1951-4bd0-b4a5-5ca4c9827bd0"

# ─── Read API key from .env ──────────────────────────────────────────────────
ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
api_key = None
if os.path.exists(ENV_PATH):
    with open(ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if line.startswith("VAPI_API_KEY="):
                api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
if not api_key:
    api_key = os.environ.get("VAPI_API_KEY", "")
if not api_key:
    print("ERROR: VAPI_API_KEY not found")
    sys.exit(1)

# ─── Read new system prompt ────────────────────────────────────────────────
PROMPT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vapi_system_prompt.txt")
if os.path.exists(PROMPT_PATH):
    with open(PROMPT_PATH) as f:
        SYSTEM_PROMPT = f.read()
else:
    print("ERROR: vapi_system_prompt.txt not found")
    sys.exit(1)

# ─── Tool Definitions (all 35) ──────────────────────────────────────────────
TOOL_SCHEMA = {
    "type": "object",
    "properties": {},
}


def make_tool(name, description, parameters):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": parameters,
        }
    }


TOOLS = [
    # ─── Auth ───
    make_tool("verifyCaller",
        "Verify a caller's identity using their EZ ID and PIN, or name and PIN. Returns verification status, greeting, and caller profile. If the caller's phone number matches, returns auto_verified=true.",
        {"type": "object", "properties": {
            "caller_ez_id": {"type": "string", "description": "The caller's EZ ID (employee badge ID number)"},
            "caller_name": {"type": "string", "description": "The caller's full name (fallback if no EZ ID)"},
            "caller_pin": {"type": "string", "description": "The caller's 4-digit PIN"},
        }, "required": ["caller_pin"]}),

    make_tool("takeMessage",
        "Save a message for Shareef. Collects caller info, message content, callback number, and email for confirmation.",
        {"type": "object", "properties": {
            "caller_name": {"type": "string", "description": "Name of the caller"},
            "message": {"type": "string", "description": "The message content — what they want Shareef to know"},
            "phone": {"type": "string", "description": "Best callback phone number"},
            "email": {"type": "string", "description": "Email for confirmation receipt (optional)"},
            "callback_requested": {"type": "boolean", "description": "Whether the caller wants a callback"},
        }, "required": ["caller_name", "message"]}),

    # ─── Schedule: Call Coverage ───
    make_tool("getTodaySchedule",
        "Get today's attending call coverage schedule (Moses, Wakefield, Weiler campuses). Returns primary, backup, and peds coverage.",
        {"type": "object", "properties": {}}),

    make_tool("getWeekendSchedule",
        "Get this weekend's attending call coverage schedule.",
        {"type": "object", "properties": {}}),

    make_tool("getPersonSchedule",
        "Get a specific person's upcoming call coverage schedule.",
        {"type": "object", "properties": {
            "name": {"type": "string", "description": "Full name of the person to look up"},
        }, "required": ["name"]}),

    make_tool("getPersonMonth",
        "Get a specific person's call coverage for the current month.",
        {"type": "object", "properties": {
            "name": {"type": "string", "description": "Full name of the person to look up"},
        }, "required": ["name"]}),

    make_tool("scheduleByDate",
        "Get call coverage schedule for a specific date. Pass the date exactly as the caller said it (e.g. 'today', 'tomorrow', 'July 2', 'next Monday'). The backend normalizes it.",
        {"type": "object", "properties": {
            "date": {"type": "string", "description": "Date as spoken by caller (e.g. 'today', 'tomorrow', 'July 2', 'next Monday')"},
        }, "required": ["date"]}),

    # ─── GME / Reimbursement ───
    make_tool("getGmeBalance",
        "Get a verified caller's GME reimbursement balance. ONLY for the verified caller's own data.",
        {"type": "object", "properties": {
            "name": {"type": "string", "description": "Full name of the verified caller"},
        }, "required": ["name"]}),

    # ─── QGenda ───
    make_tool("qgendaToday",
        "Get today's QGenda clinic/OR physician assignments. Can filter by person name.",
        {"type": "object", "properties": {
            "name": {"type": "string", "description": "Optional: filter to a specific person's assignment"},
        }}),

    make_tool("qgendaUpcoming",
        "Get a person's upcoming QGenda clinic/OR assignments for the next N days.",
        {"type": "object", "properties": {
            "name": {"type": "string", "description": "Full name of the person"},
            "days": {"type": "integer", "description": "Number of days to look ahead (default 7)"},
        }, "required": ["name"]}),

    make_tool("qgendaWhere",
        "Find who is assigned to a specific QGenda task or clinic today.",
        {"type": "object", "properties": {
            "task": {"type": "string", "description": "Task or clinic name to look up"},
        }}),

    # ─── Staff / Location ───
    make_tool("staffFind",
        "Look up a support staff member's location and schedule.",
        {"type": "object", "properties": {
            "name": {"type": "string", "description": "Full name of the staff member"},
        }, "required": ["name"]}),

    make_tool("staffAtLocation",
        "Get all staff scheduled at a specific location on a given date. Returns data_status field for phrasing.",
        {"type": "object", "properties": {
            "location": {"type": "string", "description": "Location name (e.g. 'Nursing', 'Clerical', 'PH2')"},
            "date": {"type": "string", "description": "Date as spoken (e.g. 'today', 'tomorrow', 'July 2'). Defaults to today."},
        }, "required": ["location"]}),

    # ─── Knowledge Base ───
    make_tool("knowledgeSearch",
        "Search the knowledge base for factual/policy/institutional questions about Montefiore Urology, Grand Rounds, resident education, conferences, protocols.",
        {"type": "object", "properties": {
            "q": {"type": "string", "description": "Concise search query"},
            "top_k": {"type": "integer", "description": "Max results (default 3)"},
        }, "required": ["q"]}),

    # ─── Sick Call ───
    make_tool("submitSickCall",
        "Submit a sick call / call-out. Automatically finds eligible backup coverage and emails Shareef with suggestions.",
        {"type": "object", "properties": {
            "employee_id": {"type": "string", "description": "Employee ID of the caller"},
            "start_date": {"type": "string", "description": "Start date of the sick call (YYYY-MM-DD or date as spoken)"},
            "days_requested": {"type": "integer", "description": "Number of days off (default 1)"},
            "name": {"type": "string", "description": "Caller's full name"},
            "campus": {"type": "string", "description": "Campus they were assigned to (optional)"},
        }, "required": ["employee_id", "start_date"]}),

    # ─── Swap Call ───
    make_tool("swapCall",
        "Request a call swap. Returns eligible swap candidates from the same service line. Logs the request and notifies Shareef by email.",
        {"type": "object", "properties": {
            "caller": {"type": "string", "description": "Name of the person requesting the swap"},
            "date": {"type": "string", "description": "Date of the call to swap"},
            "reason": {"type": "string", "description": "Reason for the swap request"},
            "preferred": {"type": "string", "description": "Preferred person to swap with (optional)"},
        }, "required": ["caller", "date"]}),

    # ─── Meeting ───
    make_tool("scheduleMeeting",
        "Schedule a meeting — creates a Google Calendar event and sends email invitations to attendees.",
        {"type": "object", "properties": {
            "title": {"type": "string", "description": "Meeting title"},
            "date": {"type": "string", "description": "Meeting date (YYYY-MM-DD)"},
            "start_time": {"type": "string", "description": "Start time HH:MM (24h, default 12:00)"},
            "duration_minutes": {"type": "integer", "description": "Duration in minutes (default 30)"},
            "attendees": {"type": "array", "items": {"type": "string"}, "description": "List of attendee email addresses"},
            "description": {"type": "string", "description": "Meeting description/notes"},
        }, "required": ["title", "date"]}),

    # ─── Email ───
    make_tool("emailSchedule",
        "Generate a professional PDF of the call coverage schedule and email it to the caller.",
        {"type": "object", "properties": {
            "email": {"type": "string", "description": "Recipient email address"},
            "date_from": {"type": "string", "description": "Start date YYYY-MM-DD (optional)"},
            "date_to": {"type": "string", "description": "End date YYYY-MM-DD (optional)"},
            "person": {"type": "string", "description": "Person name for person-specific schedule (optional)"},
            "campus": {"type": "string", "description": "Filter by campus name (optional)"},
        }, "required": ["email"]}),

    make_tool("emailStaffRoster",
        "Email the support staff roster for a location on a given date as a professional PDF.",
        {"type": "object", "properties": {
            "location": {"type": "string", "description": "Location/department name (e.g. 'Nursing', 'Clerical')"},
            "date": {"type": "string", "description": "Date as spoken or YYYY-MM-DD (defaults to today)"},
            "email": {"type": "string", "description": "Recipient email (optional, defaults to caller's email)"},
        }, "required": ["location"]}),

    make_tool("emailMyDashboard",
        "Generate a professional PDF of the verified caller's complete dashboard (clinic assignments, call coverage, GME balance, deadlines, evaluations) and email it to them.",
        {"type": "object", "properties": {
            "name": {"type": "string", "description": "Verified caller's full name"},
            "role": {"type": "string", "description": "Caller's role (attending, resident, staff, administrator)"},
            "email": {"type": "string", "description": "Recipient email address"},
        }, "required": ["name", "email"]}),

    # ─── Dashboard ───
    make_tool("getMyDashboard",
        "Get the verified caller's complete dashboard: clinic assignments, call coverage, GME balance, deadlines, and evaluations — all merged into one response. Use when caller asks for everything / their overview / show me my stuff.",
        {"type": "object", "properties": {
            "name": {"type": "string", "description": "Verified caller's full name"},
            "role": {"type": "string", "description": "Caller's role (attending, resident, staff, administrator)"},
        }, "required": ["name"]}),

    # ─── Roster ───
    make_tool("queryLocationRoster",
        "Query the raw location roster data for a location on a given date.",
        {"type": "object", "properties": {
            "location": {"type": "string", "description": "Location name"},
            "date": {"type": "string", "description": "Date as spoken or YYYY-MM-DD"},
        }, "required": ["location"]}),

    # ─── Deadlines / Evaluations ───
    make_tool("getDeadlines",
        "Get upcoming deadline reminders for a caller role.",
        {"type": "object", "properties": {
            "role": {"type": "string", "description": "Caller role (attending, resident, staff, administrator)"},
        }}),

    make_tool("getEvaluationsDue",
        "Get evaluations due for a specific person.",
        {"type": "object", "properties": {
            "name": {"type": "string", "description": "Full name of the person"},
        }, "required": ["name"]}),

    # ─── Misc ───
    make_tool("getWeather",
        "Get current weather for a location.",
        {"type": "object", "properties": {
            "location": {"type": "string", "description": "City/area (default Bronx, NY)"},
        }}),

    make_tool("getNews",
        "Get recent news headlines, optionally filtered by topic.",
        {"type": "object", "properties": {
            "topic": {"type": "string", "description": "Topic to filter news by"},
        }}),

    make_tool("searchCrm",
        "Search the CRM/contact directory by name.",
        {"type": "object", "properties": {
            "q": {"type": "string", "description": "Search query — full or partial name"},
        }, "required": ["q"]}),

    make_tool("getFaculty",
        "List all faculty members in the directory.",
        {"type": "object", "properties": {}}),

    make_tool("getResidents",
        "List all residents in the directory.",
        {"type": "object", "properties": {}}),

    # ─── Admin (Shareef only) ───
    make_tool("resetUserPin",
        "ADMIN ONLY: Reset a user's PIN. Only available to Shareef (EZ ID 504615).",
        {"type": "object", "properties": {
            "name": {"type": "string", "description": "Name of the user whose PIN to reset"},
            "new_pin": {"type": "string", "description": "New 4-digit PIN"},
        }, "required": ["name", "new_pin"]}),

    make_tool("unlockUser",
        "ADMIN ONLY: Clear auth lockout for a user. Only available to Shareef.",
        {"type": "object", "properties": {
            "name": {"type": "string", "description": "Name of the user to unlock"},
        }, "required": ["name"]}),

    make_tool("addUser",
        "ADMIN ONLY: Add a new user to the system with default PIN. Only available to Shareef.",
        {"type": "object", "properties": {
            "name": {"type": "string", "description": "Full name of the new user"},
            "role": {"type": "string", "description": "Role (staff, resident, attending, administrator)"},
            "phone": {"type": "string", "description": "Phone number"},
            "ez_id": {"type": "string", "description": "EZ ID (employee badge ID)"},
        }, "required": ["name"]}),

    make_tool("departmentStatus",
        "ADMIN ONLY: Get today's department status — call coverage overview. Available to Shareef.",
        {"type": "object", "properties": {}}),

    make_tool("broadcastMessage",
        "ADMIN ONLY: Log a broadcast message to a group (residents, faculty, all). Available to Shareef.",
        {"type": "object", "properties": {
            "group": {"type": "string", "description": "Target group: 'residents', 'faculty', or 'all'"},
            "message": {"type": "string", "description": "Message to broadcast"},
        }, "required": ["message"]}),

    # ── Directions / Traffic (Mapbox real-time) ──
    make_tool("getDirections",
        "Get real-time driving directions with traffic. Returns brief summary (distance, time, traffic) for voice + full turn-by-turn for email. ALWAYS offer to email — do NOT read all steps aloud.",
        {"type": "object", "properties": {
            "origin": {"type": "string", "description": "Starting location (address, place name, or resident name)"},
            "destination": {"type": "string", "description": "Destination (address, place name, or Montefiore campus name)"},
        }, "required": ["origin", "destination"]}),

    # ── Email Directions / Weather / News ──
    make_tool("emailDirections",
        "Get real-time driving directions with traffic and email them as formatted HTML. Use when caller asks for directions, traffic, or commute info. Do NOT read turn-by-turn aloud — email it.",
        {"type": "object", "properties": {
            "origin": {"type": "string", "description": "Starting location (address, place name, or resident name)"},
            "destination": {"type": "string", "description": "Destination (address, place name, or Montefiore campus name)"},
            "email": {"type": "string", "description": "Email address to send the directions to"},
        }, "required": ["origin", "destination", "email"]}),

    make_tool("emailWeather",
        "Get the weather forecast and email it as formatted HTML. Use when caller asks for weather. Say the brief summary aloud, then email the full forecast.",
        {"type": "object", "properties": {
            "location": {"type": "string", "description": "Location (default: Bronx, NY)"},
            "email": {"type": "string", "description": "Email address to send the forecast to"},
        }, "required": ["email"]}),

    make_tool("emailNews",
        "Get medical/urology news and email it as formatted HTML. Use when caller asks for news. Say the top headline aloud, then email the full list.",
        {"type": "object", "properties": {
            "topic": {"type": "string", "description": "Topic to search for (default: urology/medical education)"},
            "email": {"type": "string", "description": "Email address to send the news to"},
        }, "required": ["email"]}),
]

print(f"Defined {len(TOOLS)} tools")

# ─── First Message ─────────────────────────────────────────────────────────
FIRST_MESSAGE = (
    "Hey, thanks for calling Montefiore Urology. I'm Shareef's assistant. "
    "Do you have your EZ ID number handy? That's your employee badge ID."
)

END_CALL_MESSAGE = (
    "Thanks for calling. Take care."
)

# ─── Voice Settings ────────────────────────────────────────────────────────
VOICE_CONFIG = {
    "voiceId": "shimmer",
    "provider": "openai",
}

# ─── Build PATCH Payload ──────────────────────────────────────────────────
payload = {
    "name": "Big Reef Personal Assistant",
    "firstMessage": FIRST_MESSAGE,
    "endCallMessage": END_CALL_MESSAGE,
    "voice": VOICE_CONFIG,
    "silenceTimeoutSeconds": 30,
    "responseDelaySeconds": 0.4,
    "model": {
        "model": "gpt-4o",
        "provider": "openai",
        "temperature": 0.7,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}],
        "tools": TOOLS,
    },
}

# ─── Push to Vapi ──────────────────────────────────────────────────────────
print("Pushing assistant config to Vapi...")
resp = requests.patch(
    f"https://api.vapi.ai/assistant/{ASSISTANT_ID}",
    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    json=payload,
    timeout=60,
)

if resp.status_code == 200:
    data = resp.json()
    tool_count = len(data.get("model", {}).get("tools", []))
    print(f"✅ SUCCESS — Assistant updated with {tool_count} tools")
    print(f"  First message: {data.get('firstMessage', '')[:80]}...")
    print(f"  Voice: {data.get('voice', {}).get('voiceId', 'unknown')}")
    print(f"  Silence timeout: {data.get('silenceTimeoutSeconds')}s")
    print(f"  Response delay: {data.get('responseDelaySeconds')}s")
    prompt_preview = data.get("model", {}).get("messages", [{}])[0].get("content", "")[:100]
    print(f"  System prompt starts: {prompt_preview}...")
else:
    print(f"❌ FAILED — Status {resp.status_code}")
    print(resp.text[:500])
    sys.exit(1)