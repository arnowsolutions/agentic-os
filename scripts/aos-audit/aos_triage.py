#!/usr/bin/env python3
"""Precise triage: which flagged payloads carry a REAL error (truthy), not error:null clutter."""
import json, urllib.request

TOK = ""
d = json.load(open("/workspace/agentic-os/data/sessions.json"))
items = list(d.items()) if isinstance(d, dict) else [(x.get("token"), x) for x in d]
rows = sorted(((v.get("created_at", ""), k) for k, v in items if isinstance(v, dict)), reverse=True)
TOK = rows[0][1]

FLAGGED = [
    "/api/selftest", "/api/staff-schedule", "/api/vapi/data-health", "/api/crm/launchpad",
    "/api/health/full", "/api/telegram/status", "/api/tools/notebooks", "/api/tools/telegram",
    "/api/chief-meetings/generate-eml", "/api/journal/search", "/api/user/1",
    "/api/qgenda/users", "/api/letters/generate",
]


def get(p):
    req = urllib.request.Request("http://localhost:8082" + p, headers={"Cookie": f"aos_session={TOK}"})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:
        return 0, str(e)


def truthy_errors(obj, path="$", out=None, depth=0):
    out = [] if out is None else out
    if depth > 4:
        return out
    if isinstance(obj, dict):
        for k, v in obj.items():
            kl = str(k).lower()
            if kl in ("error", "err", "exception") and v not in (None, "", False, [], {}):
                out.append(f"{path}.{k}={str(v)[:110]}")
            elif kl in ("status", "state", "result") and str(v).lower() in ("error", "failed", "down", "fail"):
                out.append(f"{path}.{k}={v}")
            else:
                truthy_errors(v, f"{path}.{k}", out, depth + 1)
    elif isinstance(obj, list):
        for i, v in enumerate(obj[:25]):
            truthy_errors(v, f"{path}[{i}]", out, depth + 1)
    return out


for p in FLAGGED:
    st, body = get(p)
    print(f"\n### {p}  (HTTP {st}, {len(body)}b)")
    try:
        j = json.loads(body)
    except Exception:
        print("   non-JSON:", body[:200].replace("\n", " "))
        continue
    print("   top-level keys:", list(j.keys())[:12] if isinstance(j, dict) else f"list[{len(j)}]")
    errs = truthy_errors(j)
    if errs:
        for e in errs[:8]:
            print("   ⚠", e)
    else:
        print("   ✓ no truthy error/status fields")
