# Phase 6.9: API Surface Audit

## API Inventory

~50+ endpoints across server.py and extracted modules.

### Route Groups

| Prefix | Module | Endpoints | Auth | Notes |
|--------|--------|-----------|------|-------|
| `/api/status` | server.py | 1 | Public | Health + agent status |
| `/api/selftest` | server.py | 1 | Public | One-click health check |
| `/api/health/full` | server.py | 1 | Public | Full health dashboard |
| `/api/auth/*` | auth.py | 4+ | Public (login) / Session | Login, logout, session check |
| `/api/crm/*` | crm.py | 10+ | Session | Contacts CRUD, GME, email groups |
| `/api/kanban/*` | kanban.py | 5+ | Session | Board, tasks, complete, block |
| `/api/vapi/*` | vapi_bridge.py | 5+ | Vapi auth | Pins, status, webhooks |
| `/api/schedule/*` | schedule.py | 3+ | Session | On-call, staff schedule |
| `/api/oncall/*` | server.py | 5+ | Public | Allowlisted — no auth required |
| `/api/staff-schedule` | server.py | 1 | Public | Allowlisted |
| `/api/calendar/*` | server.py | 2+ | Public | Allowlisted |
| `/api/eval/*` | server.py | 2+ | Public | Allowlisted |
| `/api/conference/*` | server.py | 1+ | Public | Allowlisted |
| `/api/user/*` | server.py | 1 | Public | Resident portal |
| `/api/cost*` | server.py | 2 | Session | Cost history + recording |
| `/api/chat*` | server.py | 2 | Session | Agent chat + history |
| `/api/skills*` | server.py | 5+ | Session | Skills CRUD + run + eval |
| `/api/scheduler/*` | server.py | 4+ | Session | Jobs CRUD |
| `/api/brain*` | server.py | 3 | Session | Memory file CRUD |
| `/api/backup*` | server.py | 3 | Session | Backup create/restore/list |
| `/api/settings*` | server.py | 2 | Session | Settings get/update |
| `/api/plugins*` | server.py | 2 | Session | Plugin list/install |
| `/api/standards*` | server.py | 2 | Session | Standards get/discover |
| `/api/prompts*` | server.py | 1 | Session | Prompt library |
| `/api/quick-action` | server.py | 1 | Session | Generic subprocess runner |
| `/api/call-schedule/pdf` | server.py | 1 | Session | PDF generation |
| `/api/telegram/*` | server.py | 2 | Session | Telegram status/logs |
| `/api/notifications*` | server.py | 2 | Session | Notification feed |
| `/api/fs/*` | server.py | 2 | Session | File browser |
| `/api/router/*` | server.py | 2 | Session | Agent routing |
| `/api/swap/*` | server.py | 1 | Session | Swap processing |
| `/api/agent-runs*` | server.py | 1 | Session | Agent run history |
| `/api/pdf-archive` | server.py | 1 | Session | PDF archive list |
| `/api/gme/detail` | server.py | 1 | Session | GME detail |
| `/api/morning-briefing` | server.py | 1 | Session | Briefing data |
| `/api/images-to-pdf` | server.py | 1 | Public | Image conversion |
| `/metrics` | server.py | 1 | Public | Prometheus metrics |
| `/api/omniroute-chat` | server.py | 1 | Public | OmniRoute proxy |
| `/api/crm-data-gaps` | server.py | 1 | Public | Data gap analysis |
| `/api/calendar-invites` | server.py | 1 | Public | Calendar invite endpoint |

## API Quality Issues

### Auth Inconsistency
- Some endpoints are public (allowlisted), others require session
- No clear principle for what's public vs protected
- `/api/oncall/` data is public but `/api/schedule/` requires auth

### Naming Inconsistency
- `/api/cost` vs `/api/cost/record` (some use sub-paths, others use query params)
- `/api/telegram/status` vs `/api/telegram/logs` (pluralization mismatch)
- `/api/oncall/now` vs `/api/oncall/date` (some use sub-paths, some query params)

### Response Format Inconsistency
- Some return `{"status": "ok", "data": [...]}`
- Some return `{"events": [...], "count": N}`
- Some return bare arrays
- Error format varies: `{"error": "..."}`, `{"detail": "..."}`, or HTTPException

### Missing Features
- No pagination on any list endpoint
- No filtering on most endpoints (except CRM)
- No sorting options
- No field selection (always returns full objects)
- No API versioning (`/api/v1/`)

## API Score: 5.5/10

Comprehensive API surface but inconsistent auth, naming, and response formats. No pagination or versioning.
