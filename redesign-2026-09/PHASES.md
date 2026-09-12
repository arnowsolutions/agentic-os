# DESIGN PHASES — Agentic OS Hub Redesign v3
> no-slop-design gate artifacts. Written BEFORE any code, per the mandatory phase discipline.

## Phase 1 — Research (adopt/reject)

| Reference | Adopt | Reject |
|-----------|-------|--------|
| Linear app shell | zoned sidebar w/ collapsible trays; command palette as first-class (⌘K); restrained single accent | scroll-forfeit: Linear hides everything behind palettes — this hub needs visible launch tiles |
| Vercel dashboard | flat thin-border cards, hairline dividers, monospace numerals for metrics | empty whitespace luxury — our home must be dense (launcher) |
| Stripe dashboards | tabular-nums, disciplined type scale, section headers not card-in-card | marketing gradients (banned) |
| Raycast launcher | "tile = service" launcher metaphor with health dot + Launch action | keyboard-only interaction |
| macOS Dock | apps grouped by domain, one row, always visible | magnification gimmicks |
| Existing AOS mass-email page | inline-tab pattern (proven in this codebase) for suite merges | — |
| Unified Platform (row 14) | none — deliberately different | dark-glass navy skin, dense-tool archetype |
| Trade Compass (row 15) | none — deliberately different | media-realism hero, navy, candlestick motif |

## Phase 2 — Moodboard (written)

Adjectives: **terminal-precise, dense-but-calm, black-slab, single-teal-pulse, instrument-panel**.
THIS HUB IS an operator's instrument panel: black hardware, one live status color, mono digits, hairline rules. No glass, no glow, no marketing surfaces.
Explicit reject list: purple/pink gradients, emoji decoration, heavy shadows, 4-equal-card stat rows, card-in-card nesting, rounded-everything, radial halos, chip clouds, glassmorphism.

## Phase 3 — Design tokens (extends approved system, does NOT replace)

Keep the live v2 token set (bg #0c0c0e stack, teal #0d9488 accent, Inter). Additions only:
- `--font-data: 'JetBrains Mono'` enforced on all numeric/stat displays with `font-feature-settings:'tnum'`
- `--border-hairline: rgba(255,255,255,0.08)` for section dividers (replaces nested card borders)
- `--tile-ok / --tile-warn / --tile-down` status colors for launchpad health dots
- Row rhythm: 32px table rows; stat strip is a single pill row, not 4 cards

## Phase 4 — Platform rules

- Web SPA, dark-first + maintained light mode (grep-sweep all `rgba(255,255,255,` into tokens)
- Class names in styles.css are FROZEN (279 classes, 70+ pages) — CSS-first only
- No emoji anywhere in chrome or page headers (▸ ● ◆ and hex-glyphs only)
- Deploy: static files live via shared volume; bump `?v=` querystrings in index.html every deploy; module/server.py changes need `docker restart hermes-webui-gsga-agentic-os-1`; new API endpoints go under an allowlisted prefix (`/api/crm/…`) and the session allowlist
- Verification: 3-page dark/light spot check, hash-route parity, curl chain through Traefik

## Fingerprint statement (Anti-Repeat Gate)

**Fingerprint of AOS Hub v3:** mode=Dark near-black neutral (#0c0c0e, NOT navy) · palette=black-slab / teal #0d9488 single accent · type=Inter + JetBrains Mono data voice · archetype=**Command-shell instrument panel** (launcher tiles + status rails + mono digits — distinct from Unified's "dense tool UI" and Trade Compass's "media trading dashboard") · hero=Live launchpad tile grid · surface/motion=hairline dividers, hover-only, no shadows/glow · motif=**status dot** (the live pulse dot is the brand mark of the hub).
Differs from last 2 rows (14 Unified: dark-glass/navy/tool-UI, 15 Trade Compass: media-navy/realism/candlestick) on axes 1 (neutral black vs navy), 3 (adds mono data voice), 5 (launcher tiles vs scene/tool), 6 (hairline flat vs glass/media), 7 (status-dot vs candlestick/unified-chrome) = 5 axes.


## Accepted build log (2026-09-12, PR1+PR2 shipped)
- Deployed: utils.js (NAV v3 zones) · index.html (mono-teal logo, chrome cleanup, cache-bust 20260912) · styles.css (subsection CSS append, 256 classes preserved) · app.js (DEFAULT_ROUTE -> dashboard)
- Verified live: all 4 assets 200 on os.srv1738752.hstgr.cloud; node --check OK on utils.js & app.js; all 80 page modules serve 200; no errors in container logs (10m); purple/pink logo colors = 0 occurrences
- Pending: fingerprint row to DESIGN-FINGERPRINT-LOG.md after user visual sign-off; PR 3 (launchpad) shipped — see below.

## Accepted build log (2026-09-12, PR3 shipped — Launchpad)

- Files: `dashboard/pages/dashboard.js` (Launchpad rebuild — tiles, agent+cron strip, quick actions) · `dashboard/pages/operations.js` (NEW — legacy dashboard content migrated) · `dashboard/utils.js` (nav: System → Operations; topbar health-widget emoji → glyphs) · `dashboard/styles.css` (+119 lines `.lp-*` components) · `dashboard/index.html` (cache-bust `?v=20260913` on all 4 tags) · `data/launchpad.json` (NEW registry — 18 services / 5 zones, probe spec per service) · `modules/crm.py` (+`GET /api/crm/launchpad` — TCP/HTTPS probes, 60 s cache) · `server.py` (session_enforcement allowlist entry).
- Verified live: endpoint 200 through `os.srv1738752.hstgr.cloud` — 18/18 up, cache hit 26 ms on second call; all assets + page modules 200; `node --check` + `py_compile` clean; container restart ~10 s; no error output in logs; Node render smoke test of both pages (tiles/zones/down-state class/pills/ops cards all render).
- Registry zones: Hosting 5 · AI 4 · Data 3 · Comms 2 · Media 4. Excluded after probing: `therec` + `ink-and-ember` (both currently serve an "Arnow Solutions — Writing Academy" page on :8108 — misrouted), `ce-full` (502). Available to add later: tc-report, nursing-videos, manim, masterb-pilot, workflow.
- Pending: user visual sign-off; PR4 (visual pass) next.

## Build progress (2026-09-12, evening — PR4 partial + AI Chat fix)

- **Live now:** styles.css refinements (stat strips → compact label/value pills, hairline cards — no shadow/glow/glass, tabular-nums on stat + table values, 32px table rows, flat tabs) · app.js chrome emoji removed (empty states ⌕/!/△, invite modal, custom-page titles) · index.html cache-bust → `v=20260914` · AI Chat page: Gemini removed, opencode toolchain restored (self-contained at `agentic-os/.tools/opencode/`; `/api/chat` verified returning real answers via OpenCode Go, model `deepseek-v4.1-flash`).
- **Shipped (approved + verified):** emoji sweep of the 10 worst pages (323 chars → glyph set; 0 leftover; all node-checked) · `therec.srv` → The Rec (unit `static-therec` on 8145) · `tc-report.srv` → Trade Compass report (8146) · `ce-full.srv` → CE:FULL report (8147) — all three titles verified live through Traefik (file-watch reload, no restart) · four bare static servers (nursing 8140 / manim 8141 / masterb-pilot 8142 / animation-studio 8143) converted to reboot-proof systemd units · launchpad registry +3 tiles (The Rec, Ink & Ember, Animation Studio). PR4 = complete for the worst-10; full sweep deferred to PR8 per plan.

## Accepted build log (2026-09-12, PR5 shipped — Schedule Suite + canonical Calendar)

- **Schedule Suite:** new `dashboard/pages/schedule-suite.js` — tabs Weekly Call / Staff / PDF Export, hash-addressable (`#schedule-suite?tab=call|staff|pdf`). Delegates to the three original modules via an optional `target` param — `const content = target || document.getElementById('suitePane') || document.getElementById('pageContent')` — so standalone routes still work and each sub-page's own Refresh/Reset stays inside the suite pane. Modules lazy-load once (fn-existence guard).
- **Routing:** `app.js` — `LEGACY_REDIRECTS` map (`oncall`→suite call tab · `staff-schedule`→staff · `call-schedule-pdf`→pdf · `cal-new`/`calendar2`→`calendar`); `navigate()` now parses `?tab=` params (route = hash base) and rewrites legacy keys before resolution. Old bookmarks keep working; renders stay single-pass via hashchange.
- **Calendar canonical: `calendar.js` wins** — newer (Jul 13) and already on `/api/crm/tasks`; `cal-new.js`/`calendar2.js` are byte-identical older builds on the dead `/api/calendar/todos` (files archived in PR9; both hashes redirect now).
- **Nav (`utils.js`, root-owned — deployed via SSH):** Work zone folds Call+Staff into one **Schedule Suite** item; Rotation ops drops the merged entries; hiddenRoutes gain the 4 merged pages (`Merged into …`) so command search still finds them.
- **Cleanup while in-file:** the 3 schedule modules swept — 40+ emoji → glyph set / removed; purple `#6c5ce7` + `rgba(108,92,231,·)` → `var(--accent)`/`var(--accent-dim)` (0 left); unused `HOSPITAL_EMOJIS` map deleted.
- **Verified:** `node --check` clean on all touched files; Node smoke test (tab parse incl. bogus→default, delegation passes `#suitePane`, tab row renders, LEGACY_REDIRECTS complete); live through Traefik — `utils.js` md5 match after root push, `schedule-suite.js` HTTP 200, served `app.js` contains `LEGACY_REDIRECTS` (5 refs), `index.html` serving `v=20260915`.
- **Pending:** user visual sign-off; PR6 (Compliance Suite · Grand Rounds Hub · CRM tabs) next.

## Fixes staged (2026-09-12 late — GME single-source + staff schedules)

- **AOS GME tracker rewired to the platform's single source of truth** (`modules/crm.py`): `/api/crm/gme/summary` + `/residents` now read `unified.reimb_*` via the `crm_db` Postgres connection instead of the contacts store (which structurally had zero reimbursements → everyone showed $0 while the platform holds 662 approved submissions / $387k). Per-resident rows now list ALL fund transactions (account + status + description), GME-approved totals drive the $1,250 cap; `CURRENT_AY` is now computed dynamically (2026-27); POST `/gme/reimbursement` inserts into `unified.reimb_submissions` (person-linked, cap-checked, status-mapped paid/pending/denied→paid/pending/rejected).
- **AOS staff endpoint fixed** (`server.py`): `_load_faculty_schedule()` never existed → 500 → page fell back to hardcoded demo names. Now reads `data/staff_schedule.json` (21/19/21 across Moses/Wakefield/Weiler); demo fallback removed from `staff-schedule.js` (explicit empty/error states only). `gme-tracker.js` AY dropdown → 2026-27 current; cache-bust `v=20260916`.
- **Verified:** py_compile + node --check clean; contacts PG reachable (127 rows); verifier script `/tmp/verify_gme.py` ready. **Pending: AOS container restart (approval) to activate Python changes.**
- **Platform fixes staged** (`redesign-2026-09/fixes-20260912/`): staff-schedule.ts month-end clamp (fixes Sep "2026-09-31" 500 — reproduced from logs+psql); GmeFundStatusTab dynamic DEFAULT_YEAR; `deploy-platform-fixes.sh` (patch → typecheck → build → restart → JWT probe verify).
- **Data gap found (not yet fixed):** urology_roster admin shifts missing for **Jul 5–Aug 1, Aug 30–Oct 25** — source xlsx files exist in `/workspace/2026/Scheduling Grids/` but were never imported; that's why the Admin/Staff grid is empty for the current period. Backfill = staged import after one recon step.
- **OR/Clinic:** live APIs verified healthy (current + next weeks return data; coverage runs to ~Sep 25 = weekly-sheet horizon; Call runs to Jan 2027). No reproducible server-side break — awaiting user screenshot if the symptom persists.

## PR6 built + staged (2026-09-12 night — Compliance Suite · Grand Rounds Hub · CRM suite)

- **3 new suites** (same pattern as PR5): `compliance-suite.js` (Overview · Eval Portal · Eval Dashboard · GME Tracker · GME Deep Dive) · `grand-rounds-hub.js` (Grand Rounds · Attendance · Invites · Chief Meetings) · `crm-suite.js` (People · Contacts · Residents · Audit).
- **10 sub-pages refactored** for suite embedding: `target || #suitePane || #pageContent` chain (main renders take `target`; secondary re-render paths in grand-rounds/attendance use suitePane-first fallback). All node-checked.
- **Router:** `app.js` LEGACY_REDIRECTS +11 (`compliance`, `eval-portal`, `eval-dashboard`, `gme-tracker`, `gme-detail` → Compliance Suite tabs; `grand-rounds`, `grand-rounds-attendance` → GR Hub; `people`, `contacts`, `resident-roster`, `crm-audit` → CRM tabs).
- **Nav (utils v4, ready to push):** Work zone 'Compliance' → 'Compliance Suite'; 'GME & evals' section removed (4 items → hiddenRoutes); Rotation ops drops 'Attendance'; 'Grand Rounds' → 'Grand Rounds Hub'; Admin drops People/Contacts/Roster/Audit → single 'CRM'. Cache-bust `v=20260917`.
- **Verified:** node --check on all touched files; Node smoke test PASS (tab parse incl. bogus→default, delegation to #suitePane in all 3 suites, LEGACY_REDIRECTS complete). **Pending: utils.js push (approval) + visual sign-off.**
- **Backfill status:** 1,967 rows extracted + all checks green; VPS import blocked on one approval click (scp prompt timed out). Runner has empty-window pre-flight; nothing half-applied.
