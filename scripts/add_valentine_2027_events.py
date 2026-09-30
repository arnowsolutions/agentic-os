
import json, os, datetime
from pathlib import Path

P = Path('/workspace/agentic-os/data/calendar_events.json')
data = json.loads(P.read_text())
TZ = "America/New_York"

new = [
    ("Valentine Essays Due!",
     "Valentine Essays Due! Rules of Engagement for the essay will be sent out in the weeks before this date.",
     "2027-01-08"),
    ("The Michael J. Droller Chief Residents' Debate Meeting",
     "The Michael J. Droller Chief Residents' Debate Meeting.",
     "2027-03-11"),
    ("Ferdinand C. Valentine Medal & Resident Essay Meeting",
     "Ferdinand C. Valentine Medal & Resident Essay Meeting.",
     "2027-04-20"),
]

manual = data.setdefault("manual_events", [])
events = data.setdefault("events", [])
added = []
for summary, desc, day in new:
    d = datetime.date.fromisoformat(day)
    ev = {"summary": summary, "description": desc,
          "start": {"date": d.isoformat(), "timeZone": TZ},
          "end": {"date": (d + datetime.timedelta(days=1)).isoformat(), "timeZone": TZ},
          "source": "manual"}
    if any(m.get("summary") == summary and m.get("start", {}).get("date") == day for m in manual):
        print("already present:", summary); continue
    manual.append(ev); events.append(ev); added.append(ev)

events.sort(key=lambda x: x.get("start", {}).get("date") or x.get("start", {}).get("dateTime", ""))

tmp = P.with_name(P.name + ".tmp-write")
tmp.write_text(json.dumps(data, indent=2))
os.chmod(tmp, 0o644)
os.replace(tmp, P)          # atomic swap; dir is writable, target file is root-owned
print("added:", [e["summary"] for e in added])
print("manual_events:", len(manual), "| events:", len(events), "| archived:", len(data.get("archived_events", [])))
