#!/usr/bin/env python3
"""
Grand Rounds Single Source of Truth Sync (merge / backfill-only).

CANONICAL source of truth:  urology_qgenda.grand_rounds_schedule  (public schema)
   - This is the table that outlook_deeplink_generator.py (the main Friday
     Grand Rounds deeplink/ics sender) reads as its FIRST choice.

Merge rule (per field, comparing canonical DB -> downstream target):
    * target blank            -> copy canonical value
    * target populated, !=    -> canonical wins (overwrite target)
    * canonical blank (target has data) -> KEEP target (never lose data to a blank)

Downstream targets synced FROM canonical (derived, never the source):
   1) unified.grand_rounds  (postgres DB, unified schema)  -> Unified Platform display
   2) dashboard/pages/grand-rounds.js GR_DATA array        -> Agentic OS dashboard + legacy senders

Usage (run on the VPS so psql + the app .env are available):
    python3 sync_grand_rounds_single_source.py            # dry-run (shows changes)
    python3 sync_grand_rounds_single_source.py --apply    # apply
"""

import os, re, sys, subprocess
from pathlib import Path

CANONICAL_DB = "urology_qgenda"
DOWNSTREAM_DB = "postgres"
DOWNSTREAM_TABLE = "unified.grand_rounds"
GR_JS_FILE = "/workspace/agentic-os/dashboard/pages/grand-rounds.js"

APPLY = "--apply" in sys.argv

# Field mapping canonical -> unified.
# SAFE set: only sync the genuine AGENDA TITLE fields (mon_topic, gr7, gr8) and
# backfill-only for the "notes" column. Do NOT sync month/mon_date/attending/resident —
# the canonical (urology_qgenda) table has noisy/typo'd values there (e.g. attending=':(',
# mon_topic double-spaces, notes '4-9' typos) that would corrupt unified's cleaner data.
UNI_MAP = {
    # target_field: (canonical_field, unified_field)
    "mon_topic": ("mon_topic", "mon_topic"),
    "fri_gr7": ("gr_7_8", "fri_gr7"),
    "fri_gr8": ("gr_8_9", "fri_gr8"),
    "notes": ("notes", "notes"),
}

# Fields that are backfill-ONLY (never overwrite a populated downstream value).
# notes is backfill-only because canonical has punctuation typos ('4-9') while
# unified's '4/9' is correct — we only fill empty notes, never overwrite.
BACKFILL_ONLY = {"notes"}


def get_pw():
    for env_path in ["/workspace/agentic-os/.env",
                     "/workspace/projects/unified/app/.env"]:
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("POSTGRES_PASSWORD") and "=" in line:
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get("POSTGRES_PASSWORD", "")


def psql(db, sql):
    env = dict(os.environ); env["PGPASSWORD"] = get_pw()
    r = subprocess.run(["psql","-h","127.0.0.1","-p","5432","-U","postgres",
                        "-d",db,"-t","-A","-F","|","-c",sql],
                       capture_output=True, text=True, env=env, timeout=60)
    if r.returncode != 0:
        raise RuntimeError(f"psql {db}: {r.stderr.strip()}")
    return r.stdout.strip()


def esc(v):
    v = (v or "").strip()
    if not v:
        return "NULL"
    return "'" + v.replace("'", "''") + "'"


def fetch_canonical():
    sql = ("SELECT id, month, mon_date, mon_topic, resident, attending, "
           "fri_date, gr_7_8, gr_8_9, notes FROM grand_rounds_schedule "
           "WHERE fri_date IS NOT NULL ORDER BY fri_date")
    out = {}
    for line in psql(CANONICAL_DB, sql).splitlines():
        p = line.split("|")
        if len(p) < 10:
            continue
        fri = p[6].strip()
        if not re.match(r"\d{4}-\d{2}-\d{2}", fri):
            continue
        out[fri] = {
            "id": p[0].strip(), "month": p[1].strip(), "mon_date": p[2].strip(),
            "mon_topic": p[3].strip(), "resident": p[4].strip(),
            "attending": p[5].strip(), "fri_date": fri, "gr_7_8": p[7].strip(),
            "gr_8_9": p[8].strip(), "notes": p[9].strip()
        }
    return out


def fetch_unified():
    sql = (f"SELECT id, month, mon_date, mon_topic, mon_resident, mon_attending, "
           f"fri_date, fri_gr7, fri_gr8, notes FROM {DOWNSTREAM_TABLE} "
           f"WHERE fri_date IS NOT NULL ORDER BY fri_date")
    out = {}
    for line in psql(DOWNSTREAM_DB, sql).splitlines():
        p = line.split("|")
        if len(p) < 10:
            continue
        fri = p[6].strip()
        if not re.match(r"\d{4}-\d{2}-\d{2}", fri):
            continue
        out[fri] = {
            "id": p[0].strip(), "month": p[1].strip(), "mon_date": p[2].strip(),
            "mon_topic": p[3].strip(), "mon_resident": p[4].strip(),
            "mon_attending": p[5].strip(), "fri_date": fri, "fri_gr7": p[7].strip(),
            "fri_gr8": p[8].strip(), "notes": p[9].strip()
        }
    return out


def merge_plan(canon, target, direction="unified"):
    """Return list of (fri, {target_field: new_value}) per merge rule."""
    plan = []
    for fri, c in canon.items():
        t = target.get(fri)
        if t is None:
            # missing in target -> insert new row from canonical
            plan.append((fri, None)); continue
        changes = {}
        for tf, (cf, uf) in UNI_MAP.items():
            if direction == "js":
                continue  # handled separately
            cv = (c.get(cf) or "").strip()
            tv = (t.get(uf) or "").strip()
            if cv == tv:
                continue
            if not cv:
                continue  # canonical blank -> keep target (backfill-only)
            if tf in BACKFILL_ONLY and tv:
                continue  # backfill-only field that's already populated -> keep target
            changes[uf] = cv  # canonical wins (incl. filling a blank)
        if changes:
            plan.append((fri, changes))
    return plan


def apply_unified(plan, canon):
    conn_sql = []
    for fri, changes in plan:
        if changes is None:
            c = canon[fri]
            sql = (f"INSERT INTO {DOWNSTREAM_TABLE} (id, month, mon_date, mon_topic, "
                   f"mon_resident, mon_attending, fri_date, fri_gr7, fri_gr8, notes, "
                   f"created_at, updated_at) VALUES ({esc(c['id'])}, {esc(c['month'])}, "
                   f"{esc(c['mon_date'])}, {esc(c['mon_topic'])}, {esc(c['resident'])}, "
                   f"{esc(c['attending'])}, {esc(c['fri_date'])}, {esc(c['gr_7_8'])}, "
                   f"{esc(c['gr_8_9'])}, {esc(c['notes'])}, NOW(), NOW())")
            psql(DOWNSTREAM_DB, sql)
            print(f"  INSERT unified {fri}")
        else:
            setp = ", ".join(f"{k} = {esc(v)}" for k, v in changes.items())
            sql = (f"UPDATE {DOWNSTREAM_TABLE} SET {setp}, updated_at = NOW() "
                   f"WHERE fri_date = '{fri}'")
            psql(DOWNSTREAM_DB, sql)
            print(f"  UPDATE unified {fri}: " + ", ".join(changes))


def js_plan(canon, js_rows):
    """Plan changes for JS GR_DATA array (backfill-only)."""
    js_by_fri = {}
    for row in js_rows:
        fri = str(row[7]) if len(row) > 7 else ""
        if re.match(r"\d{4}-\d{2}-\d{2}", fri):
            js_by_fri[fri] = row
    changes = []
    idx_cols = {"month":0,"mon_date":1,"mon_topic":2,"resident":3,"attending":4,
                "fri_gr7":8,"fri_gr8":9,"notes":10}
    for fri, c in canon.items():
        if fri in js_by_fri:
            row = js_by_fri[fri]
            dif = {}
            # map canonical field -> js col
            for canon_field, col in idx_cols.items():
                if canon_field in ("fb","mon_resident"):
                    col = {"fri_gr7":8,"fri_gr8":9}[canon_field] if canon_field in("fri_gr7","fri_gr8") else col
                cv = (c.get(canon_field) or "").strip()
                jv = (row[col] or "").strip() if col < len(row) else ""
                if cv and cv != jv:
                    dif[col] = cv
            if dif:
                changes.append((fri, row, dif))
    return changes


def js_apply(canon_ordered, js_rows, js_changes):
    # js_changes: list of (fri, row, {col:newval}); apply to rows in place, then rewrite file
    change_map = {}
    for fri, row, dif in js_changes:
        change_map[fri] = dif
    new_rows = []
    for row in js_rows:
        fri = str(row[7]) if len(row) > 7 else ""
        if fri in change_map:
            for col, val in change_map[fri].items():
                while len(row) <= col:
                    row.append("")
                row[col] = val
        new_rows.append(row)
    def q(s):
        return '"' + (s or "").replace('"','\\"') + '"'
    body = "\n".join("  [" + ", ".join(q(v) for v in r) + "]," for r in new_rows)
    with open(GR_JS_FILE) as f:
        src = f.read()
    m = re.search(r"(const\s+GR_DATA\s*=\s*\[)[\s\S]*?(\]\s*;)", src)
    if not m:
        raise RuntimeError("GR_DATA not found")
    new_src = src[:m.start(1)] + m.group(1) + "\n" + body + "\n" + m.group(2) + src[m.end(2):]
    with open(GR_JS_FILE, "w") as f:
        f.write(new_src)
    print(f"  Rewrote grand-rounds.js GR_DATA ({len(new_rows)} rows)")


def main():
    print(f"Mode: {'APPLY' if APPLY else 'DRY-RUN'}\n")
    canon = fetch_canonical()
    print(f"Canonical rows (urology_qgenda.grand_rounds_schedule): {len(canon)}")
    uni = fetch_unified()
    print(f"Downstream rows (unified.grand_rounds): {len(uni)}")

    plan = merge_plan(canon, uni)
    print("\n=== unified.grand_rounds merge plan (canonical -> unified) ===")
    if not plan:
        print("  (already in sync — nothing to change)")
    for fri, changes in plan:
        if changes is None:
            c = canon[fri]
            print(f"  INSERT {fri}: mon_topic='{c['mon_topic']}' gr7='{c['gr_7_8']}' gr8='{c['gr_8_9']}'")
        else:
            print(f"  UPDATE {fri}:")
            for k, v in changes.items():
                print(f"    {k} -> '{v}'")

    if not APPLY:
        print("\nDry-run only. Re-run with --apply to write changes.")
        return 0

    print("\n=== APPLYING ===")
    apply_unified(plan, canon)
    print("\nSync complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
