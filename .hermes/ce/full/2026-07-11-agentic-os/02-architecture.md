# Phase 6.2: Architecture Review

**Project:** Agentic OS  
**Date:** 2026-07-11  
**Analyzed:** 88 Python files, 73 JS files, 1 CSS file, 70 dashboard pages

---

## 1. System Architecture

### 1.1 Top-Level Structure

```
agentic-os/
├── server.py (3,400+ lines) — Monolithic FastAPI backend
├── dashboard/                  — SPA frontend (vanilla JS, no framework)
│   ├── index.html              — Shell with sidebar + topbar
│   ├── app.js                  — Hash router + dynamic page loader
│   ├── utils.js                — NAV_CONFIG, toast, theme, helpers
│   ├── api.js                  — REST client (get/post/put/patch/del)
│   ├── styles.css              — All styles (~1 file, CSS variables)
│   └── pages/                  — 70 page files, one JS per route
├── modules/                    — 8+ extracted Python modules
│   ├── crm.py                  — CRM contacts, GME, email groups
│   ├── auth.py                 — Session-based web auth
│   ├── config.py               — Settings from env/.env
│   ├── cost_tracker.py         — Spend/quota analytics
│   ├── kanban.py               — Kanban board
│   ├── vapi_bridge.py          — Vapi voice assistant bridge
│   ├── schedule.py             — On-call schedule
│   ├── skill_runner.py         — Agent skill execution
│   ├── metrics.py              — Prometheus metrics
│   ├── logging_config.py       — Structured logging
│   ├── llm_client.py           — OpenRouter LLM client
│   ├── identity.py             — Identity layer
│   └── supabase_client.py      — Supabase helper
├── data/                       — JSON data files (~127 files)
├── skills/                     — Skill definitions
├── brain/                      — Memory/brain files
├── scheduler/                  — APScheduler jobs
└── scripts/                    — Utility scripts
```

### 1.2 Architectural Pattern

**Monolith with Module Extraction (in-progress refactor):**

`server.py` started as a single-file FastAPI app (~3,400 lines). Several subsystems have been extracted into `modules/` (crm, auth, kanban, vapi, schedule, cost_tracker, metrics). However, `server.py` still contains:
- Agent execution engine (opencode, hermes, gemini)
- All remaining API routes (~50+ endpoints)
- Health checks, selftest, chat, cost recording
- File browser, brain, skills, scheduler, backups, settings
- Conference email, calendar, eval, GME, staff schedule
- Quick actions, PDF generation, Telegram

**Extraction status:** ~40% complete. 8 modules extracted; ~60% of server.py still monolithic.

### 1.3 Frontend Architecture

**Pattern:** Vanilla JS SPA with hash-based routing

```
User click → hashchange event → navigate()
  → loadPage(name) — dynamic <script> injection
  → window.renderXxx() — page render function
  → document.getElementById('pageContent').innerHTML = ...
```

- **No framework** — no React, Vue, or bundler
- **Dynamic script loading** — each page is a separate JS file loaded on first access
- **Page caching** — `pageCache` object prevents reloading
- **Hash routing** — `#page-name` → `renderPageName()` via camelCase conversion
- **NAV_CONFIG driven sidebar** — `utils.js` contains grouped nav items
- **Single CSS file** — CSS variables for theming (dark/light)

**Pros:** Zero build step, fast iteration, simple mental model  
**Cons:** No component reuse, template strings everywhere, manual DOM manipulation, no TypeScript

---

## 2. Data Flow

### 2.1 Request Lifecycle

```
Browser
  ↓ fetch('/api/xxx')
FastAPI middleware chain:
  1. metrics_middleware — counts requests
  2. session_enforcement — auth gate (allowlist or session cookie)
  3. webhook_validation — Vapi IP/signature check
  4. CORS middleware
  ↓
Route handler (in server.py or included router)
  ↓ reads/writes
JSON files in data/ (or Hermes cron/state files)
  ↓ returns
JSONResponse → Browser → innerHTML render
```

### 2.2 Auth Flow

```
Login: /api/auth/login → validate PIN from data/user_pins.json + CRM lookup
  → create opaque session token (secrets.token_urlsafe)
  → set aos_session cookie
  → redirect to /dashboard/

Subsequent requests:
  session_enforcement middleware → extract token from cookie
  → get_session(token) → touch_session(token) → request.state.user = session
  → allow or 401/redirect

Allowlisted paths: /api/status, /api/oncall/, /api/staff-schedule,
  /api/calendar/, /api/eval/, /api/conference/, /api/user/, /vapi/, /login, etc.
```

### 2.3 State Management

- **No client-side state manager** — all state is in DOM or local module variables
- **No server-side sessions for data** — JSON files on disk, read on every request
- **localStorage** for: theme preference, sidebar collapse state
- **No shared state between pages** — each render function is self-contained

---

## 3. Module Analysis

### 3.1 server.py (Monolith Core)

| Section | Lines (est.) | Status |
|---------|-------------|--------|
| Imports, setup, middleware | 1-200 | Clean |
| Session enforcement | 52-103 | Well-structured |
| Models, helpers, routing | 215-480 | OK |
| Status, health, selftest | 483-650 | Good |
| Agent execution engine | 650-1200 | Complex but extracted |
| API routes (skills, brain, etc.) | 1200-3400 | Still monolithic |

**Issues:**
1. **Duplicate `BASE_DIR` assignment** (lines 106 and 181)
2. **Manual .env loading** (lines 107-123) duplicates `config.py` functionality
3. **No route grouping** — all routes are flat `@app.get/post` decorators
4. **Large function bodies** — some routes are 50+ lines with nested logic

### 3.2 modules/crm.py

- **Pattern:** FastAPI APIRouter with `/api/crm` prefix
- **Size:** Moderate (~500+ lines)
- **Responsibilities:** Contacts CRUD, GME reimbursement, email groups, access logging
- **Data:** Reads/writes JSON files in `data/`
- **Quality:** Good — well-structured with helpers, logging, AY filtering

### 3.3 modules/auth.py

- **Pattern:** APIRouter + exported helper functions
- **Size:** Moderate
- **Auth model:** Session-based (cookie `aos_session`), PIN validation against CRM
- **Features:** Rate limiting, lockout, session expiry, identity integration
- **Quality:** Good — clean separation of concerns

### 3.4 modules/cost_tracker.py

- **Pattern:** Stateless functions operating on `data/cost-history.json`
- **Size:** Small (~100 lines)
- **Features:** Entry recording, daily totals, monthly projection, free-tier alerts
- **Quality:** Excellent — well-documented, single-responsibility

### 3.5 modules/config.py

- **Pattern:** Singleton Settings class with `@lru_cache`
- **Features:** Environment variable loading, .env file, typed settings
- **Quality:** Good, but `.env` loading in server.py (lines 107-123) duplicates this

---

## 4. Dashboard Page Architecture

### 4.1 Page Patterns Identified

The 70 pages fall into these patterns:

| Pattern | Pages | Example |
|---------|-------|---------|
| **Live API Dashboard** | dashboard, system-overview, health | Fetch status, render cards |
| **Filterable Feed** | notifications, audit, gme-tracker | Event stream with filters |
| **Iframe Embed** | vs-coder, claude-code, google-studio | Sandboxed external tools |
| **Form + Result** | call-schedule-pdf, conference-email, user | Input → API call → render |
| **Summary Stats + Tables** | eval-portal, compliance, gme-detail | Stat bar + data table |
| **CRUD Management** | contacts, email-groups, email-templates | List/create/edit/delete |
| **Tabbed Layout** | staff-schedule, oncall | Hospital tabs |
| **Chat Interface** | chat, omniroute | SSE streaming |
| **Events Timeline** | calendar, grand-rounds | Monthly-grouped cards |
| **Tool Launcher Grid** | quick-actions, my-tools | Clickable action cards |

### 4.2 Page Naming Convention

Pages follow kebab-case naming → camelCase render functions:
- `#call-schedule-pdf` → `renderCallSchedulePdf()`
- `#email-groups` → `renderEmailGroups()`
- `#grand-rounds` → `renderGrandRounds()`

### 4.3 NAV_CONFIG Architecture

The sidebar is populated dynamically from `NAV_CONFIG` in `utils.js`:

```js
NAV_CONFIG = {
  groups: [
    { label: '🏠 Home', items: [{page: 'dashboard', icon: '📊', label: 'Dashboard', ...}, ...] },
    { label: '🤖 Agents', items: [...] },
    { label: '💻 Development', items: [...] },
    { label: '📋 Operations', items: [...] },
    { label: '🏥 Urology', items: [...] },
    { label: '📱 Messaging', items: [...] },
    { label: '⚙️ System', items: [...] },
  ]
}
```

This is rendered by `renderSidebar()` which builds DOM from the config.

---

## 5. Integration Patterns

### 5.1 Agent Execution Engine

Three agents are managed:
- **opencode** — code generation, file operations, git
- **hermes** — persistent memory, cron, messaging
- **gemini** — research, multi-modal analysis

Each has:
- `check_agent(name)` — filesystem-based existence check
- `execute_agent(agent, message)` — subprocess execution with timeout
- `_agent_unavailable(agent, message)` — graceful fallback via OpenRouter LLM

### 5.2 External Service Integration

| Service | Integration Point | Pattern |
|---------|------------------|---------|
| Hermes Agent | CLI binary discovery | Subprocess |
| Cron jobs | `/home/hermeswebui/.hermes/cron/jobs.json` | Read-only |
| OpenRouter | `modules/llm_client.chat_completion` | HTTP API |
| Supabase | `modules/supabase_client` | HTTP API |
| Google OAuth | Token file at `data/google_token.json` | File-based |
| Vapi | Webhook endpoint | HTTP POST with signature validation |
| Telegram | Hermes gateway | Indirect via state.db |
| code-server | Iframe embed | External URL |
| OmniRoute | Client-side SSE | Direct from browser |

---

## 6. Architecture Health Assessment

### Strengths

1. **Clean module extraction pattern** — APIRouter + helper functions, well-isolated
2. **Auth middleware is solid** — allowlist pattern, session management, rate limiting
3. **No-framework frontend** — zero build step, fast iteration for a single-developer project
4. **CSS variable theming** — dark/light mode with clean variable names
5. **NAV_CONFIG-driven sidebar** — single source of truth for navigation
6. **Well-documented skills integration** — AGENTS.md is comprehensive

### Weaknesses

1. **server.py still too large** — 3,400+ lines, ~60% of routes not yet extracted
2. **No TypeScript** — 73 JS files with zero type safety
3. **No tests** — zero test files found in the entire project
4. **No component reuse** — each page duplicates header/tables/filter patterns
5. **JSON file database** — no migrations, no concurrency, no querying
6. **Manual DOM manipulation** — no virtual DOM, error-prone innerHTML
7. **No build/bundle step** — no minification, no tree shaking
8. **Duplicate .env loading** — server.py and config.py both load environment
9. **No API versioning** — all routes at `/api/`, no `/api/v1/` prefix

### Architecture Score: 6.0/10

A functional monolith with good extraction discipline but lacking modern engineering practices (tests, types, bundling, API versioning).

---

## 7. Recommendations

### Quick Wins
1. **Remove duplicate BASE_DIR / .env loading** in server.py
2. **Extract agent execution engine** from server.py to `modules/agent_engine.py`
3. **Extract remaining route groups** — brain, skills, chat, scheduler, reports, settings

### Medium Term
4. **Add TypeScript** — migrate `api.js`, `utils.js`, `app.js` first
5. **Add a test framework** — pytest for backend, at minimum smoke tests
6. **Introduce component pattern** — simple function-based components to reduce duplication

### Long Term
7. **Consider migration to template engine** (Jinja2 server-side rendering) or a lightweight framework (Alpine.js, htmx) for better component reuse
8. **Add API versioning** — `/api/v1/` prefix before routes proliferate further
9. **Database migration** — move from JSON files to SQLite for data that needs querying/transactions (contacts, evals, schedules)
