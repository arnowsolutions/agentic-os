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
- **Verified:** node --check on all touched files; Node smoke test PASS (tab parse incl. bogus→default, delegation to #suitePane in all 3 suites, LEGACY_REDIRECTS complete). **SHIPPED 2026-09-12 night: utils.js v4 pushed (md5 6591cb78… matched), all 3 suite modules serve 200, v=20260917 live.**
- **Backfill SHIPPED:** CSRF double-submit handled (GET /api/v1/csrf-token → cookie + x-csrf-token header); **1,967/1,967 imported, 0 skipped, 0 errors** (666 + 611 + 690). Post-verify: current week = 130 admin shifts (was 0), Sep month = 594 rows (was 500), 14 previously-absent clerks now visible, coverage continuous Aug 25 → Sep 5.

## PR7 SHIPPED (2026-09-12 — AI Builder Suite · Workspace suite · Colophon)

- **AI Builder Suite** (`ai-builder-suite.js`): tabs Builder / Image / Video / Gallery. Builder delegates to `ai-builder.js`; Gallery delegates to `image-gallery.js`; Image + Video **embed** the standalone `prompt-image.html` / `prompt-video.html` in place (new `.suite-embed` iframe pattern — these were the only pages that bounced the whole SPA out to a bare page). Tab 1 note: the plan's merge map listed 3 tabs (Image/Video/Gallery); the existing Gemini "AI Builder" page was folded in as tab 1 because (a) the PR's 8-file count includes `ai-builder.js`, (b) two items named "AI Builder" + "AI Builder Suite" in one zone would be worse IA than one suite.
- **Workspace suite** (`workspace-suite.js`): tabs Files / Scripts / VS Coder / Apps Script — delegates to `file-browser.js` / `script-runner.js` / `vs-coder.js` / `google-studio.js`, all refactored to the `target || #suitePane || #pageContent` chain.
- **Colophon** (`colophon.js`): production-notes page (identity · redesign ledger PR1–PR9 · deployment mechanics · design system) placed in System → Admin tray. The plan's one-word "colophon" scope item, implemented as a real page.
- **Router:** app.js LEGACY_REDIRECTS +8 (`ai-builder`, `prompt-tools-image`, `prompt-tools-video`, `image-gallery` → AI Builder Suite tabs; `file-browser`, `script-runner`, `vs-coder`, `google-studio` → Workspace tabs).
- **Nav (utils v5, md5 c7f998e9… live):** Build zone: 4 direct + 3 trays → 6 direct + 1 tray ('Media & prompts' + 'Dev environment' trays retired; social-media-hub promoted to direct). 8 old rows → 2 suites; 8 new hiddenRoutes. Cache-bust `v=20260918`.
- **Emoji swept in-scope:** all 8 touched modules cleaned as part of the refactor (file-browser had 8, script-runner 18, google-studio 20, image-gallery 15 — all mapped to the approved glyph set; ▤/▦ kept as the gallery's view-toggle pair, ☰→▤). 0 leftovers.
- **Verified:** transform assertions all hit; node --check ×11; Node smoke test PASS (tab parse incl. bogus→default, delegation panes, embed srcs, 8/8 redirects, nav greps); all 9 modules + utils + index 200 through Traefik; utils md5 matched build↔VPS↔local.
- **Backups:** `redesign-2026-09/backup-pre-pr7/` (8 modules + app.js + utils.js + index.html).

## PR8 SHIPPED (2026-09-12 — full emoji sweep · light-mode hardening · mobile nav)

- **Emoji sweep:** 52 JS modules + 4 standalone HTML (prompt-image/video, omniroute-chat, login) → **0 leftover** (calendar.js excluded: its emoji are functional regexes/keywords — event classification + title cleaning; cal-new/calendar2 pending archive). Approved glyph set only; ☰ kept solely as the menu/view-toggle convention glyph, ▤/▦ as the gallery's view toggle pair.
- **Purple/pink purge:** contacts / gme-tracker / social-media-hub / morning-briefing / resident-roster + login.html + omniroute-chat.html → teal palette (#14b8a6 / #0d9488 / #2dd4bf); omniroute user-avatar gradient #f093fb→teal.
- **Light-mode hardening:** 6 new tokens × 2 themes (--hover-bg, --hover-bg-strong, --fill-muted, --border-soft, --scrollbar, --scrollbar-hover); 25 styles.css + 35 page rgba(255,255,255,α) literals → tokens; 0 remain outside the token definitions.
- **Mobile nav fixes (real bugs found):** (a) the mobile menu button carried inline `style="display:none"` that no media query could override → the drawer was unreachable on phones; removed (b) `.sidebar-overlay{display:block}` was unconditional at ≤768px → overlay permanently intercepting taps; now `.active` only (c) sidebar max-width 85vw; suite tabs scroll horizontally on mobile.
- **Verified:** node --check ×88 modules; leftover scans 0; live curl through Traefik (styles tokens 26 refs, kanban.js clean, button live). Backup: `backup-pre-pr8/` (89 files + styles.css + index.html).

## PR9 SHIPPED (2026-09-12 — cleanup · parity · final audit)

- **Archived out of `pages/`:** `cal-new.js`, `calendar2.js` (byte-identical twins; canonical = `calendar.js`), `grand-rounds.js.bak-theme-20260909` → `redesign-2026-09/archived-pages/`. Legacy hashes (`#cal-new`, `#calendar2`) still redirect via LEGACY_REDIRECTS — the files are never loaded.
- **Dead link fixed:** tools.js "Big Reef Dashboard @ localhost:8501" — verified NOTHING listens on 8501 — replaced with a "System Status" card → `https://status.srv1738752.hstgr.cloud` (live 200; matches launchpad-registry entry `status`). No `localhost:` links remain in page bodies.
- **DEFAULT_ROUTE:** confirmed already `'dashboard'` (flipped in PR2) — no change needed.
- **Final audit (`pr9-audit.js`, re-runnable from `redesign-2026-09/scripts/`):** 58 visible nav pages → all modules + render fns exist · 26 legacy redirects → all targets resolve · 30 hidden routes valid · sidebar parity rendered 58 == expected 58 · inventory 86 modules = 58 live · 22 suite tabs · 6 hidden · **0 orphans** → `redesign-2026-09/final-inventory.md`.
- **Cache-bust** `v=20260919` (4 refs). Colophon: PR8/PR9 marked shipped + inventory row.
- **`DESIGN.md` written** (repo root) — token spec contract: colors (teal-only), typography, glyph set, component patterns, layout, deploy conventions. Future pages consume this instead of re-deciding.
- **Verified live:** tools.js 0 refs to 8501 / System Status present · archived files 404 · all suites 200 · index v19.
- **Scripts preserved:** `redesign-2026-09/scripts/` (pr7-transform, smoke-pr7/pr6, pr8-sweep, pr8-styles, pr9-audit, utils-v5).
- **Backups:** `backup-pre-pr8/` covers pre-PR9 state for pages. PR9 touched: tools.js, colophon.js, index.html (bump only).

## Hermes WebUI embed fix (2026-09-12 — AI Chat → Hermes)

- **Root causes (two):** (a) chat.js iframed the *relative* path `/hermes-webui/` → bounced through AOS `/login` → the dashboard loaded inside the frame ("agentic os again"); (b) the server's proxy targeted `127.0.0.1:8787` — inside the AOS container that is nothing (WebUI is a sibling container at `hermes-webui:8787` via compose DNS) → ConnectError. Also the WebUI sends `X-Frame-Options: DENY` — the proxy must strip it for same-origin embedding.
- **Fix:** proxy rewritten (`server.py`): target `os.environ.get("HERMES_WEBUI_URL", "http://hermes-webui:8787")` · **raw streaming relay** (`client.send(stream=True)` + `aiter_raw()`, `httpx.Timeout(read=None)`) so SSE + gzip pass intact · strips CSP/X-Frame-Options + hop-by-hop headers · rewrites same-origin `Location` to the proxied path · `/hermes-webui` (no slash) → 307 `/hermes-webui/`. chat.js: embed toolbar with **↗ Open in new tab** (`window.open(HERMES_WEBUI_URL,'hermes-webui')` — reusable named tab) + ↻ Reload; `let`→`var` top-level (re-execution safety); iframe rebuilt fresh per visit.
- **Why embedding works:** the WebUI officially supports subpath mounts — base href = `location.origin + pathname-dir`; all fetches are `new URL('api/…', document.baseURI)`, so everything routes through the proxy at `/hermes-webui/`.
- **Verified with a temp session** (mint → curl → delete, sessions.json restored to 2): authenticated `/hermes-webui/` → **200** real WebUI HTML (title "Hermes"), frame headers ABSENT; `/hermes-webui` → 307; assets + manifest 200; unauthenticated → 307 `/login` (gate unchanged). `x-frame-options: DENY` on the direct domain (hermes-webui-gsga.srv…) is why the new-tab button points there and the in-pane path uses the proxy.
- **Deployed:** container restarted 2026-09-12 15:12 UTC (approved); cache-bust `v=20260920`.
- **Follow-up fix (same day): "Switch failed: Cross-origin mismatch - check reverse proxy headers"** (red toast on profile/model switch). Cause: the WebUI's global CSRF/same-origin gate compares the request `Origin`/`Referer` host against its `Host` header — through the proxy the upstream saw `Host: hermes-webui:8787` (httpx default) while the browser sent `Origin: https://os.srv1738752.hstgr.cloud` → 403. Fix: the proxy now presents the **public host upstream** (`X-Forwarded-Host` from Traefik, fallback to client Host → set as `Host` + `X-Forwarded-Host`, plus `X-Forwarded-Proto: https`) — standard reverse-proxy practice; exactly the header pass-through the WebUI's error message asks for. **Proven before/after** with a no-side-effect probe (browser-style POST to an unknown API path, temp session): before = `403 {"error":"Cross-origin mismatch - check reverse proxy headers"}` (reproduced the toast), after = `404` (gate passed, router answered). GET /hermes-webui/ + static assets re-verified 200.
