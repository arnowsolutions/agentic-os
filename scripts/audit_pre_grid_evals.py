#!/usr/bin/env python3
"""Audit all eval sheets: flag evals that will ALWAYS show 'Not Assessed' steps.

What matters is the SHEET content (that's what the dashboard displays):
  - Real step ratings exist in Jan-Mar rows (grid existed then, was removed,
    re-added 7/31). Those evals are FINE.
  - Evals with real scores but ZERO step cells = the grid wasn't on the form
    when submitted -> steps can never be recovered. Those are flagged.

Non-step columns are known and identical across all sheets:
Timestamp, Role, Resident Name, Faculty Name, Procedure, Procedure Date,
Overall Competency, Efficiency, Faculty Trust, Comments.
EVERYTHING ELSE is a step column (grid row).
Read-only. Uses ~/.hermes/google_token_urologyresidencyprogram.json.
"""
import json, time, urllib.request, urllib.error
from datetime import datetime, date, timedelta

SSID = "1lIdC-Hf8S6eBgJ98I4--tgjRm_eiSvcCD0svDtoKjmM"
GRID_READDED = date(2026, 7, 31)

TOKEN_PATH = "/home/hermeswebui/.hermes/google_token_urologyresidencyprogram.json"
tok = json.load(open(TOKEN_PATH))
BASE = f"https://sheets.googleapis.com/v4/spreadsheets/{SSID}"

def refresh():
    body = {"client_id": tok["client_id"], "client_secret": tok["client_secret"],
            "refresh_token": tok["refresh_token"], "grant_type": "refresh_token"}
    req = urllib.request.Request("https://oauth2.googleapis.com/token",
                                 data=json.dumps(body).encode(), method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            fresh = json.loads(r.read())
    except urllib.error.HTTPError as e:
        print("REFRESH ERROR", e.code, e.read().decode()[:500]); raise
    tok["token"] = fresh["access_token"]
    tok["expiry"] = time.time() + fresh.get("expires_in", 3600) - 60
    json.dump(tok, open(TOKEN_PATH, "w"), indent=2)
    return fresh["access_token"]

access = refresh()

def api(method, url, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {access}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        print("HTTP ERROR", e.code, e.read().decode()[:800]); raise

NON_STEP = ("timestamp", "role", "resident", "faculty", "procedure",
            "overall", "competency", "efficiency", "trust", "comment")

def parse_date(v):
    if v is None: return None
    s = str(v).strip()
    if not s: return None
    try:
        n = float(s)
        if 20000 < n < 80000:
            return date(1899, 12, 30) + timedelta(days=n)
    except ValueError:
        pass
    for fmt in ("%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M", "%m/%d/%Y",
                "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s[:19], fmt).date()
        except ValueError:
            continue
    return None

def col_roles(headers):
    """Return (role_idx, step_idx) where role_idx maps header idx -> role string."""
    roles, steps = {}, []
    for i, h in enumerate(headers):
        hx = (h or "").strip().lower()
        if hx.startswith("timestamp"):
            roles[i] = "timestamp"
        elif "comment" in hx:
            roles[i] = "comments"
        elif "resident" in hx or "trainee" in hx:
            roles[i] = "resident"
        elif "faculty" in hx or "evaluator" in hx or "attending" in hx:
            roles[i] = "faculty"
        elif "procedure" in hx and "date" in hx:
            roles[i] = "proc_date"
        elif "procedure" in hx:
            roles[i] = "procedure"
        elif "role" in hx:
            roles[i] = "role"
        elif any(k in hx for k in ("overall", "competency", "efficiency", "trust")):
            roles[i] = "score"
        else:
            steps.append(i)
    return roles, steps

meta = api("GET", BASE + "?fields=sheets.properties(sheetId,title)")
sheets = [s["properties"]["title"] for s in meta["sheets"]]
eval_sheets = [t for t in sheets if t.startswith(("FAC -", "RES -"))]

summary, flagged, post_missing, zero_score = [], [], [], []
for title in eval_sheets:
    try:
        resp = api("GET", f"{BASE}/values/{urllib.request.quote(title)}")
    except Exception as e:
        print(f"  !! {title}: {e}"); continue
    values = resp.get("values", [])
    if len(values) < 2:
        summary.append({"sheet": title, "rows": 0, "ok": 0, "pre_grid": 0, "no_scores": 0}); continue
    headers = values[0]
    roles, steps = col_roles(headers)
    ts_i = next((i for i, r in roles.items() if r == "timestamp"), 0)
    res_i = next((i for i, r in roles.items() if r == "resident"), None)
    fac_i = next((i for i, r in roles.items() if r == "faculty"), None)
    com_i = next((i for i, r in roles.items() if r == "comments"), None)
    score_i = next((i for i, r in roles.items() if r == "score"), None)

    ok = pre_grid = no_scores = 0
    for row in values[1:]:
        ts = parse_date(row[ts_i]) if ts_i < len(row) else None
        steps_filled = sum(1 for c in steps if c < len(row) and str(row[c]).strip())
        has_scores = bool(score_i is not None and score_i < len(row) and str(row[score_i]).strip())
        name = (row[res_i] if res_i is not None and res_i < len(row) else "") or ""
        fac = (row[fac_i] if fac_i is not None and fac_i < len(row) else "") or ""
        comment = (row[com_i] if com_i is not None and com_i < len(row) else "") or ""
        rec = {"sheet": title, "date": ts.isoformat() if ts else "?",
               "resident": name.strip(), "faculty": fac.strip(),
               "steps": steps_filled, "scores": has_scores,
               "comment": bool(comment.strip()), "ts": ts}
        if not has_scores:
            no_scores += 1
            zero_score.append(rec)   # orphan/test rows - dashboard skips
        elif steps_filled == 0:
            pre_grid += 1
            flagged.append(rec)
        else:
            ok += 1
            if ts is not None and ts >= GRID_READDED:
                post_missing.append(rec)  # should never happen now
    summary.append({"sheet": title, "rows": len(values) - 1, "ok": ok,
                    "pre_grid": pre_grid, "no_scores": no_scores})

print("=" * 88)
print("EVAL AUDIT — sheets with real scores, zero steps = will always show 'Not Assessed'")
print("=" * 88)
print(f"{'Sheet':<14}{'Rows':>6}{'OK (steps)':>12}{'ZERO STEPS':>12}{'No scores*':>12}")
t = {"r": 0, "ok": 0, "p": 0, "z": 0}
for s in summary:
    print(f"{s['sheet']:<14}{s['rows']:>6}{s['ok']:>12}{s['pre_grid']:>12}{s['no_scores']:>12}")
    t["r"] += s["rows"]; t["ok"] += s["ok"]; t["p"] += s["pre_grid"]; t["z"] += s["no_scores"]
print("-" * 88)
print(f"{'TOTAL':<14}{t['r']:>6}{t['ok']:>12}{t['p']:>12}{t['z']:>12}")
print("* No scores = orphan/test rows (portal init, never completed) — dashboard skips them.")

print()
print("=" * 88)
print(f"FLAGGED: {len(flagged)} evals with real scores but ZERO step ratings (data never collected)")
print("=" * 88)
for r in sorted(flagged, key=lambda r: (r["sheet"], r["date"])):
    print(f"  {r['sheet']:<14} {r['date']}  {r['resident'] or '?':<26} fac={r['faculty'] or '?':<22} comment={'Y' if r['comment'] else 'N'}")

if post_missing:
    print()
    print("NOTE: rows with steps on/after 7/31 (grid re-added):")
    for r in post_missing:
        print(f"  {r['sheet']:<14} {r['date']}  {r['resident']}")
