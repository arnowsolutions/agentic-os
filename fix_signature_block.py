#!/usr/bin/env python3
"""
One-off correction: replace the contact block under Dr. Sankin's signature in
the department letterhead template.

The as-received template carried the residency coordinator's cell (929-696-3195,
Shareef Frasier) as "Cell" and the program office number as "Office". The real
block, as supplied by the user, is:

    Montefiore Medical Center
    The University Hospital for Albert Einstein College of Medicine
    Montefiore Hutchinson Campus
    1250 Waters Place, Tower One, Penthouse
    Bronx, New York 10461
    347-842-1700 Office
    267-980-4606 Mobile
    917-962-5410 Fax

Only the paragraphs from "Montefiore Medical Center" (under the signature) to the
Fax line are touched -- the letterhead header, the signature image, and the title
lines above are left exactly as they are.

Usage: python3 fix_signature_block.py [--apply]
       (without --apply it writes next to the input as *.preview.docx)
"""
import re
import shutil
import sys
import zipfile
from pathlib import Path

SRC = Path("/workspace/agentic-os/data/letterhead/Residency_Program_Letterhead_-_Alex_Sankin.docx")
ORIG_DIR = SRC.parent / "originals"
ORIG = ORIG_DIR / (SRC.stem + ".as-received-2026-09-25" + SRC.suffix)

REAL_BLOCK = [
    "Montefiore Medical Center",
    "The University Hospital for Albert Einstein College of Medicine",
    "Montefiore Hutchinson Campus",
    "1250 Waters Place, Tower One, Penthouse",
    "Bronx, New York 10461",
    "347-842-1700 Office",
    "267-980-4606 Mobile",
    "917-962-5410 Fax",
]

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
P_RE = re.compile(rb"<w:p(?:\s[^>]*)?/>|<w:p(?:\s[^>]*)?>.*?</w:p>", re.S)
T_RE = re.compile(rb"(<w:t(?:\s[^>]*)?>)(.*?)(</w:t>)", re.S)


def text_of(par: bytes) -> str:
    return "".join(m.group(2).decode("utf-8", "replace") for m in T_RE.finditer(par)).strip()


def set_text(par: bytes, text: str) -> bytes:
    """Reduce the paragraph to one text run carrying `text` (keeps formatting)."""
    runs = list(re.finditer(rb"<w:r(?:\s[^>]*)?>.*?</w:r>", par, re.S))
    keep = next((m for m in runs if b"<w:t" in m.group(0)), None)
    if keep is None:
        raise ValueError("no text-bearing run")
    par = par[:keep.start()] + keep.group(0) + par[keep.end():]
    matches = list(T_RE.finditer(par))
    m = matches[-1]
    esc = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").encode()
    return par[: m.start(2)] + esc + par[m.end(2):]


def main(apply_changes: bool):
    if not ORIG.exists():
        ORIG_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SRC, ORIG)
        print("pristine original archived ->", ORIG)

    with zipfile.ZipFile(SRC) as z:
        doc = z.read("word/document.xml")
        infos = [i for i in z.infolist() if i.filename != "word/document.xml"]
        parts = [(i, z.read(i.filename)) for i in infos]

    paras = [m for m in P_RE.finditer(doc)]
    texts = [text_of(m.group(0)) for m in paras]

    sig_idx = next((i for i, t in enumerate(texts) if t.startswith("Alex Sankin")), None)
    if sig_idx is None:
        raise SystemExit("could not find the signature name paragraph")
    start = next((i for i in range(sig_idx, len(paras))
                  if texts[i].startswith("Montefiore Medical Center")), None)
    end = next((i for i in range(start, len(paras)) if texts[i].endswith("Fax")), None)
    if start is None or end is None:
        raise SystemExit("could not locate the contact block under the signature")

    print(f"replacing paragraphs {start}..{end}:")
    for i in range(start, end + 1):
        print(f"   OLD {texts[i]!r}")
    for line in REAL_BLOCK:
        print(f"   NEW {line!r}")

    # Styling: the original block has the institution name bold (para 34) and the
    # address/phone lines regular (para 36). Mirror that, otherwise every line
    # comes out bold and the generator loses its non-bold formatting source.
    bold_par = paras[start].group(0)

    def _non_bold_with_text(p: bytes) -> bool:
        runs = [m.group(0) for m in re.finditer(rb"<w:r(?:\s[^>]*)?>.*?</w:r>", p, re.S)]
        if not runs or b"<w:t" not in runs[0]:
            return False
        return not any(b"<w:b/>" in r or b"<w:b " in r for r in runs)

    plain_idx = next((i for i in range(start, end + 1) if _non_bold_with_text(paras[i].group(0))), None)
    if plain_idx is None:
        raise SystemExit("no regular-weight paragraph found in the block to use as the format source")
    plain_par = paras[plain_idx].group(0)
    print(f"format sources: bold<-para {start}, regular<-para {plain_idx}")

    new_paras = set_text(bold_par, REAL_BLOCK[0]) + \
        b"".join(set_text(plain_par, line) for line in REAL_BLOCK[1:])
    new_doc = doc[: paras[start].start()] + new_paras + doc[paras[end].end():]

    out = SRC if apply_changes else SRC.with_suffix(".preview.docx")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for info, data in parts:
            z.writestr(info, data)
        z.writestr("word/document.xml", new_doc)
    print("wrote", out)
    return out


if __name__ == "__main__":
    main("--apply" in sys.argv)
