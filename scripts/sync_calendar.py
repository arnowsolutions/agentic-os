#!/usr/bin/env python3
"""
Sync Google Calendar events to the Agentic OS calendar data file.
Run manually or via cron: python3 /workspace/agentic-os/scripts/sync_calendar.py

Pulls events from the primary Google Calendar for the next 365 days,
merges them with any manually-added events.
"""
import json, os, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE_DIR = Path('/workspace/agentic-os')
DATA_FILE = BASE_DIR / 'data' / 'calendar_events.json'

# Google API imports
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as AuthRequest
from googleapiclient.discovery import build

TOKEN_PATHS = [
    # Primary account (letsgetmoney2009)
    '/home/hermeswebui/.hermes/google_token.json',
    # Urology residency program account
    '/home/hermeswebui/.hermes/google_token_urologyresidencyprogram.json',
]

def fetch_from_account(token_path, account_label):
    """Fetch events from a single Google account. Returns list of events or raises."""
    creds = Credentials.from_authorized_user_file(
        token_path,
        ['https://www.googleapis.com/auth/calendar']
    )
    
    if creds.expired and creds.refresh_token:
        request = AuthRequest()
        creds.refresh(request)
        with open(token_path, 'w') as f:
            f.write(creds.to_json())
    
    service = build('calendar', 'v3', credentials=creds)
    
    now = datetime.now(timezone.utc)
    time_min = now.isoformat()
    time_max = (now + timedelta(days=365)).isoformat()
    
    page_token = None
    all_events = []
    while True:
        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime',
            pageToken=page_token,
        ).execute()
        all_events.extend(events_result.get('items', []))
        page_token = events_result.get('nextPageToken')
        if not page_token:
            break
    
    synced = []
    for ev in all_events:
        synced.append({
            "summary": ev.get('summary', 'Untitled'),
            "description": ev.get('description', ''),
            "start": ev.get('start', {}),
            "end": ev.get('end', {}),
            "location": ev.get('location', ''),
            "source": "google_calendar",
            "google_id": ev.get('id', ''),
            "account": account_label,
        })
    
    return synced

def main():
    # Load existing data (to preserve manual events)
    existing = {"events": [], "manual_events": []}
    if DATA_FILE.exists():
        try:
            existing = json.loads(DATA_FILE.read_text())
        except:
            pass
    
    manual_events = existing.get("manual_events", [])
    all_synced = []
    errors = []
    
    for token_path in TOKEN_PATHS:
        if not os.path.exists(token_path):
            errors.append(f"Token not found: {token_path}")
            continue
        
        label = "urology" if "urologyresidency" in token_path else "primary"
        try:
            events = fetch_from_account(token_path, label)
            all_synced.extend(events)
            print(f"Synced {len(events)} events from {label} account")
        except Exception as e:
            errors.append(f"{label}: {e}")
            print(f"Sync failed for {label}: {e}")
    
    # Merge: manual events + all synced events
    merged = {
        "events": manual_events + all_synced,
        "manual_events": manual_events,
        "last_synced": datetime.now().isoformat(),
        "sync_count": len(all_synced),
    }
    if errors:
        merged["sync_errors"] = errors
    
    # Sort by start date
    merged["events"].sort(key=lambda e: e['start'].get('date', e['start'].get('dateTime', '')))
    
    DATA_FILE.write_text(json.dumps(merged, indent=2))
    print(f"Total events in data file: {len(merged['events'])}")
    print("Sync complete!")

def add_manual_event(summary, start_date, end_date, description=""):
    """Add a manual event to the calendar data. Callable from other scripts."""
    if DATA_FILE.exists():
        data = json.loads(DATA_FILE.read_text())
    else:
        data = {"events": [], "manual_events": []}
    
    event = {
        "summary": summary,
        "description": description,
        "start": {"date": start_date, "timeZone": "America/New_York"},
        "end": {"date": end_date, "timeZone": "America/New_York"},
        "source": "manual",
    }
    
    data.setdefault("manual_events", []).append(event)
    data["events"] = data["manual_events"] + [
        e for e in data.get("events", [])
        if e.get("source") != "manual"  # keep synced events
    ]
    
    DATA_FILE.write_text(json.dumps(data, indent=2))
    print(f"Added manual event: {summary} ({start_date} to {end_date})")
    return event

if __name__ == '__main__':
    main()
