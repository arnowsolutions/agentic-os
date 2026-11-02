"""
Site analytics router — traffic for the sites tracked in the self-hosted Umami
instance on the VPS.

Read-only. The Umami login lives in `data/umami.json` (0600) or in UMAMI_* env
vars and never leaves the server; the browser only ever sees aggregate numbers.

Config shape (data/umami.json)
------------------------------
  {
    "base_url": "https://analytics.srv1738752.hstgr.cloud",
    "username": "...", "password": "...",
    "sites": [
      {"key": "arnow", "name": "Arnow Solutions", "domain": "arnowsolutions.com", "website_id": "..."},
      {"key": "rec",   "name": "The Rec",         "domain": "thereccenterworks.com", "website_id": "..."}
    ]
  }

A legacy single-site config (top-level `website_id`, no `sites`) still works.

Endpoints
---------
  GET /api/site-analytics/sites                        sites this dashboard can show
  GET /api/site-analytics/overview?site=KEY&days=30    everything the page renders
  GET /api/site-analytics/health                       config + reachability, no secrets
"""
from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger("agentic_os.site_analytics")

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE_DIR / "data" / "umami.json"

router = APIRouter(prefix="/api/site-analytics", tags=["site-analytics"])

# ── tiny caches (single-process; restart clears them) ────────────────────────
_TOKEN: Dict[str, Any] = {"value": None, "at": 0.0}
_CACHE: Dict[str, Any] = {}
CACHE_TTL = 60          # seconds — dashboard freshness vs load on Umami
TOKEN_TTL = 1800        # re-login every 30 min even if nothing 401s


def _config() -> Optional[Dict[str, Any]]:
    """Env vars win; otherwise data/umami.json. Returns None when unconfigured."""
    env = {
        "base_url": os.environ.get("UMAMI_BASE_URL"),
        "username": os.environ.get("UMAMI_USERNAME"),
        "password": os.environ.get("UMAMI_PASSWORD"),
        "website_id": os.environ.get("UMAMI_WEBSITE_ID"),
    }
    cfg: Optional[Dict[str, Any]] = None
    if env["base_url"] and env["username"] and env["password"] and env["website_id"]:
        cfg = {k: str(v) for k, v in env.items()}
    elif CONFIG_FILE.exists():
        try:
            raw = json.loads(CONFIG_FILE.read_text())
            if all(raw.get(k) for k in ("base_url", "username", "password")):
                cfg = raw
        except Exception as exc:  # pragma: no cover - surfaces in /health
            logger.warning("umami.json unreadable: %s", exc)
    if not cfg:
        return None

    sites = cfg.get("sites")
    if not isinstance(sites, list) or not sites:
        if cfg.get("website_id"):  # legacy single-site config
            sites = [{"key": "site", "name": cfg.get("site") or "Website",
                      "domain": cfg.get("domain") or "", "website_id": cfg["website_id"]}]
        else:
            return None
    cfg["sites"] = [s for s in sites if s.get("website_id")]
    return cfg if cfg["sites"] else None


def _site(cfg: Dict[str, Any], key: Optional[str]) -> Dict[str, Any]:
    """Resolve a site by key or website_id; default to the first entry."""
    sites = cfg["sites"]
    if key:
        for s in sites:
            if key in (s.get("key"), s.get("website_id")):
                return s
    return sites[0]


def _login(cfg: Dict[str, Any]) -> str:
    now = time.time()
    if _TOKEN["value"] and now - _TOKEN["at"] < TOKEN_TTL:
        return _TOKEN["value"]
    with httpx.Client(timeout=10.0) as client:
        r = client.post(
            cfg["base_url"].rstrip("/") + "/api/auth/login",
            json={"username": cfg["username"], "password": cfg["password"]},
        )
    if r.status_code != 200:
        raise HTTPException(502, f"Umami login failed ({r.status_code})")
    _TOKEN["value"] = r.json().get("token")
    _TOKEN["at"] = now
    return _TOKEN["value"]


def _get(cfg: Dict[str, Any], path: str, params: Optional[dict] = None) -> Any:
    """GET an Umami API path, refreshing the token once on 401."""
    url = cfg["base_url"].rstrip("/") + path
    for attempt in (0, 1):
        token = _login(cfg)
        with httpx.Client(timeout=12.0) as client:
            r = client.get(url, params=params, headers={"Authorization": f"Bearer {token}"})
        if r.status_code == 401 and attempt == 0:
            _TOKEN["value"] = None
            continue
        if r.status_code != 200:
            raise HTTPException(502, f"Umami {path} returned {r.status_code}")
        return r.json()
    raise HTTPException(502, "Umami rejected the session")


def _cached(key: str, fn):
    hit = _CACHE.get(key)
    if hit and time.time() - hit[0] < CACHE_TTL:
        return hit[1]
    value = fn()
    _CACHE[key] = (time.time(), value)
    return value


def _rows(data: Any) -> List[Dict[str, Any]]:
    """Normalise Umami metric rows ({x,y}) into {label, value}, biggest first."""
    if not isinstance(data, list):
        return []
    out = []
    for row in data:
        if not isinstance(row, dict):
            continue
        label = row.get("x") or row.get("label") or ""
        if isinstance(label, dict):  # some dimensions return {x: {value: ...}}
            label = label.get("value") or label.get("name") or ""
        try:
            value = int(row.get("y") or row.get("value") or 0)
        except (TypeError, ValueError):
            value = 0
        out.append({"label": str(label), "value": value})
    return sorted(out, key=lambda r: r["value"], reverse=True)


@router.get("/sites")
def sites() -> Dict[str, Any]:
    """The sites this dashboard can display (no credentials)."""
    cfg = _config()
    if not cfg:
        return {"configured": False, "sites": []}
    return {
        "configured": True,
        "sites": [{"key": s.get("key") or s["website_id"], "name": s.get("name") or "",
                   "domain": s.get("domain") or ""} for s in cfg["sites"]],
    }


@router.get("/health")
def health() -> Dict[str, Any]:
    """Is the page wired up? Never returns credentials."""
    cfg = _config()
    if not cfg:
        return {"configured": False, "detail": "data/umami.json missing or incomplete"}
    try:
        with httpx.Client(timeout=8.0) as client:
            r = client.get(cfg["base_url"].rstrip("/") + "/api/heartbeat")
        return {
            "configured": True,
            "reachable": r.status_code == 200,
            "base_url": cfg["base_url"],
            "sites": len(cfg["sites"]),
        }
    except Exception as exc:
        return {"configured": True, "reachable": False, "detail": str(exc)[:200],
                "base_url": cfg["base_url"], "sites": len(cfg["sites"])}


@router.get("/overview")
def overview(site: Optional[str] = Query(None), days: int = Query(30, ge=1, le=365)) -> Dict[str, Any]:
    """Everything the Site Traffic page renders, for one site."""
    cfg = _config()
    if not cfg:
        raise HTTPException(503, "Site analytics is not configured (data/umami.json)")

    target = _site(cfg, site)
    sid = target["website_id"]

    def build() -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=days)
        span = {
            "startAt": int(start.timestamp() * 1000),
            "endAt": int(now.timestamp() * 1000),
        }

        stats = _get(cfg, f"/api/websites/{sid}/stats", span)
        trend = _get(cfg, f"/api/websites/{sid}/pageviews",
                     {**span, "unit": "day", "timezone": "America/New_York"})
        pages = _rows(_get(cfg, f"/api/websites/{sid}/metrics", {**span, "type": "path", "limit": 8}))
        sources = _rows(_get(cfg, f"/api/websites/{sid}/metrics", {**span, "type": "referrer", "limit": 8}))
        countries = _rows(_get(cfg, f"/api/websites/{sid}/metrics", {**span, "type": "country", "limit": 8}))
        devices = _rows(_get(cfg, f"/api/websites/{sid}/metrics", {**span, "type": "device", "limit": 5}))
        browsers = _rows(_get(cfg, f"/api/websites/{sid}/metrics", {**span, "type": "browser", "limit": 5}))
        events = _rows(_get(cfg, f"/api/websites/{sid}/metrics", {**span, "type": "event", "limit": 10}))

        try:
            recent_raw = _get(cfg, f"/api/websites/{sid}/events", {**span, "pageSize": 15})
            recent = [{
                "when": e.get("createdAt"),
                "path": e.get("urlPath") or "/",
                "source": e.get("referrerDomain") or "direct",
                "country": e.get("country"),
                "city": e.get("city"),
                "device": e.get("device"),
                "browser": e.get("browser"),
                "event": e.get("eventName"),
            } for e in (recent_raw.get("data") or [])]
        except HTTPException:
            recent = []

        try:
            active = _get(cfg, f"/api/websites/{sid}/active").get("visitors", 0)
        except (HTTPException, AttributeError):
            active = 0

        visitors = int(stats.get("visitors") or 0)
        visits = int(stats.get("visits") or 0)
        comparison = stats.get("comparison") or {}
        leads = sum(e["value"] for e in events if e["label"] == "lead")

        return {
            "ok": True,
            "site": {"key": target.get("key") or sid, "name": target.get("name") or "",
                     "domain": target.get("domain") or "", "website_id": sid},
            "range": {"days": days, "start": start.isoformat(), "end": now.isoformat()},
            "totals": {
                "visitors": visitors,
                "pageviews": int(stats.get("pageviews") or 0),
                "visits": visits,
                "bounces": int(stats.get("bounces") or 0),
                "bounce_rate": round(100.0 * int(stats.get("bounces") or 0) / visits, 1) if visits else 0.0,
                "avg_seconds": round(int(stats.get("totaltime") or 0) / visits, 0) if visits else 0,
                "leads": leads,
                "lead_rate": round(100.0 * leads / visitors, 1) if visitors else 0.0,
                "active_now": int(active or 0),
            },
            "comparison": {
                "visitors": int(comparison.get("visitors") or 0),
                "pageviews": int(comparison.get("pageviews") or 0),
            },
            "trend": [{"date": (p.get("x") or "")[:10], "pageviews": int(p.get("y") or 0)}
                      for p in (trend.get("pageviews") or [])],
            "sessions_trend": [{"date": (p.get("x") or "")[:10], "visitors": int(p.get("y") or 0)}
                               for p in (trend.get("sessions") or [])],
            "top_pages": pages,
            "sources": sources,
            "countries": countries,
            "devices": devices,
            "browsers": browsers,
            "events": events,
            "recent": recent,
        }

    return _cached(f"overview:{sid}:{days}", build)
