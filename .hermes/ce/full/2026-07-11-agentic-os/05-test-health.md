# Phase 6.6: Test Health

**Status: CRITICAL — Essentially zero test coverage**

## Test Inventory

- **Test files found:** 2 (likely scaffold/example tests)
- **Test framework:** None detected (no pytest.ini, no conftest.py, no jest.config)
- **Coverage:** ~0%

## What Should Be Tested

### Backend (pytest)

| Area | Priority | Effort |
|------|----------|--------|
| Auth middleware (session validation) | P0 | Low |
| CRM CRUD operations | P0 | Low |
| Cost tracker calculations | P0 | Low |
| Agent routing logic | P1 | Low |
| Selftest endpoint | P1 | Low |
| Safe path validation | P1 | Low |
| Schedule parsing | P1 | Medium |
| Email template rendering | P2 | Medium |

### Frontend (no framework — manual or Playwright)

| Area | Priority | Effort |
|------|----------|--------|
| Hash routing (navigate function) | P0 | Low |
| NAV_CONFIG rendering | P1 | Low |
| API error handling | P1 | Medium |
| Page render smoke tests (70 pages) | P2 | High |

## Recommended First Tests

```python
# test_auth.py
def test_allowlisted_paths_bypass_auth():
    """Paths in allowlist should not require session cookie."""
    
def test_protected_paths_require_auth():
    """Non-allowlisted paths should return 401 without cookie."""

# test_cost_tracker.py
def test_record_computes_daily_totals():
    """Recording a cost entry should update daily totals."""

def test_free_tier_alert_triggers():
    """When usage exceeds warn_pct, alert should be generated."""
```

## Test Score: 0.5/10

Two scaffold test files. No framework, no coverage, no CI. Adding even 5 smoke tests would dramatically improve confidence.
