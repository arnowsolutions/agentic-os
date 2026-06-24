#!/usr/bin/env python3
"""Fix all existing Grand Rounds + Monday calendar events with proper Zoom details."""
import subprocess, json, os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

GAPI = "/home/hermeswebui/.hermes/skills/productivity/google-workspace/scripts/google_api.py"
TOKEN_PATH = "/home/hermeswebui/.hermes/google_token.json"

ZOOM_GR = {
    "link": "https://us02web.zoom.us/j/86773878358?pwd=RUxySVVzUjFWL0lyRWtjdDBacTVPZz09",
    "id": "867 7387 8358",
    "passcode": "466916",
}
ZOOM_MON = {
    "link": "https://montefiore.zoom.us/j/92009850717?pwd=25ask1SzLX2SdSrTbbhzb159UsyDFY.1",
    "id": "920 0985 0717",
    "passcode": "808018",
}


def list_all_events():
    cmd = ["python3", GAPI, "calendar", "list", "--start", "2026-07-01T00:00:00Z",
           "--end", "2027-07-01T00:00:00Z"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return json.loads(result.stdout) if result.returncode == 0 else []


def update_event(event_id, description, location=""):
    creds = Credentials.from_authorized_user_file(TOKEN_PATH,
        ["https://www.googleapis.com/auth/calendar"])
    service = build("calendar", "v3", credentials=creds)
    event = service.events().get(calendarId="primary", eventId=event_id).execute()
    # Fix literal \n text and add Zoom
    event["description"] = description.replace("\\n", "\n")
    if location:
        event["location"] = location
    result = service.events().update(calendarId="primary", eventId=event_id, body=event).execute()
    return result.get("htmlLink")


# Main
all_events = list_all_events()
print(f"Total events in range: {len(all_events)}")

gr = [e for e in all_events if "Grand Rounds" in e.get("summary", "")]
mon = [e for e in all_events if "SASP" in e.get("summary", "")]
print(f"Grand Rounds: {len(gr)}, Monday SASP: {len(mon)}")

for label, events, zoom in [("GR", gr, ZOOM_GR), ("MON", mon, ZOOM_MON)]:
    fixed = 0
    for e in events:
        eid = e["id"]
        summary = e.get("summary", "")
        desc = e.get("description", "") or ""

        if zoom["link"] in desc:
            continue  # already has Zoom

        # Remove literal \n, add Zoom details
        desc_clean = desc.replace("\\n", "\n").strip()
        new_desc = f"""{desc_clean}

ZOOM MEETING
Join: {zoom["link"]}
Meeting ID: {zoom["id"]}
Passcode: {zoom["passcode"]}"""

        try:
            update_event(eid, new_desc, "Zoom - Montefiore Urology")
            fixed += 1
        except Exception as ex:
            print(f"  ❌ {summary[:40]}: {str(ex)[:60]}")
    print(f"  {label}: {fixed}/{len(events)} fixed")
