#!/usr/bin/env python3
"""
Arnow Solutions — Portfolio Report → HTML
==========================================
Builds a standalone, self-contained HTML page from the portfolio data so it can
be published to a public URL and viewed on a phone.

Usage:
    python3 portfolio_html.py                 # writes data/portfolio/reports/portfolio.html
    python3 portfolio_html.py --out /path.html
"""
import argparse
import html
import json
import re
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
PF = BASE / "data" / "portfolio"
NOTES = PF / "notes"
PROJECTS = PF / "projects"
REPORTS = PF / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)

REQUIRED = ["why", "problem", "cool"]
TITLES = {
    "why": "Why it was created",
    "problem": "What problem it solved",
    "cool": "What's cool about it",
}


def parse_frontmatter(text):
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    meta = {}
    for line in parts[1].strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, parts[2].strip()


def parse_project(path):
    raw = path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(raw)
    sections, current, buf = {}, None, []
    for line in body.splitlines():
        if line.startswith("## "):
            if current:
                sections[current] = "\n".join(buf).strip()
            title = line[3:].strip().lower()
            current = None
            for key, heading in TITLES.items():
                if key in title or heading.lower() in title:
                    current = key
                    break
            if current is None:
                current = title
            buf = []
        elif line.startswith("# "):
            continue
        else:
            buf.append(line)
    if current:
        sections[current] = "\n".join(buf).strip()
    return {
        "name": meta.get("name") or path.stem.replace("-", " ").title(),
        "category": meta.get("category", "Uncategorized"),
        "status": meta.get("status", "shipped"),
        "url": meta.get("url", ""),
        "tech": meta.get("tech", ""),
        "sections": sections,
    }


def md_to_html(text):
    """Tiny markdown → HTML: paragraphs + inline emphasis."""
    if not text:
        return ""
    out = []
    for para in re.split(r"\n\s*\n", text.strip()):
        p = html.escape(para.strip()).replace("\n", " ")
        p = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", p)
        p = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", p)
        p = re.sub(r"`(.+?)`", r"<code>\1</code>", p)
        out.append(f"<p>{p}</p>")
    return "\n".join(out)


def build(out_path: Path):
    projects = [parse_project(p) for p in sorted(PROJECTS.glob("*.md"))]
    note_count = len(list(NOTES.glob("*.md")))

    by_cat = {}
    for p in projects:
        by_cat.setdefault(p["category"], []).append(p)

    complete = sum(
        1 for p in projects
        if all(p["sections"].get(k, "").strip() for k in REQUIRED)
    )
    now = datetime.now().strftime("%B %d, %Y")

    nav = "".join(
        f'<a class="chip" href="#{html.escape(cat).lower().replace(" ", "-")}">'
        f'{html.escape(cat)}</a>'
        for cat in sorted(by_cat, key=str.lower)
    )

    cards = []
    for cat in sorted(by_cat, key=str.lower):
        cards.append(
            f'<h2 id="{html.escape(cat).lower().replace(" ", "-")}">'
            f'{html.escape(cat)}</h2>'
        )
        for p in sorted(by_cat[cat], key=lambda x: x["name"].lower()):
            ok = all(p["sections"].get(k, "").strip() for k in REQUIRED)
            dot = "done" if ok else "partial"
            meta_bits = []
            if p["status"]:
                meta_bits.append(f'<span class="tag">{html.escape(p["status"])}</span>')
            if p["tech"]:
                meta_bits.append(f'<span class="tag ghost">{html.escape(p["tech"])}</span>')
            if p["url"]:
                u = html.escape(p["url"])
                meta_bits.append(f'<span class="tag ghost">{u}</span>')

            body = []
            for k in REQUIRED:
                txt = p["sections"].get(k, "").strip()
                body.append(
                    f'<div class="sec"><h4>{TITLES[k]}</h4>'
                    f'{md_to_html(txt) if txt else "<p class=\'empty\'>Not captured yet.</p>"}'
                    f"</div>"
                )

            cards.append(f"""
<article class="card">
  <header>
    <span class="status {dot}" aria-hidden="true"></span>
    <h3>{html.escape(p['name'])}</h3>
  </header>
  <div class="meta">{' '.join(meta_bits)}</div>
  <div class="body">{''.join(body)}</div>
</article>""")

    if not projects:
        cards.append('<p class="empty">No projects documented yet.</p>')

    doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Arnow Solutions — Portfolio</title>
<style>
  :root {{
    --bg:#0d1117; --panel:#161b22; --panel-2:#1c2230; --line:#2a3444;
    --ink:#e6edf3; --muted:#8b98a9; --accent:#003da5; --accent-2:#4c8dff;
    --done:#2ea043; --partial:#d29922;
  }}
  * {{ box-sizing:border-box; }}
  body {{
    margin:0; background:var(--bg); color:var(--ink);
    font:16px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,sans-serif;
    -webkit-font-smoothing:antialiased;
  }}
  .wrap {{ max-width:960px; margin:0 auto; padding:32px 20px 80px; }}
  header.top {{ border-bottom:1px solid var(--line); padding-bottom:24px; margin-bottom:28px; }}
  .eyebrow {{
    text-transform:uppercase; letter-spacing:.14em; font-size:11px;
    color:var(--accent-2); font-weight:700; margin:0 0 10px;
  }}
  h1 {{ font-size:clamp(26px,5vw,40px); line-height:1.15; margin:0 0 12px; letter-spacing:-.02em; }}
  .sub {{ color:var(--muted); font-size:15px; margin:0; }}
  .stats {{ display:flex; gap:22px; flex-wrap:wrap; margin-top:20px; }}
  .stat b {{ display:block; font-size:22px; color:var(--ink); }}
  .stat span {{ font-size:12px; color:var(--muted); text-transform:uppercase; letter-spacing:.08em; }}
  .chips {{ display:flex; gap:8px; flex-wrap:wrap; margin:24px 0 8px; }}
  .chip {{
    border:1px solid var(--line); background:var(--panel); color:var(--ink);
    padding:7px 14px; border-radius:999px; font-size:13px; text-decoration:none;
  }}
  .chip:hover {{ border-color:var(--accent-2); }}
  h2 {{
    font-size:13px; text-transform:uppercase; letter-spacing:.14em;
    color:var(--muted); margin:40px 0 16px; padding-bottom:10px;
    border-bottom:1px solid var(--line);
  }}
  .card {{
    background:var(--panel); border:1px solid var(--line);
    border-radius:14px; padding:22px 22px 6px; margin-bottom:16px;
  }}
  .card header {{ display:flex; align-items:center; gap:12px; }}
  .card h3 {{ margin:0; font-size:20px; letter-spacing:-.01em; }}
  .status {{ width:9px; height:9px; border-radius:50%; flex:none; }}
  .status.done {{ background:var(--done); box-shadow:0 0 0 3px rgba(46,160,67,.15); }}
  .status.partial {{ background:var(--partial); box-shadow:0 0 0 3px rgba(210,153,34,.15); }}
  .meta {{ display:flex; gap:8px; flex-wrap:wrap; margin:12px 0 4px; }}
  .tag {{
    font-size:11px; text-transform:uppercase; letter-spacing:.08em;
    background:rgba(76,141,255,.12); color:var(--accent-2);
    padding:4px 9px; border-radius:6px; font-weight:600;
  }}
  .tag.ghost {{ background:var(--panel-2); color:var(--muted); text-transform:none; letter-spacing:0; }}
  .sec {{ margin:18px 0; }}
  .sec h4 {{
    margin:0 0 6px; font-size:11px; text-transform:uppercase;
    letter-spacing:.12em; color:var(--accent-2); font-weight:700;
  }}
  .sec p {{ margin:0 0 10px; color:#c9d4e0; }}
  .empty {{ color:var(--muted); font-style:italic; }}
  code {{ background:var(--panel-2); padding:1px 5px; border-radius:4px; font-size:.9em; }}
  footer {{
    margin-top:56px; padding-top:20px; border-top:1px solid var(--line);
    color:var(--muted); font-size:12px;
  }}
  @media (prefers-color-scheme: light) {{
    :root {{
      --bg:#f7f8fa; --panel:#ffffff; --panel-2:#eef1f6; --line:#dfe4ec;
      --ink:#111823; --muted:#5c6a7d;
    }}
    .sec p {{ color:#2c3746; }}
  }}
</style>
</head>
<body>
<div class="wrap">
  <header class="top">
    <p class="eyebrow">Arnow Solutions</p>
    <h1>Portfolio</h1>
    <p class="sub">Every project, what it was built for, what it fixed, and what makes it worth a look.</p>
    <div class="stats">
      <div class="stat"><b>{len(projects)}</b><span>Projects</span></div>
      <div class="stat"><b>{complete}</b><span>Fully documented</span></div>
      <div class="stat"><b>{note_count}</b><span>Voice notes</span></div>
      <div class="stat"><b>{now}</b><span>Updated</span></div>
    </div>
    <nav class="chips">{nav}</nav>
  </header>
  {''.join(cards)}
  <footer>Built from voice notes on the Agentic OS · regenerated automatically</footer>
</div>
</body>
</html>"""

    out_path.write_text(doc, encoding="utf-8")
    return out_path, len(projects), complete, note_count


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(REPORTS / "portfolio.html"))
    args = ap.parse_args()
    p, n, c, notes = build(Path(args.out))
    print(json.dumps({"ok": True, "html": str(p), "projects": n,
                      "complete": c, "notes": notes}, indent=2))


if __name__ == "__main__":
    main()
