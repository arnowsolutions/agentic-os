#!/usr/bin/env python3
"""
Arnow Solutions — Portfolio Voice Note Intake
=============================================
Takes a voice note (audio file) or raw text, transcribes it locally with
faster-whisper, saves the note to data/portfolio/notes/, and prints structured
output the agent uses to update the portfolio report.

Usage:
    # Transcribe an audio file
    python3 portfolio_note.py --audio /path/to/note.ogg --project "Repo Vault"

    # Save a text note directly (no transcription)
    python3 portfolio_note.py --text "The repo vault was built because..." --project "Repo Vault"

    # List notes / projects
    python3 portfolio_note.py --list-notes
    python3 portfolio_note.py --list-projects

Output: JSON on stdout with the saved note path, transcript, and detected project.
"""
import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
PF = DATA / "portfolio"
NOTES = PF / "notes"
PROJECTS = PF / "projects"
AUDIO = PF / "audio"
REPORTS = PF / "reports"

for d in (NOTES, PROJECTS, AUDIO, REPORTS):
    d.mkdir(parents=True, exist_ok=True)

WHISPER_SIZE = os.environ.get("PF_WHISPER_SIZE", "small")


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def transcribe(audio_path: Path) -> tuple[str, str]:
    """Return (transcript_text, language) using local faster-whisper."""
    from faster_whisper import WhisperModel

    model = WhisperModel(WHISPER_SIZE, device="cpu", compute_type="int8")
    segments, info = model.transcribe(
        str(audio_path), beam_size=5, vad_filter=True
    )
    parts = []
    for seg in segments:
        parts.append(seg.text.strip())
    text = " ".join(p for p in parts if p)
    return text, getattr(info, "language", "en")


def known_projects() -> list[str]:
    """Projects discovered from projects/ filenames + a built-in seed list."""
    found = {p.stem.replace("-", " ") for p in PROJECTS.glob("*.md")}
    # Seed aliases so early notes still match before a project file exists.
    seeds = {
        "Repo Vault", "The Listening Room", "Master B Trading",
        "Nursing Video Archive", "Lesson Animation Studio", "Bluemonkee",
        "Ink & Ember", "Academy", "Progress Compass", "Unified Platform",
        "Interview Portal", "Big Reef CRM", "OR Schedule Pipeline",
        "Reimbursement Platform", "Call Out Line", "Vapi Voice Assistant",
        "Agentic OS", "Grand Rounds", "Movie Night",
    }
    return sorted(found | seeds, key=str.lower)


def guess_project(text: str) -> str | None:
    """Best-effort match of transcript to a known project by name overlap."""
    low = text.lower()
    best, best_score = None, 0
    for proj in known_projects():
        # Strip noise chars, require most words of the project name to appear
        words = [w for w in re.split(r"[^a-z0-9]+", proj.lower()) if len(w) > 2]
        if not words:
            continue
        hits = sum(1 for w in words if w in low)
        score = hits / len(words)
        if score > best_score and score >= 0.6:
            best, best_score = proj, score
    return best


def save_note(text: str, project: str | None, source: str, language: str = "en") -> Path:
    ts = datetime.now()
    stamp = ts.strftime("%Y-%m-%d_%H%M%S")
    proj_slug = slugify(project) if project else "unassigned"
    path = NOTES / f"{stamp}__{proj_slug}.md"
    body = f"""---
date: {ts.isoformat(timespec='seconds')}
project: {project or "unassigned"}
source: {source}
language: {language}
---

# Voice Note — {ts.strftime('%B %d, %Y %I:%M %p')}

{text.strip()}
"""
    path.write_text(body, encoding="utf-8")
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio", help="Path to an audio file to transcribe")
    ap.add_argument("--text", help="Raw text note (skips transcription)")
    ap.add_argument("--project", help="Project name this note belongs to")
    ap.add_argument("--list-notes", action="store_true")
    ap.add_argument("--list-projects", action="store_true")
    args = ap.parse_args()

    if args.list_projects:
        print(json.dumps({"projects": known_projects()}, indent=2))
        return
    if args.list_notes:
        notes = sorted(NOTES.glob("*.md"), reverse=True)
        out = []
        for n in notes:
            head = n.read_text(encoding="utf-8")[:400]
            m = re.search(r"^project:\s*(.+)$", head, re.M)
            d = re.search(r"^date:\s*(.+)$", head, re.M)
            out.append({
                "file": n.name,
                "project": (m.group(1).strip() if m else "?"),
                "date": (d.group(1).strip() if d else "?"),
            })
        print(json.dumps({"count": len(out), "notes": out}, indent=2))
        return

    transcript = ""
    language = "en"
    source = "text"

    if args.audio:
        src = Path(args.audio)
        if not src.exists():
            print(json.dumps({"ok": False, "error": f"audio not found: {src}"}))
            sys.exit(1)
        # Archive the original audio
        dest_audio = AUDIO / f"{datetime.now().strftime('%Y-%m-%d_%H%M%S')}_{src.name}"
        try:
            shutil.copy2(src, dest_audio)
        except Exception:
            dest_audio = src
        transcript, language = transcribe(dest_audio)
        source = f"audio:{src.name}"
    elif args.text:
        transcript = args.text
    else:
        print(json.dumps({"ok": False, "error": "provide --audio or --text"}))
        sys.exit(1)

    project = args.project or guess_project(transcript)
    note_path = save_note(transcript, project, source, language)

    print(json.dumps({
        "ok": True,
        "note_file": str(note_path),
        "project": project,
        "language": language,
        "source": source,
        "transcript": transcript,
        "chars": len(transcript),
    }, indent=2))


if __name__ == "__main__":
    main()
