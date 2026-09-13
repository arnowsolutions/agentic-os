"""
Calendar archive — keep the Calendar of Events forward-looking.

Past events are moved out of the live ``events`` / ``manual_events`` lists in the
canonical store (``data/calendar_events.json``) into an ``archived_events``
section of that same file, so they disappear from the upcoming list on their own
as the dates pass while staying referenceable later.

Date semantics (must match the frontend's ``fmtDateRange``):

* **All-day events** — Google's ``end.date`` is *exclusive*: a Jul 6–10 vacation
  is stored as start ``2026-07-06`` end ``2026-07-11``. The last real day is
  ``end.date - 1``.
* **Timed events** — ``end.dateTime`` is the real end instant.
* Events with no end fall back to their start.

An event is **past** when its last day is strictly before today (in
America/New_York). In-progress multi-day events stay in the live list.

``keep_active`` exempts an event from auto-archiving — set by the dashboard's
"restore" action so a deliberately un-archived event does not bounce straight
back into the archive on the next read.
"""

from __future__ import annotations

import hashlib
import json
import logging
import zoneinfo
from datetime import date, datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "calendar_events.json"
TZ = zoneinfo.ZoneInfo("America/New_York")

ARCHIVE_SECTION = "archived_events"


# ─── Date helpers ────────────────────────────────────────────

def _start_raw(ev: dict) -> str:
    s = ev.get("start") or {}
    return s.get("date") or s.get("dateTime") or ""


def _end_raw(ev: dict) -> str:
    e = ev.get("end") or {}
    return e.get("date") or e.get("dateTime") or ""


def _is_all_day(ev: dict) -> bool:
    return bool((ev.get("start") or {}).get("date"))


def last_day(ev: dict) -> date | None:
    """Return the event's final calendar day, or None if it has no usable date."""
    if _is_all_day(ev):
        end = _end_raw(ev)
        if end:
            try:
                return date.fromisoformat(end[:10]) - timedelta(days=1)
            except ValueError:
                pass
        start = _start_raw(ev)
        try:
            return date.fromisoformat(start[:10])
        except ValueError:
            return None

    end = _end_raw(ev) or _start_raw(ev)
    if not end:
        return None
    try:
        dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
    except ValueError:
        try:
            return date.fromisoformat(end[:10])
        except ValueError:
            return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(TZ)
    return dt.date()


def first_day(ev: dict) -> date | None:
    start = _start_raw(ev)
    if not start:
        return None
    try:
        return date.fromisoformat(start[:10])
    except ValueError:
        return None


def is_past(ev: dict, today: date | None = None) -> bool:
    """True when the event has finished before ``today``."""
    if ev.get("keep_active"):
        return False
    end = last_day(ev)
    if end is None:
        return False  # undated events are never auto-archived
    return end < (today or datetime.now(TZ).date())


def event_key(ev: dict) -> str:
    """Stable identity for dedupe / restore (google_id when available)."""
    if ev.get("google_id"):
        return f"g:{ev['google_id']}"
    raw = "|".join([
        (ev.get("summary") or "").strip().lower(),
        _start_raw(ev),
        _end_raw(ev),
    ])
    return "k:" + hashlib.sha1(raw.encode()).hexdigest()[:16]


# ─── Store IO ────────────────────────────────────────────────

def _load(path: Path) -> dict:
    if not path.exists():
        return {"events": [], "manual_events": []}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise RuntimeError(f"{path} has unexpected shape: {type(data).__name__}")
    return data


def _save(path: Path, data: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    tmp.replace(path)


def _sort_key(ev: dict) -> str:
    return _start_raw(ev)


# ─── Archive / restore ───────────────────────────────────────

def archive_past_events(path: Path | str | None = None, today: date | None = None,
                        dry_run: bool = False) -> dict:
    """Move finished events into the archive section.

    Idempotent: writes only when the live lists actually change. An event whose
    key is already in the archive is still dropped from the live list — that is
    what stops a re-sync from resurrecting a duplicate of an archived event.

    Returns stats with ``removed`` (dropped from the live list),
    ``newly_archived`` (freshly appended to the archive) and ``archived_total``.
    """
    p = Path(path) if path else DATA_FILE
    data = _load(p)
    archive = data.setdefault(ARCHIVE_SECTION, [])
    seen = {event_key(e) for e in archive}

    # The same event can appear in both lists (sync merges manual events into
    # `events`). Decide on the key, not the copy, so a divergent keep_active flag
    # can never leave one copy live and the other archived.
    live_events = data.get("events", [])
    live_manual = data.get("manual_events", [])
    exempt = {event_key(e) for e in list(live_events) + list(live_manual) if e.get("keep_active")}

    def _finished(ev: dict) -> bool:
        return event_key(ev) not in exempt and is_past(ev, today)

    dropped: list[dict] = []
    kept_events: list[dict] = []
    for ev in live_events:
        (dropped if _finished(ev) else kept_events).append(ev)

    kept_manual: list[dict] = []
    dropped_keys = {event_key(e) for e in dropped}
    for ev in live_manual:
        key = event_key(ev)
        if _finished(ev):
            if key not in dropped_keys:
                dropped.append(ev)
                dropped_keys.add(key)
        else:
            kept_manual.append(ev)

    stamp = datetime.now(TZ).isoformat()
    added: list[dict] = []
    for ev in dropped:
        key = event_key(ev)
        if key in seen:
            continue
        seen.add(key)
        entry = dict(ev)
        entry.pop("keep_active", None)  # only live events are ever exempt
        entry["archived_at"] = stamp
        added.append(entry)

    stats = {
        "removed": len(dropped),
        "newly_archived": len(added),
        "moved": len(added),  # kept as an alias: what the user sees land in the archive
        "removed_events": dropped,
        "moved_events": added,
        "archived_total": len(archive) + len(added),
        "as_of": stamp,
        "dry_run": dry_run,
    }

    if dropped and not dry_run:
        data["events"] = sorted(kept_events, key=_sort_key)
        data["manual_events"] = kept_manual
        data[ARCHIVE_SECTION] = sorted(archive + added, key=_sort_key)
        data["last_archived"] = stamp
        data["last_archive_moved"] = len(added)
        data["last_archive_removed"] = len(dropped)
        _save(p, data)
        logger.info("calendar archive: removed %d finished event(s) from the live list (%d newly archived)",
                    len(dropped), len(added))

    return stats


def restore_events(keys: list[str], path: Path | str | None = None) -> dict:
    """Move events back to the live list and exempt them from auto-archiving."""
    p = Path(path) if path else DATA_FILE
    data = _load(p)
    archive = data.get(ARCHIVE_SECTION, [])
    wanted = set(keys)

    restored, remaining = [], []
    for ev in archive:
        if event_key(ev) in wanted:
            ev = dict(ev)
            ev.pop("archived_at", None)
            ev["keep_active"] = True
            restored.append(ev)
        else:
            remaining.append(ev)

    if restored:
        data[ARCHIVE_SECTION] = remaining
        manual = data.setdefault("manual_events", [])
        events = data.setdefault("events", [])
        for ev in restored:
            if ev.get("source") == "manual" and not any(event_key(m) == event_key(ev) for m in manual):
                manual.append(ev)
            if not any(event_key(e) == event_key(ev) for e in events):
                events.append(ev)
        data["events"] = sorted(events, key=_sort_key)
        data["manual_events"] = sorted(manual, key=_sort_key)
        _save(p, data)
        logger.info("calendar archive: restored %d event(s) to the live list", len(restored))

    return {"restored": len(restored), "keys": [event_key(e) for e in restored],
            "archived_total": len(data.get(ARCHIVE_SECTION, []))}


def archived_events(path: Path | str | None = None, month: str | None = None,
                    q: str | None = None, limit: int = 500, offset: int = 0) -> dict:
    """Return archived events (newest first), optionally filtered.

    ``month`` is ``YYYY-MM``; ``q`` matches summary or description.
    ``months`` carries per-month counts for the whole archive, not the page.
    """
    p = Path(path) if path else DATA_FILE
    data = _load(p)
    items = list(data.get(ARCHIVE_SECTION, []))

    counts: dict[str, int] = {}
    for ev in items:
        d = first_day(ev)
        if d:
            counts[d.strftime("%Y-%m")] = counts.get(d.strftime("%Y-%m"), 0) + 1

    filtered = items
    if month:
        filtered = [e for e in filtered if (first_day(e) or date.min).strftime("%Y-%m") == month]
    if q:
        needle = q.strip().lower()
        filtered = [e for e in filtered
                    if needle in (e.get("summary") or "").lower()
                    or needle in (e.get("description") or "").lower()]

    filtered = sorted(filtered, key=_sort_key, reverse=True)

    return {
        "events": filtered[offset:offset + limit],
        "count": len(filtered),
        "total": len(items),
        "months": [{"month": m, "count": counts[m]} for m in sorted(counts, reverse=True)],
        "filters": {"month": month, "q": q},
    }


if __name__ == "__main__":  # manual run: python3 -m modules.calendar_archive [--dry-run]
    import argparse

    ap = argparse.ArgumentParser(description="Archive finished calendar events.")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--file", default=None)
    args = ap.parse_args()

    res = archive_past_events(path=args.file, dry_run=args.dry_run)
    print(f"removed={res['removed']} newly_archived={res['newly_archived']} "
          f"archived_total={res['archived_total']} dry_run={args.dry_run}")
    for ev in res["removed_events"]:
        print("  -", _start_raw(ev), ev.get("summary"))
