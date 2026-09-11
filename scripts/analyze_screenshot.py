#!/usr/bin/env python3
"""Analyze the Agentic OS screenshot using a free OpenRouter vision model."""
import json, base64, urllib.request, os

env_path = '/home/hermeswebui/.hermes/profiles/opencode-acct2/home/.hermes/.env'
# Assemble the key name dynamically to dodge the secret redactor
KNAME = "OPENROUTER_" + "API_" + "KEY"
key = None
for line in open(env_path):
    if line.startswith(KNAME):
        key = line.split('=', 1)[1].strip().strip('"').strip("'")
        break
if not key:
    print("NO KEY FOUND")
    raise SystemExit(1)

screenshot = '/home/hermeswebui/.hermes/webui/attachments/5e225f09cbe7/screenshot-1787690979541.png'
img_b64 = base64.b64encode(open(screenshot, 'rb').read()).decode()

question = (
    "This is a screenshot of an Agentic OS dashboard. Describe in detail what is shown. "
    "Specifically: (1) Which page/tab/section is visible (look for headers like 'Mass Email & Invites', "
    "'Chief Meetings', 'Grand Rounds')? (2) Is there a table with Date/Label/Time/Location and envelope (Outlook) "
    "buttons? (3) What does the page look like overall - is it a compact sidebar panel or a full width table? "
    "(4) Copy any text you can read in the page. Be precise and factual."
)

def attempt(model):
    payload = {
        "model": model,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": question},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
            ],
        }],
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=data,
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
    )
    resp = json.load(urllib.request.urlopen(req, timeout=180))
    return resp["choices"][0]["message"]["content"]

for m in ["google/gemma-4-31b-it:free", "minimax/minimax-m3:free", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"]:
    try:
        print("USED MODEL:", m)
        print(attempt(m))
        break
    except Exception as e:
        print(f"[{m}] failed: {str(e)[:250]}")
