# Vapi / Agentic OS Technical Debt & Cleanup

> Captured during the V3 knowledge-base + caller-verification hardening pass.
> Core fixes are live; the items below should be resolved in priority order.

## P0 — Fix before next production incident
1. **Legacy deploy scripts** — [x] archived to `legacy/`; `deploy_vapi_v5.py` is canonical.
2. **Hardcoded API keys** — [x] moved to `.env` via `modules/config.py`; source files no longer contain keys.
3. **Rate limiting + PIN lockout** — [x] `_AuthLimiter` with 5 attempts / 5-minute lockout in `vapi_bridge.py`.
4. **Structured logging** — [x] `modules/logging_config.py` writes JSON lines to `logs/vapi_webhook.log`.

## P1 — Harden architecture and reduce bugs
5. **Integration tests** — [x] `tests/test_vapi_webhooks.py` (17 tests passing).
6. **Route prefix unification** — [x] `/vapi` used everywhere; `/api/vapi` references removed.
7. **`vapi_data.py` / `vapi_unified.py` validation** — [x] reviewed; modules import and core functions execute. Missing data files cause empty results locally, but code paths are sound.
8. **Webhook validation middleware** — [x] added in `server.py`; configure `WEBHOOK_SECRET` / `WEBHOOK_IP_ALLOWLIST` when ready. HMAC-SHA256 signature verified against `x-signature-sha256`.
9. **CRM/PIN cache** — [x] `_load_json_cached()` with 60-second TTL in `vapi_bridge.py`.
10. **Supabase `auth_attempts` table** — [x] migration at `migrations/001_create_auth_attempts.sql`; `_log_auth_attempt()` writes caller name, PIN length, success, reason, client IP, user agent, and assistant ID via `modules/supabase_client.py`.

## P2 — Improve operability and scalability
11. **Containerize / systemd-ize** — [x] `Dockerfile` + `docker-compose.yml` added; non-root user, healthcheck, log/data volumes.
12. **Hybrid knowledge search** — [x] TF-IDF + LSA semantic implemented locally; migration path to Supabase `pgvector` documented below and in `migrations/002_enable_pgvector.sql`.
13. **Admin dashboard** — [x] live at `/vapi/admin` and `/vapi/admin/api/audit`.
14. **Centralized configuration** — [x] `modules/config.py` with env loading; `.env.example` provided.
15. **Prometheus metrics** — [x] `/metrics` endpoint in `server.py`; counters/histograms for requests, Vapi webhooks, and auth attempts in `modules/metrics.py`. `prometheus-client` added to `requirements.txt`; scrape config in `monitoring/prometheus.yml`.

## P3 — Next-gen features built in this pass
16. **Post-call summary pipeline** — [x] `modules/vapi_call_summary.py`.
17. **Predictive call-swap intelligence** — [x] `modules/vapi_swap.py`.
18. **Voice concierge expansion** — [x] `getDeadlines`, `getEvaluationsDue`.

## Supabase `pgvector` migration path
When you want to move from local LSA to a managed vector store:
1. Enable the `pgvector` extension in Supabase.
2. Run `migrations/002_enable_pgvector.sql` to create the `knowledge_chunks` table, index, and `match_knowledge_chunks` RPC function.
3. Swap `modules/vapi_knowledge.py` to embed chunks with `sentence-transformers/all-MiniLM-L6-v2`
   (or OpenAI embeddings) and query Supabase via `pgvector` using `modules/supabase_client.py`.
4. Keep the TF-IDF keyword index as a fallback for offline resilience.

## Auth attempt audit table
Run `migrations/001_create_auth_attempts.sql` in the Supabase SQL Editor. The
`auth_attempts` table records every PIN attempt with:
- `caller_name`, `pin_length`, `success`, `reason`, `source`
- `client_ip`, `user_agent`, `assistant_id`
- `created_at`

A public-safe view `auth_attempts_public` is included for dashboards.

## Operational commands
- Start server: `python3 server.py --port 8090 --host 0.0.0.0`
- Run tests: `pytest tests/test_vapi_webhooks.py -v`
- Deploy to Vapi: `python3 deploy_vapi_v5.py`
- Health watchdog: `python3 vapi_health_check.py`
- Tunnel watchdog: `python3 vapi_url_watchdog.py`
- Admin dashboard: `https://<tunnel>/vapi/admin`
- Metrics: `http://localhost:8090/metrics`

### Docker
```bash
cp .env.example .env        # fill in secrets
docker compose up --build   # exposes http://localhost:8090
```

### Prometheus (optional)
Uncomment the `prometheus` service in `docker-compose.yml` or point an external
Prometheus instance at `monitoring/prometheus.yml`.

## Done in this pass
- [x] Fixed `vapi_knowledge.py` regex, duplicate state, and rebuilt index (219 docs).
- [x] Rewrote `vapi_bridge.py` `_handle_auth()` with structured response envelope and STT name normalization.
- [x] Updated webhook handler to consume `verifyCaller`/`authUser` and propagate `retry_pin` / `take_message` next steps.
- [x] Updated `shareef-vapi-v2-prompt.md` to enforce `knowledgeSearch` and deterministic PIN retry flow.
- [x] Aligned `deploy_vapi_v5.py` server URL to `{tunnel}/vapi` and tool list to `/tmp/v5_tools.json`.
- [x] Fixed `vapi_health_check.py` and `vapi_url_watchdog.py` endpoint paths and deploy-script references.
- [x] Fixed `/api/health/full` vapi_bridge URL check to `/vapi/status`.
- [x] Deployed Vapi V5 to production assistant (22 tools, GPT-4o).
- [x] Added `modules/supabase_client.py` with SDK + httpx fallback.
- [x] Added `migrations/001_create_auth_attempts.sql` and `migrations/002_enable_pgvector.sql`.
- [x] Added `Dockerfile`, `docker-compose.yml`, and `monitoring/prometheus.yml`.
- [x] Added Prometheus `/metrics` endpoint and request/webhook/auth instrumentation.
