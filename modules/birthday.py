"""
Birthday Email router — Agentic OS dashboard API.

Wraps `birthday_emails.py` (engine) so the dashboard can list upcoming
birthdays, preview a generated card, and trigger/send greetings.

Endpoints
---------
  GET  /api/birthday/upcoming?days=60   upcoming birthdays from the live CRM
  GET  /api/birthday/today              today's birthdays
  GET  /api/birthday/settings           engine settings (test_mode, prompt, ...)
  PUT  /api/birthday/settings           update settings
  GET  /api/birthday/log                send history
  GET  /api/birthday/cards              generated card files
  GET  /api/birthday/card/{filename}    serve a card image (for preview)
  POST /api/birthday/preview            generate one card, do not send
  POST /api/birthday/send               run the pipeline (respects test_mode)
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

logger = logging.getLogger("agentic_os.birthday")

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

router = APIRouter(prefix="/api/birthday", tags=["birthday"])

DATA_DIR = BASE_DIR / "data" / "birthday"
CARDS_DIR = DATA_DIR / "cards"


def _engine():
    """Import the engine lazily so a broken dependency can't break app startup."""
    try:
        import birthday_emails  # type: ignore
        return birthday_emails
    except Exception as e:  # pragma: no cover
        logger.error(f"birthday engine unavailable: {e}")
        raise HTTPException(503, f"birthday engine unavailable: {e}")


@router.get("/upcoming")
def upcoming(days: int = Query(60, ge=1, le=400)) -> Dict[str, Any]:
    eng = _engine()
    rows = eng.upcoming(days)
    return {
        "days": days,
        "count": len(rows),
        "today_count": sum(1 for r in rows if r["days_until"] == 0),
        "birthdays": [
            {
                "id": r.get("id"),
                "name": f"{r.get('first_name','')} {r.get('last_name','')}".strip(),
                "first_name": r.get("first_name"),
                "last_name": r.get("last_name"),
                "email": r.get("email"),
                "category": r.get("category"),
                "birthday": r.get("birthday"),
                "next_birthday": r.get("next_birthday"),
                "turns_on": r.get("turns_on"),
                "days_until": r.get("days_until"),
                "already_sent": eng.already_sent(r.get("id") or "", r.get("next_birthday") or ""),
            }
            for r in rows
        ],
    }


@router.get("/today")
def today() -> Dict[str, Any]:
    eng = _engine()
    t = eng.local_today()
    contacts = eng.fetch_contacts()
    people = eng.birthdays_on(t.month, t.day, contacts)
    settings = eng.load_settings()
    return {
        "date": t.strftime("%Y-%m-%d"),
        "timezone": str(t.tzinfo),
        "test_mode": bool(settings.get("test_mode", True)),
        "enabled": bool(settings.get("enabled", True)),
        "contacts_with_birthday": len(contacts),
        "source": contacts[0].get("source") if contacts else None,
        "birthdays": [
            {
                "id": p.get("id"),
                "name": f"{p.get('first_name','')} {p.get('last_name','')}".strip(),
                "email": p.get("email"),
                "category": p.get("category"),
                "birthday": p.get("birthday"),
                "already_sent": eng.already_sent(p.get("id") or "", t.strftime("%Y-%m-%d")),
            }
            for p in people
        ],
    }


@router.get("/settings")
def get_settings() -> Dict[str, Any]:
    eng = _engine()
    s = eng.load_settings()
    s.pop("notes", None)  # long; available via PUT if needed
    return s


@router.put("/settings")
def put_settings(payload: Dict[str, Any]) -> Dict[str, Any]:
    eng = _engine()
    s = eng.load_settings()
    allowed = {
        "enabled", "test_mode", "test_recipient", "subject_template", "signature",
        "image_model", "image_size", "image_prompt", "negative_prompt",
        "overlay_kicker", "note_source", "llm_model", "notes", "cc", "noise_source",
        "footer_note", "design", "card_dept", "design_exclude",
        # outlook handoff (the delivery path that actually reaches @montefiore.org)
        "handoff_enabled", "public_base_url", "notify_recipient", "notify_mirror",
        "keep_published_cards",
    }
    unknown = [k for k in payload if k not in allowed]
    if unknown:
        raise HTTPException(400, f"unknown setting(s): {', '.join(sorted(unknown))}")
    s.update(payload)
    eng.save_settings(s)
    out = dict(s)
    out.pop("notes", None)
    return {"success": True, "settings": out}


@router.get("/log")
def get_log(limit: int = Query(50, ge=1, le=500)) -> Dict[str, Any]:
    eng = _engine()
    entries = eng.load_log()
    return {"total": len(entries), "entries": list(reversed(entries))[:limit]}


@router.get("/designs")
def list_designs() -> Dict[str, Any]:
    """Available card designs (drives the dashboard picker — never hardcode these)."""
    try:
        import card_designs
    except Exception as e:
        raise HTTPException(503, f"design system unavailable: {e}")
    return {
        "rotation": list(card_designs.ROTATION),
        "designs": [
            {
                "key": k,
                "label": v.get("label", k),
                "blurb": v.get("blurb", ""),
                "in_rotation": k in card_designs.ROTATION,
            }
            for k, v in card_designs.DESIGNS.items()
        ],
    }


@router.get("/cards")
def list_cards(limit: int = Query(24, ge=1, le=200)) -> Dict[str, Any]:
    CARDS_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(CARDS_DIR.glob("*.jpg"), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]
    return {
        "count": len(files),
        "cards": [
            {
                "filename": f.name,
                "url": f"/api/birthday/card/{f.name}",
                "bytes": f.stat().st_size,
                "modified": f.stat().st_mtime,
            }
            for f in files
        ],
    }


@router.get("/card/{filename}")
def get_card(filename: str):
    # path-traversal guard
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(400, "invalid filename")
    path = CARDS_DIR / filename
    if not path.exists():
        raise HTTPException(404, "card not found")
    return FileResponse(str(path), media_type="image/jpeg")


@router.post("/preview")
def preview(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a card for one person without sending anything."""
    eng = _engine()
    person_ref = (payload.get("person") or "").strip()
    if not person_ref:
        raise HTTPException(400, "person is required (email or name)")
    settings = eng.load_settings()
    contacts = eng.fetch_contacts()
    frag = person_ref.lower()
    match = [
        c for c in contacts
        if frag in (c.get("email") or "").lower()
        or frag in f"{c.get('first_name','')} {c.get('last_name','')}".lower()
    ]
    if not match:
        raise HTTPException(404, f"no contact matched {person_ref!r}")
    art = eng.generate_base_art(settings, force=bool(payload.get("regen_art")))
    card = eng.prepare_card(match[0], settings, reuse_art=art)
    if not card:
        raise HTTPException(500, "card generation failed (no artwork available)")
    note = eng.pick_note(match[0], settings, payload.get("note_source") or settings.get("note_source", "template"))
    return {
        "success": True,
        "person": f"{match[0].get('first_name','')} {match[0].get('last_name','')}".strip(),
        "email": match[0].get("email"),
        "card": str(card),
        "card_url": f"/api/birthday/card/{Path(card).name}",
        "note": note,
    }


@router.post("/handoff")
def handoff_endpoint(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Build send-ready Outlook compose links for a day's birthdays.

    This is the delivery path that actually reaches @montefiore.org: the card is
    published to a public URL and the returned `outlook_link` opens Outlook with
    recipient, subject and card pre-filled, ready for the user to press Send.
    """
    eng = _engine()
    return eng.handoff(
        target_date=payload.get("date"),
        only=payload.get("person"),
        notify=bool(payload.get("notify")),
        regen_art=bool(payload.get("regen_art")),
        note_source=payload.get("note_source"),
        verbose=False,
    )


@router.post("/send")
def send(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Run the birthday pipeline.

    Defaults come from settings.json — including `test_mode`, which routes every
    message to the test recipient. Pass `test: false` to override for a live send.
    """
    eng = _engine()
    test_mode: Optional[bool] = payload.get("test")
    if test_mode is not None:
        test_mode = bool(test_mode)
    res = eng.run(
        target_date=payload.get("date"),
        dry_run=bool(payload.get("dry_run")),
        test_mode=test_mode,
        force=bool(payload.get("force")),
        only=payload.get("person"),
        note_source=payload.get("note_source"),
        regen_art=bool(payload.get("regen_art")),
        verbose=False,
    )
    return res
