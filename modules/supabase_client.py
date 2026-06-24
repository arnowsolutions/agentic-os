"""Thin Supabase client helper for Agentic OS.

Prefers the official `supabase` Python SDK when installed, but falls back to
plain `httpx` REST calls so the project keeps working with only the deps in
requirements.txt.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any

import httpx

from modules.config import get_settings

logger = logging.getLogger("agentic_os.supabase_client")

# Optional official SDK import
try:
    from supabase import Client as SupabaseClient, create_client
    _HAS_SDK = True
except Exception:  # pragma: no cover
    _HAS_SDK = False
    SupabaseClient = Any  # type: ignore


class SupabaseHelper:
    """Minimal wrapper around Supabase REST for auth audits and pgvector."""

    def __init__(self):
        self.settings = get_settings()
        cfg = self.settings.supabase_config()
        self.url = cfg.get("supabase_url", "") if cfg else ""
        self.key = cfg.get("service_key", "") if cfg else ""
        self._sdk: Any | None = None
        self._headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
        }

    def available(self) -> bool:
        return bool(self.url and self.key)

    def _sdk_client(self) -> Any | None:
        if not _HAS_SDK or not self.available():
            return None
        if self._sdk is None:
            self._sdk = create_client(self.url, self.key)
        return self._sdk

    def insert(self, table: str, record: dict[str, Any]) -> dict[str, Any]:
        """Insert a single row, returning the server response."""
        if not self.available():
            return {"status": "skipped", "reason": "supabase_not_configured"}

        # Prefer SDK when installed.
        sdk = self._sdk_client()
        if sdk is not None:
            try:
                resp = sdk.table(table).insert(record).execute()
                return {"status": "ok", "data": resp.data}
            except Exception as e:
                logger.warning("Supabase SDK insert failed, falling back to httpx", extra={"error": str(e)})

        try:
            r = httpx.post(
                f"{self.url}/rest/v1/{table}",
                json=record,
                headers={**self._headers, "Prefer": "return=representation"},
                timeout=10,
            )
            r.raise_for_status()
            return {"status": "ok", "data": r.json()}
        except Exception as e:
            logger.warning("Supabase insert failed", extra={"table": table, "error": str(e)})
            return {"status": "error", "reason": str(e)}

    def rpc(self, fn: str, params: dict[str, Any]) -> dict[str, Any]:
        """Call a Postgres RPC function."""
        if not self.available():
            return {"status": "skipped", "reason": "supabase_not_configured"}

        sdk = self._sdk_client()
        if sdk is not None:
            try:
                resp = sdk.rpc(fn, params).execute()
                return {"status": "ok", "data": resp.data}
            except Exception as e:
                logger.warning("Supabase SDK rpc failed, falling back to httpx", extra={"error": str(e)})

        try:
            r = httpx.post(
                f"{self.url}/rest/v1/rpc/{fn}",
                json=params,
                headers=self._headers,
                timeout=15,
            )
            r.raise_for_status()
            return {"status": "ok", "data": r.json()}
        except Exception as e:
            logger.warning("Supabase rpc failed", extra={"fn": fn, "error": str(e)})
            return {"status": "error", "reason": str(e)}


def get_supabase_helper() -> SupabaseHelper:
    return SupabaseHelper()
