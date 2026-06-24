# Recent Decisions

## 2026-05-17
- Created Agentic OS project structure
- 3-agent architecture: opencode (code) + Hermes (memory/channels) + Gemini CLI (research)
- Web dashboard only (no CLI dashboard) — FastAPI + vanilla JS SPA
- Maximum breadth skill set (all-in: DevOps, content, research, coding, productivity)
- Git auto-versioning enabled for brain/ and skills/

## 2026-06-24
- Vapi voice assistant now at V5: GPT-4o, full tool suite, new routing rules
- PH2 = Penthouse 2, a support-staff office location — NOT a call campus (distinct from Moses/Wakefield/Weiler)
- Location-roster source: urologyresidencyprogram@gmail.com Google Drive folder (synced via drive_sync module)
- Interim email policy: SCHEDULE_EMAIL_RECIPIENT env var (default: sfrasier@montefiore.org); go-live will switch to per-caller CRM email lookup
- New tools registered on assistant: staffAtLocation, emailSchedule, emailStaffRoster
- System prompt extracted to prompts/vapi_assistant_v5.md — both update_vapi_config.py and deploy_vapi_v5.py read from this single source of truth
- GET /api/vapi/data-health endpoint live — monitors all 5 data sources (call_schedule, qgenda, associates, location_rosters, google_auth) with status enum and next_action hints

## 2026-06-24 18:09:00 — Heartbeat Alert
- Agent 'opencode' is offline or not responding (binary not found in PATH)
- Agent 'hermes' is offline or not responding (binary not found in PATH)
- Agent 'gemini' is offline or not responding (binary not found in PATH)
