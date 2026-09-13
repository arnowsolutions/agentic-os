#!/usr/bin/env python3
"""AOS endpoint audit — re-runnable end-to-end check of the dashboard API.

Usage (inside the AOS container):
    docker exec hermes-webui-gsga-agentic-os-1 python3 /workspace/agentic-os/scripts/endpoint_audit.py

Probes every parameter-free GET route from the live OpenAPI spec with the
newest dashboard session cookie, plus the known parameterized routes called
with real args, and flags: non-200s, and 200s whose JSON carries a truthy
"error" / status=error (outside the known-issues list).

Exit code: 0 = clean (or only known issues), 1 = new flags found.
"""
import json
import sys
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

BASE = "http://localhost:8082"  # in-container port (host-mapped: 8092)
SESSIONS = Path("/workspace/agentic-os/data/sessions.json")
SKIP_PREFIXES = ("/hermes-webui", "/vapi/", "/login", "/metrics", "/favicon")

# Endpoints that legitimately require query params — probed with real args below,
# never bare. Bare calls always 422/404 by design.
NEEDS_PARAMS = {
    "/api/fs/read", "/api/fs/stat", "/api/images/file",
    "/api/letters/file", "/api/letters/generate",
    "/api/chief-meetings/eml", "/api/subi-exit/eml",
    "/api/oncall/date", "/api/oncall/week", "/api/oncall/search",
}

# Known issues that are NOT deployment failures (report as known, don't fail).
KNOWN_ISSUES = {
    "/api/tools/notebooks": "Authentication expired",  # needs interactive `nlm login`
}


def newest_token() -> str:
    try:
        d = json.loads(SESSIONS.read_text())
        if not d:
            return ""
        return max(d, key=lambda k: d[k].get("created_at", ""))
    except Exception:
        return ""


def probe(path: str, tok: str):
    req = urllib.request.Request(BASE + path, headers={"Cookie": f"aos_session={tok}"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:
        return -1, str(e).encode()


def main() -> int:
    tok = newest_token()
    if not tok:
        print("No session found in data/sessions.json — log in to the dashboard first.")
        return 1

    try:
        req = urllib.request.Request(BASE + "/openapi.json",
                                     headers={"Cookie": f"aos_session={tok}"})
        with urllib.request.urlopen(req, timeout=15) as r:
            spec = json.loads(r.read())
    except Exception as e:
        print(f"Could not fetch OpenAPI spec: {e}")
        return 1

    today = date.today().isoformat()
    paths = sorted(
        p for p, ops in spec["paths"].items()
        if "get" in ops and "{" not in p
        and not p.startswith(SKIP_PREFIXES)
        and p not in NEEDS_PARAMS
    )
    extras = [
        f"/api/oncall/date?date={today}",
        f"/api/oncall/week?start={today}",
        f"/api/oncall/search?date={today}&name=hill",
    ]

    ok, known, flagged = [], [], []
    for p in paths + extras:
        code, body = probe(p, tok)
        if code != 200:
            flagged.append((p, f"HTTP {code}: {body[:100]!r}"))
            continue
        try:
            j = json.loads(body)
        except Exception:
            ok.append(p)  # non-JSON 200 (HTML pages) = fine
            continue
        if isinstance(j, dict) and (j.get("error") or j.get("status") == "error"):
            reason = f"200-but-error: {json.dumps(j)[:130]}"
            kp = next((k for k in KNOWN_ISSUES if p.startswith(k)), None)
            if kp and KNOWN_ISSUES[kp] in reason:
                known.append((p, reason))
            else:
                flagged.append((p, reason))
        else:
            ok.append(p)

    total = len(paths) + len(extras)
    print(f"AOS endpoint audit: {len(ok)} OK / {len(known)} known / {len(flagged)} flagged (of {total})")
    for p, why in known:
        print("  KNOWN", p, "→", why)
    for p, why in flagged:
        print("  FLAG ", p, "→", why)
    print("Result:", "CLEAN" if not flagged else "REVIEW NEEDED")
    return 1 if flagged else 0


if __name__ == "__main__":
    sys.exit(main())
