#!/usr/bin/env python3
"""Verify the new DB-backed endpoints after the chief/audit/NLM changes."""
import json, urllib.request, urllib.error

d = json.load(open("/workspace/agentic-os/data/sessions.json"))
items = list(d.items()) if isinstance(d, dict) else [(x.get("token"), x) for x in d]
TOK = sorted(((v.get("created_at", ""), k) for k, v in items if isinstance(v, dict)), reverse=True)[0][1]
H = {"Cookie": f"aos_session={TOK}"}


def get(path):
    req = urllib.request.Request("http://localhost:8082" + path, headers=H)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read().decode())
    except Exception as e:
        return 0, {"error": str(e)}


st, j = get("/api/chief-meetings")
print(f"chief-meetings: http={st} meetings={len(j.get('meetings', []))} attendees={len(j.get('attendees', []))} err={j.get('error')}")
print("   dates:", [m["date"] for m in j.get("meetings", [])])
print("   attendees:", [a.get("display") for a in j.get("attendees", [])])

st, j = get("/api/admin/audit-log?limit=5")
if isinstance(j, list):
    print(f"admin/audit-log: http={st} rows={len(j)}")
    for r in j[:4]:
        print(f"   {r['created_at'][:16]} | {r['actor_name']} | {r['action']} | {r['entity_type']} | person={r['person_name']!r}")
else:
    print("admin/audit-log:", st, j)

st, j = get("/api/tools/notebooklm/profiles")
print(f"notebooklm/profiles: http={st} count={j.get('count')} storage={j.get('storage')}")
for p in j.get("profiles", []):
    print(f"   {p['name']:20} persistent_profile={p['persistent_profile']}")

st, j = get("/api/tools/notebooks?profile=podcast")
print(f"tools/notebooks(podcast): notebooks={len(j.get('notebooks') or [])} source={j.get('source')}")

print("\n-- regression: earlier fixes --")
st, j = get("/api/subi-exit-interviews")
print("subi count:", j.get("count"))
st, j = get("/api/health/full")
print("health services:", {k: v.get("ok") for k, v in j.get("services", {}).items()})
st, j = get("/api/telegram/status")
print("telegram:", j.get("connected"), "| recent:", len(j.get("recent_messages", [])))
