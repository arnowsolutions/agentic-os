#!/usr/bin/env python3
"""
Letterhead letters — fill the department's own Word letterhead template.

Hard rule: NEVER rebuild the letterhead. The department's .docx already carries
the Montefiore/Einstein banner (in the header), the department block, and
Dr. Sankin's signature + credential block. This module copies that file and
writes only the body content between the ``Date:`` line and the ``Thank You``
closing, so the letterhead and signature come through untouched.

Deliberately stdlib-only (zipfile + re): the Agentic OS container has no
python-docx, and adding a dependency to a running service for this is not
worth it. Nothing outside document.xml is modified -- every other part of the
.docx is copied byte-for-byte.

Templates live in ``data/letter_templates/*.json`` (letter body + placeholders),
the .docx letterhead lives in ``data/letterhead/``.

Usage:
    python3 letterhead_letters.py --list-years
    python3 letterhead_letters.py --exam-year 2027 [--out DIR]
    python3 letterhead_letters.py --template abu-chief-confirmation \
        --name "John Hill" --set exam_year=2027 --set start_year=2022 --out /tmp
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import zipfile
from datetime import date, datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BASE_DIR / "data" / "letter_templates"
LETTERHEAD_DIR = BASE_DIR / "data" / "letterhead"
LETTERS_DIR = BASE_DIR / "data" / "letters"

DOCUMENT_PART = "word/document.xml"

# one <w:p ...>...</w:p> (paragraphs never nest, so a non-greedy match is safe;
# <w:pPr> can't match because the next char after "w:p" must be space or ">")
_P_RE = re.compile(rb"<w:p(?:\s[^>]*)?/>|<w:p(?:\s[^>]*)?>.*?</w:p>", re.S)
_T_RE = re.compile(rb"(<w:t(?:\s[^>]*)?>)(.*?)(</w:t>)", re.S)


# ─────────────────────────── docx plumbing ───────────────────────────

def _text_of(par: bytes) -> str:
    return "".join(m.group(2).decode("utf-8", "replace") for m in _T_RE.finditer(par))


def _set_last_text(par: bytes, text: str) -> bytes:
    """Replace the content of the last <w:t> in a paragraph (keeps formatting)."""
    matches = list(_T_RE.finditer(par))
    if not matches:
        raise ValueError("paragraph has no <w:t> to write into")
    m = matches[-1]
    escaped = (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                   .encode("utf-8"))
    return par[:m.start(2)] + escaped + par[m.end(2):]


def _is_non_bold(par: bytes) -> bool:
    """True when the paragraph's run properties carry no <w:b/> (i.e. not bold)."""
    runs = re.findall(rb"<w:r(?:\s[^>]*)?>.*?</w:r>", par, re.S)
    if not runs:
        return False
    return b"<w:b/>" not in runs[0] and b'<w:b ' not in runs[0]


def _locate_parts(doc: bytes):
    """Return (paras, date_idx, thankyou_idx, fmt_idx) for the letterhead template."""
    paras = [m for m in _P_RE.finditer(doc)]
    texts = [_text_of(m.group(0)).strip() for m in paras]

    date_idx = next((i for i, t in enumerate(texts) if t.startswith("Date:")), None)
    thank_idx = next((i for i, t in enumerate(texts) if t == "Thank You"), None)
    if date_idx is None or thank_idx is None or thank_idx <= date_idx:
        raise ValueError("template does not look like the department letterhead "
                         "(expected a 'Date:' paragraph before a 'Thank You' paragraph)")
    # a non-bold paragraph in the closing block supplies the body formatting;
    # prefer one whose first run actually carries text (some carry a lone <w:br/>)
    def _first_run_has_text(par: bytes) -> bool:
        m = re.search(rb"<w:r(?:\s[^>]*)?>.*?</w:r>", par, re.S)
        return bool(m and b"<w:t" in m.group(0))

    fmt_idx = next((i for i in range(thank_idx, len(paras))
                    if _is_non_bold(paras[i].group(0)) and _first_run_has_text(paras[i].group(0))),
                   None)
    if fmt_idx is None:
        fmt_idx = next((i for i in range(thank_idx, len(paras)) if _is_non_bold(paras[i].group(0))), None)
    if fmt_idx is None:
        raise ValueError("no non-bold body paragraph found in the closing block")
    return paras, date_idx, thank_idx, fmt_idx


def _strip_break_runs(par: bytes) -> bytes:
    """Drop runs that contribute no text (e.g. a stray <w:br/>).

    The closing block contains a paragraph with a leading manual line break;
    cloning it verbatim made every inserted line render on two lines. Only
    text-bearing runs are wanted from the formatting source.
    """
    runs = list(re.finditer(rb"<w:r(?:\s[^>]*)?>.*?</w:r>", par, re.S))
    for m in reversed(runs):
        if b"<w:t" not in m.group(0):
            par = par[:m.start()] + par[m.end():]
    return par


def _keep_only_text_run(par: bytes) -> bytes:
    """Reduce a paragraph to a single run: the one carrying <w:t>."""
    runs = list(re.finditer(rb"<w:r(?:\s[^>]*)?>.*?</w:r>", par, re.S))
    keep = next((m for m in runs if b"<w:t" in m.group(0)), None)
    if keep is None:
        raise ValueError("paragraph has no text-bearing run")
    return par[:keep.start()] + keep.group(0) + par[keep.end():]


def fill_letterhead(paragraphs, out_path, template_docx=None, letter_date=None):
    """Write a filled copy of the letterhead template.

    paragraphs: list[str] -- the letter body; "" renders as a blank line.
    Returns the output path.
    """
    template_docx = Path(template_docx or (LETTERHEAD_DIR / DEFAULT_LETTERHEAD))
    if not template_docx.exists():
        raise FileNotFoundError(f"letterhead template not found: {template_docx}")

    if letter_date is None:
        letter_date = date.today()
    if isinstance(letter_date, str):
        date_text = letter_date
    else:
        date_text = f"{letter_date.month}/{letter_date.day}/{letter_date.year}"

    with zipfile.ZipFile(template_docx) as z:
        doc = z.read(DOCUMENT_PART)
        others = [(i, z.read(i.filename)) for i in z.infolist() if i.filename != DOCUMENT_PART]
        infos = [i for i in z.infolist() if i.filename != DOCUMENT_PART]

    paras, date_idx, thank_idx, fmt_idx = _locate_parts(doc)
    date_p = _set_last_text(paras[date_idx].group(0), " " + date_text)
    # the formatting source must be break-free and reduced to its single text run
    fmt_p = _keep_only_text_run(_strip_break_runs(paras[fmt_idx].group(0)))

    filled = []
    for text in paragraphs:
        filled.append(_set_last_text(fmt_p, text))
    filled_joined = b"".join(filled)

    # splice: keep everything before the Date paragraph (header spacers) and
    # everything from "Thank You" onward (closing + signature + sectPr) verbatim
    new_doc = (doc[:paras[date_idx].start()] + date_p + filled_joined
               + doc[paras[thank_idx].start():])

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        for info, data in zip(infos, [d for _, d in others]):
            z.writestr(info, data)
        z.writestr(DOCUMENT_PART, new_doc)
    return out_path


# ─────────────────────────── template registry ───────────────────────────

DEFAULT_LETTERHEAD = "Residency_Program_Letterhead_-_Alex_Sankin.docx"


def list_templates():
    out = []
    if TEMPLATE_DIR.exists():
        for f in sorted(TEMPLATE_DIR.glob("*.json")):
            try:
                t = json.loads(f.read_text())
            except Exception:
                continue
            out.append(t)
    return out


def load_template(template_id: str):
    path = TEMPLATE_DIR / f"{template_id}.json"
    if not path.exists():
        candidates = [t for t in list_templates() if t.get("id") == template_id]
        if not candidates:
            raise FileNotFoundError(f"no letter template {template_id!r} in {TEMPLATE_DIR}")
        return candidates[0]
    return json.loads(path.read_text())


def render_template(template: dict, fields: dict):
    """Substitute {placeholders} and return the paragraph list."""
    rendered = []
    for line in template.get("content", []):
        try:
            rendered.append(line.format(**fields) if "{" in line else line)
        except KeyError as e:
            raise ValueError(f"template placeholder {e} has no value; "
                             f"available: {sorted(fields)}") from None
    return rendered


def build_letter(template_id: str, fields: dict, out_path=None, letter_date=None):
    t = load_template(template_id)
    letterhead = t.get("letterhead_docx", f"data/letterhead/{DEFAULT_LETTERHEAD}")
    docx = BASE_DIR / letterhead
    if out_path is None:
        safe = re.sub(r"[^A-Za-z0-9]+", "_", fields.get("name", "letter")).strip("_")
        out_path = LETTERS_DIR / f"{template_id}_{safe}.docx"
    return fill_letterhead(render_template(t, fields), out_path,
                           template_docx=docx, letter_date=letter_date)


# ─────────────────────────── roster lookup ───────────────────────────

def _db_conn():
    """psycopg2 connection to the canonical postgres DB (unified schema)."""
    import psycopg2
    pw = os.environ.get("POSTGRES_PASSWORD", "")
    if not pw:
        for env_path in (BASE_DIR / ".env", Path("/workspace/projects/unified/app/.env")):
            try:
                for line in Path(env_path).read_text().splitlines():
                    if line.strip().startswith("POSTGRES_PASSWORD="):
                        pw = line.strip().split("=", 1)[1].strip()
                        break
            except Exception:
                continue
            if pw:
                break
    for host in ("172.16.3.1", "127.0.0.1", "localhost"):
        try:
            return psycopg2.connect(host=host, port=5432, dbname="postgres",
                                    user="postgres", password=pw or None, connect_timeout=4)
        except Exception:
            continue
    return None


def find_chiefs(exam_year=None):
    """Chief residents from the canonical store.

    `unified.chief_meeting_attendees` carries the explicit role; resident facts
    (name, pgy, graduation year) come from `public.contacts`. `exam_year`
    filters to the cohort graduating that June -- i.e. the ones sitting the
    Qualifying exam that year. With no exam_year, returns the current chiefs.
    """
    conn = _db_conn()
    if not conn:
        return []
    try:
        cur = conn.cursor()
        sql = """
            SELECT c.first_name, c.last_name, c.email, c.pgy,
                   c.graduation_year, c.program_start
            FROM unified.chief_meeting_attendees a
            JOIN public.contacts c ON lower(c.email) = lower(a.email)
            WHERE a.role = 'chief'
        """
        params = []
        if exam_year:
            sql += " AND c.graduation_year = %s"
            params.append(str(exam_year))
        sql += " ORDER BY c.last_name, c.first_name"
        cur.execute(sql, params)
        rows = cur.fetchall()
        cur.close()
        conn.close()
    except Exception:
        return []
    chiefs = []
    for first, last, email, pgy, grad, start in rows:
        name = f"{first or ''} {last or ''}".strip()
        # staff/CRM sometimes stores the whole name in first_name
        if not last and " " in (first or ""):
            name = first
        # drop parenthetical nicknames for formal Board correspondence
        # ("So Yeon (Jen) Pak" -> "So Yeon Pak")
        name = re.sub(r"\s*\([^)]*\)", "", name).strip()
        name = re.sub(r"\s+", " ", name)
        chiefs.append({
            "name": name,
            "last": (last or name.split()[-1]),
            "email": email or "",
            "pgy": (pgy or "").replace("PG-", "PGY-"),
            "exam_year": int(grad) if grad else None,
            "start_year": int(start) if start else None,
        })
    return chiefs


def chief_years():
    conn = _db_conn()
    if not conn:
        return []
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT c.graduation_year
            FROM unified.chief_meeting_attendees a
            JOIN public.contacts c ON lower(c.email) = lower(a.email)
            WHERE a.role = 'chief' AND c.graduation_year IS NOT NULL
            ORDER BY c.graduation_year
        """)
        years = [int(r[0]) for r in cur.fetchall() if str(r[0]).isdigit()]
        cur.close()
        conn.close()
        return years
    except Exception:
        return []


def generate_chief_letters(exam_year=None, out_dir=None, letter_date=None):
    """Build one confirmation letter per chief resident. Returns a list of dicts."""
    chiefs = find_chiefs(exam_year)
    if not chiefs:
        return []
    out_dir = Path(out_dir or LETTERS_DIR)
    produced = []
    for c in chiefs:
        fields = {
            "name": c["name"],
            "last": c["last"],
            "exam_year": c["exam_year"] or exam_year,
            "start_year": c["start_year"] or "",
        }
        safe = re.sub(r"[^A-Za-z0-9]+", "_", c["name"]).strip("_")
        path = fill_letterhead(
            render_template(load_template("abu-chief-confirmation"), fields),
            out_dir / f"ABU_Chief_Resident_Confirmation_{safe}_{fields['exam_year']}.docx",
            template_docx=LETTERHEAD_DIR / DEFAULT_LETTERHEAD,
            letter_date=letter_date,
        )
        produced.append({**c, "file": path.name, "path": str(path)})
    return produced


# ─────────────────────────── CLI ───────────────────────────

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--template", default="abu-chief-confirmation")
    ap.add_argument("--exam-year", type=int)
    ap.add_argument("--name", help="render a single letter for this name")
    ap.add_argument("--set", action="append", default=[], metavar="KEY=VALUE",
                    help="template field (repeatable)")
    ap.add_argument("--out", help="output directory")
    ap.add_argument("--list-years", action="store_true", help="exam years with chief data")
    args = ap.parse_args()

    if args.list_years:
        print("chief cohorts:", chief_years())
        for c in find_chiefs():
            print(f"  {c['name']:<24} {c['pgy']:<6} grad {c['exam_year']}  start {c['start_year']}")
        sys.exit(0)

    if args.name:
        fields = {"name": args.name, "last": args.name.split()[-1]}
        for kv in args.set:
            k, _, v = kv.partition("=")
            fields[k] = int(v) if v.isdigit() else v
        out = Path(args.out) / f"letter_{args.name.replace(' ', '_')}.docx" if args.out else None
        print("wrote", build_letter(args.template, fields, out))
    else:
        made = generate_chief_letters(args.exam_year, args.out)
        for m in made:
            print("wrote", m["path"])
        print(f"{len(made)} letter(s)")
