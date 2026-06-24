#!/usr/bin/env python3
"""Parse Grand Rounds data from dashboard JS and create Google Calendar events + cron."""
import re, json, subprocess, os, sys

# ── Read the Grand Rounds data more robustly ──────────────
def parse_gr_data():
    """Parse GR_DATA from JS file, handling trailing commas JS-style."""
    with open("/workspace/agentic-os/dashboard/pages/grand-rounds.js") as f:
        js = f.read()
    
    # Extract the array content between [ and ]; (handle nested brackets)
    start = js.find("const GR_DATA = ")
    if start < 0:
        print("ERROR: GR_DATA not found")
        sys.exit(1)
    start = js.index("[", start)
    # Find the matching closing bracket
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
    # Convert JS array to JSON: wrap strings, remove trailing commas
    # First handle the easy case - it's mostly string arrays
    # Replace JS-style strings (double quotes work in both)
    # Remove trailing commas before ] or }
    import re as regex
    array_str = regex.sub(r",\s*]", "]", array_str)  # trailing comma in outer array
    array_str = regex.sub(r",\s*\]", "]", array_str)  # in nested arrays too
    # Remove comments (// style)
    array_str = regex.sub(r"//.*", "", array_str)
    
    return json.loads(array_str)

gr_data = parse_gr_data()
print(f"Found {len(gr_data)} Grand Rounds entries")

# ── Parse into events ─────────────────────────────────────
events = []
for row in gr_data:
    fri_date = row[7] if len(row) > 7 and row[7] else ""
    gr_7_8 = row[8] if len(row) > 8 else ""
    gr_8_9 = row[9] if len(row) > 9 else ""
    notes = row[10] if len(row) > 10 else ""

    if not fri_date or not fri_date.startswith("20"):
        continue  # skip invalid dates

    # Skip cancelled Grand Rounds
    if "NO GRAND ROUNDS" in gr_7_8 or "NO GRAND ROUNDS" in gr_8_9:
        print(f"  SKIP {fri_date}: No Grand Rounds")
        continue

    # Determine meeting types
    is_peds = "Peds" in gr_7_8 or "Peds Multidisciplinary" in gr_8_9
    is_faculty = "FACULTY MEETING" in gr_7_8 or "FACULTY MEETING" in gr_8_9
    is_journal = "Journal Club" in gr_7_8 or "Journal Club" in gr_8_9

    topic_7_8 = gr_7_8.strip() if gr_7_8 else "Grand Rounds"
    topic_8_9 = gr_8_9.strip() if gr_8_9 else ""

    events.append({
        "date": fri_date,
        "topic_7_8": topic_7_8,
        "topic_8_9": topic_8_9,
        "is_peds": is_peds,
        "is_faculty": is_faculty,
        "is_journal": is_journal,
        "notes": notes,
    })

print(f"\nParsed {len(events)} Grand Rounds events to create")
for e in events[:5]:
    print(f"  {e['date']}: {e['topic_7_8'][:40]} | {e['topic_8_9'][:40]}")

# ── Create Google Calendar events ─────────────────────────
GAPI = "/home/hermeswebui/.hermes/skills/productivity/google-workspace/scripts/google_api.py"
token_path = "/home/hermeswebui/.hermes/google_token.json"

if not os.path.exists(token_path):
    print(f"\n⚠ No Google token at {token_path}")
    print("  Run Google OAuth setup first, or create events manually.")
    sys.exit(1)

if not os.path.exists(GAPI):
    print(f"\n⚠ Google API script not found at {GAPI}")
    sys.exit(1)

print("\nCreating Google Calendar events...")
created = 0
errors = 0

for event in events:
    date = event["date"]
    topic_7_8 = event["topic_7_8"]
    topic_8_9 = event["topic_8_9"]

    # Determine summary
    if topic_7_8 and topic_8_9 and topic_7_8 != topic_8_9:
        summary = f"Grand Rounds: {topic_7_8} / {topic_8_9}"
    else:
        summary = f"Grand Rounds: {topic_7_8 or topic_8_9}"

    prefix = "🎓 "
    if event["is_peds"]:
        prefix = "👶 "
    elif event["is_faculty"]:
        prefix = "🏛 "
    elif event["is_journal"]:
        prefix = "📚 "

    summary = prefix + summary

    desc_parts = [f"Grand Rounds - Montefiore Urology"]
    if event["is_peds"]:
        desc_parts.append("Type: Peds Multidisciplinary")
    if event["is_faculty"]:
        desc_parts.append("Type: Faculty Meeting")
    desc_parts.append(f"7-8 AM: {topic_7_8}")
    if topic_8_9 and topic_8_9 != topic_7_8:
        desc_parts.append(f"8-9 AM: {topic_8_9}")
    if event["notes"]:
        desc_parts.append(f"Notes: {event['notes']}")
    description = "\n".join(desc_parts)

    # Create 7-8 AM event
    start = f"{date}T07:00:00-04:00"
    end = f"{date}T09:00:00-04:00"

    # Build calendar command
    cmd = [
        "python3", GAPI,
        "calendar", "create",
        "--summary", summary[:100],
        "--start", start,
        "--end", end,
        "--description", description[:500],
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            print(f"  ✅ {date}: {summary[:50]}... → {data.get('htmlLink','?')[:50]}")
            created += 1
        else:
            print(f"  ❌ {date}: {result.stderr[:100]}")
            errors += 1
    except Exception as e:
        print(f"  ❌ {date}: {str(e)[:100]}")
        errors += 1

print(f"\n{'='*50}")
print(f"Created: {created} events")
print(f"Errors: {errors}")
print(f"{'='*50}")
print(f"\nNext step: Set up weekly reminder cron job.")
print(f"  (Run: cronjob create name='Grand Rounds Reminder' schedule='0 8 * * 4' prompt='...')")
