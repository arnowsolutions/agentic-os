# Arnow Solutions — Portfolio System

Voice notes in, living portfolio report out.

## What this is

You send me a voice note about a project. I transcribe it, file it, and update
your portfolio report. The report tracks every project you've given me,
organized by category, each with the three things you asked for:

1. **Why it was created**
2. **What problem it solved**
3. **What's cool about it**

## Folder map (browsable)

```
data/portfolio/
├── notes/       ← every voice note you send, transcribed, one file each
├── projects/    ← one structured file per project (the report is built from these)
├── audio/       ← the original audio, archived
└── reports/
    └── PORTFOLIO-REPORT.md   ← the living report — always current
```

## How to use it

**Send a voice note.** Just talk. Tell me the project, why you built it, what
it fixed, and what you think is cool about it. I'll handle the rest.

**Send a text note.** Same thing, typed.

**Ask for the report.** Say "show me the portfolio" and I'll give you the
current state of every project you've given me, plus which ones still have
gaps.

## Commands (for me)

```bash
# Transcribe a voice note and file it
python3 portfolio_note.py --audio /path/to/note.ogg --project "Project Name"

# Save a text note directly
python3 portfolio_note.py --text "..." --project "Project Name"

# List everything on file
python3 portfolio_note.py --list-notes
python3 portfolio_note.py --list-projects

# Rebuild the report
python3 portfolio_report.py

# Coverage check — which projects are missing which sections
python3 portfolio_report.py --stats
```

## Adding a project by hand

Drop a file in `projects/` like this:

```markdown
---
name: Project Name
category: Client Work          # or Personal Tools, Healthcare, Experiments…
status: live                   # live | shipped | in-progress | archived
tech: Python, FastAPI
url: https://…
---

# Project Name

## Why it was created

…

## What problem it solved

…

## What's cool about it

…
```

Then run `python3 portfolio_report.py` and it appears in the report.

## Notes on transcription

Transcription runs **locally** with faster-whisper (small model). Nothing is
sent to a cloud API — your audio stays on the box. Model size can be
overridden with `PF_WHISPER_SIZE` (tiny / base / small / medium).
