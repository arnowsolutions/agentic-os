# Phase 6.17: Agile Backlog — User Stories

## Epic 1: Production Reliability

### US-1.1: Server Auto-Restart
**As a** program manager  
**I want** the dashboard server to restart automatically if it crashes  
**So that** I don't lose access during critical operations  

**Acceptance Criteria:**
- [ ] Systemd unit or Docker restart policy configured
- [ ] Server recovers within 10 seconds of crash
- [ ] Health check endpoint responds within 30 seconds of restart

**Story Points:** 3

---

### US-1.2: Automated Backups
**As a** system administrator  
**I want** daily automated backups of all data files  
**So that** I can recover from data corruption or accidental deletion  

**Acceptance Criteria:**
- [ ] Cron job runs daily at 2 AM
- [ ] Backs up all JSON files in `data/`
- [ ] Keeps 7 days of rolling backups
- [ ] Backup success/failure is logged

**Story Points:** 5

---

### US-1.3: Data Validation Layer
**As a** developer  
**I want** all API mutation endpoints to validate input data  
**So that** invalid data can't corrupt the data store  

**Acceptance Criteria:**
- [ ] Pydantic models defined for all POST/PATCH/PUT endpoints
- [ ] Validation errors return 422 with clear messages
- [ ] CRM contact creation validates required fields
- [ ] Email group updates validate email format

**Story Points:** 8

---

## Epic 2: Testing Foundation

### US-2.1: Backend Smoke Tests
**As a** developer  
**I want** a basic test suite covering critical paths  
**So that** I can make changes with confidence  

**Acceptance Criteria:**
- [ ] 10+ pytest tests covering: auth middleware, CRM CRUD, cost tracker, agent routing, selftest, safe_path
- [ ] Tests run in CI or pre-commit
- [ ] All tests pass on clean checkout

**Story Points:** 8

---

### US-2.2: Frontend Linting
**As a** developer  
**I want** ESLint configured for JavaScript files  
**So that** code style is consistent and common bugs are caught early  

**Acceptance Criteria:**
- [ ] ESLint config with recommended rules
- [ ] `"use strict"` added to all JS files
- [ ] No lint errors on `api.js`, `utils.js`, `app.js`
- [ ] Pre-commit hook runs ESLint

**Story Points:** 3

---

## Epic 3: Mobile Support

### US-3.1: Responsive Dashboard
**As a** resident  
**I want** to check my schedule and complete evals from my phone  
**So that** I can do it between cases in the OR  

**Acceptance Criteria:**
- [ ] CSS media query at 768px collapses sidebar to hamburger menu
- [ ] Cards stack single-column on mobile
- [ ] Font sizes are readable (14px minimum)
- [ ] Touch targets are 44px minimum
- [ ] Tables scroll horizontally with visible scroll indicator

**Story Points:** 8

---

### US-3.2: Mobile Resident Portal
**As a** resident  
**I want** a quick way to access my portal from my phone  
**So that** I don't have to type my EZ ID and PIN every time  

**Acceptance Criteria:**
- [ ] EZ ID remembered in localStorage
- [ ] "Remember me" checkbox on login
- [ ] "Open in Resident Portal" shortcut on mobile home screen (PWA manifest)

**Story Points:** 5

---

## Epic 4: Developer Experience

### US-4.1: Extract Monolith Routes
**As a** developer  
**I want** route groups extracted from server.py into modules  
**So that** the codebase is navigable and changes are scoped  

**Acceptance Criteria:**
- [ ] Brain routes → `modules/brain.py`
- [ ] Skills routes → `modules/skills.py`
- [ ] Chat routes → `modules/chat.py`
- [ ] Scheduler routes → `modules/scheduler.py`
- [ ] Reports routes → `modules/reports.py`
- [ ] server.py is under 1000 lines

**Story Points:** 13

---

### US-4.2: TypeScript Core Files
**As a** developer  
**I want** TypeScript added to shared JavaScript modules  
**So that** IDE autocomplete works and field renames are safe  

**Acceptance Criteria:**
- [ ] `api.js` → `api.ts` with typed response interfaces
- [ ] `utils.js` → `utils.ts` with typed utility functions
- [ ] `app.js` → `app.ts` with typed router
- [ ] Page files remain vanilla JS (gradual migration)

**Story Points:** 8

---

### US-4.3: Shared UI Components
**As a** developer  
**I want** reusable components for common UI patterns  
**So that** I don't copy-paste the same HTML 70 times  

**Acceptance Criteria:**
- [ ] `PageHeader(title, subtitle, actions)` component
- [ ] `StatCard(icon, value, label, change)` component
- [ ] `DataTable(headers, rows, actions)` component
- [ ] `EmptyState(icon, message, action)` component
- [ ] 10+ pages refactored to use components

**Story Points:** 13

---

## Epic 5: Data Layer Upgrade

### US-5.1: SQLite Migration
**As a** system architect  
**I want** structured data migrated from JSON files to SQLite  
**So that** we have transactions, referential integrity, and querying  

**Acceptance Criteria:**
- [ ] SQLite schema for: contacts, evals, schedules, costs, sessions
- [ ] Migration script that preserves all existing data
- [ ] API endpoints updated to use SQLite
- [ ] Write operations use transactions
- [ ] JSON files are synced as backup (dual-write during transition)

**Story Points:** 21

---

### US-5.2: Full-Text Search
**As a** manager  
**I want** to search across all contacts, evals, and schedules  
**So that** I can find information without knowing which page it's on  

**Acceptance Criteria:**
- [ ] Search box queries SQLite FTS5 index
- [ ] Results show: contact name, page, matching snippet
- [ ] Search is fast (< 200ms for 1000+ records)

**Story Points:** 8

---

## Epic 6: User Experience

### US-6.1: Confirmation Dialogs
**As a** manager  
**I want** to see a confirmation before sending emails or making destructive changes  
**So that** I don't accidentally send to the wrong list or delete data  

**Acceptance Criteria:**
- [ ] Email resend shows "Send to N recipients?" with recipient count
- [ ] Contact deletion shows "Delete [Name]?" with undo option
- [ ] All destructive actions have confirmation

**Story Points:** 5

---

### US-6.2: Notification Center
**As a** user  
**I want** to see notifications for eval assignments, email results, and system alerts  
**So that** I don't miss important events  

**Acceptance Criteria:**
- [ ] Bell icon in topbar with unread count badge
- [ ] Notification dropdown shows recent 20 notifications
- [ ] Clicking notification navigates to relevant page
- [ ] Notifications persist across sessions

**Story Points:** 8

---

## Backlog Summary

| Epic | Stories | Total Points | Priority |
|------|---------|-------------|----------|
| Production Reliability | 3 | 16 | P0 |
| Testing Foundation | 2 | 11 | P0 |
| Mobile Support | 2 | 13 | P1 |
| Developer Experience | 3 | 34 | P1 |
| Data Layer Upgrade | 2 | 29 | P2 |
| User Experience | 2 | 13 | P2 |

**Total: 14 stories, 116 story points across 6 epics.**
