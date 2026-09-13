#!/usr/bin/env python3
"""Final verification of all fixed endpoints + the dead-route findings."""
import json, urllib.request, urllib.error

d = json.load(open("/workspace/agentic-os/data/sessions.json"))
items = list(d.items()) if isinstance(d, dict) else [(x.get("token"), x) for x in d]
TOK = sorted(((v.get("created_at", ""), k) for k, v in items if isinstance(v, dict)), reverse=True)[0][1]
H = {"Cookie": f"aos_session={TOK}"}


def call(path, method="GET", body=None):
    req = urllib.request.Request("http://localhost:8082" + path, headers=H, method=method,
                                 data=json.dumps(body).encode() if body else None)
    if body:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:200]
    except Exception as e:
        return 0, f"{type(e).__name__}: {e}"


print("── fixed endpoints ──")
st, b = call("/api/health/full")
j = json.loads(b)
for k, v in j["services"].items():
    print(f"  health/full.{k:14} ok={v.get('ok')} status={v.get('status')} err={v.get('error', '')[:40]}")

st, b = call("/api/telegram/status")
j = json.loads(b)
print(f"  telegram/status: connected={j['connected']} detail={j['detail'][:60]} recent={len(j['recent_messages'])}")

st, b = call("/api/tools/telegram")
j = json.loads(b)
print(f"  tools/telegram: sessions={len(j.get('sessions', []))} total={j.get('total')} error={j.get('error')}")

st, b = call("/api/tools/notebooks")
j = json.loads(b)
print(f"  tools/notebooks: notebooks={len(j.get('notebooks') or [])} source={j.get('source')} err={str(j.get('error'))[:70]}")

st, b = call("/api/chief-meetings/generate-eml")
j = json.loads(b)
print(f"  chief-meetings/generate-eml: success={j.get('success')} msg={str(j.get('message'))[:70]}")

st, b = call("/api/crm/launchpad?refresh=1")
j = json.loads(b)
down = [(s.get("label"), (s.get("status") or {}).get("state"), (s.get("status") or {}).get("detail", "")[:40])
        for s in j.get("services", []) if (s.get("status") or {}).get("state") != "up"]
print(f"  launchpad: {len(j.get('services', []))} tiles, not-up={down}")

print("\n── regression: sub-I + mass-email pages ──")
st, b = call("/api/subi-exit-interviews")
print(f"  subi-exit-interviews: count={json.loads(b).get('count')}")
st, b = call("/api/subi-exit-invites?test=false")
print(f"  subi-exit-invites: http={st} bytes={len(b)} rows_marker={'11 interviews' in b}")
st, b = call("/api/conference/schedule")
print(f"  conference/schedule: rows={json.loads(b).get('count')}")
st, b = call("/api/staff-schedule")
print(f"  staff-schedule: staff={len(json.loads(b).get('staff', []))} source={json.loads(b).get('source')}")

print("\n── dead-route findings (page calls these; do they exist?) ──")
for p, m in [("/api/letters/generate", "GET"), ("/api/letters/generate", "POST"), ("/api/admin/audit-log?limit=10", "GET")]:
    st, b = call(p, m)
    print(f"  {m:5} {p:34} -> {st} {b[:60]!r}")
