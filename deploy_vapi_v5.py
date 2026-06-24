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
    
    payload = {
        "name": "Big Reef Personal Assistant",
        "firstMessage": current.get("firstMessage"),
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
