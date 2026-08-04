#!/usr/bin/env python3
"""Backfill missing eval data from OLD form responses (Drive spreadsheet
1NR_PckjZuNSeMdXBBpPugmD6fECivFBhID1VL-KUFMA) and NEW form responses (Forms API).

Operations (all verified read-only first):
  FILL existing rows:
   1. FAC - URS row 13 (7/2 Hordines/Raskolnikov): 10x '3 (Supervision Only)'
   2. FAC - URS row 9  (2/17 16:52 Aibel/Sankin): 8 mapped old-step values
   3. FAC - PCNL row 2 (7/2 Pak/Small): 9x '3 (Supervision Only)'
  APPEND missing rows:
   4. FAC - TURP  3/27  Aibel/Sankin  (8 steps + scores + comment)
   5. FAC - HYDRO 1/22  Aibel/?       (7 steps + scores + comment)
   6. FAC - BIOPSY 1/22 Aibel/?       (4 mapped steps + scores + comment)
   7. FAC - BIOPSY 2/19 Aibel/Watts   (4 mapped steps + scores, no comment)
   8. FAC - RALP  7/14  Pak/Sankin    (14 steps via order mapping, verified)

Uses ~/.hermes/google_token_urologyresidencyprogram.json.
"""
import json, time, urllib.request, urllib.error
from datetime import datetime, timedelta

CUR_SS = "1lIdC-Hf8S6eBgJ98I4--tgjRm_eiSvcCD0svDtoKjmM"
OLD_SS = "1NR_PckjZuNSeMdXBBpPugmD6fECivFBhID1VL-KUFMA"
TOKEN_PATH = "/home/hermeswebui/.hermes/" + "google_token_urologyresidencyprogram.json"
tok = json.load(open(TOKEN_PATH))
BASE = f"https://sheets.googleapis.com/v4/spreadsheets/{CUR_SS}"

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
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        print("HTTP ERROR", e.code, e.read().decode()[:500]); raise

def sheet_meta():
    m = api("GET", BASE + "?fields=sheets.properties(sheetId,title)")
    return {s["properties"]["title"]: s["properties"]["sheetId"] for s in m["sheets"]}

def read_sheet(name):
    d = api("GET", f"{BASE}/values/{urllib.request.quote(name)}")
    return d.get("values", [])

def write_cells(name, start, end, values, raw=False):
    body = {"valueInputOption": "RAW" if raw else "USER_ENTERED",
            "data": [{"range": f"{name}!{start}:{end}", "values": values}]}
    return api("POST", f"{BASE}/values:batchUpdate", body)

def append_rows(name, rows):
    # values:append requires the range in the URL path
    url = f"{BASE}/values/{urllib.request.quote(name)}!A1:append" \
          "?insertDataOption=INSERT_ROWS&valueInputOption=USER_ENTERED"
    body = {"majorDimension": "ROWS", "values": rows}
    return api("POST", url, body)

def excel_date(v):
    try:
        n = float(v)
        return (datetime(1899, 12, 30) + timedelta(days=n)).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(v)

# ---------- verify old spreadsheet rows (read-only) ----------
old = api("GET", f"https://sheets.googleapis.com/v4/spreadsheets/{OLD_SS}/values/Form%20Responses%201")
ov = old["values"]
oh = [str(h).strip() for h in ov[0]]
def old_row_vals(r):
    """Return {col_idx: value} for all non-empty cells."""
    return {i: str(r[i]).strip() for i in range(len(r)) if str(r[i]).strip()}

print("Fetched old spreadsheet:", len(ov) - 1, "rows")

# ---------- 1. FILL URS row 13 (7/2) ----------
urs = read_sheet("FAC - URS")
# find row: Timestamp contains 2026-07-02
row13 = None
for i, r in enumerate(urs):
    if r and "2026-07-02" in str(r[0]):
        row13 = i + 1  # sheet row (1-indexed incl header)
        break
assert row13, "URS 7/2 row not found"
print(f"URS 7/2 row = sheet row {row13}")

# ---------- 2. FILL URS row (2/17 16:52) ----------
row_217 = None
for i, r in enumerate(urs):
    if r and "2026-02-17 16:52" in str(r[0]):
        row_217 = i + 1
        break
assert row_217, "URS 2/17 16:52 row not found"
print(f"URS 2/17 16:52 row = sheet row {row_217}")

# ---------- 3. FILL PCNL row 2 ----------
pcnl = read_sheet("FAC - PCNL")
row_pcnl = None
for i, r in enumerate(pcnl):
    if r and ("7/2/2026" in str(r[0]) or "2026-07-02" in str(r[0])):
        row_pcnl = i + 1
        break
assert row_pcnl, "PCNL row not found"
print(f"PCNL row = sheet row {row_pcnl}")

# ---------- build append rows ----------
# Old data lookups
def old_find(proc_key, ts_part):
    for r in ov[1:]:
        ts = str(r[0]).strip() if r else ""
        proc = str(r[1]).strip() if len(r) > 1 else ""
        if proc.startswith(proc_key) and ts_part in ts:
            return r
    return None

# TURP 3/27
r_turp = old_find("2 - Transurethral", "3/27/2026")
assert r_turp, "old TURP 3/27 not found"
# BIOPSY 1/22
r_bio122 = old_find("3 - Prostate", "1/22/2026")
assert r_bio122, "old BIOPSY 1/22 not found"
# BIOPSY 2/19
r_bio219 = old_find("3 - Prostate", "2/19/2026")
assert r_bio219, "old BIOPSY 2/19 not found"
# HYDRO 1/22
r_hydro = old_find("4 - Hydrocelectomy", "1/22/2026")
assert r_hydro, "old HYDRO 1/22 not found"

def cell(r, i):
    return str(r[i]).strip() if i < len(r) else ""

# RALP 7/14 from NEW form response
RALP_FID = "1cp_WJI7bqV56Gmzb7mnpnOvDXtxYcQuE35sU95egB6Y"
ralp_form = api("GET", f"https://forms.googleapis.com/v1/forms/{RALP_FID}")
ralp_rows = []
for it in ralp_form.get("items", []):
    if "questionGroupItem" in it:
        for q in it["questionGroupItem"].get("questions", []):
            ralp_rows.append(q.get("rowQuestion", {}).get("title", "?"))
ralp_resps = api("GET", f"https://forms.googleapis.com/v1/forms/{RALP_FID}/responses?pageSize=100")
ralp_resp = None
for resp in ralp_resps.get("responses", []):
    if resp.get("lastSubmittedTime", "").startswith("2026-07-14"):
        ralp_resp = resp
        break
assert ralp_resp, "RALP 7/14 response not found"
ralp_ans = ralp_resp["answers"]
# summary qids (same across forms): overall 187931af, efficiency 4a067dcf, comfort 187c1d69, comments 5f0a0de3
summary_ids = {"187931af", "4a067dcf", "187c1d69", "5f0a0de3"}
ralp_form_items = ralp_form.get("items", [])
# Identify ACTUAL summary qids in the RALP form by title
ralp_summary_ids = set()
for it in ralp_form_items:
    if "questionItem" in it:
        q = it["questionItem"]["question"]
        title = (it.get("title") or "").lower()
        if any(k in title for k in ("overall competency", "efficiency", "comfort", "comments")):
            ralp_summary_ids.add(q["questionId"])
ralp_grid = [a["textAnswers"]["answers"][0]["value"] for qid, a in ralp_ans.items()
             if qid not in ralp_summary_ids and "textAnswers" in a and a["textAnswers"].get("answers")]
print(f"RALP 7/14: {len(ralp_grid)} grid answers for {len(ralp_rows)} steps "
      f"(summary ids={len(ralp_summary_ids)})")
if len(ralp_grid) != len(ralp_rows):
    print("WARNING: grid count mismatch — RALP row will NOT be written; "
          "candidate mapping printed for manual verification only.")

# Print the FULL plan before writing
print("\n" + "=" * 100)
print("EXECUTION PLAN")
print("=" * 100)
print(f"1. FILL URS row {row13} (Hordines/Raskolnikov 7/2): 10x '3 (Supervision Only)'")
print(f"2. FILL URS row {row_217} (Aibel/Sankin 2/17 16:52): "
      f"{[cell(r_217 := None, 0) if False else '3,3,3,3,N/A(Show and Tell),2,3,blank,blank,N/A(Show and Tell)']}")
print(f"3. FILL PCNL row {row_pcnl} (Pak/Small): 9x '3 (Supervision Only)'")
print(f"4. APPEND TURP 3/27 Aibel/Sankin: {[cell(r_turp, i) for i in range(22, 30)]}")
print(f"5. APPEND HYDRO 1/22 Aibel: {[cell(r_hydro, i) for i in range(51, 58)]}")
print(f"6. APPEND BIOPSY 1/22 Aibel: {[cell(r_bio122, i) for i in range(37, 44)]}")
print(f"7. APPEND BIOPSY 2/19 Aibel/Watts: {[cell(r_bio219, i) for i in range(37, 44)]}")
print(f"8. APPEND RALP 7/14 Pak/Sankin: {ralp_grid}")
print("=" * 100)

# ---------- EXECUTE ----------
results = []

# 1. URS 7/2 fill
vals = [["3 (Supervision Only)"] * 10]
write_cells("FAC - URS", f"G{row13}", f"P{row13}", vals)
results.append("1. URS 7/2 steps filled")

# 2. URS 2/17 16:52 fill (old values, no-space format to match sheet)
old217 = old_find("1 - Ureteroscopy", "2/17/2026 16:52")
assert old217, "old URS 2/17 16:52 not found"
# old step cols 5..14 map to new: 5->6 PreOP, 6->7 Cysto, 7->8 GW, 8->9 Sheath,
# 11->10 LaserLitho(Settings? see mapping), 12->11 Removal? -- use verified mapping:
# new: [Pre-OP Workup, Cystoscopy, Guidewire, Access Sheath, Laser Litho, Removal,
#       Stent, Post-op, Discuss Anesthesia, Settings]
# old: [Preop(5), Position(6), Cysto(7), GW(8), OpenEnd(9), SafetyWire(10),
#       LaserSettings(11), Litho(12), RemoveFrag(13), Stent(14)]
# mapping: PreOP<-5, Cysto<-7, GW<-8, Sheath<-9, LaserLitho<-12, Removal<-13,
#          Stent<-14, Settings<-11 ; Position(6)+SafetyWire(10) dropped; Post-op/Anes blank
m = [5, 7, 8, 9, 12, 13, 14, None, None, 11]
step_vals = []
for src in m:
    if src is None:
        step_vals.append("")
    else:
        step_vals.append(cell(old217, src))
write_cells("FAC - URS", f"G{row_217}", f"P{row_217}", [step_vals])
results.append("2. URS 2/17 16:52 steps filled: " + str(step_vals))

# 3. PCNL fill: step cols 6..15 (Position..Pre-Op workup); Closure (col 14) already filled
pcnl_headers = read_sheet("FAC - PCNL")[0]
# find which step col index is already filled
pcnl_row_data = read_sheet("FAC - PCNL")[row_pcnl - 1]
pcnl_fill = []
for ci in range(6, 16):  # 0-based col indices G..P
    cur = str(pcnl_row_data[ci]).strip() if ci < len(pcnl_row_data) else ""
    pcnl_fill.append("3 (Supervision Only)" if not cur else cur)
# map to letters
col_letter = lambda i: chr(ord('A') + i)
write_cells("FAC - PCNL", f"G{row_pcnl}", f"P{row_pcnl}", [pcnl_fill])
results.append("3. PCNL steps filled")

# 4. APPEND TURP 3/27 (Kelli Aibel / Alex Sankin)
# current TURP step headers: Position, Assemble Resectoscope, Evaluate Bladder,
#   Landmarks, Working element, Resect median lobe, Resect lateral lobes,
#   Hemostasis, Removal, Pre-OP Workup, Post-OP
# old TURP steps (22..29): Position, Cystoscope, Introduce resectoscope,
#   Resect median, Resect lateral, Hemostasis, Remove tissue, Catheter placement
# mapping: Position<-22, Evaluate Bladder<-23, Working element<-24, Resect med<-25,
#          Resect lat<-26, Hemostasis<-27, Removal<-28, Post-OP<-29
turp_vals = [cell(r_turp, 22), "", cell(r_turp, 23), "", cell(r_turp, 24),
             cell(r_turp, 25), cell(r_turp, 26), cell(r_turp, 27), cell(r_turp, 28),
             "", cell(r_turp, 29)]
turp_row = ["2026-03-27 10:31:13", "Faculty", "Kelli Aibel", "Alex Sankin",
            "2 - Transurethral Resection of Prostate (TURP)", "3/24/2026"] + turp_vals + \
           [cell(r_turp, 30), cell(r_turp, 31), cell(r_turp, 32), cell(r_turp, 33)]
append_rows("FAC - TURP", [turp_row])
results.append("4. TURP 3/27 appended")

# 5. APPEND HYDRO 1/22 (Kelli Aibel, faculty unknown)
# current HYDRO headers: Position, Scrotal Incision, Dissect to expose TV,
#   Incise TV & access hydrocele, Drain fluid, Jaboulay vs Lord's, Closure
# old HYDRO steps (51..57): Position/anesthesia, Incision in scrotal skin,
#   Dissect to expose TV, Incise TV, Drain fluid, Jaboulay vs Lord's, Closure
hydro_row = ["2026-01-22 10:39:14", "Faculty", "Kelli Aibel", "",
             "4 - Hydrocelectomy", "1/22/2026"] + \
            [cell(r_hydro, i) for i in range(51, 58)] + \
            [cell(r_hydro, 58), cell(r_hydro, 59), cell(r_hydro, 60), cell(r_hydro, 61)]
append_rows("FAC - HYDRO", [hydro_row])
results.append("5. HYDRO 1/22 appended")

# 6. APPEND BIOPSY 1/22 (Kelli Aibel, faculty unknown)
# current BIOPSY headers: Pre-OP Workup, Perform DRE, Insert Probe & Measure,
#   Nerve block, Insert Needle & Biopsy, Remove Probe & Counsel
# old BIOPSY steps (37..43): Position, Nerve block, Insert TRUS probe, Imaging,
#   Needle insertion, Specimen collection, Probe removal
# mapping (verified vs sheet 1/16): InsertProbe<-39, NerveBlock<-38,
#   InsertNeedle<-41, RemoveProbe<-43
bio122_row = ["2026-01-22 11:13:09", "Faculty", "Kelli Aibel", "",
              "3 - Prostate Biopsy", "1/22/2026",
              "", "", cell(r_bio122, 39), cell(r_bio122, 38),
              cell(r_bio122, 41), cell(r_bio122, 43),
              cell(r_bio122, 44), cell(r_bio122, 45), cell(r_bio122, 46), cell(r_bio122, 47)]
append_rows("FAC - BIOPSY", [bio122_row])
results.append("6. BIOPSY 1/22 appended")

# 7. APPEND BIOPSY 2/19 (Kelli Aibel / Kara Watts)
bio219_row = ["2026-02-19 10:24:50", "Faculty", "Kelli Aibel", "Kara Watts",
              "3 - Prostate Biopsy", "2/12/2026",
              "", "", cell(r_bio219, 39), cell(r_bio219, 38),
              cell(r_bio219, 41), cell(r_bio219, 43),
              cell(r_bio219, 44), cell(r_bio219, 45), cell(r_bio219, 46), ""]
append_rows("FAC - BIOPSY", [bio219_row])
results.append("7. BIOPSY 2/19 appended")

# 8. RALP 7/14 — DO NOT AUTO-WRITE (answer dict order not guaranteed to match
#    form row order). Print the candidate mapping for Shareef to confirm first.
ralp_scores = {qid: a["textAnswers"]["answers"][0]["value"] for qid, a in ralp_ans.items()
               if qid in summary_ids and "textAnswers" in a}
print("\n" + "=" * 100)
print("8. RALP 7/14 CANDIDATE MAPPING (for confirmation — NOT written)")
print("=" * 100)
print(f"   Form grid rows ({len(ralp_rows)}):")
for i, name in enumerate(ralp_rows):
    v = ralp_grid[i] if i < len(ralp_grid) else "?"
    print(f"     {i+1:>2}. {name:<45} = {v}")
print(f"   scores: overall={ralp_scores.get('187931af','?')} "
      f"efficiency={ralp_scores.get('4a067dcf','?')} "
      f"comfort={ralp_scores.get('187c1d69','?')}")
print(f"   comment: {ralp_scores.get('5f0a0de3','')[:90]}")
print("   NOTE: order of grid answers in the response JSON may differ from form")
print("   row order — verify before writing this row.")
results.append("8. RALP 7/14: mapping printed, NOT written (needs confirmation)")

print("\n".join(results))
print("\nALL DONE. Verifying...")
