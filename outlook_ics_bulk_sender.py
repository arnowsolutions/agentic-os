#!/usr/bin/env python3
"""
Outlook Calendar Bulk Invite Sender
====================================
Send .ics-equivalent calendar invites via Outlook/Exchange when Gmail SMTP is blocked.

THREE MODES:
  Mode 1 (Graph):   Microsoft Graph API — one-time device-code auth, then create events
                    and send invites programmatically. No headless browser needed.
  Mode 2 (Browser): Playwright browser automation — logs into Outlook Web, opens deeplink
                    compose forms, clicks Send.
  Mode 3 (Deeplink):Generates CSV of Outlook deeplink URLs you can open in your own browser.

Usage:
  python3 outlook_ics_bulk_sender.py --help

Examples:
  # Graph API — authenticate once (device code flow)
  python3 outlook_ics_bulk_sender.py --mode graph-auth

  # Graph API — batch send invites
  python3 outlook_ics_bulk_sender.py --mode graph --type monday --limit 5

  # Generate deeplink CSV (no browser, no setup)
  python3 outlook_ics_bulk_sender.py --mode deeplinks --type all

  # Test — print a single deeplink to preview
  python3 outlook_ics_bulk_sender.py --mode test --date 2026-07-10

  # Check progress
  python3 outlook_ics_bulk_sender.py --mode report
"""
import json, re, os, sys, time, csv, argparse
from datetime import date, datetime, timedelta
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.resolve()
GR_DATA_FILE = BASE_DIR / "dashboard" / "pages" / "grand-rounds.js"
EMAIL_GROUPS_FILE = BASE_DIR / "data" / "email_groups.json"
PROGRESS_DIR = BASE_DIR / "data"
MONDAY_PROGRESS = PROGRESS_DIR / "monday_outlook_progress.json"
GR_PROGRESS = PROGRESS_DIR / "grand_rounds_outlook_progress.json"
DEEPLINK_DIR = BASE_DIR / "data" / "outlook_deeplinks"
GRAPH_TOKEN_FILE = Path.home() / ".outlook_graph_token.json"
COOKIE_FILE = Path.home() / ".outlook_cookies.json"

# ── Zoom Config ─────────────────────────────────────────────
GR_ZOOM_LINK = "https://us02web.zoom.us/j/86773878358?pwd=RUxySVVzUjFWL0lyRWtjdDBacTVPZz09"
GR_MEETING_ID = "867 7387 8358"
GR_PASSCODE = "466916"

MON_ZOOM_LINK = "https://montefiore.zoom.us/j/92009850717?pwd=25ask1SzLX2SdSrTbbhzb159UsyDFY.1"
MON_MEETING_ID = "920 0985 0717"
MON_PASSCODE = "808018"

# Microsoft Graph API — device code flow app
# Uses MSAL public client with device code flow for auth
GRAPH_CLIENT_ID = "872cd9fa-d31f-45e0-9eab-6e460a02d1f1"
GRAPH_AUTHORITY = "https://login.microsoftonline.com/common"
GRAPH_SCOPES = ["https://graph.microsoft.com/Calendars.ReadWrite", "https://graph.microsoft.com/Mail.Send"]


# ══════════════════════════════════════════════════════════════
#  DATA SOURCES
# ══════════════════════════════════════════════════════════════

def parse_gr_data():
    """Parse GR_DATA from grand-rounds.js into a Python list."""
    with open(GR_DATA_FILE) as f:
        js = f.read()
    start = js.index("const GR_DATA = ")
    start = js.index("[", start)
    depth = 0
    end = start
    for i, c in enumerate(js[start:]):
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                end = start + i + 1
                break
    array_str = js[start:end]
    array_str = re.sub(r",\s*]", "]", array_str)
    array_str = re.sub(r"//.*", "", array_str)
    return json.loads(array_str)


def get_monday_events():
    """Get all Monday SASP conference events from GR_DATA."""
    gr_data = parse_gr_data()
    events = []
    for row in gr_data:
        mon_date = row[1] if len(row) > 1 else ""
        if not mon_date or not mon_date.startswith("20"):
            continue
        topic = (row[2] or "").strip()
        resident = (row[3] or "").strip()
        attending = (row[4] or "").strip()
        notes = (row[10] or "").strip() if len(row) > 10 else ""
        if not topic or "holiday" in topic.lower():
            continue
        if "[see next yr" in topic.lower():
            continue
        events.append({
            "date": mon_date, "type": "monday", "topic": topic,
            "resident": resident, "attending": attending, "notes": notes,
            "zoom_link": MON_ZOOM_LINK, "meeting_id": MON_MEETING_ID, "passcode": MON_PASSCODE,
        })
    events.sort(key=lambda e: e["date"])
    return events


def get_grand_rounds_events():
    """Get all Friday Grand Rounds events from GR_DATA."""
    gr_data = parse_gr_data()
    events = []
    for row in gr_data:
        fri_date = row[7] if len(row) > 7 else ""
        if not fri_date or not fri_date.startswith("20"):
            continue
        gr_7_8 = (row[8] or "").strip()
        gr_8_9 = (row[9] or "").strip()
        notes = (row[10] or "").strip() if len(row) > 10 else ""
        if "NO GRAND ROUNDS" in gr_7_8 or ("NO GRAND ROUNDS" in gr_8_9):
            continue
        if not gr_7_8 and not gr_8_9:
            continue
        meeting_type = "Grand Rounds"
        if "Peds" in gr_7_8 or "Peds" in gr_8_9:
            meeting_type = "Peds Grand Rounds"
        elif "FACULTY MEETING" in gr_7_8 or "FACULTY MEETING" in gr_8_9:
            meeting_type = "Faculty Meeting"
        elif "Journal Club" in gr_7_8 or "Journal Club" in gr_8_9:
            meeting_type = "Journal Club"
        elif "Quality Improvement" in gr_7_8 or "Quality Improvement" in gr_8_9:
            meeting_type = "QI"
        topic_7_8 = gr_7_8 if gr_7_8 else gr_8_9
        topic_8_9 = gr_8_9 if gr_8_9 else gr_7_8
        events.append({
            "date": fri_date, "type": "grand-rounds", "meeting_type": meeting_type,
            "topic_7_8": topic_7_8, "topic_8_9": topic_8_9, "notes": notes,
            "zoom_link": GR_ZOOM_LINK, "meeting_id": GR_MEETING_ID, "passcode": GR_PASSCODE,
        })
    events.sort(key=lambda e: e["date"])
    return events


def load_email_groups():
    if not EMAIL_GROUPS_FILE.exists():
        return {}
    return json.load(open(EMAIL_GROUPS_FILE))


def get_recipients_for_grand_rounds(meeting_type=""):
    groups = load_email_groups()
    if "Faculty" in meeting_type:
        return groups.get("faculty_meeting", {}).get("emails", [])
    return groups.get("grand_rounds", {}).get("emails", [])


def get_recipients_for_monday():
    groups = load_email_groups()
    return groups.get("resident_conference", {}).get("emails", [])


# ══════════════════════════════════════════════════════════════
#  PROGRESS TRACKING
# ══════════════════════════════════════════════════════════════

def load_progress(event_type):
    file = MONDAY_PROGRESS if event_type == "monday" else GR_PROGRESS
    if file.exists():
        return json.load(open(file))
    return {"sent_dates": [], "last_run": None}


def save_progress(event_type, progress):
    file = MONDAY_PROGRESS if event_type == "monday" else GR_PROGRESS
    PROGRESS_DIR.mkdir(parents=True, exist_ok=True)
    json.dump(progress, open(file, "w"), indent=2)


# ══════════════════════════════════════════════════════════════
#  SUBJECT & BODY BUILDERS
# ══════════════════════════════════════════════════════════════

def build_monday_subject(event):
    topic = event["topic"]
    attending = event["attending"]
    if attending:
        return f"Invitation: Urology Monday Conference - {topic}, Dr. {attending}"
    return f"Invitation: Urology Monday Conference - {topic}"


def build_monday_body(event):
    topic = event["topic"]
    attending = event["attending"]
    resident = event["resident"]
    zoom = event["zoom_link"]
    mid = event["meeting_id"]
    pwd = event["passcode"]
    d = datetime.strptime(event["date"], "%Y-%m-%d")
    formatted = d.strftime("%A, %B %d, %Y")
    parts = [
        f"Urology Department — Resident AM Conference",
        f"",
        f"Date: {formatted}",
        f"Time: 7:00 - 8:00 AM (ET)",
        f"",
        f"Topic: {topic}",
        f"Resident: {resident or 'TBD'}",
        f"Attending: {attending or 'TBD'}",
        f"",
        f"Zoom Meeting:",
        f"  Join: {zoom}",
        f"  Meeting ID: {mid}",
        f"  Passcode: {pwd}",
        f"",
        f"---",
        f"Montefiore Medical Center · Department of Urology",
    ]
    return "\n".join(parts)


def build_grand_rounds_subject(event):
    mt = event["meeting_type"]
    t7 = event["topic_7_8"]
    t8 = event["topic_8_9"]
    if "Faculty" in mt:
        summary = "[FACULTY] Faculty Meeting"
    elif "Peds" in mt:
        summary = "Urology Grand Rounds - Peds / Peds Multidisciplinary"
    elif "Journal" in mt:
        summary = "Urology Grand Rounds - Journal Club"
    else:
        topics = " / ".join(p for p in [t7, t8] if p and p != t7)
        summary = f"Urology Grand Rounds - {topics}" if topics else "Urology Grand Rounds"
    return f"Invitation: {summary}"


def build_grand_rounds_body(event):
    mt = event["meeting_type"]
    t7 = event["topic_7_8"]
    t8 = event["topic_8_9"]
    zoom = event["zoom_link"]
    mid = event["meeting_id"]
    pwd = event["passcode"]
    d = datetime.strptime(event["date"], "%Y-%m-%d")
    formatted = d.strftime("%A, %B %d, %Y")
    parts = [
        f"Urology Department — Grand Rounds",
        f"",
        f"Date: {formatted}",
        f"Time: 7:00 - 9:00 AM (ET)",
        f"",
        f"Agenda:",
        f"  7:00 - 8:00 AM | {t7}",
        f"  8:00 - 9:00 AM | {t8}",
        f"",
        f"Meeting Type: {mt}",
        f"",
        f"Zoom Meeting:",
        f"  Join: {zoom}",
        f"  Meeting ID: {mid}",
        f"  Passcode: {pwd}",
        f"",
        f"---",
        f"Montefiore Medical Center · Department of Urology",
    ]
    return "\n".join(parts)


# ══════════════════════════════════════════════════════════════
#  MICROSOFT GRAPH API CLIENT
# ══════════════════════════════════════════════════════════════

class MsGraphClient:
    """
    Microsoft Graph API client using device code flow for auth.
    Creates calendar events and sends invites programmatically.
    
    After one-time auth, the refresh token is saved to GRAPH_TOKEN_FILE
    and reused automatically.
    """
    
    def __init__(self):
        self.token = None
        self._load_token()
    
    def _load_token(self):
        """Load saved token from disk."""
        if GRAPH_TOKEN_FILE.exists():
            try:
                self.token = json.load(open(GRAPH_TOKEN_FILE))
            except Exception:
                self.token = None
    
    def _save_token(self, token):
        """Save token to disk for reuse."""
        self.token = token
        GRAPH_TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        json.dump(token, open(GRAPH_TOKEN_FILE, "w"), indent=2)
        print(f"  💾 Token saved to {GRAPH_TOKEN_FILE}")
    
    def authenticate(self, force=False):
        """Run device code flow to get a token.
        
        If force=False and a saved token exists, just returns it.
        If force=True, always re-authenticates.
        """
        if not force and self.token:
            # Check if token is still valid
            if self.token.get("expires_at", 0) > time.time() + 60:
                print("  ✅ Using saved token (valid)")
                return True
            # Try refreshing
            if self._refresh_token():
                return True
        
        try:
            from msal import PublicClientApplication
            
            app = PublicClientApplication(
                GRAPH_CLIENT_ID,
                authority=GRAPH_AUTHORITY,
            )
            
            # Request device code
            flow = app.initiate_device_flow(scopes=GRAPH_SCOPES)
            if "user_code" not in flow:
                print(f"❌ Device flow failed: {flow.get('error', 'unknown')}")
                return False
            
            print(f"\n🔐 Microsoft Graph Authentication")
            print(f"{'='*60}")
            print(f"  1. Open: {flow['verification_uri']}")
            print(f"  2. Enter code: {flow['user_code']}")
            print(f"{'='*60}")
            print(f"\nThis will log you into your Montefiore Office 365 account.")
            print(f"The code expires in {flow.get('expires_in', 900)//60} minutes.\n")
            
            # Poll for token
            result = app.acquire_token_by_device_flow(flow)
            
            if "access_token" in result:
                # Add expiry timestamp
                result["expires_at"] = time.time() + result.get("expires_in", 3600)
                self._save_token(result)
                print("  ✅ Authenticated successfully!")
                return True
            else:
                print(f"❌ Authentication failed: {result.get('error_description', result.get('error', 'unknown'))}")
                return False
                
        except ImportError:
            print("❌ msal library not installed. Run: pip install msal")
            return False
    
    def _refresh_token(self):
        """Try to refresh the saved token."""
        if not self.token or "refresh_token" not in self.token:
            return False
        
        try:
            from msal import PublicClientApplication
            
            app = PublicClientApplication(
                GRAPH_CLIENT_ID,
                authority=GRAPH_AUTHORITY,
            )
            
            result = app.acquire_token_by_refresh_token(
                self.token["refresh_token"],
                scopes=GRAPH_SCOPES,
            )
            
            if "access_token" in result:
                result["expires_at"] = time.time() + result.get("expires_in", 3600)
                self._save_token(result)
                return True
            
            # If refresh fails, clear token so authenticate() starts fresh
            self.token = None
            if GRAPH_TOKEN_FILE.exists():
                GRAPH_TOKEN_FILE.unlink()
            return False
            
        except ImportError:
            return False
    
    def _get_access_token(self):
        """Get a valid access token, refreshing if needed."""
        if not self.token:
            return None
        
        if self.token.get("expires_at", 0) > time.time() + 60:
            return self.token.get("access_token")
        
        # Try refresh
        if self._refresh_token():
            return self.token.get("access_token")
        
        return None
    
    def send_event(self, event, recipients, subject, body, start_time, end_time, is_test=False, test_email=""):
        """Create a calendar event via Microsoft Graph and send as invite.
        
        Args:
            event: Event dict with date, topic, etc.
            recipients: List of recipient email addresses
            subject: Email/event subject
            body: Email body text
            start_time: "HH:MM" format
            end_time: "HH:MM" format
            is_test: If True, only sends to test_email
            test_email: Test recipient email
            
        Returns:
            True if successful
        """
        token = self._get_access_token()
        if not token:
            print("  ❌ No valid token. Run --mode graph-auth first.")
            return False
        
        import urllib.request
        import base64
        
        date_str = event["date"]
        attending_emails = []
        
        if is_test:
            attending_emails = [{"emailAddress": {"address": test_email}}]
        else:
            attending_emails = [{"emailAddress": {"address": e}} for e in recipients]
        
        dt_start = datetime.strptime(f"{date_str} {start_time}", "%Y-%m-%d %H:%M")
        dt_end = datetime.strptime(f"{date_str} {end_time}", "%Y-%m-%d %H:%M")
        
        # Build event payload
        event_payload = {
            "subject": subject,
            "body": {
                "contentType": "text",
                "content": body,
            },
            "start": {
                "dateTime": dt_start.strftime("%Y-%m-%dT%H:%M:00"),
                "timeZone": "America/New_York",
            },
            "end": {
                "dateTime": dt_end.strftime("%Y-%m-%dT%H:%M:00"),
                "timeZone": "America/New_York",
            },
            "location": {
                "displayName": "Zoom",
            },
            "attendees": attending_emails,
            "isOnlineMeeting": True,
            "onlineMeetingProvider": "unknown",
            "showAs": "busy",
        }
        
        # Send via Graph API
        api_url = "https://graph.microsoft.com/v1.0/me/calendar/events"
        
        req = urllib.request.Request(
            api_url,
            data=json.dumps(event_payload).encode(),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Prefer": 'outlook.timezone="America/New_York"',
            },
            method="POST",
        )
        
        try:
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read())
                event_id = result.get("id", "unknown")
                web_link = result.get("webLink", "")
                print(f"  ✅ Created event: {result.get('subject', '')}")
                if web_link:
                    print(f"     📎 {web_link}")
                return True
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            print(f"  ❌ Graph API error ({e.code}): {error_body[:300]}")
            return False
        except Exception as e:
            print(f"  ❌ Request failed: {e}")
            return False


# ══════════════════════════════════════════════════════════════
#  OUTLOOK DEEP LINK BUILDERS
# ══════════════════════════════════════════════════════════════

def build_monday_deeplink(event, recipients, test_mode=False, test_email=""):
    import urllib.parse
    to_param = test_email if test_mode else ",".join(recipients)
    subject = build_monday_subject(event)
    body = build_monday_body(event)
    params = urllib.parse.urlencode({
        "subject": subject, "body": body, "to": to_param,
        "startdt": f"{event['date']}T07:00:00", "enddt": f"{event['date']}T08:00:00",
        "location": "Zoom",
    }, quote_via=urllib.parse.quote)
    return f"https://outlook.office.com/calendar/deeplink/compose?{params}"


def build_grand_rounds_deeplink(event, recipients, test_mode=False, test_email=""):
    import urllib.parse
    to_param = test_email if test_mode else ",".join(recipients)
    subject = build_grand_rounds_subject(event)
    body = build_grand_rounds_body(event)
    params = urllib.parse.urlencode({
        "subject": subject, "body": body, "to": to_param,
        "startdt": f"{event['date']}T07:00:00", "enddt": f"{event['date']}T09:00:00",
        "location": "Zoom",
    }, quote_via=urllib.parse.quote)
    return f"https://outlook.office.com/calendar/deeplink/compose?{params}"


# ══════════════════════════════════════════════════════════════
#  MODE: DEEP LINK CSV GENERATION
# ══════════════════════════════════════════════════════════════

def generate_deeplinks_csv(event_type="all"):
    DEEPLINK_DIR.mkdir(parents=True, exist_ok=True)
    created = []
    
    if event_type in ("all", "monday"):
        events = get_monday_events()
        recipients = get_recipients_for_monday()
        rows = []
        for ev in events:
            url = build_monday_deeplink(ev, recipients)
            rows.append({
                "date": ev["date"], "type": "Monday SASP",
                "topic": ev["topic"], "resident": ev["resident"],
                "attending": ev["attending"], "outlook_url": url,
            })
        filepath = DEEPLINK_DIR / "monday_sasp_deeplinks.csv"
        with open(filepath, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["date", "type", "topic", "resident", "attending", "outlook_url"])
            w.writeheader()
            w.writerows(rows)
        created.append((str(filepath), len(rows)))
    
    if event_type in ("all", "grand-rounds"):
        events = get_grand_rounds_events()
        rows = []
        for ev in events:
            recipients = get_recipients_for_grand_rounds(ev["meeting_type"])
            url = build_grand_rounds_deeplink(ev, recipients)
            rows.append({
                "date": ev["date"], "type": ev["meeting_type"],
                "topic_7_8": ev["topic_7_8"], "topic_8_9": ev["topic_8_9"],
                "recipient_group": "faculty" if "Faculty" in ev["meeting_type"] else "grand_rounds",
                "outlook_url": url,
            })
        filepath = DEEPLINK_DIR / "grand_rounds_deeplinks.csv"
        with open(filepath, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["date", "type", "topic_7_8", "topic_8_9", "recipient_group", "outlook_url"])
            w.writeheader()
            w.writerows(rows)
        created.append((str(filepath), len(rows)))
    
    for path, count in created:
        print(f"  ✅ Generated {count} deeplinks → {path}")
    print(f"\nTotal: {sum(c for _, c in created)} deeplinks generated.")
    print("Open these URLs in a browser logged into Outlook Web — each opens a pre-filled compose form.")


# ══════════════════════════════════════════════════════════════
#  MODE: GRAPH API BATCH SEND
# ══════════════════════════════════════════════════════════════

def run_graph_batch(events, subject_fn, body_fn, recipients_fn, event_type,
                    is_test=True, test_email="sfrasier@montefiore.org",
                    start_date=None, limit=5):
    """Send invites via Microsoft Graph API."""
    
    progress = load_progress(event_type)
    sent_dates = set(progress.get("sent_dates", []))
    
    unsent = [e for e in events if e["date"] not in sent_dates]
    if start_date:
        unsent = [e for e in unsent if e["date"] >= start_date]
    
    if not unsent:
        print(f"✅ All {event_type} invites already sent!")
        return
    
    batch = unsent[:limit]
    recipients = recipients_fn()
    
    print(f"\n{'='*60}")
    print(f"📅 Sending up to {len(batch)} {event_type.upper()} invites via Graph API")
    print(f"   Test mode: {'ON (only to ' + test_email + ')' if is_test else 'OFF (to ' + str(len(recipients)) + ' recipients)'}")
    print(f"   Unsent remaining: {len(unsent)}")
    print(f"{'='*60}\n")
    
    client = MsGraphClient()
    if not client.authenticate():
        print("❌ Authentication failed. Run --mode graph-auth first.")
        return
    
    start_t, end_t = ("07:00", "08:00") if event_type == "monday" else ("07:00", "09:00")
    
    sent_count = 0
    for ev in batch:
        print(f"\n  ── {event_type.upper()} — {ev['date']} ──")
        subject = subject_fn(ev)
        body = body_fn(ev)
        
        ok = client.send_event(ev, recipients, subject, body, start_t, end_t, is_test, test_email)
        
        if ok:
            progress.setdefault("sent_dates", []).append(ev["date"])
            sent_count += 1
            save_progress(event_type, progress)
        else:
            print(f"  ⛔ Stopping due to failure")
            break
        
        if sent_count < len(batch):
            delay = 3
            print(f"  ⏳ Waiting {delay}s...")
            time.sleep(delay)
    
    progress["last_run"] = datetime.now().isoformat()
    save_progress(event_type, progress)
    total_sent = len(progress.get("sent_dates", []))
    total = len(events)
    print(f"\n{'='*60}")
    print(f"📊 Summary: Sent {sent_count} today, {total_sent}/{total} total")
    print(f"{'='*60}")


# ══════════════════════════════════════════════════════════════
#  MODE: REPORT
# ══════════════════════════════════════════════════════════════

def show_report(event_type="all"):
    if event_type in ("all", "monday"):
        events = get_monday_events()
        progress = load_progress("monday")
        sent = set(progress.get("sent_dates", []))
        unsent = [e for e in events if e["date"] not in sent]
        print(f"\n📋 Monday SASP ({len(events)} total)")
        print(f"   ✅ Sent: {len(sent)}")
        print(f"   ⏳ Unsent: {len(unsent)}")
        if unsent:
            print(f"   Next: {unsent[0]['date']} - {unsent[0]['topic']}")
    
    if event_type in ("all", "grand-rounds"):
        events = get_grand_rounds_events()
        progress = load_progress("grand-rounds")
        sent = set(progress.get("sent_dates", []))
        unsent = [e for e in events if e["date"] not in sent]
        print(f"\n📋 Grand Rounds ({len(events)} total)")
        print(f"   ✅ Sent: {len(sent)}")
        print(f"   ⏳ Unsent: {len(unsent)}")
        if unsent:
            print(f"   Next: {unsent[0]['date']} - {unsent[0]['meeting_type']}")


def reset_progress(event_type):
    if event_type in ("monday", "all"):
        file = MONDAY_PROGRESS
        if file.exists():
            file.unlink()
            print(f"  🗑  Reset Monday SASP progress")
    if event_type in ("grand-rounds", "all"):
        file = GR_PROGRESS
        if file.exists():
            file.unlink()
            print(f"  🗑  Reset Grand Rounds progress")
    if GRAPH_TOKEN_FILE.exists():
        GRAPH_TOKEN_FILE.unlink()
        print(f"  🗑  Removed Graph API token")


# ══════════════════════════════════════════════════════════════
#  MAIN CLI
# ══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Outlook Calendar Bulk Invite Sender",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Graph API — authenticate once (device code flow)
  python3 outlook_ics_bulk_sender.py --mode graph-auth

  # Graph API — batch send invites
  python3 outlook_ics_bulk_sender.py --mode graph --type monday --limit 5

  # Generate deeplink CSV (no setup needed)
  python3 outlook_ics_bulk_sender.py --mode deeplinks --type all

  # Test — print a single deeplink to preview
  python3 outlook_ics_bulk_sender.py --mode test --date 2026-07-10 --type grand-rounds

  # Check progress
  python3 outlook_ics_bulk_sender.py --mode report
        """
    )
    
    parser.add_argument("--mode", choices=["graph", "graph-auth", "batch", "test", "deeplinks", "report", "reset"],
                        default="report", help="Operating mode")
    parser.add_argument("--type", choices=["monday", "grand-rounds", "all"],
                        default="all", help="Event type to process")
    parser.add_argument("--date", type=str, default="",
                        help="Specific date for test mode (YYYY-MM-DD)")
    parser.add_argument("--start-date", type=str, default="",
                        help="Start from this date (YYYY-MM-DD)")
    parser.add_argument("--limit", type=int, default=5,
                        help="Max invites to send per run (default: 5)")
    parser.add_argument("--email", type=str, default="",
                        help="Email for browser login")
    parser.add_argument("--password", type=str, default="",
                        help="Password for browser login")
    parser.add_argument("--test-mode", action="store_true", default=True,
                        help="Send only to test email")
    parser.add_argument("--no-test", action="store_true",
                        help="Send to real recipients")
    parser.add_argument("--test-email", type=str, default="sfrasier@montefiore.org",
                        help="Test email address (default: sfrasier@montefiore.org)")
    
    args = parser.parse_args()
    test_mode = not args.no_test
    
    # ── Report ──
    if args.mode == "report":
        show_report(args.type)
        return
    
    # ── Reset ──
    if args.mode == "reset":
        reset_progress(args.type)
        return
    
    # ── Deeplinks ──
    if args.mode == "deeplinks":
        generate_deeplinks_csv(args.type)
        return
    
    # ── Graph Auth ──
    if args.mode == "graph-auth":
        client = MsGraphClient()
        client.authenticate(force=True)
        return
    
    # ── Graph API Batch ──
    if args.mode == "graph":
        if args.type in ("all", "monday"):
            events = get_monday_events()
            run_graph_batch(
                events, build_monday_subject, build_monday_body,
                get_recipients_for_monday, "monday",
                test_mode, args.test_email, args.start_date, args.limit,
            )
        if args.type in ("all", "grand-rounds"):
            events = get_grand_rounds_events()
            run_graph_batch(
                events, build_grand_rounds_subject, build_grand_rounds_body,
                get_recipients_for_grand_rounds, "grand-rounds",
                test_mode, args.test_email, args.start_date, args.limit,
            )
        return
    
    # ── Test (single date deeplink preview) ──
    if args.mode == "test" and args.date:
        test_mode = True
        if args.type in ("all", "monday"):
            events = [e for e in get_monday_events() if e["date"] == args.date]
            if events:
                print(f"\n🧪 TEST: Monday SASP invite for {args.date}")
                recipients = get_recipients_for_monday()
                deeplink = build_monday_deeplink(events[0], recipients, True, args.test_email)
                print(f"\n📧 Outlook Deep Link:\n   {deeplink}")
                print(f"\n📋 Open in a browser logged into Outlook Web — just click Send.\n")
                return
        if args.type in ("all", "grand-rounds"):
            events = [e for e in get_grand_rounds_events() if e["date"] == args.date]
            if events:
                print(f"\n🧪 TEST: Grand Rounds invite for {args.date}")
                recipients = get_recipients_for_grand_rounds(events[0]["meeting_type"])
                deeplink = build_grand_rounds_deeplink(events[0], recipients, True, args.test_email)
                print(f"\n📧 Outlook Deep Link:\n   {deeplink}")
                print(f"\n📋 Open in a browser logged into Outlook Web — just click Send.\n")
                return
        print(f"❌ No event found for {args.date}")
        return


if __name__ == "__main__":
    main()
