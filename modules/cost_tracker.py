"""
Single source of truth for spend / quota analytics in ``data/cost-history.json``.

Owns all reads and writes — no other module touches the file directly.
Recomputes ``daily_totals``, ``monthly_projection``, and per-provider free-tier
alerts on every ``record()`` call.

This module handles **spend analytics**.  Prometheus request instrumentation
lives in ``modules/metrics.py`` and is intentionally separate: metrics tracks
HTTP-level request counts / durations / webhook auth counters; cost_tracker
tracks per-agent token usage, dollar spend, and free-tier quota burn.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from modules.config import get_settings

logger = logging.getLogger("agentic_os.cost_tracker")

# ── Constants ──────────────────────────────────────────────────────────

DEFAULT_SHAPE: dict[str, Any] = {
    "entries": [],
    "daily_totals": {},
    "monthly_projection": 0,
    "free_tier_alerts": [],
}

MAX_ENTRIES = 1000  # cap to bound file growth

# Sensible per-provider free-tier defaults when settings are absent.
# Derived from public pricing pages (June 2026).  0 = no cap.
DEFAULT_FREE_TIER_LIMITS: dict[str, dict[str, Any]] = {
    "gemini": {
        "monthly_token_cap": 1_000_000,
        "monthly_cost_cap": 0.0,
        "warn_pct": 80,
        "description": "Gemini Flash free tier",
    },
    "opencode": {
        "monthly_token_cap": 2_000_000,
        "monthly_cost_cap": 0.0,
        "warn_pct": 80,
        "description": "OpenCode Go free tier (2M tokens/month)",
    },
}

# Default warn percentage used when a provider has no explicit `warn_pct`
DEFAULT_WARN_PCT = 80


# ── Helpers ────────────────────────────────────────────────────────────

def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _settings_file() -> Path:
    return get_settings().DATA_DIR / "settings.json"


def _history_path() -> Path:
    return get_settings().DATA_DIR / "cost-history.json"


def _load() -> dict[str, Any]:
    """Load cost-history.json, returning the canonical default shape
    when the file is missing or unparseable."""
    path = _history_path()
    if not path.exists():
        return _default_copy()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        logger.warning("cost-history.json is corrupt; resetting", exc_info=True)
        return _default_copy()
    # Fill in any missing keys
    for key, default in DEFAULT_SHAPE.items():
        data.setdefault(key, default)
    return data


def _default_copy() -> dict[str, Any]:
    return json.loads(json.dumps(DEFAULT_SHAPE))


def _save(data: dict[str, Any]) -> None:
    """Persist atomically — ensure DATA_DIR exists, then write."""
    path = _history_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def _resolve_limits() -> dict[str, dict[str, Any]]:
    """Merge defaults with any per-provider overrides in settings.json."""
    limits = dict(DEFAULT_FREE_TIER_LIMITS)  # shallow copy
    sf = _settings_file()
    if sf.exists():
        try:
            custom = json.loads(sf.read_text()).get("free_tier_limits", {})
            if isinstance(custom, dict):
                for provider, cfg in custom.items():
                    if isinstance(cfg, dict):
                        limits.setdefault(provider, {}).update(cfg)
        except Exception:
            logger.warning("Could not read free_tier_limits from settings.json", exc_info=True)
    return limits


# ── Core API ───────────────────────────────────────────────────────────

def record(
    agent: str,
    model: str,
    tokens: int,
    cost: float,
    provider: Optional[str] = None,
) -> dict[str, Any]:
    """Record one cost entry, recompute aggregates, and persist.

    Returns the full updated structure (same shape as ``get_history()``).
    """
    data = _load()

    entry = {
        "timestamp": _iso_now(),
        "agent": agent,
        "model": model,
        "tokens": tokens,
        "cost": cost,
    }
    if provider:
        entry["provider"] = provider

    data["entries"].append(entry)

    # ── Recompute daily_totals ──────────────────────────────────────
    daily: dict[str, float] = {}
    for e in data["entries"]:
        day = e["timestamp"][:10]  # YYYY-MM-DD
        daily[day] = daily.get(day, 0.0) + (e.get("cost", 0.0) or 0.0)
    data["daily_totals"] = daily

    # ── Recompute monthly_projection ─────────────────────────────────
    now = datetime.now(timezone.utc)
    current_month = now.strftime("%Y-%m")  # e.g. "2026-06"
    month_days = [d for d in daily if d.startswith(current_month)]
    if month_days:
        daily_avg = sum(daily[d] for d in month_days) / len(month_days)
        # Days in current month
        next_month = (now.month % 12) + 1
        next_year = now.year + (1 if now.month == 12 else 0)
        days_in_month = (
            datetime(next_year, next_month, 1, tzinfo=timezone.utc)
            - datetime(now.year, now.month, 1, tzinfo=timezone.utc)
        ).days
        projection = daily_avg * days_in_month
    else:
        projection = 0.0
    data["monthly_projection"] = round(projection, 6)

    # ── Recompute free_tier_alerts ───────────────────────────────────
    data["free_tier_alerts"] = _evaluate_free_tier(data)

    # ── Cap entries for file growth ──────────────────────────────────
    if len(data["entries"]) > MAX_ENTRIES:
        data["entries"] = data["entries"][-MAX_ENTRIES:]

    _save(data)
    return data


def get_history() -> dict[str, Any]:
    """Return the full cost-history structure (entries, daily_totals, etc.)."""
    return _load()


def record_agent_usage(
    agent: str,
    model: str,
    message: str,
    response_text: str,
    provider: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    """Convenience wrapper for ``execute_agent``.

    Derives a rough heuristic token estimate (``(len(message) + len(response)) // 4``)
    and a cost estimate.  For free-tier models cost is set to ``0.0``, but
    the token count still burns quota.
    """
    # Heuristic token estimate (chars ÷ 4, standard approximation)
    try:
        msg_len = len(message) if message else 0
        resp_len = len(response_text) if response_text else 0
        tokens = (msg_len + resp_len) // 4
    except Exception:
        tokens = 0

    # Cost is 0.0 for free-tier models; we still track usage
    cost_est = 0.0

    return record(agent=agent, model=model, tokens=tokens, cost=cost_est, provider=provider)


# ── Free-Tier Guardrails ───────────────────────────────────────────────

def _evaluate_free_tier(data: dict[str, Any]) -> list[str]:
    """Compute per-provider free-tier usage and emit alerts when thresholds
    are crossed.  De-duplicates so the same alert is not appended repeatedly
    within a day.
    """
    limits = _resolve_limits()
    if not limits:
        return []

    now = datetime.now(timezone.utc)
    current_month = now.strftime("%Y-%m")
    today = now.strftime("%Y-%m-%d")

    # Build per-provider usage from entries
    provider_usage: dict[str, dict[str, Any]] = {}
    for e in data.get("entries", []):
        if not e.get("timestamp", "").startswith(current_month):
            continue
        prov = e.get("provider")
        if not prov:
            # Try to infer from agent name
            agent = e.get("agent", "").lower()
            if "gemini" in agent:
                prov = "gemini"
            elif "opencode" in agent:
                prov = "opencode"
            else:
                continue

        if prov not in provider_usage:
            provider_usage[prov] = {"tokens": 0, "cost": 0.0}
        provider_usage[prov]["tokens"] += e.get("tokens", 0) or 0
        provider_usage[prov]["cost"] += e.get("cost", 0.0) or 0.0

    alerts: list[str] = []

    for provider, cfg in limits.items():
        cap = cfg.get("monthly_token_cap", 0)
        warn_pct = cfg.get("warn_pct", DEFAULT_WARN_PCT)
        usage = provider_usage.get(provider, {})
        used = usage.get("tokens", 0)

        if cap <= 0:
            continue

        pct_used = (used / cap) * 100

        if pct_used >= warn_pct:
            remaining = cap - used
            alert = (
                f"{provider}: {pct_used:.0f}% of monthly free-tier tokens used "
                f"({used:,}/{cap:,}) — {remaining:,} remaining. "
                f"Consider throttling or switching models."
            )
            # De-duplicate: don't append the same alert if already present
            # for today (check by looking at the last few alerts for this provider)
            if not _alert_already_present(alert, data.get("free_tier_alerts", []), today):
                alerts.append(alert)

    # Also emit breach notifications if configured
    _maybe_notify_breach(alerts)

    return alerts


def _alert_already_present(alert: str, existing: list[str], today: str) -> bool:
    """Check if an equivalent alert already exists for today."""
    alert_key = alert.split(":")[0] if ":" in alert else alert
    for existing_alert in existing[-10:]:  # check recent ones
        if alert_key in existing_alert:
            return True
    return False


def _maybe_notify_breach(alerts: list[str]) -> None:
    """Opt-in: send email/Telegram notification when a threshold is newly breached."""
    if not alerts:
        return

    sf = _settings_file()
    notify_enabled = False
    if sf.exists():
        try:
            notify_enabled = json.loads(sf.read_text()).get("free_tier_alerts_notify", False)
        except Exception:
            pass

    if not notify_enabled:
        return

    settings = get_settings()
    recipient = settings.ADMIN_EMAIL or settings.SCHEDULE_EMAIL_RECIPIENT
    if not recipient:
        return

    # Attempt email delivery
    try:
        from modules.google_workspace import GoogleWorkspace
        ws = GoogleWorkspace()
        alert_lines = "\n".join(f"• {a}" for a in alerts)
        ws.send_email(
            user_id="default",
            to=recipient,
            subject="⚠ Agentic OS – Free Tier Alert",
            body=(
                "<html><body>"
                f"<h2>Free Tier Threshold Breached</h2>"
                f"<p>The following providers have crossed their warning thresholds:</p>"
                f"<pre>{alert_lines}</pre>"
                "</body></html>"
            ),
            is_html=True,
        )
        logger.info("Free-tier breach notification sent to %s", recipient)
    except Exception:
        logger.warning("Could not send free-tier breach notification", exc_info=True)
