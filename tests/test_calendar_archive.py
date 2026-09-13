"""Calendar archive tests — past events leave the live list and stay referenceable.

Covers the date boundary rules (all-day exclusive end dates vs timed events),
idempotency, the keep_active exemption used by "Restore", and month/filter listing.
"""
import json
from datetime import date

import pytest

from modules import calendar_archive as ca

TODAY = date(2026, 9, 13)


def _write(tmp_path, events, manual=None, archived=None):
    p = tmp_path / "calendar_events.json"
    p.write_text(json.dumps({
        "events": events,
        "manual_events": manual if manual is not None else [],
        "archived_events": archived or [],
    }))
    return p


def _allday(summary, start, end):
    return {"summary": summary, "start": {"date": start}, "end": {"date": end}, "source": "google_calendar"}


def _timed(summary, start, end):
    return {"summary": summary,
            "start": {"dateTime": start}, "end": {"dateTime": end},
            "source": "google_calendar"}


# ─── Boundary rules ──────────────────────────────────────────

def test_multiday_spanning_today_stays_active():
    ev = _allday("Rotation", "2026-09-10", "2026-09-16")  # last real day = Sep 15
    assert ca.last_day(ev) == date(2026, 9, 15)
    assert ca.is_past(ev, TODAY) is False


def test_allday_ending_today_stays_until_tomorrow():
    ev = _allday("Deadline", "2026-09-13", "2026-09-14")  # exclusive end → last day = Sep 13
    assert ca.last_day(ev) == date(2026, 9, 13)
    assert ca.is_past(ev, TODAY) is False


def test_allday_ended_yesterday_is_past():
    ev = _allday("Vacation", "2026-09-11", "2026-09-13")  # last day = Sep 12
    assert ca.is_past(ev, TODAY) is True


def test_undated_event_is_never_archived():
    assert ca.is_past({"summary": "Floating note"}, TODAY) is False


def test_keep_active_is_exempt():
    ev = _allday("Restored", "2026-08-01", "2026-08-02")
    assert ca.is_past(ev, TODAY) is True
    ev["keep_active"] = True
    assert ca.is_past(ev, TODAY) is False


def test_divergent_keep_active_across_lists_keeps_event_live(tmp_path):
    """The same event in both lists must not be half-archived."""
    plain = _allday("Restored", "2026-08-01", "2026-08-02")
    exempt_copy = dict(plain)
    exempt_copy["keep_active"] = True
    p = _write(tmp_path, [plain], manual=[exempt_copy])

    stats = ca.archive_past_events(path=p, today=TODAY)
    assert stats["newly_archived"] == 0
    data = json.loads(p.read_text())
    # both copies survive together, so the next sync cannot resurrect a stray
    assert [e["summary"] for e in data["events"]] == ["Restored"]
    assert [e["summary"] for e in data["manual_events"]] == ["Restored"]
    assert data["archived_events"] == []


def test_archived_entries_never_carry_keep_active(tmp_path):
    ev = _allday("Old", "2026-07-06", "2026-07-11")
    ev["keep_active"] = False
    p = _write(tmp_path, [ev])
    ca.archive_past_events(path=p, today=TODAY)
    assert "keep_active" not in json.loads(p.read_text())["archived_events"][0]


# ─── Archiving ───────────────────────────────────────────────

def test_archive_moves_past_and_keeps_future(tmp_path):
    past = _allday("Old vacation", "2026-07-06", "2026-07-11")
    future = _allday("Upcoming", "2026-10-01", "2026-10-02")
    p = _write(tmp_path, [past, future], manual=[past])

    stats = ca.archive_past_events(path=p, today=TODAY)
    assert stats["moved"] == 1

    data = json.loads(p.read_text())
    assert [e["summary"] for e in data["events"]] == ["Upcoming"]
    assert data["manual_events"] == []
    assert len(data["archived_events"]) == 1
    assert data["archived_events"][0]["summary"] == "Old vacation"
    assert "archived_at" in data["archived_events"][0]


def test_archive_is_idempotent(tmp_path):
    past = _allday("Old", "2026-07-06", "2026-07-11")
    p = _write(tmp_path, [past])
    assert ca.archive_past_events(path=p, today=TODAY)["moved"] == 1
    assert ca.archive_past_events(path=p, today=TODAY)["moved"] == 0
    assert len(json.loads(p.read_text())["archived_events"]) == 1


def test_dry_run_writes_nothing(tmp_path):
    past = _allday("Old", "2026-07-06", "2026-07-11")
    p = _write(tmp_path, [past])
    stats = ca.archive_past_events(path=p, today=TODAY, dry_run=True)
    assert stats["moved"] == 1
    data = json.loads(p.read_text())
    assert len(data["events"]) == 1
    assert data.get("archived_events") == []


def test_sync_merge_preserves_archive(tmp_path):
    """A re-sync must not resurrect or drop archived events."""
    past = _allday("Old", "2026-07-06", "2026-07-11")
    p = _write(tmp_path, [past])
    ca.archive_past_events(path=p, today=TODAY)

    archived = json.loads(p.read_text())["archived_events"]
    merged = {"events": [past], "manual_events": [], "archived_events": archived}
    p.write_text(json.dumps(merged))

    stats = ca.archive_past_events(path=p, today=TODAY)
    assert stats["newly_archived"] == 0      # already known
    assert stats["removed"] == 1             # but still dropped from the live list
    data = json.loads(p.read_text())
    assert len(data["archived_events"]) == 1
    assert data["events"] == []


def test_duplicate_of_archived_event_is_dropped_not_duplicated(tmp_path):
    past = _allday("Old", "2026-07-06", "2026-07-11")
    p = _write(tmp_path, [past])
    ca.archive_past_events(path=p, today=TODAY)
    # sync re-injects the same event twice
    d = json.loads(p.read_text())
    d["events"] = [dict(past), dict(past)]
    p.write_text(json.dumps(d))

    ca.archive_past_events(path=p, today=TODAY)
    d = json.loads(p.read_text())
    assert d["events"] == []
    assert len(d["archived_events"]) == 1


# ─── Listing + restore ───────────────────────────────────────

def test_archived_listing_filters_and_counts(tmp_path):
    events = [
        _allday("Sankin vacation", "2026-07-06", "2026-07-11"),
        _allday("Sankin vacation", "2026-08-24", "2026-09-08"),
        _allday("SAU webinar", "2026-08-19", "2026-08-20"),
    ]
    p = _write(tmp_path, events)
    ca.archive_past_events(path=p, today=TODAY)

    all_items = ca.archived_events(path=p)
    assert all_items["total"] == 3
    assert {m["month"] for m in all_items["months"]} == {"2026-07", "2026-08"}

    assert ca.archived_events(path=p, q="sankin")["count"] == 2
    assert ca.archived_events(path=p, month="2026-08")["count"] == 2
    # newest first
    first = all_items["events"][0]
    assert first["start"]["date"] == "2026-08-24"


def test_restore_returns_event_and_prevents_rearchive(tmp_path):
    past = _allday("Old", "2026-07-06", "2026-07-11")
    p = _write(tmp_path, [past])
    ca.archive_past_events(path=p, today=TODAY)

    key = ca.event_key(json.loads(p.read_text())["archived_events"][0])
    res = ca.restore_events([key], path=p)
    assert res["restored"] == 1
    assert res["archived_total"] == 0

    data = json.loads(p.read_text())
    assert [e["summary"] for e in data["events"]] == ["Old"]
    assert data["events"][0]["keep_active"] is True
    assert data["events"][0].get("archived_at") is None

    assert ca.archive_past_events(path=p, today=TODAY)["moved"] == 0


def test_event_key_uses_google_id_when_present():
    a = {"summary": "x", "start": {"date": "2026-01-01"}, "end": {"date": "2026-01-02"}, "google_id": "abc"}
    b = {"summary": "DIFFERENT", "start": {"date": "2026-02-02"}, "end": {"date": "2026-02-03"}, "google_id": "abc"}
    assert ca.event_key(a) == ca.event_key(b) == "g:abc"
