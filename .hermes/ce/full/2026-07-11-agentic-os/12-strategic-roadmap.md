# Phase 6.13: Strategic Roadmap

## Current State: v1.1.0 — "Functional Prototype"

Agentic OS is a working multi-agent dashboard that successfully orchestrates opencode, Hermes, and Gemini agents for Montefiore Urology operations. It's feature-rich (70 pages, 50+ API endpoints) but built as a solo-developer monolith.

---

## Phase 1: Foundation (Month 1) — "Productionize"

**Goal:** Make the current system reliable, secure, and maintainable.

### Week 1-2: Critical Fixes
- [ ] Remove debug prints, duplicate code, consolidate .env loading
- [ ] Add atomic writes for all JSON data files
- [ ] Add input validation (Pydantic models) for mutation endpoints
- [ ] Add error handling to all fetch() calls in dashboard pages
- [ ] Add confirmation dialogs for destructive actions

### Week 3-4: Testing & Monitoring
- [ ] Set up pytest with 10 smoke tests (auth, CRM, cost tracker, routing)
- [ ] Add ESLint for JavaScript files
- [ ] Add process supervisor (systemd or Docker restart policy)
- [ ] Configure health check endpoint for Traefik
- [ ] Set up daily backup cron job

**Deliverable:** v1.2.0 — Reliable, tested, monitored dashboard

---

## Phase 2: Growth (Month 2-3) — "Scale & Polish"

**Goal:** Make the system ready for multiple contributors and broader adoption.

### Month 2: Developer Experience
- [ ] Extract remaining route groups from server.py to modules (brain, skills, chat, scheduler, reports)
- [ ] Add TypeScript to `api.js`, `utils.js`, `app.js`
- [ ] Introduce simple component pattern for shared UI (page header, stat card, data table)
- [ ] Add CSS methodology (BEM) and split styles.css
- [ ] Add API versioning (`/api/v1/`)
- [ ] Add pagination to list endpoints

### Month 3: User Experience
- [ ] Mobile responsive layout (hamburger menu, single-column cards)
- [ ] Role-based default landing pages
- [ ] Recently visited pages in sidebar
- [ ] Notification center for in-app alerts
- [ ] "Remember me" for Resident Portal
- [ ] Loading skeletons instead of spinners

**Deliverable:** v2.0.0 — Polished, multi-contributor-ready dashboard

---

## Phase 3: Maturity (Month 4-6) — "Platform"

**Goal:** Transform from dashboard into a platform.

### Month 4-5: Data Layer
- [ ] Migrate from JSON files to SQLite for structured data (contacts, evals, schedules, costs)
- [ ] Add schema migrations (Alembic or simple versioned SQL files)
- [ ] Add foreign key constraints and referential integrity
- [ ] Add full-text search across contacts, evals, skills

### Month 6: Ecosystem
- [ ] Plugin marketplace (real integration, not mock)
- [ ] Webhook system for external integrations
- [ ] Public API with rate limiting and API keys
- [ ] Analytics dashboard (page views, feature usage, error rates)
- [ ] Automated onboarding flow for new residents

**Deliverable:** v3.0.0 — Platform with data integrity, search, and extensibility

---

## Phase 4: Vision (Month 7-12) — "Ambition"

**Goal:** Features from AGENTS.md that aren't yet implemented.

- [ ] Voice mode integration (Hermes voice → dashboard)
- [ ] Batch/parallel skill execution
- [ ] Self-improving skills loop (automated eval → improvement)
- [ ] AI-powered search ("find the resident who was on call when...")
- [ ] Predictive scheduling suggestions
- [ ] Mobile native app (PWA)

---

## Resource Estimates

| Phase | Effort | Risk | Impact |
|-------|--------|------|--------|
| Phase 1: Foundation | 40 hrs | Low | High — reliability |
| Phase 2: Growth | 80 hrs | Medium | High — usability + maintainability |
| Phase 3: Maturity | 120 hrs | High | Medium — platform value |
| Phase 4: Vision | 200+ hrs | High | Variable — depends on adoption |
