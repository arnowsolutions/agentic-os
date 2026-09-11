#!/usr/bin/env python3
"""
Reimbursement data reader backed by the UNIFIED reimbursement database
(postgres.unified.reimb_* on the VPS) — the authoritative current source,
replacing the legacy SQLite reimbursement.db reader.

Access path: SSH to the VPS + `docker exec supabase-db psql` (same method used
and verified for all unified data operations). This avoids depending on a local
tunnel to 147.93.113.241:5432, which is not reachable from this box.

Public API mirrors what send-report.py needs:
    get_resident_data(name) -> dict | None
Builds transactions from unified.reimb_allocations (real per-fund accounts,
incl. split transactions) joined to reimb_submissions (real dates / academic_year).
GME cap = $1250/resident/academic year (current AY = Jul 1..Jun 30).
"""
import os
import re
import json
import subprocess
import sys
from collections import OrderedDict, defaultdict
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
VPS_HOST = os.environ.get("UNIFIED_DB_HOST", "root@147.93.113.241")
SSH_KEY = os.environ.get("UNIFIED_SSH_KEY", "")   # e.g. "-i /path/key"
GME_CAP = 1250.0

# Account full-name (in reimb_allocations.account) -> display label
ACCT_LABEL = OrderedDict([
    ("GME Funds", "GME Funds"),
    ("Teaching Funds", "Teaching Funds"),
    ("Dept Funds", "Dept Funds"),
    ("Dept Stipend", "Dept Stipend"),
    ("Donation Funds", "MISC"),
    ("Chair Fund", "Chair Fund"),
    ("Sleep Deprivation", "Sleep Deprivation"),
])


def _label(account: str) -> str:
    return ACCT_LABEL.get(account, account or "Other")


def _is_vps_host() -> bool:
    """True when running directly on the VPS (where docker/supabase-db is local)."""
    try:
        import socket
        hn = socket.gethostname().lower()
        return "srv1738752" in hn
    except Exception:
        return False


def _psql(sql: str, timeout: int = 40) -> str:
    """Run a SQL statement on the unified reimbursement DB and return raw psql stdout.

    - On the VPS: `docker exec -i supabase-db psql ...` directly (local docker).
    - Elsewhere: ssh to the VPS and run the same docker exec (stdin piped through).
    """
    docker_cmd = [
        "docker", "exec", "-i", "supabase-db", "psql",
        "-U", "postgres", "-d", "postgres", "-t", "-A", "-F", "|",
    ]
    if _is_vps_host():
        proc = subprocess.run(docker_cmd, input=sql, capture_output=True,
                              text=True, timeout=timeout)
    else:
        base = ["ssh", "-o", "BatchMode=yes"]
        if SSH_KEY:
            base += ["-i", SSH_KEY]
        base.append(VPS_HOST)
        remote = " ".join(docker_cmd)
        proc = subprocess.run(base + [remote], input=sql, capture_output=True,
                              text=True, timeout=timeout)
    if proc.returncode != 0:
        raise RuntimeError(f"psql failed: {proc.stderr[-400:]}")
    return proc.stdout


def _name_like_rows():
    """Return all (id, name, cls, email) rows from unified.reimb_persons resident-ish,
    joined to CRM contacts for the authoritative on-file email (CRM is source of truth)."""
    sql = (
        "SELECT rp.id, rp.name, rp.cls, "
        "COALESCE(NULLIF(rp.email,''), c.email) AS email "
        "FROM unified.reimb_persons rp "
        "LEFT JOIN public.contacts c "
        "  ON lower(coalesce(c.first_name,'')||' '||coalesce(c.last_name,''))=lower(rp.name) "
        "WHERE rp.beneficiary_type='resident' OR rp.cls ~* '^(PG|PGY)' "
    )
    rows = _psql(sql)
    out = []
    for line in rows.splitlines():
        if not line or "|" not in line and not line.strip():
            continue
        parts = line.split("|")
        if len(parts) >= 3:
            out.append({
                "id": parts[0],
                "name": parts[1],
                "cls": parts[2],
                "email": (parts[3] if len(parts) > 3 else "").strip() or "",
            })
    return out


def _normalize(name: str) -> str:
    return re.sub(r"[\s,\.'\-]", "", name).lower()


def _resolve_person(resident_name: str):
    """Match resident_name against unified.reimb_persons (exact->substr->double-letter)."""
    want = _normalize(resident_name)
    people = _name_like_rows()
    # exact
    for p in people:
        if _normalize(p["name"]) == want:
            return p
    # substring
    for p in people:
        if want in _normalize(p["name"]) or _normalize(p["name"]) in want:
            return p
    # double-letter
    for p in people:
        if _normalize(p["name"]).replace("ll", "l") == want.replace("ll", "l"):
            return p
    return None


# SQL-safe identifier injection guard (only used for known-good name strings)
def _esc(s: str) -> str:
    return s.replace("'", "''")


def _normalize_ay(year: str):
    """Normalize a user-supplied year to 'YYYY-YY'. Accepts '2025-26', '2025-2026',
    '2025/26', '25-26', '2025'. Returns a canonical 'YYYY-YY' or None if invalid."""
    if not year:
        return None
    y = str(year).strip().replace("/", "-").replace(" ", "-")
    m = re.match(r"^(?:20)?(\d{2})-(?:20)?(\d{2})$", y)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        if b == a + 1 or (a == 99 and b == 0):
            base = 2000 + a if a >= 50 else 2000 + a
            # interpret 25-26 as 2025-26
            if a <= 99 and a < 50:
                base = 2000 + a
            return f"{base}-{str(b).zfill(2)}"
    m2 = re.match(r"^(?:20)?(\d{2})$", y)
    if m2:
        base = 2000 + int(m2.group(1)) if int(m2.group(1)) < 90 else 1900 + int(m2.group(1))
        return f"{base}-{str((base % 100) + 1).zfill(2)}"  # '2025' -> 2025-26
    return None


def _matches_ay(actual_ay: str, wanted_ay: str) -> bool:
    """True if actual_academic_year (from DB, 'YYYY-YY' or 'YYYY') is in the wanted AY."""
    if not wanted_ay:
        return True
    w = _normalize_ay(wanted_ay)
    if not w:
        return True
    a = (actual_ay or "").strip()
    if a == w:
        return True
    # handle bare 'YYYY' faculty/manager rows vs 'YYYY-YY' wanted
    if re.match(r"^\d{4}$", a):
        return a in (w[:4], str(int(w[:4]) + 1))
    return False


def get_resident_data(resident_name: str, year: str = None):
    """Return reimbursement summary for a resident from the unified DB.

    Returns None if the person can't be resolved. Else dict with keys:
      name, cls, email, txns (each with date, description, amount, account,
      academic_year), by_account, grand_total, gme_used, gme_remaining, gme_pct,
      years (ordered list of academic years present), grouped_txns (dict ay->list),
      requested_year (normalized or None=all), per_year_totals.

    `year` filters to a single academic year; None/''/'all' returns all grouped.
    Split transactions appear as one row per fund (their allocation amount/account).
    """
    person = _resolve_person(resident_name)
    if not person:
        return None
    pid = person["id"]

    wanted = None
    if year and str(year).strip().lower() not in ("all", "any", "everything"):
        wanted = _normalize_ay(year)
        if wanted is None:
            wanted = str(year).strip()

    sql = (
        "SELECT s.date, s.academic_year, s.description, a.amount, a.account, a.status, p.cls "
        "FROM unified.reimb_allocations a "
        "JOIN unified.reimb_submissions s ON s.id = a.submission_id "
        "JOIN unified.reimb_persons p ON p.id = a.beneficiary_id "
        f"WHERE a.beneficiary_id = {int(pid)} AND a.status = 'approved' "
        "  AND s.is_deleted = false "
        "ORDER BY s.date, a.account;"
    )
    out = _psql(sql)
    txns = []
    by_account = defaultdict(float)

    now = datetime.now()
    ay_start_year = now.year if now.month >= 7 else now.year - 1
    ay_end_year = now.year + 1 if now.month >= 7 else now.year
    current_ay = f"{ay_start_year}-{str(ay_end_year)[-2:]}"

    gme_current_ay = 0.0

    for line in out.splitlines():
        if not line or "|" not in line:
            continue
        parts = line.split("|")
        if len(parts) < 6:
            continue
        date_s = (parts[0] or "")[:10]
        ay = (parts[1] or "").strip()
        desc = (parts[2] or "").strip()
        try:
            amt = float(parts[3] or 0)
        except ValueError:
            amt = 0.0
        acct_raw = parts[4] or ""
        status = (parts[5] or "").strip()

        if amt <= 0 or status != "approved":
            continue

        # AY filter
        if wanted and not _matches_ay(ay, wanted):
            continue

        label = _label(acct_raw)
        txns.append({
            "date": date_s,
            "description": desc,
            "amount": amt,
            "account": label,
            "academic_year": ay,
        })
        by_account[label] += amt
        if label == "GME Funds":
            if ay == current_ay:
                gme_current_ay += amt

    txns.sort(key=lambda t: (t["date"], t["account"]))

    # Group by academic year (newest first). 'NO DATE'/blank AY bucket last.
    grouped = {}
    for t in txns:
        key = t["academic_year"] or "NO DATE"
        grouped.setdefault(key, []).append(t)
    def _ay_sort(k):
        if k == "NO DATE":
            return (0, "")
        m = re.match(r"^(\d{4})", k)
        return (1, m.group(1)) if m else (1, k)
    ordered_years = sorted(grouped.keys(), key=_ay_sort, reverse=True)
    grouped_txns = {k: grouped[k] for k in ordered_years}

    per_year_totals = {k: round(sum(t["amount"] for t in v), 2) for k, v in grouped_txns.items()}

    # GME cap box: if filtered to a specific year, show that year's GME spend,
    # otherwise the current academic year's GME spend ($1,250 annual cap per AY).
    if wanted and _normalize_ay(wanted):
        gme_for_cap = sum(float(t["amount"]) for t in txns if t["account"] == "GME Funds")
    else:
        gme_for_cap = gme_current_ay

    remaining = max(0.0, GME_CAP - gme_for_cap)
    pct = min(100.0, round((gme_for_cap / GME_CAP) * 100.0, 1))

    return {
        "name": person["name"],
        "cls": person.get("cls", ""),
        "email": person.get("email", ""),
        "txns": txns,
        "by_account": dict(by_account),
        "grand_total": round(sum(t["amount"] for t in txns), 2),
        "gme_used": round(gme_for_cap, 2),
        "gme_remaining": round(remaining, 2),
        "gme_pct": pct,
        "academic_year_label": current_ay,
        "requested_year": (wanted if (year and str(year).strip().lower() not in ("all", "any", "everything")) else None),
        "years": ordered_years,
        "grouped_txns": grouped_txns,
        "per_year_totals": per_year_totals,
    }


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--resident", required=True)
    a = ap.parse_args()
    d = get_resident_data(a.resident)
    if not d:
        print("NOT_FOUND")
        sys.exit(1)
    print(f"name: {d['name']}  cls: {d['cls']}")
    print(f"grand_total: {d['grand_total']}  gme_used: {d['gme_used']}  gme_remaining: {d['gme_remaining']} ({d['gme_pct']}%)")
    for t in d["txns"]:
        print(f"  {t['date']}  {t['account']:<18}  {t['amount']:>9.2f}  {t['description'][:45]}")
