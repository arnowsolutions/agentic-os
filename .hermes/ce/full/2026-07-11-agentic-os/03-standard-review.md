# Phase 6.3: Standard Code Review

**Project:** Agentic OS  
**Date:** 2026-07-11

## Summary

Standard ce:review run on the full codebase (no git diff — full project audit). 88 Python files, 73 JS files analyzed.

---

## P0 — Critical

### P0-1: No authentication on CRM write endpoints
**File:** `modules/crm.py`  
**Severity:** P0  
The CRM module's write endpoints (POST/PATCH/DELETE) are behind the `session_enforcement` middleware but the CRM router uses `/api/crm` prefix which is NOT in the allowlist. This means all CRM mutations require a valid session cookie — which is correct behavior. However, the read endpoints are also blocked, requiring auth for basic CRM lookups. **Status: By-design, not a vulnerability.**

### P0-2: No CSRF protection
**File:** `server.py`  
The session cookie (`aos_session`) has no `SameSite` attribute set. All POST/PUT/DELETE endpoints accept requests with the cookie alone — no CSRF token required. Combined with CORS allowing wildcard methods, this is a theoretical CSRF risk if the dashboard is accessible from other origins. **Mitigation:** The dashboard is internal-only (localhost/VPS).

### P0-3: API key in client-side code
**File:** `dashboard/pages/omniroute.js`  
The OmniRoute chat page embeds an API key for direct client-side API calls. This is intentional (the page calls OmniRoute directly) but the key is visible in browser devtools. **Risk:** Low — the key is scoped to OmniRoute and the dashboard is authenticated.

---

## P1 — High

### P1-1: No input validation on most endpoints
Many API routes accept raw JSON bodies without Pydantic model validation. Routes that DO use models (chat, brain update, settings update) are protected, but custom routes (quick-action, PDF generation) accept generic `data: dict`.

### P1-2: JSON file concurrency
Multiple endpoints read/write the same JSON files without file locking. Under concurrent requests, this can corrupt data files (e.g., `cost-history.json`, `eval_forms.json`, `crm_contacts.json`).

### P1-3: Path traversal in fs/read and fs/list
The `_safe_path()` function exists but its usage is inconsistent. Some fs endpoints accept user-supplied paths directly.

### P1-4: No rate limiting on login
`/api/auth/login` has lockout after 5 attempts but no IP-based rate limiting. Brute-force across different accounts is possible.

---

## P2 — Medium

### P2-1: Unused imports in server.py
`httpx` imported but usage unclear; `asyncio` imported but server uses synchronous handlers.

### P2-2: Print-based debugging left in production
```python
print(f"[AUTH DEBUG] path={path}", flush=True)  # server.py line 60
```

### P2-3: Redundant `/metrics` endpoint
Prometheus metrics are exposed at both `/metrics` (standard) and via the `metrics_endpoint` function. No authentication on the metrics endpoint.

### P2-4: No request logging
No structured request logging beyond the Prometheus middleware. Failed requests are hard to debug.

### P2-5: Script injection via page rendering
All 70 page JS files use `innerHTML` for rendering. While inputs are mostly API-driven, any user-controlled data rendered via `innerHTML` without sanitization is an XSS vector. The `escapeHtml()` utility exists but usage is inconsistent.

---

## P3 — Low

### P3-1: No docstrings on most route handlers
Only a handful of endpoints have docstrings. The selftest endpoint is well-documented; most others have none.

### P3-2: Inconsistent error response format
Some endpoints return `{"error": "..."}`, others return `{"detail": "..."}`, others throw HTTPException.

### P3-3: Duplicate `BASE_DIR` assignment
Lines 106 and 181 both set `BASE_DIR = Path(__file__).parent.resolve()`.

### P3-4: No .gitignore entry for `.env`
The `.env` file with API keys could be accidentally committed.

---

## Code Quality Score: 6.5/10

**Good:** Clean module extraction, well-structured middleware, consistent API patterns in extracted modules.  
**Needs work:** Input validation, file concurrency, error formatting consistency, debug print removal.
