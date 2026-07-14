# Phase 6.5: Dependency & Supply Chain Audit

## Python Dependencies (from imports)

| Package | Usage | Risk |
|---------|-------|------|
| fastapi | Web framework | Low — mature, widely used |
| uvicorn | ASGI server | Low |
| pydantic | Data validation | Low |
| httpx | HTTP client | Low |
| apscheduler | Cron scheduling | Low |
| paramiko | SSH/SFTP for VPS deploy | Low |
| supabase | Database client | Medium — external service dependency |
| google-auth | Google OAuth | Medium — token expiry issues documented |
| scikit-learn | ML (unclear usage) | Medium — heavy dep for dashboard |

## Frontend Dependencies

| Library | Usage | Risk |
|---------|-------|------|
| Chart.js (CDN) | Dashboard gauges | Low — but CDN dependency |
| Inter font (Google Fonts CDN) | Typography | Low |

## Supply Chain Risks

1. **CDN dependencies** — Chart.js and Inter font loaded from external CDNs. If CDN is down, dashboard loses charts and typography.
2. **No lockfile** — no `requirements.txt` with pinned versions visible. Dependency drift risk.
3. **scikit-learn dependency** — imported but unclear if actually used. Heavy package for a dashboard.
4. **No vulnerability scanning** — no `pip-audit`, `safety`, or Dependabot
5. **Google API dependency** — Gmail API for email sending. Token refresh issues have caused production outages (documented in agentic-os-dashboard skill pitfalls).

## Dependency Score: 6.0/10

Minimal dependency footprint is good. Lack of pinning and vulnerability scanning is a gap.
