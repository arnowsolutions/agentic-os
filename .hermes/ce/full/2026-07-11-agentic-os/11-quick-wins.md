# Phase 6.12: Quick Wins (< 30 min each)

These fixes require minimal code changes with maximum impact.

---

## ⚡ Security

| # | Fix | File | Time | Impact |
|---|-----|------|------|--------|
| QW1 | Remove debug print in middleware | `server.py:60` | 1 min | Removes log noise, no auth path leakage |
| QW2 | Add `.env` to `.gitignore` | `.gitignore` | 1 min | Prevents accidental secret commit |
| QW3 | Add `SameSite=Strict` to session cookie | `auth.py` / `server.py` | 5 min | CSRF hardening |

## ⚡ Code Quality

| # | Fix | File | Time | Impact |
|---|-----|------|------|--------|
| QW4 | Remove duplicate `BASE_DIR` assignment | `server.py:181` | 1 min | Code cleanliness |
| QW5 | Remove duplicate `.env` loading (keep `config.py` version) | `server.py:107-123` | 5 min | Single source of truth for config |
| QW6 | Add `"use strict"` to `api.js`, `utils.js`, `app.js` | 3 files | 3 min | Catches silent JS errors |
| QW7 | Add JSDoc types to `api.js` functions | `api.js` | 15 min | IDE autocomplete for all pages |

## ⚡ User Experience

| # | Fix | File | Time | Impact |
|---|-----|------|------|--------|
| QW8 | Store EZ ID in localStorage for Resident Portal | `pages/user.js` | 10 min | Residents don't re-enter EZ ID |
| QW9 | Add confirmation dialog to conference email resend | `pages/conference-email.js` | 10 min | Prevents accidental mass email |
| QW10 | Add "Recently Visited" to sidebar | `app.js` + `utils.js` | 20 min | Faster navigation |

## ⚡ Reliability

| # | Fix | File | Time | Impact |
|---|-----|------|------|--------|
| QW11 | Add `try/catch` to `fetch()` calls missing error handling | ~10 page files | 20 min | Prevents white-screen crashes |
| QW12 | Add timeout to `fetch()` calls (10s default) | `api.js` | 10 min | Prevents hanging on network issues |
| QW13 | Add atomic write to CRM save operation | `modules/crm.py` | 15 min | Prevents data corruption |

## ⚡ Mobile

| # | Fix | File | Time | Impact |
|---|-----|------|------|--------|
| QW14 | Add single `@media (max-width: 768px)` breakpoint | `styles.css` | 15 min | Dashboard usable on phones |
| QW15 | Add hamburger menu toggle for mobile | `index.html` + `app.js` | 20 min | Mobile navigation |

---

**Total: ~2.5 hours for 15 high-impact fixes.**
