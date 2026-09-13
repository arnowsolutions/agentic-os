#!/usr/bin/env python3
"""AOS inner-page audit: probe every GET endpoint, flag silent failures.

Run INSIDE the AOS container:
  docker exec -w /workspace/agentic-os hermes-webui-gsga-agentic-os-1 python3 /workspace/aos_page_audit.py
Uses the in-container port (8082) and the newest dashboard session cookie.
"""
import json
import re
import urllib.request
import urllib.error
from pathlib import Path

BASE = "http://localhost:8082"
SESS = Path("/workspace/agentic-os/data/sessions.json")


def token():
    d = json.loads(SESS.read_text())
    items = list(d.items()) if isinstance(d, dict) else [(x.get("token"), x) for x in d]
    rows = [(v.get("created_at", ""), k) for k, v in items if isinstance(v, dict)]
    rows.sort(reverse=True)
    return rows[0][1] if rows else ""


TOK = token()


def get(path, timeout=45):
    req = urllib.request.Request(BASE + path, headers={"Cookie": f"aos_session={TOK}"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read().decode("utf-8", "replace")
            return r.status, body
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:400]
    except Exception as e:
        return 0, f"{type(e).__name__}: {e}"


def verdict(status, body):
    """Classify a payload the playbook way: 200 + error key == failure."""
    notes = []
    if status == 0:
        return "TRANSPORT-FAIL", notes
    snippet = body[:600]
    if re.search(r'"(error|detail)"\s*:', snippet) and status != 422:
        m = re.search(r'"(?:error|detail)"\s*:\s*"?([^",}]{0,120})', snippet)
        return "ERROR-IN-BODY", [m.group(1) if m else "error key present"]
    if status == 500:
        return "HTTP-500", [snippet[:200]]
    if status == 422:
        m = re.search(r"(\w+)\.(\w+)?\s*\n?\s*Field required", snippet)
        return "NEEDS-PARAM", []
    if status == 401:
        return "UNAUTH", []
    if status == 404:
        return "HTTP-404", []
    if status != 200:
        return f"HTTP-{status}", [snippet[:150]]
    # empty-data heuristics
    try:
        j = json.loads(body)
    except Exception:
        return "OK(html/text)", [f"{len(body)}b"]
    if isinstance(j, dict):
        for k in ("rows", "items", "results", "data", "entries", "messages", "jobs"):
            v = j.get(k)
            if isinstance(v, list):
                return ("OK-EMPTY" if not v else "OK"), [f"{k}={len(v)}"]
        if "count" in j and j.get("count") == 0:
            return "OK-EMPTY", [f"count=0"]
    if isinstance(j, list):
        return ("OK-EMPTY" if not j else "OK"), [f"list={len(j)}"]
    return "OK", [f"{len(body)}b"]


def main():
    st, spec = get("/openapi.json")
    print(f"openapi: {st} ({len(spec)}b)")
    if st != 200:
        print(spec[:300])
        return
    paths = json.loads(spec)["paths"]
    gets = sorted(p for p, m in paths.items() if "get" in m and "{" not in p)
    print(f"parameterless GETs: {len(gets)}\n")
    results = []
    for p in gets:
        st, body = get(p)
        v, notes = verdict(st, body)
        results.append((v, p, st, notes))
        if v not in ("OK",):
            print(f"{v:16} {st} {p} {notes}")

    # ── targeted probes: endpoints that need params (page-specific) ──
    print("\n── parameterized / page-critical probes ──")
    extra = [
        "/api/oncall/date?date=2026-09-13",
        "/api/oncall/week",
        "/api/oncall/now",
        "/api/oncall/schedule",
        "/api/fs/list?path=/workspace",
        "/api/fs/read?path=/workspace/agentic-os/DESIGN.md",
        "/api/user/1",
        "/api/gme/detail?id=1",
        "/api/brain/tasks-data/tasks.json",
        "/api/call-schedule/pdf",
        "/api/calendar-invites?test=true",
        "/api/subi-exit-invites?test=true",
        "/api/pdf-archive",
        "/api/images/list",
        "/api/health/full",
        "/api/status",
        "/api/attention",
        "/api/agent-activity",
        "/api/cron/jobs",
        "/api/crm-data-gaps",
        "/api/morning-briefing",
        "/api/notifications",
        "/api/eval/dashboard",
        "/api/eval/forms",
        "/api/telegram/status",
        "/api/telegram/logs",
        "/api/email/send-log",
        "/api/conference/schedule",
        "/api/conference/events",
        "/api/documents",
        "/api/quick-action",
        "/api/skill-manifest",
        "/api/compliance/overview",
        "/api/staff-schedule",
        "/api/crm/launchpad",
        "/api/crm/contacts",
        "/api/crm/email-groups",
        "/api/reimbursement/residents",
        "/api/qgenda/users",
        "/api/letters/generate",
        "/api/vapi/pins",
        "/api/app",
    ]
    for p in extra:
        st, body = get(p)
        v, notes = verdict(st, body)
        results.append((v, p, st, notes))
        print(f"{v:16} {st} {p} {notes}")

    print("\n=== SUMMARY ===")
    from collections import Counter
    c = Counter(v for v, *_ in results)
    for k, n in c.most_common():
        print(f"  {k}: {n}")
    Path("/workspace/aos_audit_results.json").write_text(
        json.dumps([{"verdict": v, "path": p, "status": s, "notes": n} for v, p, s, n in results], indent=1))
    print("saved: /workspace/aos_audit_results.json")


if __name__ == "__main__":
    main()
