# Phase 6.8a: Data Integrity Audit

## Data Stores & Their Integrity Risks

### 1. CRM Contacts (`data/crm_contacts.json`)
- **Risk:** Concurrent writes can corrupt the file
- **Backup:** No automated backup
- **Validation:** No schema enforcement — any shape can be written
- **Referential integrity:** EZ IDs referenced in eval_forms, user_pins, gme_tracker — no guarantee they exist in CRM
- **Status:** ⚠️ High risk for primary data store

### 2. User PINs (`data/user_pins.json`)
- **Risk:** PINs stored as SHA256 hashes — good
- **Issue:** Default PINs generated from phone numbers (last 4 digits) — predictable
- **Status:** ⚠️ PIN generation is deterministic and weak

### 3. Sessions (`data/sessions.json`)
- **Risk:** Session tokens stored in plain JSON. If file is readable, all sessions are compromised.
- **Issue:** No session timeout enforcement at file level — relies on expiry check
- **Status:** ⚠️ File-based session store is inherently less secure than server-side memory

### 4. Cost History (`data/cost-history.json`)
- **Risk:** Single writer pattern enforced by cost_tracker module — good
- **Cap:** MAX_ENTRIES = 1000 — will silently drop old entries
- **Status:** ✅ Well-managed with atomic writes

### 5. Eval Forms (`data/eval_forms.json`)
- **Risk:** Growing file with all eval history — no archiving
- **Status:** ⚠️ No size limits, no archival strategy

### 6. Email Groups (`data/email_groups.json`)
- **Risk:** Manual edits to recipient lists — no validation that emails are valid
- **Status:** ⚠️ Typos in email addresses will cause silent delivery failures

### 7. Conference/Calendar Data
- **GR_DATA** in `grand-rounds.js` IS the canonical source for academic schedule
- **calendar_events.json** — merged manual + Google-synced events
- **Risk:** Two sources of truth for events; merge conflicts possible
- **Status:** ⚠️ Manual + automated sync = drift risk

## Critical Data Integrity Gaps

1. **No backup system** — backup endpoint exists but no scheduled backups
2. **No data validation layer** — each endpoint validates (or doesn't) independently
3. **No foreign key enforcement** — orphaned references across JSON files
4. **No audit trail for data changes** — CRM access is logged, but mutations aren't
5. **No data recovery procedure** — if a JSON file is corrupted, there's no restore process

## Data Integrity Score: 4.0/10

JSON files are convenient but fragile. No transactions, no validation layer, no backups, no recovery plan.
