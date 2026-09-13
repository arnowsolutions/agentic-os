---
date: 2026-09-12
project: agentic-os (AOS Hub)
total_ideas: 5
picked_up: 0
---

# Ideation: Agentic OS Hub — data sync, design & flow for an AI-generalist operations base

## Evidence gathered (on-disk audit, 2026-09-12)

- IA redesign PR1–9 landed today: 87 page modules, suites merged, 26 legacy redirects, emoji sweep done, launchpad home built (25 services in `data/launchpad.json`). **The skin/IA problem is solved; what remains is the data layer.**
- The real "pages not working" cause: `daily_sync.py` (cron) refreshes `data/sync_cache.db` at 09:01 daily with fresh QGenda / call-schedule / staff / GME tables — but **most dashboard endpoints still read frozen JSON snapshots** instead:
  - 81–96d stale: `gme_detail.json` (→ GME Detail), `notifications.json` (→ Compliance Overview), `pdf_archive.json` (→ Staff Schedule), `eval_forms.json`, `agent-routes.json` (→ Smart Router), `settings.json`, `goals.json` (EMPTY → Goals page blank)
  - 60–76d stale: `staff_schedule.json`, `calendar_events.json` (26d), `grand_rounds_*_progress.json`, `monday_sasp_progress.json`, `grand_rounds_send_log.json`
  - CRM/GME pages were rewired to the unified DB single-source, but the older JSON-backed duplicates remain live as suite tabs → same job, two doors with different data.
- Overview fragmentation: 9+ status/overview surfaces coexist — `dashboard` (Launchpad), `unified-dashboard`, `manager` (Command Center), `manager-command-center` (Staff CC), `system-overview`, `health`, `operations`, `agent-health`, `tools`.
- Sync-cache DB (`sync_cache.db`: qgenda_schedule, staff_directory, call_schedule, gme_residents) is consumed almost exclusively by the Vapi voice bridge — the dashboard barely touches it. The freshest data in the house serves the phone, not the hub.
- Live HTTP probing was not possible (session auth wall, 307); findings are from source + file mtimes, which is stronger evidence for "sync" than one response sample.

## Generated Ideas

### 1. SSOT rewiring — endpoints read the live stores, not frozen JSON
- **Effort:** Medium (1 session; per-endpoint swap to `sync_cache.db` / unified Postgres / Supabase + container restarts)
- **Benefit:** Kills the actual complaint. Calendar, Staff Schedule, GME, Grand Rounds, Compliance, Smart Router pages show real current data. Every merged suite tab and its old JSON page stop disagreeing with each other.
- **Risk:** Some JSON files carry fields the DB doesn't (manual annotations); a strict swap could regress those pages. Mitigate: merge DB-over-JSON, never pure replace. Auth allowlist pitfall applies to renamed paths.
- **Status:** pending
- **Next step:** ce-plan (endpoint-by-endpoint swap table)

### 2. Staleness badges + "Sync now" on every data-backed page
- **Effort:** Small (shared render helper in api.js + one `as_of` field per endpoint response)
- **Benefit:** Make-hidden-silence impossible: each page header shows "as of 2026-09-12 09:01 · sync_cache.db" vs "FROZEN snapshot — 81d". One button re-runs the existing sync script. User's stated hatred of silent failures and empty grids addressed structurally, and Data Gaps page becomes the system's watchdog home.
- **Risk:** Touches ~20 page files; keep to the stat-strip header so it doesn't balloon scope. If #1 lands first, some badges just turn green for free.
- **Status:** pending
- **Next step:** implement directly after #1 decision

### 3. Collapse 9 overview pages into 2 surfaces: Launchpad + Today
- **Effort:** Medium (mostly deletion-as-tabs + redirect entries; no new backend)
- **Benefit:** Dashboard = machine view (services, health dots, launch). New **Today** page = operator view (see #5). `system-overview`/`health`/`operations`/`agent-health` become tabs of one Health suite (the proven merge pattern); `manager` + `manager-command-center` + `unified-dashboard` fold into Today with role-scoped sections (Tier 1 coordinator vs Tier 2 staff).
- **Risk:** You actively use two of these pages daily — folding them wrong = workflow friction. Mitigate: legacy-hash redirects + hiddenRoutes, same as PR2–7; ask which of manager vs unified-dashboard is the keeper before merging.
- **Status:** pending
- **Next step:** confirm keeper pages, then ce-plan

### 4. Today = job-first action queue (your actual day, as one page)
- **Effort:** Medium (one new composite page, 5–6 existing endpoints + review-gate + kanban)
- **Benefit:** Mirrors your real rhythm instead of a page catalog: ① Morning briefing digest (exists) → ② **Needs you** list (review-gate pending email drafts, swap approvals, data-gap rows, eval reminders, cron failures) → ③ schedule-at-a-glance (who's on call today, next GR, clinic) → ④ quick sends. Every item deep-links or resolves inline — clear the queue = day done. This is the "hub for everyday duties" ask.
- **Risk:** Aggregation page goes stale fast → must poll/refetch on focus, and depends on #1 for trustworthy data. Don't build before SSOT or it inherits frozen numbers.
- **Status:** pending
- **Next step:** ce-brainstorm the attention-queue contents with you

### 5. AI-generalist role layer — every page is agent-drivable + page-aware chat
- **Effort:** Large (manifest + chat context plumbing), stageable in small slices
- **Benefit:** Turns "AI generalist" from a routing joke into the hub's core: (a) a `data/skill-manifest.json` machine contract — for each page its endpoints, actions, and one-line description so any agent (Hermes/opencode/Gemini) can operate the hub headlessly and the Smart Router finally routes on real capability data; (b) AI Chat gets "context: this page" injection — ask about the data you're looking at; (c) an agent-activity rail on Today (cron runs, skill runs, delegation results) so AI work is visible and reviewable, feeding the audit log.
- **Risk:** Manifest rots if hand-maintained → generate it from NAV_CONFIG + route decorators at build/deploy time (script, not prose). Scope creep: stage (c) → (b) → (a).
- **Status:** ✅ BUILT 2026-09-12/13 (all three slices)
- **Delivered:** (a) `modules/skill_manifest.py` generator → `data/skill-manifest.json` (91 pages, 188 routes, mtime-freshness guard, auto-regenerates when sources change); endpoints GET/POST `/api/skill-manifest[/regenerate]`, `/api/skill-manifest/page/{page}`. (b) page-aware chat: `ChatRequest.page_context` + `_build_context_block()` injects the page's manifest entry into the agent prompt; chat UI Context selector auto-defaults to the last-viewed data page. (c) Today agent-activity rail: `/api/agent-activity` (audit events + cron) rendered by `agentActivitySec()`. Bonus: `/api/router/suggest` now returns `related_pages` grounded in the manifest (verified: grand-rounds invite task → calendar-invites, grand-rounds-hub).

## Rejected / deferred ideas (for reference)
- **More visual redesign** — PR1–9 already shipped the token/IA/emoji work today; visual skin is not the gap.
- **Auto-deleting the 12 old JSON pages** — violates additive-first rule; keep as hiddenRoutes until SSOT swap proves parity.
- **Rebuilding launchpad tiles** — fresh and working; leave alone.

## Dependency order (recommended)
1. #1 SSOT rewiring → 2. #2 staleness badges → 3. #4 Today queue → 4. #3 overview collapse → 5. #5 agent role layer
