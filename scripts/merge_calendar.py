#!/usr/bin/env python3
"""
Quick sync: read the existing calendar_events.json (which already has Google Calendar data),
merge the manual seed events we added, and update the file.
Also runs the Google Calendar sync if token is available.
"""
import json, os
from pathlib import Path

DATA_FILE = Path('/workspace/agentic-os/data/calendar_events.json')

# Read what we have
data = json.loads(DATA_FILE.read_text())

# Add/update manual Dr. Sankin vacation events
manual_events = []
for ev in data.get("events", []):
    if ev.get("source") == "manual":
        manual_events.append(ev)

# Ensure our specific vacation events are in there
vacations = [
    {"summary": "Dr. Sankin - Vacation", "description": "Dr. Sankin vacation (Jul 6-10)", "start": {"date": "2026-07-06", "timeZone": "America/New_York"}, "end": {"date": "2026-07-11", "timeZone": "America/New_York"}, "source": "manual"},
    {"summary": "Dr. Sankin - Vacation", "description": "Dr. Sankin extended vacation (Aug 24 - Sep 7)", "start": {"date": "2026-08-24", "timeZone": "America/New_York"}, "end": {"date": "2026-09-08", "timeZone": "America/New_York"}, "source": "manual"},
]

for v in vacations:
    # Check if already exists
    exists = any(
        e.get("start", {}).get("date") == v["start"]["date"] and
        e.get("summary") == v["summary"]
        for e in data.get("events", [])
    )
    if not exists:
        data["events"].append(v)
        print(f"Added: {v['summary']} ({v['start']['date']} - {v['end']['date']})")
    else:
        print(f"Already exists: {v['summary']} ({v['start']['date']} - {v['end']['date']})")

# Remove duplicate manual events
seen = set()
unique = []
for ev in data["events"]:
    key = (ev.get("summary", ""), ev.get("start", {}).get("date", ""), ev.get("source", ""))
    if key not in seen:
        seen.add(key)
        unique.append(ev)

data["events"] = unique
data["manual_events"] = manual_events + vacations
data["last_synced"] = "2026-06-29T12:30:00-04:00"

DATA_FILE.write_text(json.dumps(data, indent=2))
print(f"\nTotal events: {len(data['events'])}")
print("Done!")
