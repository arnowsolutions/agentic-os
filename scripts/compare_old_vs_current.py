#!/usr/bin/env python3
"""Compare OLD form responses (Urology Resident Surgical Competency) against
current eval sheets. Old responses carry the ORIGINAL grid step names (pre-7/31
renaming). Goal: find which old responses are missing from sheets or missing steps.

Sources:
- OLD spreadsheet: 1NR_PckjZuNSeMdXBBpPugmD6fECivFBhID1VL-KUFMA (129 rows, the
  full old-form response log; the 27-row xlsx Shareef uploaded is a subset)
- CURRENT eval spreadsheet: 1lIdC-Hf8S6eBgJ98I4--tgjRm_eiSvcCD0svDtoKjmM

Read-only. Uses ~/.hermes/google_token_urologyresidencyprogram.json.
"""
import json, time, urllib.request, urllib.error
from datetime import datetime, timedelta

OLD_SS = "1NR_PckjZuNSeMdXBBpPugmD6fECivFBhID1VL-KUFMA"
CUR_SS = "1lIdC-Hf8S6eBgJ98I4--tgjRm_eiSvcCD0svDtoKjmM"
TOKEN_PATH = "/home/hermeswebui/.hermes/google_token_urologyresidencyprogram.json"
tok = json.load(open(TOKEN_PATH))

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

def api(url):
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {access}")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"_error": e.code, "_msg": e.read().decode()[:300]}

def excel_date(v):
    try:
        n = float(v)
        return (datetime(1899, 12, 30) + timedelta(days=n)).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(v)

# ---- Load OLD spreadsheet (full) ----
BASE = "https://sheets.googleapis.com/v4/spreadsheets"
old = api(f"{BASE}/{OLD_SS}/values/Form%20Responses%201")
if "_error" in old:
    print("OLD ERR", old); raise SystemExit(1)
old_vals = old["values"]
old_hdr = [str(h).strip() for h in old_vals[0]]
print(f"OLD spreadsheet: {len(old_vals)-1} data rows, {len(old_hdr)} cols")

# Map each procedure block: for each procedure, its rating columns start at the
# first 'Autonomy Rating' col and there are N consecutive rating cols.
# Simpler: per row, extract: timestamp(A), procedure(B), date(C), yourname(D),
# resident(E), and ALL rating values (cols whose header starts with 'Autonomy Rating')
# with their headers, plus overall/efficiency/comfort/comment by matching header keywords.
rating_cols = [(i, h) for i, h in enumerate(old_hdr) if h.startswith("Autonomy Rating")]
comment_cols = [(i, h) for i, h in enumerate(old_hdr) if h.startswith("Comments")]
name_cols = [(i, h) for i, h in enumerate(old_hdr) if h.startswith("Your name") or h == "Your Name"]

print(f"rating cols: {len(rating_cols)}, comment cols: {len(comment_cols)}, name cols: {len(name_cols)}")

def get(row, idx):
    return str(row[idx]).strip() if idx < len(row) else ""

old_evals = []
for r in old_vals[1:]:
    ts = excel_date(get(r, 0))
    proc = get(r, 1)
    fac = get(r, 3)
    res = get(r, 4)
    if not ts and not proc:
        continue
    ratings = {}
    for i, h in rating_cols:
        v = get(r, i)
        if v:
            ratings[h] = v
    comments = {h: get(r, i) for i, h in comment_cols if get(r, i)}
    # resident/faculty may live in per-procedure columns; find any non-empty name col pair
    if not res or not fac:
        for i, h in name_cols:
            v = get(r, i)
            if v:
                # "Your name" = faculty; next col after it "Resident name N" = resident
                if "resident" in h.lower():
                    if not res: res = v
                elif "your" in h.lower():
                    if not fac: fac = v
    old_evals.append({"ts": ts, "proc": proc, "fac": fac, "res": res,
                      "ratings": ratings, "comments": comments})

print(f"old evals parsed: {len(old_evals)}")

# ---- Load CURRENT sheets ----
cur = api(f"{BASE}/{CUR_SS}?fields=sheets.properties(title,sheetId)")
cur_sheets = [s["properties"]["title"] for s in cur["sheets"] if s["properties"]["title"].startswith("FAC - ")]
cur_evals = {}
for title in cur_sheets:
    proc = title.replace("FAC - ", "")
    d = api(f"{BASE}/{CUR_SS}/values/{urllib.request.quote(title)}")
    vals = d.get("values", [])
    if not vals:
        continue
    hdr = [str(h).strip().lower() for h in vals[0]]
    def cidx(key):
        for i, h in enumerate(hdr):
            if key in h:
                return i
        return None
    ti, ri, fi = cidx("timestamp"), cidx("resident"), cidx("faculty")
    step_i = [i for i, h in enumerate(hdr) if h not in (hdr[ti] if ti is not None else "",) 
              and not any(k in h for k in ("timestamp","role","resident","faculty","procedure",
                                           "overall","efficiency","trust","comfort","comment","competency"))]
    rows = []
    for r in vals[1:]:
        ts = get(r, ti) if ti is not None else ""
        res = get(r, ri) if ri is not None else ""
        fac = get(r, fi) if fi is not None else ""
        steps = sum(1 for i in step_i if get(r, i))
        rows.append({"ts": ts, "res": res, "fac": fac, "steps": steps})
    cur_evals[proc] = rows

print(f"current sheets: {list(cur_evals.keys())}")

# ---- Compare: for each old eval, is there a matching sheet row? ----
def norm(s):
    return (s or "").strip().lower().replace(",", " ")

def lastname(s):
    n = norm(s)
    parts = n.split()
    return parts[-1] if parts else ""

PROC_MAP = {"1 - Ureteroscopy / Laser Lithotripsy / Stent": "URS",
            "2 - Transurethral Resection of Prostate (TURP)": "TURP",
            "3 - Prostate Biopsy": "BIOPSY",
            "4 - Hydrocelectomy": "HYDRO",
            "5 - Inflatable Penile Prosthesis": "IPP",
            "6 - Synthetic Mid-urethral Sling": "SLING",
            "7 - Percutaneous Nephrolithotomy (PCNL)": "PCNL",
            "8 - Robotic-assisted Radical Prostatectomy (RALP)": "RALP",
            "9 - Pediatric Orchiopexy": "ORCH",
            "10 - Laparoscopic Nephrectomy": "NEPH"}

missing_rows = []   # old eval has ratings but no sheet row at all
missing_steps = []  # sheet row exists but 0 steps
ok_rows = []

for ev in old_evals:
    if not ev["ratings"]:
        continue  # empty/test row
    proc = PROC_MAP.get(ev["proc"].strip())
    if not proc:
        print(f"  UNMAPPED PROC: {ev['proc']!r} @ {ev['ts']}")
        continue
    sheet_rows = cur_evals.get(proc, [])
    # match by date + resident/faculty lastname (normalize both date formats)
    def norm_date(s):
        # accepts 2026-01-12 or 1/12/2026 (any time suffix)
        t = s.split(" ")[0].strip()
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
            try:
                return datetime.strptime(t, fmt).date().isoformat()
            except ValueError:
                continue
        return t
    ev_date = norm_date(ev["ts"])
    matches = [s for s in sheet_rows
               if norm_date(s["ts"]) == ev_date
               and (lastname(s["res"]) == lastname(ev["res"]) or lastname(s["fac"]) == lastname(ev["fac"]) or not lastname(ev["res"]))]
    if not matches:
        missing_rows.append({**ev, "proc": proc})
    else:
        m = matches[0]
        if m["steps"] == 0:
            missing_steps.append({**ev, "proc": proc, "sheet": m})
        else:
            ok_rows.append({**ev, "proc": proc})

print("\n" + "=" * 90)
print(f"OLD EVALS WITH RATINGS: {len(ok_rows) + len(missing_rows) + len(missing_steps)} "
      f"(ok={len(ok_rows)}, no-sheet-row={len(missing_rows)}, sheet-row-0-steps={len(missing_steps)})")
print("=" * 90)

print("\n--- SHEET ROW EXISTS BUT 0 STEPS (recoverable from old data) ---")
for ev in missing_steps:
    print(f"  {ev['proc']:<8} {ev['ts']:<17} res={ev['res']:<20} fac={ev['fac']:<20} "
          f"ratings={len(ev['ratings'])} comment={'Y' if ev['comments'] else 'N'}")

print("\n--- NO SHEET ROW AT ALL (add from old data) ---")
for ev in missing_rows:
    print(f"  {ev['proc']:<8} {ev['ts']:<17} res={ev['res']:<20} fac={ev['fac']:<20} "
          f"ratings={len(ev['ratings'])} comment={'Y' if ev['comments'] else 'N'}")

# Also print the FULL rating detail for the recoverable ones so we can backfill
print("\n--- DETAIL (for backfill) ---")
for ev in missing_steps + missing_rows:
    print(f"\n  >>> {ev['proc']} {ev['ts']} res={ev['res']} fac={ev['fac']}")
    for h, v in ev["ratings"].items():
        print(f"      {h[:70]:<72} = {v}")
    for h, v in ev["comments"].items():
        print(f"      {h[:40]:<42} = {v[:100]}")
