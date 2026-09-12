# Agentic OS Hub — Redesign & Reorganization Plan
**Date:** 2026-09-12 · **Scope:** Dashboard UI/UX, Information Architecture, Visual System
**Skill chain:** no-slop-design phases + ce-review lenses + ux-flow review
**Target:** `os.srv1738752.hstgr.cloud` (Traefik → container `hermes-webui-gsga-agentic-os-1` :8092→8082, FastAPI + vanilla-JS SPA)

---

## Phase 0 — Ground Truth Audit (completed 2026-09-12, live VPS)

| Fact | Value | Source |
|------|-------|--------|
| Page JS modules | **81 files** | `dashboard/pages/` |
| Sidebar visible routes | **52 items** in 6 groups + 3 external | `dashboard/utils.js` NAV_CONFIG (line 119) |
| Orphan page files (built, no sidebar route) | **12** | chiefs-meetings, conference-email, grand-rounds, tasks, subi-exit-interviews, resident-letters, social-media-hub, email-groups, distribution, data-gaps, cal-new, calendar2 |
| Duplicate/stale files | `calendar.js` / `cal-new.js` / `calendar2.js` (3 copies of calendar UI, 2 identical sizes 18,191B); `grand-rounds.js.bak-theme-20260909` (32KB backup inside pages dir) | pages listing |
| Backend | `server.py` 186KB single file + 40 Python modules | `agentic-os/` |
| styles.css | 64KB, Linear/Stripe v2 tokens (dark #0c0c0e, teal #0d9488, Inter) + 1 light theme override | live pull |
| Default route | `tasks` (DEFAULT_ROUTE in app.js:29) — a truck-emoji custom page — NOT Dashboard | app.js |
| Hardcoded emoji in page bodies | calendar 45+ distinct, manager 10, quick-actions 10, tools 9, unified-dashboard 8 | grep audit |
| Emoji in index.html chrome | 📋 📱 👥 hard-coded inline-style Tasks/Social/Distribution links + 🌓 theme + 🔍 search — bypasses NAV_CONFIG styling | index.html lines 38-46, 53, 66 |
| External links | VS Code, Overlay Designer, Video Editor → **dead tunnel trycloudflare.com** | NAV_CONFIG `external` |
| Purple/pink leftovers | 3 × #6c5ce7 + #fd79a8 gradient in index.html logo SVG (forbidden accent) | index.html line 22 |
| Dev-vs-prod drift | raw `localhost:8501` links inside pages (Big Reef) — unreachable from the public domain | tools.js |
| Auth | Session middleware blocks non-allowlisted `/api/*`; new pages often 401 | server.py + skill pitfalls #11 |
| Deployment | Static files live instantly (shared volume); module .py changes need container restart; restart = `docker compose restart hermes-webui-gsga-agentic-os-1` (or `docker restart`), not `fuser` | docker ps confirmed |

### Design-relevant constraints
- **CSS-first redesign pattern** (skill v3.19): keep all 279 class names; rewrite tokens/components in `styles.css`; never rename classes (70+ pages reference them).
- **Forbidden patterns** (user-stated, codified in skill): no emoji in nav/headers, no purple/pink gradients, no heavy shadows, no multi-color accents.
- **Design DNA (no-slop-design):** Inter/teal Linear-style token set is APPROVED and already implemented — visual skin is NOT the problem. The problem is ✅ layout density, ✅ IA (52 flat sidebar links), ✅ logical page groupings, ✅ dead links, ✅ emoji inconsistencies.

---

## Phase 1 — Information Architecture (the BIG win)

### Diagnosis
The hub was built feature-first, not job-first. 52 sidebar links create:
- **Same job, six doors:** Call Schedule lives in oncall.js + staff-schedule.js + call-schedule-pdf.js; email lives in mass-email.js + email-templates.js + email-send-log.js + email-groups.js + distribution.js + conference-email.js; calendar UI exists in 3 duplicate copies.
- **Relational pages flagged as pages:** GME Tracker + GME Deep Dive are ONE feature at 2 zoom levels (should be 1 page, tab/detail).
- **Orphans (12 built pages, unreachable)**: dead inventory nobody can click.
- **Groups don't match mental model:** 'Communication' split apart from mass-email which is in Urology section; 'Operations' vs 'System' boundary arbitrary.

### Proposed structure — Hub (3 shells, ≤16 open links max)

Replace 6 territorial groups with **3 zones + collapsible trays**:

| Zone | Contains | Sidebar shows |
|------|----------|---------------|
| 🏠 **Home** | Dashboard, Command Center, Morning Briefing | 3 |
| 🏥 **Work** (Urology / Schedule / Care) | Schedule Suite (merged call+staff+PDF in tabs), Calendar Suite (merged, 1 copy), Mass Email & Invites (uses email-templates + distribution as in-page tools, removes 3 links), Compliance (absorbs attendance, eval-portal, eval-dashboard, gme-tracker, gme-detail with tab nav), Platforms, Telegram | 6 |
| 🧰 **Build** (Dev/Tools/Agents) | AI Chat, Skills, My Tools, AI Builder Suite (Absorbs prompt-tools-image, prompt-tools-video, image-gallery into tabs), Workspace (File Browser + Script Runner + VS Coder + Google Studio tabs), Commerce? no — remove | 5 |
| ⚙️ **System** (collapsed by default) | Health + Agent Health + Memory + Smart Router, Cost, Backups, Audit, CRM (absorbs contacts, crm-audit, resident-roster), Prompts & Standards, Plugins, PIN Manager, Settings | 6 (tray) |

**Sidebar shrinks 55 → ~20 visible access points** with search + recents handling the long tail. Every displaced link lives inside a parent page as a sub-tab, left capable of "recent" / pinned tiles on dashboard.

### Merge map (must be additive-first, no deletions)
| Old pages | New parent | Becomes |
|-----------|------------|---------|
| oncall, staff-schedule, call-schedule-pdf | Schedule Suite | tabs: Weekly Call / Staff / PDF Export |
| calendar, cal-new, calendar2 | Calendar Suite | single canonical calendar; delete 2 dupes after parity check |
| grand-rounds, grand-rounds-attendance, conference-email, chief-meetings | Grand Rounds Hub | tabs: Event / Attendance / Invites / Chief Meetings |
| compliance, eval-portal, eval-dashboard, gme-tracker, gme-detail | Compliance Suite | inner tabs: Evals / Attendance / GME / Compliance Home |
| mass-email, email-templates, email-groups, distribution, email-send-log | Mass Email & Invites | tabbed: Compose / Templates / Groups / Send Log |
| people, contacts, crm-audit, resident-roster | CRM | tabs: Contacts / Roster / Audit |
| prompt-tools-image, prompt-tools-video, image-gallery | AI Builder Suite | tabs: Image / Video / Gallery |
| file-browser, script-runner, vs-coder, google-studio | Workspace | tabs: Files / Scripts / VS Coder / Apps Script |
| subi-exit-interviews, resident-letters, data-gaps | surfaced under Urology → Review & Collections (choose placement Phase 1 review) | to be slotted by user |
| social-media-hub, tasks | index.html bottom rogue links → real NAV_CONFIG rows in Work zone (Tasks) and Build zone (Social) | promoted |
| omniroute, claude-code, memory/metrics: keep as-is | Build / System | separate top items — distinct daily value |

### Inner-tab tabs pattern (already proven on the codebase)
Reuse the established **mass-email.js tab pattern** (inline tabs + iframe or render-function swap; no new framework). All merged pages keep existing URLs (`#oncall` → redirects to `#schedule-suite` tab 1) so bookmarks don't break — implement with `hiddenRoutes` + hash-redirection in `navigate()`.

### Information density (per-page)
The audit shows pages average 1 skeleton + stats grid. Formalize a **baseline page layout** every page follows:
1. 24px page-header with title, subtle breadcrumb, and exactly ≤1 Primary action
2. 4-up stat strip (current stat-card, tightened pill styling — no shadow, thin border)
3. Two-column content area on ≥1280px, single column on mobile; 12px gap; section dividers, NOT card-steroids
4. Right-rail contextual links (deep links to related suites) — replaces "quote the nav" behavior

### Navigation behavior (kill scroll fatigue)
- **Sidebar becomes zones, not page lists.** Zone headers are always visible; pages inside the zone collapse into a single rail row. Clicking a zone toggles its tray open, ">ne at a time.
- **Command palette upgraded** (exists as topbar search) → add keybind `⌘K`/`Ctrl+K`, show recents + zone badges.
- **Sidebar footer widget** shows agent-status only (already exists).
- **Mobile**: keep today's off-canvas drawer, but zones reduce it to 3 taps + 1 expand instead of a 55-item scroll.

---

## Phase 2 — Visual & Page-Level Refinement (CSS-first, no class renames)

Already-strengths (verified in live code): Linear-Stripe token system, Inter, restrained teal, light mode. Keep all of it.

### Targeted changes (styles.css + index.html only)
1. **index.html logo**: replace the hardcoded purple/pink SVG gradient cylinders with a flat single-color geometric mark (teal `#14b8a6` or just mono). #6c5ce7 / #fd79a8 violate user's "no purple"|no pink" rule.
2. **index.html rogue emoji links** (📋 Tasks / 📱 Social Media Hub / 👥 Distribution) — migrate to proper `NAV_CONFIG` rows so `active` highlight works and inline styles go away.
3. **Emoji sweep inside page bodies** — 148+ pieces across 12 pages (calendar worst). Replace with the already-approved glyph system (▸ ● ◆ and the existing `#`-hex icon strip inside stat-card) or text. No Adobe/icon-font install needed.
4. **Card weight reduction**: currently `--shadow-lg: 0 4px 16px`. Reduce card elevation to thin `1px solid var(--border)`, no shadow. Removes the stack of "boxes-in-boxes" visual noise.
5. **`.stat-card` tightening**: today 4-up with big numbers + labels. Convert to a horizontal strip (label-left / value-right pill), reduces vertical space per row and kills the 4-equal-card stack (the "searchable page" pattern user dislikes).
6. **table/row rhythm**: enforce 32px row-height in styles.css — pageEndpoints currently use default 40+px, making data pages feel empty. Tighter rows = more information per screen without shrinking fonts.
7. **Section headers replace card-in-card**: pages that wrap a `.card` inside a `.card` (unified-dashboard does this) collapse to header + content flush.

### Typography rhythm
- Diagnostic: page-title is currently 20px (0.71em bug in `.page-title { font-size: 1.43rem }`? Verify live). Recheck — target: h1 20px/600, stat-value 24px/700, body 13.5px, mono for data values.
- Apply `font-feature-settings: "tnum"` on stat/table values so digits align across pages.

### Light-theme hardening
Skills warned: `rgba(255,255,255,…)` leaks into light theme. Run a grep sweep post-edit (`grep "255, 255, 255" styles.css`) and swap to `var(--border)` / neutral rgba-gray. Verify at least 3 pages in both modes.

---

## Phase 3 — Launchpad Mission (the "hub to launch everything on the VPS")

The stated goal: *"my hut to get access to everything on the VPS and launch all apps/features."* Today this only half-exists: `tools.js` (NotebookLM/Cron/KB), `platforms.js`, and topbar health widget. Plan builds a real **Launchpad**.

### New composite: **Dashboard = Launchpad** (redesign `dashboard.js` only; its current content migrates to System → Operations)
Rebuilt home shows, in 3 tiers:
- **Tier 1 — Live VPS services grid** (8-12 tiles, not 24): pull from a NEW `/api/launchpad` endpoint that wraps a service registry YAML/JSON file. Each tile: service name, host:port, health from existing probes (getHealth, agent status, docker ps already available to agent via new exec call), last-check time, and a Launch button (opens in new tab or iframe page).
- **Tier 2 — Agent + Cron strip**: existing agent status + cron upcoming-runs (data exists in `/api/scheduler`), rendered as a single row of pills, not cards.
- **Tier 3 — Quick Actions rail**: current quick-actions compressed to a 2-column list (Disc-like), not 19 emoji buttons.

**Service registry** (`data/launchpad.json`) maps: id, label, kind(web/api/docker), host, port, ssl, health_path, launch_url, owner group. Backend reads + probes lazily. Frontend renders tiles grouped by zone (Hosting / AI / Data / Comms / Media).

This becomes the single mental model: **sidebar = navigate within the OS; Dashboard = see & launch everything on the VPS.**

---

## Phase 4 — Cleanup & Deployment Safety

### Code hygiene (additive-first, no deletions without user sign-off)
| Item | Action |
|------|--------|
| `grand-rounds.js.bak-theme-20260909` inside pages dir | move to `/backups/` (a stray .bak can shadow router behavior in some load paths) |
| calendar duplicates | parity-diff calendar.js vs calendar2.js; promote one, keep others in `#old-calendar-hash` hiddenRoute for 2 weeks, then remove |
| `localhost:8501` link in tools.js | parameterize via launchpad registry (`kind:'internal'` → reachable host) |
| `.bak/hidden routes` audit | 12 orphan pages get submitted to a single "Full Inventory" page (System → All Pages) so nothing is truly unreachable during transition |

### Deployment mechanics (per skill pitfalls)
- Static files (styles.css, app.js, utils.js, index.html, dashboard/pages/*.js) update **instantly** through the shared Docker volume — no restart.
- `utils.js?/api.js?/app.js?v=20260825` querystrings in index.html MUST be bumped (`?v=20260913`) or browsers cache-serve old utils → sidebar stays old despite file changes. (Also bump-invalidate on every rollout: hard-refresh + `Ctrl+Shift+R` note to user.)
- app.js already cache-busts page modules with `Date.now()` — good, no change needed.
- Backend changes (server.py, new `/api/launchpad`) = `docker restart hermes-webui-gsga-agentic-os-1` and add the endpoint prefix to the `session_enforcement` allowlist (pitfall #11).
- Any endpoint used via WebUI proxy needs a prefix already forwarded, or must live under `/api/crm/…` (pitfall #12). **Decision: launchpad endpoint follows rule #12 — deploy as `/api/crm/launchpad`.**

### Verification (must-pass before user sign-off)
1. 81 → target page count is a non-goal; correctness is: every existing hash still routes (add `hiddenRoutes` entries for legacy hashes with redirect-to-tab behavior).
2. Path-parity test: `grep -c "data-page" index.html` after render, must equal number of visible NAV_CONFIG items.
3. 3-page spot check in dark + light: `#dashboard`, `#oncall` (now Suite), `#health` (now System tray).
4. `curl SSL` on every nav hash route to confirm no 307/404 surprises through Traefik.
5. Full inventory page shows all 81 files classified: live / merged/orphan / pending-archive.

---

## Phase 5 — Implementation Sequence (recommended order of PRs)

| PR | Slice | Files touched | Effort |
|----|-------|---------------|--------|
| 1 | Chrome cleanup + gate fixes | index.html (logo SVG, rogue emoji links, cache-bust) | S |
| 2 | Manifest of NAV_CONFIG v3 (3 zones, collapsed trays, hiddenRoutes legacy-map) — no page merges yet, just regroup + relabels | utils.js | S |
| 3 | Launchpad home (dashboard.js + /api/crm/launchpad + data/launchpad.json) | dashboard.js, server.py, modules/crm.py, data/launchpad.json | M |
| 4 | Styles refinement pass 1 (card weight, stat pills, emoji strip inside chrome; keep tokens) | styles.css | S |
| 5 | Suite merge: Schedule (call+staff+PDF) and Calendar (choose canonical) reusing mass-email tab pattern | 6 page files + utils.js | M |
| 6 | Suite merge: Compliance (absorbs evals+GME), Grand Rounds Hub, CRM tabs | 9 page files | M |
| 7 | Suite merge: AI Builder Suite, Workspace tabs, colophon | 8 page files | S |
| 8 | Emoji sweep remaining pages + light-mode rgba sweep + mobile nav polish | ~20 page files, styles.css | S |
| 9 | FAQ/cleanup: archive calendar2, .bak file, verify 3-page parity, flip DEFAULT_ROUTE back to `dashboard` | app.js, files | S |

**Total: ~4 focused sessions.** Slice 1-4 are skin/IA Cheap wins visible immediately; 5-7 are the IA payoff; 8-9 are polish.

### Delegation note (matches LLM routing rules)
- Planning/QA prompt tissue (already done, this doc) — session model.
- Per-page suite-merge JS code-writing — hand off to **DeepSeek (deepseek-flash)** per routing rule "DeepSeek CODES, premium TESTS", using the existing mass-email tabbed-page as the reference pattern.
- Final browser QA on `os.srv.../cloud` — session model + eyes-on screenshots only where design-token deviations might appear.

---

## Open questions for Shareef (one at a time, per conventions)

1. **Zone names** — happy with Home / Work / Build / System, or prefer Urology language? (This affects all nav labels; blocks PR 2.)
2. **DEFAULT page** — restore home to `dashboard` (Launchpad) instead of tasks? (Assume yes but confirm.)
3. **Orphan placement** — Sub-I exit interviews, resident letters, social-media-hub, distribution lists: which zone and are any retired?
4. **calendar.js vs calendar2.js vs cal-new.js** — which is the canonical current build, or let me run the parity diff and decide with evidence?
5. **Purple/pink logo mark** — replace with flat teal geometric logo (recommended), or keep shape only and just strip gradient colors?

---

## Risks & mitigations
| Risk | Mitigation |
|------|-----------|
| Class renames break 70 pages | hard rule: rename NOTHING (kept in plan verification) |
| User lands on stale cached sidebar | bump `?v=` on every index.html script tag per deploy (codified in deploy step) |
| Merged page loses a deep-coded fetch | run endpoint inventory per merged file before merge; each merged page keeps its own fetch code (tab pattern isolates render code) |
| Auth middleware 401s new endpoints | allowlist per pitfall #11 immediately after route add; verify with curl 307→200 chain |
| User dislikes re-org mid-flight | order PRs so sidebar-relabeled-only (PR 2) is its own deployable; every later suite merge is a reversible git revert |
