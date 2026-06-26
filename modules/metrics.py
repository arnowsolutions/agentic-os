"""Prometheus instrumentation for Agentic OS.

Provides a `/metrics` endpoint and a few key counters/histograms for the
voice webhook pipeline. The `prometheus-client` library is optional at runtime:
if it is not installed, metrics are disabled and the endpoint returns a
friendly 503 so the app keeps working with the base requirements.txt.

This module handles **HTTP-level instrumentation** (request counts, durations,
webhook counters, auth attempts).  It is intentionally separate from
``modules/cost_tracker.py`` which owns per-agent token spend, dollar cost,
free-tier quota, and cost analytics stored in ``data/cost-history.json``.
"""
from __future__ import annotations

import logging
import time
from typing import Any, Callable

from fastapi import Request, Response
from fastapi.responses import PlainTextResponse

logger = logging.getLogger("agentic_os.metrics")

# Optional dependency
try:
    from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
    _METRICS_ENABLED = True
except Exception:  # pragma: no cover
    _METRICS_ENABLED = False


def _noop(*args, **kwargs):
    pass


class MetricsCollector:
    """Wraps prometheus_client primitives with safe fallbacks."""

    def __init__(self):
        self.enabled = _METRICS_ENABLED
        if self.enabled:
            self.request_count = Counter(
                "agentic_os_requests_total",
                "Total HTTP requests",
                ["method", "path", "status_code"],
            )
            self.request_duration = Histogram(
                "agentic_os_request_duration_seconds",
                "HTTP request duration",
                ["method", "path"],
            )
            self.vapi_webhook_count = Counter(
                "agentic_os_vapi_webhooks_total",
                "Total Vapi webhooks received",
                ["function", "status"],
            )
            self.auth_attempt_count = Counter(
                "agentic_os_auth_attempts_total",
                "Total voice auth attempts",
                ["result"],
            )
        else:
            self.request_count = None
            self.request_duration = None
            self.vapi_webhook_count = None
            self.auth_attempt_count = None

    def observe_request(self, method: str, path: str, status_code: int, duration: float):
        if not self.enabled:
            return
        self.request_count.labels(method=method, path=path, status_code=str(status_code)).inc()
        self.request_duration.labels(method=method, path=path).observe(duration)

    def observe_vapi_webhook(self, function: str, status: str):
        if not self.enabled:
            return
        self.vapi_webhook_count.labels(function=function or "unknown", status=status).inc()

    def observe_auth_attempt(self, result: str):
        if not self.enabled:
            return
        self.auth_attempt_count.labels(result=result).inc()

    def metrics_response(self) -> Response:
        if not self.enabled:
            return PlainTextResponse(
                "# Prometheus metrics disabled: prometheus-client not installed\n",
                status_code=503,
            )
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Module-level singleton
_collector = MetricsCollector()


def get_collector() -> MetricsCollector:
    return _collector


def metrics_endpoint() -> Response:
    return _collector.metrics_response()


async def metrics_middleware(request: Request, call_next: Callable[[Request], Any]) -> Response:
    """FastAPI middleware that records request counts and durations."""
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start

    status = getattr(response, "status_code", 0)
    path = request.url.path
    method = request.method
    _collector.observe_request(method, path, status, duration)
    return response
