#!/usr/bin/env python3
"""Deploy Vapi assistant V5 with corrected schedule mappings."""
import json, os, sys, requests
from datetime import date, timedelta

# --- Config ---
ASSISTANT_ID = "9b00342e-1951-4bd0-b4a5-5ca4c9827bd0"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TUNNEL_URL_FILE = os.path.join(BASE_DIR, "tunnel_url.txt")

# Load system prompt from single source of truth
PROMPT_PATH = os.path.join(BASE_DIR, "prompts", "vapi_assistant_v5.md")
with open(PROMPT_PATH) as _f:
    PROMPT = _f.read().strip()
print(f"Loaded system prompt from {PROMPT_PATH} ({len(PROMPT)} chars)")

def get_tunnel_url():
    with open(TUNNEL_URL_FILE) as f:
        return f.read().strip()

def get_api_key():
    env_path = os.path.join(BASE_DIR, ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("VAPI_API_KEY="):
                    return line.split("=", 1)[1]
    return os.environ.get("VAPI_API_KEY", "")


def main():
    api_key = get_api_key()
    if not api_key:
        print("ERROR: No VAPI_API_KEY found")
        sys.exit(1)
    
    tunnel = get_tunnel_url()
    print(f"Tunnel URL: {tunnel}")
    
    # Fetch current tools
    resp = requests.get(f"https://api.vapi.ai/assistant/{ASSISTANT_ID}",
        headers={"Authorization": f"Bearer {api_key}"}, timeout=30)
    current = resp.json()
    tools = current.get("model", {}).get("tools", [])
    print(f"Tools: {len(tools)}")

    # Ensure verifyCaller tool has caller_ez_id parameter
    updated = False
    for tool in tools:
        fn = tool.get("function", {})
        if fn.get("name") == "verifyCaller":
            props = fn.get("parameters", {}).get("properties", {})
            if "caller_ez_id" not in props:
                props["caller_ez_id"] = {
                    "type": "string",
                    "description": "The caller's EZ ID (employee/badge ID number). Optional — use instead of caller_name for direct lookup."
                }
                required = fn.get("parameters", {}).get("required", [])
                fn["parameters"]["required"] = [r for r in required if r != "caller_ez_id"]
                # Ensure caller_name is not required either (or caller_ez_id)
                updated = True
            if "caller_name" not in props:
                props["caller_name"] = {
                    "type": "string",
                    "description": "The caller's full name. Optional if caller_ez_id is provided."
                }
                fn["parameters"]["required"] = [r for r in fn.get("parameters", {}).get("required", []) if r != "caller_name"]
                updated = True
            break
    
    if updated:
        print("Updated verifyCaller tool definition (added caller_ez_id)")
    else:
        print("verifyCaller tool already has caller_ez_id")
    
    # Ensure getMyDashboard tool exists
    dashboard_tool_name = "getMyDashboard"
    has_dashboard = any(
        t.get("function", {}).get("name") == dashboard_tool_name
        for t in tools
    )
    if not has_dashboard:
        tools.append({
            "type": "function",
            "function": {
                "name": dashboard_tool_name,
                "description": "Return ALL schedule data for a verified caller — clinic assignments, call coverage, GME balance, vacation time, evaluations, and deadlines — merged into one comprehensive result. Call this when the caller says 'my schedule', 'show me everything', 'what's going on', or wants a complete picture of their data. Arguments: caller_name (the verified caller's name) and caller_role (their role: administrator/faculty/resident/staff).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "caller_name": {
                            "type": "string",
                            "description": "The verified caller's full name (from verification)"
                        },
                        "caller_role": {
                            "type": "string",
                            "description": "The caller's role: administrator, faculty, resident, or staff"
                        }
                    },
                    "required": ["caller_name", "caller_role"]
                }
            }
        })
        print("Added getMyDashboard tool")

    # Ensure emailMyDashboard tool exists
    email_dash_tool = "emailMyDashboard"
    has_email_dash = any(
        t.get("function", {}).get("name") == email_dash_tool
        for t in tools
    )
    if not has_email_dash:
        tools.append({
            "type": "function",
            "function": {
                "name": email_dash_tool,
                "description": "SEND a comprehensive HTML email with ALL the caller's schedule data — clinic assignments, call coverage, GME balance, vacation, evaluations, and deadlines. Use THIS instead of reading data aloud on the phone. After verifying a caller, ask if they want it emailed, then call this with their name, role, and email. Saves phone time and credits by sending data to their inbox instead of speaking it.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "caller_name": {
                            "type": "string",
                            "description": "The verified caller's full name"
                        },
                        "caller_role": {
                            "type": "string",
                            "description": "The caller's role: administrator, faculty, resident, or staff"
                        },
                        "email": {
                            "type": "string",
                            "description": "Email address to send to. Use the caller's email from their profile if available."
                        }
                    },
                    "required": ["caller_name", "caller_role", "email"]
                }
            }
        })
        print("Added emailMyDashboard tool")
    
    payload = {
        "name": "Big Reef Personal Assistant",
        "firstMessage": "Hey, thanks for calling Shareef's line at Montefiore Urology. I'm his assistant. Do you have your EZ ID number handy?",
        "server": {"url": f"{tunnel}/vapi", "timeoutSeconds": 20},
        "model": {
            "model": "gpt-4o",
            "provider": "openai",
            "temperature": 0.7,
            "messages": [{"role": "system", "content": PROMPT}],
            "tools": tools
        }
    }
    
    resp = requests.patch(f"https://api.vapi.ai/assistant/{ASSISTANT_ID}",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload, timeout=30)
    
    if resp.status_code in (200, 201, 204):
        print("Deploy OK")
    else:
        print(f"Deploy FAILED: {resp.status_code} {resp.text[:500]}")
        sys.exit(1)

if __name__ == "__main__":
    main()
