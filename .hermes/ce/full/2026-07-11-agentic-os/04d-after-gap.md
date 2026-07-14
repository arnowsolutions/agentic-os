# Phase 6.4d: After-Effect — Feature Gap Analysis

## What's Missing vs AGENTS.md Vision

The AGENTS.md file describes 38+ features. Current implementation status:

### Fully Implemented (30/38)
F1-F7, F9, F11-F15, F17-F22, F24-F26, F28-F32, F34-F35, F37-F38 — dashboard, agents, memory, skills, scheduler, kanban, eval, routing, chat

### Partially Implemented (5/38)
- **F8 (Self-Improving Skills):** eval.json exists but learnings loop is manual
- **F16 (Memory Consolidation):** Skill exists but cron integration unclear
- **F23 (Systematic Debug):** Skill defined but not integrated into dashboard
- **F27 (Skills Registry/Hub):** plugins.js page exists but marketplace integration is mock
- **F33 (Context References):** @-syntax mentioned but implementation is basic

### Not Implemented (3/38)
- **F10 (Shared Business Brain):** `brain/business-brain.md` exists but isn't auto-loaded by agents
- **F36 (Batch Processing):** No parallel skill execution from dashboard
- **Voice Mode (F30):** Hermes native voice not integrated into dashboard

## What's Missing vs Industry Standards

| Feature | Status |
|---------|--------|
| User management / roles | ✅ Auth module with CRM-based roles |
| Audit logging | ✅ Agent runs + CRM access logged |
| API rate limiting | ❌ |
| Pagination | ❌ (most list endpoints return all) |
| Search | ⚠️ Page search only, no data search |
| Export (CSV/PDF) | ✅ Call schedule PDF, some CSV |
| Notifications | ✅ Toast system, Telegram integration |
| Dark/light mode | ✅ |
| Mobile responsive | ❌ |
| Accessibility (a11y) | ❌ (no ARIA labels, keyboard nav) |
| i18n | ❌ |
| API docs (Swagger) | ✅ (FastAPI auto-generates) |

## Gap Score: 5.5/10

Core vision is implemented but polish features (pagination, search, mobile, a11y) are missing.
