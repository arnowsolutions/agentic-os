#!/usr/bin/env python3
"""Fetch latest Vapi call transcripts"""
import urllib.request, json

API_KEY = "9ebf667a-ae3c-4b60-823f-d8045d77b939"
AID = "9b00342e-1951-4bd0-b4a5-5ca4c9827bd0"

req = urllib.request.Request(
    f"https://api.vapi.ai/call?assistantId={AID}&limit=3",
    headers={"Authorization": f"Bearer {API_KEY}", "User-Agent": "Mozilla/5.0"}
)
calls = json.loads(urllib.request.urlopen(req, timeout=10).read())

for c in calls if isinstance(calls, list) else []:
    t = c.get('transcript', '') or ''
    if t.strip():
        print(f"=== Call {c.get('id','?')[:35]} ({c.get('status')}) ===")
        for line in t.strip().split('\n'):
            print(line.strip())
        print()
    else:
        print(f"Call {c.get('id','?')[:35]}: in-progress\n")
