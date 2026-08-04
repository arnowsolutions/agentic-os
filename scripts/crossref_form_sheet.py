#!/usr/bin/env python3
"""DEFINITIVE cross-reference: form responses (Forms API) vs sheet rows (Sheets API).

For each of the 10 FAC forms:
  1. Fetch form structure -> identify NON-step question ids (overall, efficiency,
     comfort, comments, procedure date) by title keywords.
  2. Fetch all responses -> grid answers = any textAnswer whose questionId is
     NOT a known non-step id. Count = steps captured in the FORM.
  3. Fetch sheet rows -> steps present in the SHEET + resident/faculty/ts.
  4. Match responses to sheet rows by timestamp proximity (same day) + resident
     name fuzzy. Classify:
       RECOVERABLE   = response HAS grid answers, sheet row EXISTS but steps blank
       ORPHAN        = response HAS grid answers, NO sheet row at all
       SHEET_ONLY    = sheet row exists, no matching response (old/deleted form)
       TEST/NOGRID   = response has NO grid answers (test or pre-grid)
Read-only.
"""
import json, time, urllib.request, urllib.error
from datetime import datetime, date

SSID = "1lIdC-Hf8S6eBgJ98I4--tgjRm_eiSvcCD0svDtoKjmM"
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

def api(url):
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {access}")
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"_error": e.code, "_msg": e.read().decode()[:300]}

def norm(s):
    return (s or "").strip().lower().replace(",", " ").replace("  ", " ")

def name_token(s):
    """Last-name token for matching."""
    n = norm(s)
    if not n: return ""
    parts = n.split()
    return parts[-1] if parts else n

FORMS = {
  "URS":    "14f99mU2EvAqL5tT1Ab213wYb5Ekb_-qvp3xjVtROzrc",
  "TURP":   "1E-X9eMogA-XdOXQoNzsdVwkL8--l1DVXqS0Q1X3x7mc",
  "BIOPSY": "1hR6Vcv_SsbBro31a2nYBR3YWhDiOR49noDtLIaiBSPs",
  "HYDRO":  "1yvCxd_c2aAAdqNpgbaM0M5-6s5cm4cmJbWa6-9LMYJ0",
  "IPP":    "14a7ist3LdD25XsufW3qjojd57fTY9-1wRC0njvu6WNQ",
  "SLING":  "1rPaR__u7SFul05SuqA815z0B-ILUZyR3nFgWCXFu-Ds",
  "PCNL":   "1LPbO2L0JPrr3vD4oPP663rhVDWFhFxnbN8SdDqXcDrQ",
  "RALP":   "1cp_WJI7bqV56Gmzb7mnpnOvDXtxYcQuE35sU95egB6Y",
  "ORCH":   "1ppQgljL2K2ZP1edAKZzj8wXcDvoucldTW3h-8mAzNlE",
  "NEPH":   "1RRvSqoESXi-FGm_yv_o24ZrlhZXc6odJROQjRUpGd0I",
}

NONSTEP_TITLES = ("overall competency", "efficiency", "comfort", "comments",
                  "procedure date", "date of procedure", "resident name",
                  "faculty name", "procedure performed")

recoverable, orphans, sheet_only, test_no_grid = [], [], [], []
for proc, fid in FORMS.items():
    form = api(f"https://forms.googleapis.com/v1/forms/{fid}")
    if "_error" in form:
        print(f"{proc}: form ERR {form['_error']}"); continue
    nonstep_ids = set()
    for it in form.get("items", []):
        if "questionItem" in it:
            q = it["questionItem"]["question"]
            title = (it.get("title") or "").lower()
            if any(k in title for k in NONSTEP_TITLES):
                nonstep_ids.add(q["questionId"])
    # everything else (questionGroupItem rows etc.) = steps
    resps = api(f"https://forms.googleapis.com/v1/forms/{fid}/responses?pageSize=200")
    if "_error" in resps:
        print(f"{proc}: resp ERR {resps['_error']}"); continue

    # sheet rows for this procedure
    try:
        svals = api(f"{BASE}/values/{urllib.request.quote('FAC - ' + proc)}")
        rows = svals.get("values", [])
        if not rows:
            print(f"{proc}: WARNING sheet fetch empty ({svals.get('_error', 'no error key')})")
    except Exception as e:
        rows = []
        print(f"{proc}: sheet fetch EXC {e}")
    hdrs = [norm(h) for h in (rows[0] if rows else [])]
    def col_idx(key):
        for i, h in enumerate(hdrs):
            if key in h:
                return i
        return None
    ci_ts = col_idx("timestamp"); ci_res = col_idx("resident")
    ci_fac = col_idx("faculty"); ci_comment = col_idx("comment")
    step_cols = [i for i in range(len(hdrs)) if i not in (ci_ts, ci_res, ci_fac, ci_comment,
                 col_idx("procedure date"), col_idx("procedure"), col_idx("role"),
                 col_idx("overall"), col_idx("efficiency"), col_idx("trust"),
                 col_idx("comfort"), col_idx("competency"))]

    def sheet_steps(row):
        return sum(1 for c in step_cols if c < len(row) and str(row[c]).strip())

    # sheet rows indexed by (lastname, date)
    sheet_rows = []
    for r in rows[1:]:
        ts_raw = r[ci_ts] if ci_ts is not None and ci_ts < len(r) else ""
        res = r[ci_res] if ci_res is not None and ci_res < len(r) else ""
        fac = r[ci_fac] if ci_fac is not None and ci_fac < len(r) else ""
        sheet_rows.append({"ts": str(ts_raw), "res": str(res), "fac": str(fac),
                           "steps": sheet_steps(r)})

    for resp in sorted(resps.get("responses", []), key=lambda x: x.get("lastSubmittedTime","")):
        ts = resp.get("lastSubmittedTime", "")[:10]
        answers = resp.get("answers", {})
        grid = [a for qid, a in answers.items()
                if qid not in nonstep_ids and "textAnswers" in a]
        grid_vals = [g["textAnswers"]["answers"][0]["value"] for g in grid
                     if g["textAnswers"].get("answers")]
        comment = ""
        for qid, a in answers.items():
            if qid in nonstep_ids and "textAnswers" in a:
                v = a["textAnswers"]["answers"][0]["value"]
                if "comment" in nonstep_ids and qid in nonstep_ids:
                    pass
        # find comment specifically
        for it in form.get("items", []):
            if "questionItem" in it and "comment" in (it.get("title") or "").lower():
                cid = it["questionItem"]["question"]["questionId"]
                if cid in answers and "textAnswers" in answers[cid]:
                    comment = answers[cid]["textAnswers"]["answers"][0]["value"]
        rec = {"proc": proc, "ts": ts, "time": resp.get("lastSubmittedTime","")[:16],
               "grid_steps": len(grid_vals), "comment": comment[:40]}

        if len(grid_vals) == 0:
            test_no_grid.append(rec)
            continue
        # Find matching sheet row by TIME PROXIMITY: portal writes the identity
        # row ~seconds-minutes before the form is submitted. Try window 0-90 min
        # around response time, then same-day fallback.
        def sheet_ts(ts_raw):
            s = str(ts_raw).strip()
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d",
                        "%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M", "%m/%d/%Y"):
                try:
                    return datetime.strptime(s[:19], fmt)
                except ValueError:
                    continue
            return None
        resp_dt = datetime.strptime(resp.get("lastSubmittedTime", "")[:19], "%Y-%m-%dT%H:%M:%S")
        candidates = []
        for s in sheet_rows:
            sdt = sheet_ts(s["ts"])
            if sdt is None:
                continue
            diff = abs((sdt - resp_dt).total_seconds())
            if diff <= 5400:  # 90 min
                candidates.append((diff, s))
        if not candidates:
            for s in sheet_rows:
                sdt = sheet_ts(s["ts"])
                if sdt is not None and sdt.date() == resp_dt.date():
                    candidates.append((24 * 3600, s))
        if candidates:
            candidates.sort()
            m = candidates[0][1]
            if m["steps"] == 0:
                rec["sheet_row"] = f"{m['res']} / {m['fac']} @ {m['ts']} (steps=0)"
                recoverable.append(rec)
            else:
                rec["sheet_row"] = f"{m['res']} @ {m['ts']} (steps={m['steps']})"
                rec["status"] = "OK"
        else:
            rec["status"] = "NO SHEET ROW"
            orphans.append(rec)

print(f"{'Proc':<8}{'Submitted':<12}{'GridSteps':>10}  Comment                       Status")
for rec in sorted(recoverable + orphans + [dict(r, status="no-grid") for r in test_no_grid],
                  key=lambda r: (r["proc"], r["ts"])):
    print(f"{rec['proc']:<8}{rec['ts']:<12}{rec['grid_steps']:>10}  {rec.get('comment',''):<30} {rec.get('status','')}")
