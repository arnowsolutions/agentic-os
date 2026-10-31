#!/usr/bin/env python3
"""
Arnow Solutions — Portfolio Report Builder
==========================================
Reads every project file + voice note under data/portfolio/ and writes the
living report at data/portfolio/reports/PORTFOLIO-REPORT.md

Each project has three required narrative sections:
  - Why it was created
  - What problem it solved
  - What's cool about it

Usage:
    python3 portfolio_report.py            # build/refresh the report
    python3 portfolio_report.py --stats    # print coverage summary as JSON
"""
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
PF = BASE / "data" / "portfolio"
NOTES = PF / "notes"
PROJECTS = PF / "projects"
REPORTS = PF / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)

REQUIRED_SECTIONS = ["why", "problem", "cool"]

SECTION_TITLES = {
    "why": "Why it was created",
    "problem": "What problem it solved",
    "cool": "What's cool about it",
}


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Split YAML-ish frontmatter from the body (no yaml dep needed)."""
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


def parse_project(path: Path) -> dict:
    """Extract a project record from its markdown file."""
    raw = path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(raw)

    sections = {}
    current = None
    buf = []
    # Any heading (## X) starts a new block; we bucket by keyword match.
    for line in body.splitlines():
        if line.startswith("## "):
            if current:
                sections[current] = "\n".join(buf).strip()
            title = line[3:].strip().lower()
            current = None
            for key, heading in SECTION_TITLES.items():
                if key in title or heading.lower() in title:
                    current = key
                    break
            if current is None:
                current = title  # keep other sections (e.g. Stack, Links)
            buf = []
        elif line.startswith("# "):
            continue  # project title line
        else:
            buf.append(line)
    if current:
        sections[current] = "\n".join(buf).strip()

    return {
        "slug": path.stem,
        "name": meta.get("name") or path.stem.replace("-", " ").title(),
        "category": meta.get("category", "Uncategorized"),
        "status": meta.get("status", "shipped"),
        "url": meta.get("url", ""),
        "tech": meta.get("tech", ""),
        "file": path.name,
        "sections": sections,
    }


def collect_notes() -> list[dict]:
    out = []
    for n in sorted(NOTES.glob("*.md")):
        raw = n.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(raw)
        out.append({
            "file": n.name,
            "date": meta.get("date", ""),
            "project": meta.get("project", "unassigned"),
            "source": meta.get("source", ""),
            "body": body.strip(),
        })
    return out


def coverage(proj: dict) -> dict:
    """Which of the three required narrative sections are filled in?"""
    have = {}
    for k in REQUIRED_SECTIONS:
        txt = proj["sections"].get(k, "")
        have[k] = bool(txt) and len(txt) > 40
    have["complete"] = all(have[k] for k in REQUIRED_SECTIONS)
    return have


def build():
    projects = [parse_project(p) for p in sorted(PROJECTS.glob("*.md"))]
    notes = collect_notes()

    by_cat: dict[str, list[dict]] = {}
    for p in projects:
        by_cat.setdefault(p["category"], []).append(p)

    notes_by_project: dict[str, list[dict]] = {}
    for n in notes:
        notes_by_project.setdefault(n["project"], []).append(n)

    total = len(projects)
    complete = sum(1 for p in projects if coverage(p)["complete"])
    now = datetime.now().strftime("%B %d, %Y at %I:%M %p")

    L = []
    L.append("# Arnow Solutions — Portfolio Report")
    L.append("")
    L.append(f"*Last updated: {now}*")
    L.append("")
    L.append(f"**{total} project{'s' if total != 1 else ''} tracked** · "
             f"{complete} fully documented · "
             f"{len(notes)} voice note{'s' if len(notes) != 1 else ''} on file")
    L.append("")
    L.append("---")
    L.append("")

    if not projects:
        L.append("_No projects documented yet. Send a voice note about a project "
                 "and I'll add it here._")
        L.append("")

    for cat in sorted(by_cat, key=str.lower):
        L.append(f"## {cat}")
        L.append("")
        for p in sorted(by_cat[cat], key=lambda x: x["name"].lower()):
            cov = coverage(p)
            ready = "✔" if cov["complete"] else "◐"
            L.append(f"### {ready} {p['name']}")
            L.append("")
            bits = []
            if p["status"]:
                bits.append(f"**Status:** {p['status']}")
            if p["tech"]:
                bits.append(f"**Built with:** {p['tech']}")
            if p["url"]:
                bits.append(f"**Link:** {p['url']}")
            if bits:
                L.append(" · ".join(bits))
                L.append("")

            for key in REQUIRED_SECTIONS:
                title = SECTION_TITLES[key]
                txt = p["sections"].get(key, "").strip()
                L.append(f"**{title}**")
                L.append("")
                L.append(txt if txt else "_Not captured yet._")
                L.append("")

            pnotes = notes_by_project.get(p["name"], [])
            if pnotes:
                L.append(f"<sub>{len(pnotes)} note(s) on file</sub>")
                L.append("")
        L.append("")

    # Unassigned notes — surfaced so nothing gets lost
    unassigned = notes_by_project.get("unassigned", [])
    if unassigned:
        L.append("---")
        L.append("")
        L.append("## Not yet assigned to a project")
        L.append("")
        L.append(f"_{len(unassigned)} note(s) waiting to be placed._")
        L.append("")
        for n in sorted(unassigned, key=lambda x: x["date"], reverse=True)[:20]:
            first = n["body"].split("\n")[0][:160]
            L.append(f"- **{n['date'][:10]}** — {first}")
        L.append("")

    report_path = REPORTS / "PORTFOLIO-REPORT.md"
    report_path.write_text("\n".join(L), encoding="utf-8")
    return report_path, projects, notes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stats", action="store_true")
    args = ap.parse_args()

    path, projects, notes = build()

    if args.stats:
        stats = {
            "projects": len(projects),
            "notes": len(notes),
            "complete": sum(1 for p in projects if coverage(p)["complete"]),
            "by_category": {},
            "gaps": [],
        }
        for p in projects:
            stats["by_category"].setdefault(p["category"], 0)
            stats["by_category"][p["category"]] += 1
            cov = coverage(p)
            missing = [SECTION_TITLES[k] for k in REQUIRED_SECTIONS if not cov[k]]
            if missing:
                stats["gaps"].append({"project": p["name"], "missing": missing})
        print(json.dumps(stats, indent=2))
    else:
        print(json.dumps({
            "ok": True,
            "report": str(path),
            "projects": len(projects),
            "notes": len(notes),
        }, indent=2))


if __name__ == "__main__":
    main()
