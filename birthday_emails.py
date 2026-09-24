#!/usr/bin/env python3
"""
Birthday Email Engine — Agentic OS
==================================

Sends personalized birthday emails to people in the CRM whose birthday is today.

Pipeline
--------
  1. Read birthdays from the LIVE CRM (`public.contacts` on the VPS Postgres).
  2. Generate a premium card image with an LLM image model (fal.ai FLUX).
  3. Overlay the person's name in real typography (PIL + Playfair Display).
  4. Send it as an inline CID image via Gmail SMTP, and log the send.

CLI
---
  python3 birthday_emails.py --list                 # upcoming birthdays
  python3 birthday_emails.py --today                # who has a birthday today
  python3 birthday_emails.py --run --dry-run        # full pipeline, no send
  python3 birthday_emails.py --run                  # send (respects test_mode)
  python3 birthday_emails.py --run --live           # force real recipients
  python3 birthday_emails.py --run --test           # force test recipient
  python3 birthday_emails.py --preview --person <email|name>   # card only
  python3 birthday_emails.py --run --force          # re-send even if already sent

Safety
------
* `test_mode` defaults to TRUE — every send is redirected to `test_recipient`
  until it is explicitly turned off (`settings.json`, the dashboard, or `--live`).
* Sends are logged to `data/birthday/send_log.json`. The engine REFUSES to send
  the same person twice on the same day unless `--force` is passed.
* One-off/unsolicited outbound email must still go through `review_gate.py`. This
  engine is an automated recurring greeting, not a one-off — see AGENTS.md.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import smtplib
import ssl
import sys
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

DATA_DIR = BASE_DIR / "data" / "birthday"
CARDS_DIR = DATA_DIR / "cards"
ART_DIR = DATA_DIR / "art"
SETTINGS_PATH = DATA_DIR / "settings.json"
LOG_PATH = DATA_DIR / "send_log.json"
FONT_DIR = BASE_DIR / "assets" / "fonts"

# Categories that should never receive a birthday email.
EXCLUDED_CATEGORIES = {"archived", "vendor", "ai/tech"}
# Categories we consider "colleagues" for birthday purposes.
INCLUDED_CATEGORIES = {
    "resident", "fellow", "faculty", "staff", "manager", "admin",
    "medical student", "np", "pa", "other",
}

DEFAULT_SETTINGS: Dict[str, Any] = {
    "enabled": True,
    "test_mode": True,
    "test_recipient": "sfrasier@montefiore.org",
    "subject_template": "Happy Birthday, {first_name}!",
    # Format decisions (2026-09-16): first-name subject, no signature, no footer —
    # the email is deliberately just card + greeting + note. Set either of these to
    # a non-empty string to re-enable it.
    "signature": "",
    "footer_note": "",
    # The message is printed on the card artwork; keep it off the body copy so the
    # email doesn't state the same sentence twice. Flip to True to repeat it.
    "show_note_in_body": False,
    # Test sends go to the reviewer only by default (leadership would otherwise
    # receive our drafts on every iteration). True = mirror the real CC list on
    # tests too, so a format review shows exactly what leadership will receive.
    "cc_on_test": False,
    "send_time_note": "Sent automatically at 9:00 AM ET",
    # Image generation
    "image_provider": "fal",
    # fast-sdxl honours a negative prompt, which is what actually keeps the model
    # from painting its own "Happy Birthday" headline into the artwork (flux/schnell
    # ignores "no text" instructions and collides with our typography overlay).
    "image_model": "fal-ai/fast-sdxl",
    "image_size": "landscape_16_9",
    "negative_prompt": (
        "text, words, letters, numbers, typography, writing, calligraphy, "
        "watermark, logo, signature, caption, title, greeting card text, font, "
        "people, faces, hands, animals"
    ),
    "image_prompt": (
        "Elegant abstract background for a premium birthday greeting card. "
        "Deep midnight navy backdrop, soft cinematic golden bokeh lights, "
        "delicate champagne-gold confetti drifting, subtle light rays, "
        "luxurious minimal editorial style, empty negative space in the center, "
        "photographic bokeh, high-end corporate aesthetic."
    ),
    "overlay_kicker": "HAPPY BIRTHDAY",
    # Card design: "auto" rotates through card_designs.rotation() (stable per person
    # per year). Set a design key or a number to pin one. Bench designs you dislike
    # via design_exclude — no code change needed.
    "design": "auto",
    "design_exclude": [],
    "card_dept": "Montefiore Urology",
    # NOTE: spelled note_source. The engine reads settings["note_source"] with a
    # "template" fallback, so a typo here is silent — an "llm" setting never takes.
    "note_source": "template",
    "llm_model": "deepseek/deepseek-chat",
    # Rotating short notes. {first_name} is substituted.
    "notes": [
        "Wishing you a wonderful year ahead — from all of us in Urology.",
        "Hope today brings you good food, good company, and a quiet pager.",
        "Happy birthday! Thank you for everything you bring to the team.",
        "Wishing you a fantastic year. Enjoy your day — you've earned it.",
        "From everyone in the department: happiest of birthdays to you.",
    ],
    "cc": [],
    "last_run": None,
    # ── Outlook handoff ──────────────────────────────────────────
    # Montefiore's tenant quarantines the automated Gmail sender, so mail to
    # @montefiore.org never lands. The handoff builds a pre-filled Outlook
    # compose link that the user sends from their own authenticated mailbox.
    "handoff_enabled": True,
    "public_base_url": "https://os.srv1738752.hstgr.cloud",
    "notify_recipient": "sfrasier@montefiore.org",
    # Copy-Cc target is NOT a setting — it comes from ~/.hermes/scripts/.smtp.env
    # (SMTP_MIRROR_TO, house convention 2026-09-18); the personal address is gone.
    "keep_published_cards": 60,
}


# ─────────────────────────────────────────────────────────────
# Settings & logging
# ─────────────────────────────────────────────────────────────

def _ensure_dirs() -> None:
    for d in (DATA_DIR, CARDS_DIR, ART_DIR):
        d.mkdir(parents=True, exist_ok=True)


def load_settings() -> Dict[str, Any]:
    _ensure_dirs()
    s = dict(DEFAULT_SETTINGS)
    if SETTINGS_PATH.exists():
        try:
            s.update(json.loads(SETTINGS_PATH.read_text()))
        except Exception as e:  # corrupt settings must not stop the send
            print(f"[warn] could not read {SETTINGS_PATH}: {e}", file=sys.stderr)
    return s


def save_settings(s: Dict[str, Any]) -> None:
    _ensure_dirs()
    tmp = SETTINGS_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(s, indent=2))
    tmp.replace(SETTINGS_PATH)


def load_log() -> List[Dict[str, Any]]:
    _ensure_dirs()
    if LOG_PATH.exists():
        try:
            return json.loads(LOG_PATH.read_text())
        except Exception:
            return []
    return []


def append_log(entry: Dict[str, Any]) -> None:
    _ensure_dirs()
    log = load_log()
    log.append(entry)
    LOG_PATH.write_text(json.dumps(log, indent=2))


def already_sent(contact_id: str, on_date: str) -> bool:
    for e in load_log():
        if e.get("contact_id") == contact_id and e.get("date") == on_date:
            if e.get("status") in ("sent", "test-sent"):
                return True
    return False


# ─────────────────────────────────────────────────────────────
# Timezone
# ─────────────────────────────────────────────────────────────

def local_today(now: Optional[datetime] = None) -> datetime:
    """Today's date in the department's timezone (Montefiore = America/New_York)."""
    now = now or datetime.now(timezone.utc)
    try:
        from zoneinfo import ZoneInfo
        return now.astimezone(ZoneInfo("America/New_York"))
    except Exception:
        return now.astimezone(timezone(timedelta(hours=-4)))


# ─────────────────────────────────────────────────────────────
# CRM
# ─────────────────────────────────────────────────────────────

_SQL = """
    SELECT id, first_name, last_name, email, category, birthday, pgy, title, role
    FROM public.contacts
    WHERE birthday IS NOT NULL AND trim(birthday) <> ''
    ORDER BY last_name, first_name
"""


def fetch_contacts() -> List[Dict[str, Any]]:
    """Contacts that have a birthday, from the LIVE CRM.

    Primary path: direct Postgres (same credentials the dashboard uses).
    Fallback: crm_db.get_contacts() + the JSON fallback (which carries `birthday`).
    """
    try:
        from modules.crm_db import _get_pg_connection  # type: ignore
        conn = _get_pg_connection()
        if conn is not None:
            cur = conn.cursor()
            cur.execute(_SQL)
            cols = [d[0] for d in cur.description]
            rows = [dict(zip(cols, r)) for r in cur.fetchall()]
            cur.close()
            return [
                {
                    "id": r.get("id") or "",
                    "first_name": r.get("first_name") or "",
                    "last_name": r.get("last_name") or "",
                    "email": (r.get("email") or "").strip(),
                    "category": r.get("category") or "",
                    "birthday": r.get("birthday") or "",
                    "pgy": r.get("pgy") or "",
                    "title": r.get("title") or "",
                    "role": r.get("role") or "",
                    "source": "supabase-pg",
                }
                for r in rows
            ]
    except Exception as e:
        print(f"[warn] direct CRM read failed ({e}); trying fallback", file=sys.stderr)

    # Fallback — JSON snapshot
    fb = BASE_DIR / "data" / "crm_contacts.fallback.json"
    if fb.exists():
        try:
            raw = json.loads(fb.read_text())
            out = []
            for c in raw:
                bd = c.get("birthday") or ""
                if not str(bd).strip():
                    continue
                out.append({
                    "id": c.get("id") or "",
                    "first_name": c.get("firstName") or "",
                    "last_name": c.get("lastName") or "",
                    "email": (c.get("email") or "").strip(),
                    "category": c.get("category") or "",
                    "birthday": str(bd),
                    "pgy": c.get("pgy") or "",
                    "title": c.get("title") or "",
                    "role": c.get("role") or "",
                    "source": "fallback-json",
                })
            print(f"[warn] using fallback JSON ({len(out)} with birthdays)", file=sys.stderr)
            return out
        except Exception as e:
            print(f"[error] fallback read failed: {e}", file=sys.stderr)
    return []


# ─────────────────────────────────────────────────────────────
# Birthday matching
# ─────────────────────────────────────────────────────────────

_DATE_RE = re.compile(r"^\s*(\d{1,2})\s*[/\-\.]\s*(\d{1,2})\s*(?:[/\-\.]\s*(\d{2,4}))?\s*$")


def parse_birthday(value: Any) -> Optional[Tuple[int, int]]:
    """Parse '2/26', '02/26', '2-26', '2/26/1985' → (month, day). None if unusable."""
    if value is None:
        return None
    m = _DATE_RE.match(str(value))
    if not m:
        return None
    month, day = int(m.group(1)), int(m.group(2))
    if not (1 <= month <= 12 and 1 <= day <= 31):
        return None
    return month, day


_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(email: str) -> bool:
    return bool(email and _EMAIL_RE.match(email.strip()))


def _is_candidate(c: Dict[str, Any]) -> bool:
    cat = (c.get("category") or "").strip().lower()
    if cat in EXCLUDED_CATEGORIES:
        return False
    if not is_valid_email(c.get("email", "")):
        return False
    return True


def birthdays_on(month: int, day: int, contacts: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    """Everyone whose birthday is (month, day)."""
    contacts = contacts if contacts is not None else fetch_contacts()
    out = []
    for c in contacts:
        parsed = parse_birthday(c.get("birthday"))
        if parsed and parsed == (month, day) and _is_candidate(c):
            out.append(c)
    return out


def upcoming(days: int = 60, contacts: Optional[List[Dict[str, Any]]] = None,
             today: Optional[datetime] = None) -> List[Dict[str, Any]]:
    """Upcoming birthdays in the next `days` days, soonest first, with days_until."""
    contacts = contacts if contacts is not None else fetch_contacts()
    today = today or local_today()
    out = []
    for c in contacts:
        parsed = parse_birthday(c.get("birthday"))
        if not parsed or not _is_candidate(c):
            continue
        month, day = parsed
        for year in (today.year, today.year + 1):
            try:
                cand = datetime(year, month, day, tzinfo=today.tzinfo)
            except ValueError:
                continue  # e.g. 2/30 in a stale record
            delta = (cand.date() - today.date()).days
            if 0 <= delta <= days:
                item = dict(c)
                item["next_birthday"] = cand.strftime("%Y-%m-%d")
                item["days_until"] = delta
                item["turns_on"] = cand.strftime("%b %d")
                out.append(item)
                break
    out.sort(key=lambda x: x["days_until"])
    return out


# ─────────────────────────────────────────────────────────────
# Image generation
# ─────────────────────────────────────────────────────────────

def _read_env_value(name: str) -> Optional[str]:
    """Read a key from the project .env, then the Hermes home .env.

    The AOS container runs as root with HOME=/root but mounts the Hermes home
    read-only at /home/hermeswebui/.hermes, so we check that absolute path too
    (never via a shell — the secret-redaction layer mangles inline grep/echo).
    """
    candidates = [
        BASE_DIR / ".env",
        Path.home() / ".hermes" / ".env",
        Path("/home/hermeswebui/.hermes/.env"),
    ]
    for p in candidates:
        try:
            if not p.exists():
                continue
            for line in p.read_text().splitlines():
                if line.strip().startswith(name + "="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
        except Exception:
            continue
    return os.environ.get(name)


def generate_base_art(settings: Dict[str, Any], force: bool = False) -> Optional[Path]:
    """Generate (or reuse) the month's card artwork via fal.ai FLUX.

    Cached per calendar month at data/birthday/art/<YYYY-MM>.jpg — one image
    generation covers everybody that month, so a failed API call never blocks
    a birthday email (the previous month's art is reused instead).
    """
    stamp = local_today().strftime("%Y-%m")
    out = ART_DIR / f"{stamp}.jpg"
    if out.exists() and not force:
        return out

    key = _read_env_value("FAL_KEY")
    provider = settings.get("image_provider", "fal")
    if not key and provider == "fal":
        print("[warn] FAL_KEY not found — falling back to cached/blank art", file=sys.stderr)
        return _newest_art(out)

    model = settings.get("image_model", "fal-ai/fast-sdxl")
    payload = {
        "prompt": settings.get("image_prompt", DEFAULT_SETTINGS["image_prompt"]),
        "image_size": settings.get("image_size", "landscape_16_9"),
        "num_images": 1,
    }
    neg = settings.get("negative_prompt")
    if neg:
        # Models that don't accept negative_prompt 422 on it — retry without.
        payload["negative_prompt"] = neg

    def _post(body: Dict[str, Any]) -> Dict[str, Any]:
        req = urllib.request.Request(
            f"https://fal.run/{model}",
            data=json.dumps(body).encode(),
            headers={"Authorization": f"Key {key}", "Content-Type": "application/json"},
        )
        return json.loads(urllib.request.urlopen(req, timeout=180).read())

    try:
        try:
            raw = _post(payload)
        except urllib.error.HTTPError as he:
            if he.code in (400, 422) and "negative_prompt" in payload:
                print("[warn] model rejected negative_prompt — retrying without it",
                      file=sys.stderr)
                payload.pop("negative_prompt", None)
                raw = _post(payload)
            else:
                raise
        url = (raw.get("images") or [{}])[0].get("url")
        if not url:
            raise RuntimeError(f"no image url in response: {str(raw)[:200]}")
        with urllib.request.urlopen(url, timeout=120) as r:
            out.write_bytes(r.read())
        print(f"[image] generated {out.name} ({out.stat().st_size} bytes, {model})")
        return out
    except Exception as e:
        print(f"[warn] image generation failed ({e}); using cached art", file=sys.stderr)
        return _newest_art(out)


def _newest_art(fallback: Path) -> Optional[Path]:
    """Any previously generated art — so the email still goes out."""
    if fallback.exists():
        return fallback
    arts = sorted(ART_DIR.glob("*.jpg")) + sorted(ART_DIR.glob("*.png"))
    return arts[-1] if arts else None


def _font(name: str, size: int, weight: Optional[int] = None):
    from PIL import ImageFont
    path = FONT_DIR / f"{name}.ttf"
    if not path.exists():
        path = Path.home() / ".fonts" / "DejaVuSerif-Bold.ttf"
    f = ImageFont.truetype(str(path), size)
    if weight is not None:
        try:
            f.set_variation_by_axes([weight])
        except Exception:
            pass
    return f


def _draw_tracked(draw, xy, text, font, fill, tracking=0, anchor_center=None):
    """Draw text with letter-spacing. If anchor_center is given, center on that x."""
    widths = [draw.textlength(ch, font=font) for ch in text]
    total = sum(widths) + tracking * max(0, len(text) - 1)
    x, y = xy
    if anchor_center is not None:
        x = anchor_center - total / 2
    for ch, w in zip(text, widths):
        draw.text((x, y), ch, font=font, fill=fill)
        x += w + tracking
    return total


def compose_card(base_art: Path, person: Dict[str, Any], out_path: Path,
                 settings: Optional[Dict[str, Any]] = None) -> Path:
    """SUPERSEDED — kept as the reference for the original PIL compositing approach.

    The live card path is `card_designs.render_card()` (HTML/CSS rendered through
    headless Chromium), which is what `prepare_card()` calls. This function is no
    longer invoked by anything; it survives only because the tone-mapping and
    scrim maths here are still the reference for how AI artwork should be receded
    behind type.
    """
    from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

    settings = settings or load_settings()
    W, H = 1600, 900
    img = Image.open(base_art).convert("RGB")
    # cover-fit
    ratio = max(W / img.width, H / img.height)
    img = img.resize((max(1, int(img.width * ratio)), max(1, int(img.height * ratio))), Image.LANCZOS)
    left = (img.width - W) // 2
    top = (img.height - H) // 2
    img = img.crop((left, top, left + W, top + H))

    # Recede the artwork: darker, richer, softly defocused = texture, not subject.
    img = ImageEnhance.Brightness(img).enhance(0.58)
    img = ImageEnhance.Color(img).enhance(1.12)
    img = img.filter(ImageFilter.GaussianBlur(2.2))

    # Radial + band scrim, so the centre (where the words go) is calm.
    scrim = Image.new("L", (W, H), 0)
    try:
        import numpy as np
        yy, xx = np.mgrid[0:H, 0:W]
        cx, cy = W / 2.0, H / 2.0
        r = np.sqrt(((xx - cx) / cx) ** 2 + ((yy - cy) / cy) ** 2)
        vignette = np.clip((r ** 2.2) * 170, 0, 205)
        # extra calm across the vertical middle band where the type lives
        band = 92 * np.exp(-(((yy - H * 0.50) / (H * 0.20)) ** 2))
        alpha = np.clip(vignette + band, 0, 225).astype("uint8")
        scrim = Image.fromarray(alpha)
    except Exception:
        sd = ImageDraw.Draw(scrim)
        for i in range(H):
            t = i / H
            edge = min(t, 1 - t)
            sd.line([(0, i), (W, i)], fill=int(190 * (1 - min(1.0, edge / 0.5)) ** 0.8))
    scrim = scrim.filter(ImageFilter.GaussianBlur(48))
    img = Image.composite(Image.new("RGB", (W, H), (7, 11, 22)), img, scrim)

    draw = ImageDraw.Draw(img, "RGBA")
    GOLD = (232, 199, 122)
    GOLD_SOFT = (232, 199, 122, 120)
    CREAM = (255, 248, 236)
    MUTED = (206, 198, 184)

    first = (person.get("first_name") or "").strip()
    last = (person.get("last_name") or "").strip()
    name = f"{first} {last}".strip() or "Friend"

    kicker = (settings.get("overlay_kicker") or "HAPPY BIRTHDAY").upper()
    kf = _font("inter", 32, weight=500)
    sf = _font("inter", 25, weight=400)

    # Name size fits the frame
    size = 108
    while size > 46:
        nf = _font("playfair", size, weight=700)
        if draw.textlength(name, font=nf) <= W - 300:
            break
        size -= 6
    nf = _font("playfair", size, weight=700)

    # Soft dark plate behind the whole text block for guaranteed contrast
    plate_top, plate_bot = 268, 620
    plate = Image.new("L", (W, H), 0)
    ImageDraw.Draw(plate).rounded_rectangle(
        [W * 0.10, plate_top, W * 0.90, plate_bot], radius=26, fill=105)
    plate = plate.filter(ImageFilter.GaussianBlur(55))
    img = Image.composite(Image.new("RGB", (W, H), (4, 8, 18)), img, plate)

    draw = ImageDraw.Draw(img, "RGBA")
    # Hairline gold frame
    draw.rectangle([38, 38, W - 38, H - 38], outline=GOLD_SOFT, width=2)

    _draw_tracked(draw, (0, 306), kicker, kf, GOLD, tracking=13, anchor_center=W / 2)
    draw.line([(W / 2 - 132, 372), (W / 2 + 132, 372)], fill=(232, 199, 122, 165), width=2)

    # Name with a soft shadow so it separates from any residual bokeh
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).text((W / 2 + 3, 465 + 4), name, font=nf, fill=(0, 0, 0, 170), anchor="mm")
    shadow = shadow.filter(ImageFilter.GaussianBlur(9))
    img = Image.alpha_composite(img.convert("RGBA"), shadow).convert("RGB")
    draw = ImageDraw.Draw(img, "RGBA")
    draw.text((W / 2, 465), name, font=nf, fill=CREAM, anchor="mm")

    sig = (settings.get("signature") or "Montefiore Urology")
    _draw_tracked(draw, (0, 566), sig, sf, MUTED, tracking=7, anchor_center=W / 2)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "JPEG", quality=92, optimize=True)
    return out_path


# ─────────────────────────────────────────────────────────────
# Note text (LLM optional, template default)
# ─────────────────────────────────────────────────────────────

def llm_note(person: Dict[str, Any], settings: Dict[str, Any]) -> Optional[str]:
    """Ask an LLM for a one-line birthday note. Returns None on any failure."""
    key = _read_env_value("OPENROUTER_API_KEY")
    if not key:
        return None
    prompt = (
        "Write ONE short, warm, professional birthday greeting line (max 18 words) for a "
        "urology department colleague. No emoji, no quotation marks, no greeting like 'Happy birthday' "
        "(the card already says it), no name at the start — just the sentence of good wishes.\n"
        f"Person: {person.get('first_name')} {person.get('last_name')}, "
        f"role: {person.get('category') or 'colleague'}."
    )
    payload = {
        "model": settings.get("llm_model", "deepseek/deepseek-chat"),
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 60,
        "temperature": 0.9,
    }
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    try:
        raw = json.loads(urllib.request.urlopen(req, timeout=45).read())
        txt = (raw["choices"][0]["message"]["content"] or "").strip().strip('"')
        return txt or None
    except Exception as e:
        print(f"[warn] LLM note failed ({e}); using template", file=sys.stderr)
        return None


def pick_note(person: Dict[str, Any], settings: Dict[str, Any],
              source: str = "template") -> str:
    if source == "llm":
        note = llm_note(person, settings)
        if note:
            return note
    notes = settings.get("notes") or DEFAULT_SETTINGS["notes"]
    # Stable per person per year so the same greeting is used all day and a retry
    # never changes the wording. NOT builtin hash() — that is randomised per process
    # (PYTHONHASHSEED), which silently produced a different note on every run.
    key = f"{person.get('id') or person.get('email') or ''}{local_today().year}"
    idx = int(hashlib.md5(key.encode("utf-8")).hexdigest(), 16) % len(notes)
    return notes[idx].replace("{first_name}", (person.get("first_name") or "").strip())


# ─────────────────────────────────────────────────────────────
# Email
# ─────────────────────────────────────────────────────────────

def build_html(person: Dict[str, Any], settings: Dict[str, Any], note: str, cid: str) -> str:
    """The resident-facing email.

    Format decisions (2026-09-16): first-name subject, NO signature block and NO
    footer — just the card and the greeting.

    The note lives ON THE CARD (set in the artwork), so it is NOT repeated as body
    text by default — printing it in both places said the same sentence twice.
    Set `show_note_in_body` to re-enable the body copy; the greeting heading below
    the image is independent of this and is always rendered.
    """
    first = (person.get("first_name") or "").strip() or "there"
    sig = (settings.get("signature") or "").strip()
    footer = (settings.get("footer_note") or "").strip()
    show_note = bool(settings.get("show_note_in_body", False))

    note_block = (
        '<div style="font-size:15px;line-height:1.65;color:#334155;margin-top:14px;">'
        f'{note}</div>'
        if (show_note and (note or "").strip()) else ""
    )

    sig_block = (
        '<div style="font-size:14px;line-height:1.65;color:#64748b;margin-top:18px;">'
        f'Warmly,<br><strong style="color:#334155;">{sig}</strong></div>'
        if sig else ""
    )
    footer_block = (
        '<tr><td style="padding:20px 40px 30px 40px;">'
        '<div style="border-top:1px solid #e8eaee;padding-top:14px;font-size:12px;color:#94a3b8;">'
        f'{footer}</div></td></tr>'
        if footer else ""
    )

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f4f5f7;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f5f7;padding:28px 12px;">
    <tr><td align="center">
      <table role="presentation" width="640" cellpadding="0" cellspacing="0"
             style="max-width:640px;width:100%;background:#ffffff;border-radius:14px;overflow:hidden;
                    box-shadow:0 6px 24px rgba(15,23,42,.10);font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;">
        <tr><td style="padding:0;">
          <img src="cid:{cid}" alt="Happy Birthday, {first}" width="640"
               style="display:block;width:100%;height:auto;border:0;">
        </td></tr>
        <tr><td style="padding:30px 40px 34px 40px;">
          <div style="font-size:21px;font-weight:700;color:#0f172a;letter-spacing:-0.2px;">
            Happy Birthday, {first}!
          </div>
          {note_block}
          {sig_block}
        </td></tr>
        {footer_block}
      </table>
    </td></tr>
  </table>
</body></html>"""


def _smtp_cfg() -> Dict[str, str]:
    """SMTP credentials from modules.smtp_sender (authoritative .env loading)."""
    from modules.smtp_sender import _get_smtp_config  # type: ignore
    return _get_smtp_config()


def _house_copy_cc(to: str, cc=None, bcc=None):
    """Copy-Cc rule (house convention, verified 2026-09-18) — same knob as the
    rest of the stack (~/.hermes/scripts/.smtp.env, SMTP_MIRROR_TO), so fixing it
    in one place covers every sender. Adds the program account as a second
    recipient on any mail touching @montefiore.org (a single recipient gets
    silently quarantined by Montefiore's filter); the personal address must
    never appear on outbound mail. Idempotent."""
    copy_to = ""
    try:
        with open("/home/hermeswebui/.hermes/scripts/.smtp.env") as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    if k.strip() == "SMTP_MIRROR_TO":
                        copy_to = v.strip()
    except FileNotFoundError:
        pass
    if not copy_to:
        copy_to = "urologyresidencyprogram@gmail.com"
    addrs = [str(a).strip().lower() for a in ([to] + list(cc or []) + list(bcc or [])) if a]
    if not any("@montefiore.org" in a for a in addrs):
        return cc
    if copy_to.lower() in addrs:
        return cc
    return list(cc or []) + [copy_to]


def send_card(to: str, subject: str, html: str, image_path: Optional[Path],
              cc: Optional[List[str]] = None, cid: Optional[str] = None,
              bcc: Optional[List[str]] = None) -> Dict[str, Any]:
    """Send an HTML email with the card inlined via Content-ID (and attached).

    `cid` MUST be the same token referenced as `cid:<token>` in `html`.

    House copy-Cc rule (normalized 2026-09-18): every card with a @montefiore.org
    recipient (To/Cc/Bcc) automatically gets the program-account copy Cc — the
    second recipient is what gets mail past Montefiore's quarantine of the
    automated Gmail sender (verified 2026-09-18). The copy target comes from
    ~/.hermes/scripts/.smtp.env (SMTP_MIRROR_TO) and the personal address must
    never appear on outbound mail. Idempotent.

    `bcc` recipients are added to the SMTP envelope ONLY — no Bcc header is
    written, because a Bcc header leaks the blind copy to everyone on the thread
    (and some clients render it).
    """
    cc = _house_copy_cc(to, cc, bcc)
    cfg = _smtp_cfg()
    if not cfg.get("user") or not cfg.get("password"):
        return {"successful": False, "error": "SMTP not configured", "data": None}

    sender = cfg["user"]                      # envelope sender MUST equal SMTP user
    display = os.environ.get("SMTP_FROM_NAME", "Urology Residency Program")
    from email.utils import formataddr

    root = MIMEMultipart("related")
    root["From"] = formataddr((display, sender))
    root["To"] = to
    root["Subject"] = subject
    if cc:
        root["Cc"] = ", ".join(cc)
    # No Bcc header on purpose — see docstring. bcc goes to the envelope only.

    alt = MIMEMultipart("alternative")
    text = re.sub(r"<[^>]+>", " ", html)
    alt.attach(MIMEText(" ".join(text.split()), "plain"))
    alt.attach(MIMEText(html, "html"))
    root.attach(alt)

    if image_path and Path(image_path).exists():
        token = cid or f"bday-{uuid.uuid4().hex[:12]}"
        data = Path(image_path).read_bytes()
        img = MIMEImage(data, _subtype="jpeg")
        img.add_header("Content-ID", f"<{token}>")
        img.add_header("Content-Disposition", "inline",
                       filename=Path(image_path).name)
        root.attach(img)

    recipients = [to] + list(cc or []) + list(bcc or [])
    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP(cfg["host"], int(cfg["port"]), timeout=45) as server:
            server.ehlo()
            server.starttls(context=ctx)
            server.ehlo()
            server.login(cfg["user"], cfg["password"])
            server.sendmail(sender, recipients, root.as_string())
        return {"successful": True, "data": {"id": "smtp_sent"}, "error": None}
    except Exception as e:
        return {"successful": False, "error": f"{type(e).__name__}: {e}", "data": None}


# ─────────────────────────────────────────────────────────────
# Outlook handoff — the delivery path that actually reaches residents
#
# Montefiore's tenant quarantines mail from the automated Gmail sender when it
# carries a single recipient (verified 2026-09-16 with plain, HTML and image
# variants). Update 2026-09-18: a second recipient — the program-account copy
# Cc, now applied in send_card — gets the mail delivered. The handoff remains
# the belt-and-suspenders path for anything that still does not land.
#
# The handoff sidesteps it: the card is published to a public URL, and we build
# a pre-filled Outlook compose link that the user opens and sends from their own
# authenticated @montefiore.org mailbox.
# ─────────────────────────────────────────────────────────────

PUBLIC_CARDS_DIR = BASE_DIR / "dashboard" / "cards"
PREVIEW_DIR = BASE_DIR / "dashboard" / "previews"
OUTLOOK_MAIL_DEEPLINK = "https://outlook.cloud.microsoft/mail/deeplink/compose"


def publish_card(card_path: Path, settings: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """Copy the card into the public static dir and return its public URL.

    `/dashboard` is mounted as static files WITHOUT auth, so the URL is
    reachable by Outlook and by the recipient's mail client.
    """
    settings = settings or load_settings()
    if not card_path or not Path(card_path).exists():
        return None
    PUBLIC_CARDS_DIR.mkdir(parents=True, exist_ok=True)
    dest = PUBLIC_CARDS_DIR / Path(card_path).name
    dest.write_bytes(Path(card_path).read_bytes())

    # prune old published cards
    keep = int(settings.get("keep_published_cards") or 60)
    files = sorted(PUBLIC_CARDS_DIR.glob("*.jpg"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in files[keep:]:
        try:
            old.unlink()
        except Exception:
            pass

    base = (settings.get("public_base_url") or "").rstrip("/")
    return f"{base}/dashboard/cards/{dest.name}" if base else dest.name


def build_handoff_body(person: Dict[str, Any], note: str, card_url: Optional[str],
                       settings: Optional[Dict[str, Any]] = None) -> str:
    """Outlook-safe HTML body (tables + inline styles, no external CSS).

    No personal signature block on purpose — Outlook appends the sender's own
    signature on send, and duplicating it would look wrong.
    """
    settings = settings or load_settings()
    first = (person.get("first_name") or "").strip() or "there"
    sig = (settings.get("signature") or "").strip()
    # The message already sits ON the card. Repeating it here says the same
    # sentence twice in the compose window — same rule as build_html().
    show_note = bool(settings.get("show_note_in_body", False))
    note_div = (
        '<div style="font-size:14px;line-height:1.6;color:#334155;padding-bottom:16px;">'
        f'{note}</div>'
        if (show_note and (note or "").strip()) else ""
    )
    img = (f'<img src="{card_url}" alt="Happy Birthday, {first}" width="640" '
           f'style="display:block;width:100%;max-width:640px;height:auto;border:0;border-radius:10px;">'
           if card_url else "")
    sig_block = f'<div style="font-size:14px;line-height:1.6;color:#64748b;">Warmly,<br><strong style="color:#334155;">{sig}</strong></div>' if sig else ""
    return (
        '<table role="presentation" cellpadding="0" cellspacing="0" width="100%" '
        'style="font-family:Segoe UI,Arial,Helvetica,sans-serif;background:#ffffff;">'
        '<tr><td style="padding:0 0 14px 0;">' + img + '</td></tr>'
        '<tr><td style="padding:0 2px;">'
        f'<div style="font-size:19px;font-weight:700;color:#0f172a;padding-bottom:10px;">Happy Birthday, {first}!</div>'
        + note_div +
        sig_block +
        '</td></tr></table>'
    )


def build_outlook_deeplink(to: str, subject: str, html_body: str,
                           cc: Optional[str] = None) -> str:
    """Pre-filled Outlook (OWA) compose link. bodyType=HTML matches the proven
    pattern used by outlook_deeplink_generator.py in this same codebase."""
    params = {"to": to, "subject": subject, "body": html_body, "bodyType": "HTML"}
    if cc:
        params["cc"] = cc
    return f"{OUTLOOK_MAIL_DEEPLINK}?{urllib.parse.urlencode(params, quote_via=urllib.parse.quote)}"


def handoff(target_date: Optional[str] = None, only: Optional[str] = None,
            notify: bool = False, regen_art: bool = False,
            note_source: Optional[str] = None, verbose: bool = True) -> Dict[str, Any]:
    """Build send-ready Outlook handoffs for a day's birthdays.

    Returns one item per person: the published card URL, the exact subject, and
    a compose deeplink that opens Outlook with everything pre-filled.
    """
    settings = load_settings()
    note_source = note_source or settings.get("note_source", "template")

    if target_date:
        try:
            base = datetime.strptime(target_date, "%Y-%m-%d").replace(tzinfo=local_today().tzinfo)
        except ValueError:
            return {"ok": False, "error": f"bad --date {target_date!r}; use YYYY-MM-DD"}
    else:
        base = local_today()

    date_str = base.strftime("%Y-%m-%d")
    contacts = fetch_contacts()
    people = birthdays_on(base.month, base.day, contacts)

    if only:
        frag = only.strip().lower()
        people = [p for p in people
                  if frag in (p.get("email") or "").lower()
                  or frag in f"{p.get('first_name')} {p.get('last_name')}".lower()]
        if not people:
            people = [c for c in contacts
                      if frag in (c.get("email") or "").lower()
                      or frag in f"{c.get('first_name')} {c.get('last_name')}".lower()]

    result: Dict[str, Any] = {"ok": True, "date": date_str, "mode": "outlook-handoff",
                              "items": [], "candidates": len(people)}
    if not people:
        if verbose:
            print(f"No birthdays on {date_str}.")
        return result

    art = generate_base_art(settings, force=regen_art)
    for person in people:
        name = f"{person.get('first_name')} {person.get('last_name')}".strip()
        note = pick_note(person, settings, note_source)
        card = None
        try:
            card = prepare_card(person, settings, reuse_art=art, note=note)
        except Exception as e:
            print(f"[warn] card compose failed for {name}: {e}", file=sys.stderr)

        card_url = publish_card(card, settings) if card else None
        first = (person.get("first_name") or "").strip()
        subject = (settings.get("subject_template") or "Happy Birthday, {first_name}!").format(
            first_name=first, last_name=(person.get("last_name") or "").strip(), name=name)
        body = build_handoff_body(person, note, card_url, settings)
        live_cc = [a.strip() for a in (settings.get("cc") or []) if is_valid_email(a.strip())]
        cc_for_person = [a for a in live_cc
                         if a.lower() != (person.get("email") or "").lower()]
        link = build_outlook_deeplink(person.get("email") or "", subject, body,
                                      cc=",".join(cc_for_person) if cc_for_person else None)

        item = {
            "contact_id": person.get("id"),
            "name": name,
            "first_name": first,
            "email": person.get("email"),
            "category": person.get("category"),
            "subject": subject,
            "note": note,
            "card": str(card) if card else None,
            "card_url": card_url,
            "outlook_link": link,
        }
        result["items"].append(item)
        append_log({
            "date": date_str, "contact_id": person.get("id"), "name": name,
            "intended_email": person.get("email"), "sent_to": "outlook-handoff",
            "subject": subject, "card": str(card) if card else None,
            "card_url": card_url, "note": note, "test_mode": False,
            "status": "handoff", "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        })
        if verbose:
            print(f"[handoff] {name} <{person.get('email')}>")
            print(f"          card: {card_url}")
            print(f"          open: {link[:120]}...")

    settings["last_run"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    save_settings(settings)

    if notify and result["items"]:
        result["notified"] = notify_handoff(result, settings)
    return result


def notify_handoff(result: Dict[str, Any], settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Email the user their handoff links. Business mail carries the program
    account as a second recipient (house copy-Cc convention, 2026-09-18),
    applied inside send_card; the personal address is no longer involved."""
    settings = settings or load_settings()
    to = settings.get("notify_recipient") or "sfrasier@montefiore.org"
    date_str = result.get("date", "")

    rows = []
    for it in result["items"]:
        img = (f'<img src="{it["card_url"]}" width="520" style="width:100%;max-width:520px;'
               f'border-radius:10px;border:1px solid #e2e8f0;display:block;margin-bottom:12px;">'
               if it.get("card_url") else "")
        rows.append(
            '<div style="border:1px solid #e2e8f0;border-radius:12px;padding:16px;margin-bottom:18px;">'
            + img +
            f'<div style="font:600 16px/1.4 Segoe UI,Arial,sans-serif;color:#0f172a;">{it["name"]} — {it["email"]}</div>'
            f'<div style="font:400 13px/1.5 Segoe UI,Arial,sans-serif;color:#64748b;margin:6px 0 14px;">'
            f'Subject: {it["subject"]}</div>'
            f'<a href="{it["outlook_link"]}" style="display:inline-block;background:#0f766e;color:#fff;'
            'font:600 14px Segoe UI,Arial,sans-serif;padding:11px 20px;border-radius:8px;'
            'text-decoration:none;">Open in Outlook → Send</a>'
            '</div>')

    html = (
        '<div style="background:#f4f5f7;padding:24px 12px;">'
        '<div style="max-width:640px;margin:0 auto;background:#fff;border-radius:14px;padding:26px 28px;'
        'box-shadow:0 4px 18px rgba(15,23,42,.08);font-family:Segoe UI,Arial,sans-serif;">'
        f'<div style="font:700 20px/1.3 Segoe UI,Arial,sans-serif;color:#0f172a;">Birthday greeting ready — {date_str}</div>'
        '<div style="font:400 14px/1.6 Segoe UI,Arial,sans-serif;color:#475569;margin:10px 0 20px;">'
        'Each button below opens Outlook with the recipient, subject and card already '
        'filled in — just press <strong>Send</strong>.'
        '</div>'
        + "".join(rows) +
        '</div></div>')

    if not is_valid_email(to):
        return {"successful": False, "error": f"bad notify recipient {to!r}"}
    # Copy-Cc (program account) is applied inside send_card — house convention.
    res = send_card(to, f"Birthday greeting ready to send — {date_str}", html, None)
    return {"successful": bool(res.get("successful")), "to": to, "cc": None,
            "bcc": None, "error": res.get("error")}


def notify_send_result(result: Dict[str, Any],
                       settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Safety net after a LIVE run: report what went out, with a one-click fallback.

    Direct delivery to @montefiore.org is INTERMITTENT — it has landed and it has
    vanished silently, with no bounce either way (measured 2026-09-16). A clean SMTP
    accept is therefore NOT proof the recipient has the card. This notification says
    who was sent what, and carries the Outlook handoff link per person, so a card
    that didn't land can still go out the same morning.
    """
    settings = settings or load_settings()
    to = settings.get("notify_recipient") or "sfrasier@montefiore.org"
    date_str = result.get("date", "")
    sent = result.get("sent") or []
    failed = result.get("failed") or []
    if not sent and not failed:
        return {"successful": True, "skipped": "nothing to report"}

    live_cc = [a.strip() for a in (settings.get("cc") or []) if is_valid_email(a.strip())]

    rows = []
    for it in sent:
        person = {"first_name": it.get("first_name") or "",
                  "last_name": it.get("last_name") or "",
                  "email": it.get("email") or ""}
        card = Path(it["card"]) if it.get("card") else None
        card_url = publish_card(card, settings) if card else None
        img = (f'<img src="{card_url}" width="520" style="width:100%;max-width:520px;'
               'border-radius:10px;border:1px solid #e2e8f0;display:block;margin-bottom:12px;">'
               if card_url else "")
        # Fallback deeplink, rebuilt from the same builders the handoff path uses.
        body = build_handoff_body(person, it.get("note") or "", card_url, settings)
        link = build_outlook_deeplink(person["email"], it.get("subject") or "",
                                      body, cc=", ".join(live_cc) or None)
        meta = f'Sent to <strong>{it.get("sent_to")}</strong>'
        if it.get("cc"):
            meta += f' · cc {", ".join(it["cc"])}'
        first = person["first_name"] or "they"
        rows.append(
            '<div style="border:1px solid #e2e8f0;border-radius:12px;padding:16px;margin-bottom:18px;">'
            + img +
            '<div style="font:600 16px/1.4 Segoe UI,Arial,sans-serif;color:#0f172a;">'
            f'{it.get("name")} — {it.get("email")}</div>'
            '<div style="font:400 13px/1.6 Segoe UI,Arial,sans-serif;color:#64748b;margin:6px 0 14px;">'
            f'{meta}<br>Subject: {it.get("subject")}</div>'
            f'<a href="{link}" style="display:inline-block;background:#0f766e;color:#fff;'
            'font:600 14px Segoe UI,Arial,sans-serif;padding:11px 20px;border-radius:8px;'
            f'text-decoration:none;">If {first} didn\u2019t get it, resend from Outlook</a>'
            '</div>')

    fail_rows = ""
    if failed:
        items = "".join(
            '<li style="margin-bottom:4px;">{n} — {e}</li>'.format(
                n=f.get("name"), e=f.get("error") or f.get("reason") or "unknown")
            for f in failed)
        fail_rows = (
            '<div style="border:1px solid #fecaca;background:#fef2f2;border-radius:12px;'
            'padding:14px 16px;margin-bottom:18px;">'
            '<div style="font:600 14px Segoe UI,Arial,sans-serif;color:#991b1b;margin-bottom:6px;">'
            f'Failed to send ({len(failed)})</div>'
            '<ul style="margin:0;padding-left:18px;font:400 13px/1.6 Segoe UI,Arial,sans-serif;'
            f'color:#7f1d1d;">{items}</ul>'
            '</div>')

    n = len(sent)
    html = (
        '<div style="background:#f4f5f7;padding:24px 12px;">'
        '<div style="max-width:640px;margin:0 auto;background:#fff;border-radius:14px;padding:26px 28px;'
        'box-shadow:0 4px 18px rgba(15,23,42,.08);font-family:Segoe UI,Arial,sans-serif;">'
        f'<div style="font:700 20px/1.3 Segoe UI,Arial,sans-serif;color:#0f172a;">'
        f'{n} birthday greeting{"" if n == 1 else "s"} sent — {date_str}</div>'
        '<div style="font:400 14px/1.6 Segoe UI,Arial,sans-serif;color:#475569;margin:10px 0 20px;">'
        'Sent directly from the program mailbox, with the program-account copy Cc '
        'that gets it past the Montefiore quarantine. If a card still does not arrive, '
        'the button below resends it from your own Outlook.'
        '</div>'
        + fail_rows + "".join(rows) +
        '</div></div>')

    if not is_valid_email(to):
        return {"successful": False, "error": f"bad notify recipient {to!r}"}
    subject = (f"Birthday greeting sent — {date_str}" if n == 1
               else f"{n} birthday greetings sent — {date_str}")
    # Copy-Cc (program account) is applied inside send_card — house convention.
    res = send_card(to, subject, html, None)
    return {"successful": bool(res.get("successful")), "to": to, "bcc": None,
            "count": n, "error": res.get("error")}


def publish_email_preview(person: Dict[str, Any], note: Optional[str] = None,
                          settings: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """Render the EXACT resident-facing email to a public URL for format review.

    Same build_html() the real send uses, with the inline CID swapped for the
    published card file so it renders in a browser. Lets us iterate on the email
    format without emailing anyone.
    """
    settings = settings or load_settings()
    note = note or pick_note(person, settings, settings.get("note_source", "template"))
    art = generate_base_art(settings)
    card = None
    try:
        card = prepare_card(person, settings, reuse_art=art, note=note)
    except Exception as e:
        print(f"[warn] card compose failed: {e}", file=sys.stderr)
    if card:
        publish_card(card, settings)  # ensures the image sits in the public dir

    cid = f"bday-{uuid.uuid4().hex[:12]}"
    html = build_html(person, settings, note, cid)
    if card:
        html = html.replace(f"cid:{cid}", f"../cards/{Path(card).name}")

    # mark the render as a preview (the email itself has no footer by design)
    preview_note = (
        '<div style="background:#fff7e6;border-bottom:2px solid #e8c77a;padding:12px 16px;'
        'font:500 13px/1.5 Segoe UI,Arial,sans-serif;color:#7a5c00;">'
        '<strong>PREVIEW</strong> — exactly how this email renders. Nothing was sent.</div>')
    html = re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + "\n" + preview_note, html, count=1)

    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    stamp = local_today().strftime("%Y-%m-%d")
    slug = re.sub(r"[^a-z0-9]+", "-",
                  f"{person.get('first_name')}-{person.get('last_name')}".lower()).strip("-")
    out = PREVIEW_DIR / f"{stamp}_{slug}.html"
    out.write_text(html)
    base = (settings.get("public_base_url") or "").rstrip("/")
    return f"{base}/dashboard/previews/{out.name}" if base else str(out)


DESIGN_GALLERY_DIR = BASE_DIR / "dashboard" / "designs"


def publish_design_gallery(name: str = "John Hordines",
                           exclude: Optional[List[str]] = None,
                           settings: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """Render EVERY design for one name and publish a review page.

    Lets the user see all the art directions side by side and bench the ones they
    don't like, instead of judging them one email at a time.
    """
    import card_designs

    settings = settings or load_settings()
    exclude = list(exclude if exclude is not None else (settings.get("design_exclude") or []))
    DESIGN_GALLERY_DIR.mkdir(parents=True, exist_ok=True)

    first, _, last = name.partition(" ")
    person = {"first_name": first, "last_name": last, "id": "gallery-sample",
              "email": "sample@example.com", "birthday": ""}
    dept = settings.get("card_dept") or "Montefiore Urology"
    sample_note = pick_note(person, settings, settings.get("note_source", "template"))

    in_rotation = set(card_designs.rotation(exclude))
    rows = []
    for i, key in enumerate(card_designs.design_names(), 1):
        spec = card_designs.DESIGNS[key]
        out = DESIGN_GALLERY_DIR / f"{i:02d}_{key}.jpg"
        art = None
        try:
            if spec.get("needs_art"):
                art = generate_base_art(settings)
            card_designs.render_card(key, person, out, dept=dept, art_path=art,
                                     note=sample_note)
        except Exception as e:
            print(f"[warn] gallery render {key}: {e}", file=sys.stderr)
            continue

        if key in exclude:
            badge, badge_cls = "Benched", "off"
        elif key in in_rotation:
            badge, badge_cls = "In rotation", "on"
        else:
            badge, badge_cls = "Opt-in (not rotated)", "opt"

        rows.append(f"""
      <div class="item">
        <img src="{out.name}" alt="{key}">
        <div class="meta">
          <div class="row">
            <span class="idx">{i}</span>
            <span class="key">{key}</span>
            <span class="badge {badge_cls}">{badge}</span>
          </div>
          <div class="label">{spec.get('label', key)}</div>
          <div class="blurb">{spec.get('blurb', '')}</div>
        </div>
      </div>""")

    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Birthday card designs</title>
<style>
  :root {{ color-scheme: dark; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:#0b0d12; color:#e8eaee;
          font:15px/1.55 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif; }}
  header {{ padding:34px 32px 20px; border-bottom:1px solid #1e222b; }}
  h1 {{ margin:0 0 8px; font-size:22px; letter-spacing:-.01em; }}
  .sub {{ color:#8b93a7; font-size:13.5px; }}
  .sub b {{ color:#e8c77a; font-weight:600; }}
  .grid {{ display:grid; grid-template-columns:1fr; gap:26px; padding:26px 32px 60px; max-width:1180px; }}
  .item {{ border:1px solid #1e222b; border-radius:14px; overflow:hidden; background:#111419; }}
  .item img {{ display:block; width:100%; height:auto; }}
  .meta {{ padding:14px 18px 18px; }}
  .row {{ display:flex; align-items:center; gap:10px; }}
  .idx {{ width:22px; height:22px; border-radius:6px; background:#1e222b; color:#8b93a7;
          font-size:12px; font-weight:700; display:flex; align-items:center; justify-content:center; }}
  .key {{ font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:12.5px; color:#9aa3b6; }}
  .badge {{ margin-left:auto; font-size:10.5px; font-weight:700; letter-spacing:.06em;
            text-transform:uppercase; padding:4px 9px; border-radius:999px; }}
  .badge.on {{ background:rgba(0,184,148,.14); color:#34d3a3; }}
  .badge.off {{ background:rgba(214,48,49,.14); color:#ff7675; }}
  .badge.opt {{ background:rgba(148,163,184,.14); color:#94a3b8; }}
  .label {{ margin-top:10px; font-size:15px; font-weight:600; }}
  .blurb {{ color:#8b93a7; font-size:13px; margin-top:3px; }}
</style></head><body>
  <header>
    <h1>Birthday card designs</h1>
    <div class="sub">Rendered for <b>{name}</b> · {len(rows)} designs ·
      benched via <code>design_exclude</code>: <b>{', '.join(exclude) or 'none'}</b></div>
  </header>
  <div class="grid">{''.join(rows)}</div>
</body></html>"""

    index = DESIGN_GALLERY_DIR / "index.html"
    index.write_text(html, encoding="utf-8")
    base = (settings.get("public_base_url") or "").rstrip("/")
    return f"{base}/dashboard/designs/index.html" if base else str(index)


def _email_summary(person: Dict[str, Any], settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """The resident-facing email described as data (subject / from / to / body text)."""
    settings = settings or load_settings()
    note = pick_note(person, settings, settings.get("note_source", "template"))
    first = (person.get("first_name") or "").strip()
    subject = (settings.get("subject_template") or "Happy Birthday, {first_name}!").format(
        first_name=first, last_name=(person.get("last_name") or "").strip(),
        name=f"{person.get('first_name','')} {person.get('last_name','')}".strip())
    import card_designs
    _bd = parse_birthday(person.get("birthday"))
    design = card_designs.pick_design(
        person.get("id") or person.get("email") or "",
        local_today().year, _DESIGN_OVERRIDE or settings.get("design"),
        month=_bd[0] if _bd else None,
        exclude=settings.get("design_exclude"))
    return {
        "to": person.get("email"),
        "from": f"{os.environ.get('SMTP_FROM_NAME', 'Urology Residency Program')} "
                f"<{_smtp_cfg().get('user','')}>",
        "cc": [a for a in (settings.get("cc") or [])
               if is_valid_email(a) and a.lower() != (person.get("email") or "").lower()],
        "subject": subject,
        "body_text": "Happy Birthday, {first}!".format(first=(person.get("first_name") or "").strip())
                     if not settings.get("show_note_in_body", False) else note,
        "card_message": note,
        "design": f"{design} ({card_designs.DESIGNS[design]['label']})",
        "signature": settings.get("signature") or "(none)",
        "footer": settings.get("footer_note") or "(none)",
        "card_embedded_inline": True,
    }


def send_format_preview(person: Dict[str, Any], settings: Optional[Dict[str, Any]] = None,
                        to: Optional[str] = None, cc: Optional[List[str]] = None) -> Dict[str, Any]:
    """Send the EXACT resident-facing email (real subject, real embedded card) to a
    reviewer address, with a preview banner so it can't be mistaken for a real send.

    Unlike the normal test-mode send this does NOT prefix the subject, because the
    subject line is part of the format under review.
    """
    settings = settings or load_settings()
    note = pick_note(person, settings, settings.get("note_source", "template"))
    art = generate_base_art(settings)
    card = None
    try:
        card = prepare_card(person, settings, reuse_art=art, note=note)
    except Exception as e:
        print(f"[warn] card compose failed: {e}", file=sys.stderr)

    cid = f"bday-{uuid.uuid4().hex[:12]}"
    html = build_html(person, settings, note, cid)
    first = (person.get("first_name") or "").strip()
    subject = (settings.get("subject_template") or "Happy Birthday, {first_name}!").format(
        first_name=first, last_name=(person.get("last_name") or "").strip(),
        name=f"{person.get('first_name','')} {person.get('last_name','')}".strip())

    banner = (
        '<div style="background:#fff7e6;border-bottom:2px solid #e8c77a;padding:12px 16px;'
        'font:500 13px/1.5 Segoe UI,Arial,sans-serif;color:#7a5c00;">'
        f'PREVIEW — this is the email {first} would receive. Subject, card and wording are exactly '
        'what would be delivered. Nothing was sent to any resident.</div>')
    # insert the banner as the first thing in the body (lambda keeps the banner literal —
    # a plain replacement string would interpret any backslash escapes in it)
    html = re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + "\n" + banner, html, count=1)

    to = to or settings.get("test_recipient") or "sfrasier@montefiore.org"
    if cc is None:
        # Mirror the real leadership list when configured, so a format review
        # shows exactly what leadership will receive.
        cc = ([a.strip() for a in (settings.get("cc") or []) if is_valid_email(a.strip())]
              if settings.get("cc_on_test") else [])
    # never cc the recipient onto their own copy
    cc = [a for a in cc if a.lower() != (to or "").lower()]

    res = send_card(to, subject, html, card, cc=cc or None, cid=cid)
    append_log({
        "date": local_today().strftime("%Y-%m-%d"), "contact_id": person.get("id"),
        "name": f"{person.get('first_name','')} {person.get('last_name','')}".strip(),
        "intended_email": person.get("email"), "sent_to": to, "subject": subject,
        "card": str(card) if card else None, "test_mode": True, "status": "format-preview",
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    })
    return {"successful": bool(res.get("successful")), "to": to, "cc": cc,
            "subject": subject, "card": str(card) if card else None,
            "error": res.get("error")}


# ─────────────────────────────────────────────────────────────
# Orchestration
# ─────────────────────────────────────────────────────────────

# CLI-only one-shot override so `--design X` doesn't have to mutate settings.json.
# Module-level because every card path funnels through prepare_card().
_DESIGN_OVERRIDE: Optional[str] = None


def prepare_card(person: Dict[str, Any], settings: Dict[str, Any],
                 reuse_art: Optional[Path] = None,
                 note: Optional[str] = None) -> Optional[Path]:
    """Render the personalised card through the design system (card_designs.py).

    The design rotates per person (stable for the year), so a year of birthdays
    doesn't look like the same card fifteen times. Set settings["design"] to a
    design key (or "auto" for rotation), or pass a number 1-N.

    `note` is the message line printed ON the card. Callers that already picked a
    note for the email body pass it here so the card and the email always agree —
    important when note_source="llm", where two calls would differ.
    """
    import card_designs  # local import keeps module load cheap

    note = note if note is not None else pick_note(
        person, settings, settings.get("note_source", "template"))
    year = local_today().year
    bd = parse_birthday(person.get("birthday"))
    design = card_designs.pick_design(
        person.get("id") or person.get("email") or "", year,
        _DESIGN_OVERRIDE or settings.get("design"),
        month=bd[0] if bd else None,
        exclude=settings.get("design_exclude"))
    art = None
    if card_designs.DESIGNS.get(design, {}).get("needs_art"):
        art = reuse_art or generate_base_art(settings)

    stamp = local_today().strftime("%Y-%m-%d")
    safe = re.sub(r"[^a-z0-9]+", "-",
                  f"{person.get('first_name')}-{person.get('last_name')}".lower()).strip("-")
    out = CARDS_DIR / f"{stamp}_{safe}_{design}.jpg"
    try:
        return card_designs.render_card(
            design, person, out,
            dept=settings.get("card_dept") or "Montefiore Urology",
            year=year, art_path=art, note=note)
    except Exception as e:
        print(f"[warn] card render failed ({design}) for {safe}: {e}", file=sys.stderr)
        return None


def run(target_date: Optional[str] = None, dry_run: bool = False,
        test_mode: Optional[bool] = None, force: bool = False,
        only: Optional[str] = None, note_source: Optional[str] = None,
        regen_art: bool = False, verbose: bool = True) -> Dict[str, Any]:
    """Run the birthday pipeline for a given day (default: today)."""
    settings = load_settings()
    if test_mode is None:
        test_mode = bool(settings.get("test_mode", True))
    note_source = note_source or settings.get("note_source", "template")

    if target_date:
        try:
            base = datetime.strptime(target_date, "%Y-%m-%d").replace(tzinfo=local_today().tzinfo)
        except ValueError:
            return {"ok": False, "error": f"bad --date {target_date!r}; use YYYY-MM-DD"}
    else:
        base = local_today()

    date_str = base.strftime("%Y-%m-%d")
    y, m, d = base.year, base.month, base.day

    if not settings.get("enabled", True):
        return {"ok": False, "error": "birthday emails disabled in settings.json"}

    contacts = fetch_contacts()
    people = birthdays_on(m, d, contacts)

    if only:
        only_l = only.strip().lower()
        people = [p for p in people
                  if only_l in (p.get("email") or "").lower()
                  or only_l in f"{p.get('first_name')} {p.get('last_name')}".lower()]
        if not people:
            # allow testing a person whose birthday is NOT today
            people = [c for c in contacts
                      if only_l in (c.get("email") or "").lower()
                      or only_l in f"{c.get('first_name')} {c.get('last_name')}".lower()]
            if people and verbose:
                print(f"[info] --person {only!r} is not today's birthday — test-sending anyway")

    result: Dict[str, Any] = {
        "ok": True, "date": date_str, "test_mode": bool(test_mode),
        "dry_run": dry_run, "candidates": len(people), "sent": [], "skipped": [], "failed": [],
        "source": contacts[0]["source"] if contacts else "none",
        "crm_with_birthdays": len(contacts),
    }

    if not people:
        if verbose:
            print(f"No birthdays on {date_str}.")
        return result

    art = generate_base_art(settings, force=regen_art)
    if art and verbose:
        print(f"[art] {art}")

    test_recipient = settings.get("test_recipient") or "sfrasier@montefiore.org"
    live_cc = [a.strip() for a in (settings.get("cc") or []) if is_valid_email(a.strip())]

    base_bcc: List[str] = []
    if test_mode:
        # Leadership is excluded from tests by default so they don't receive our
        # drafts; `cc_on_test` mirrors the real list when a format review needs to
        # show exactly what leadership will get. The program-account copy Cc is
        # applied per-send inside send_card (house convention, 2026-09-18).
        base_cc: List[str] = list(live_cc) if settings.get("cc_on_test") else []
    else:
        # Live sends cc program leadership (settings["cc"]).
        base_cc = list(live_cc)

    for person in people:
        cid_ = person.get("id") or f"{person.get('first_name')}-{person.get('last_name')}"
        name = f"{person.get('first_name')} {person.get('last_name')}".strip()
        record = {"contact_id": cid_, "name": name, "email": person.get("email"),
                  "category": person.get("category"),
                  "first_name": (person.get("first_name") or "").strip(),
                  "last_name": (person.get("last_name") or "").strip()}
        # NOTE: `note` is deliberately NOT added here — it is picked after the
        # already-sent check below, so referencing it at this point is an
        # UnboundLocalError on any run that reaches a real candidate. It rides on
        # the per-send payloads instead (the safety-net notification needs it).

        if not force and already_sent(cid_, date_str):
            result["skipped"].append({**record, "reason": "already sent today"})
            if verbose:
                print(f"[skip] {name} — already sent today")
            continue

        card = None
        note = pick_note(person, settings, note_source)
        if art:
            try:
                card = prepare_card(person, settings, reuse_art=art, note=note)
            except Exception as e:
                print(f"[warn] card compose failed for {name}: {e}", file=sys.stderr)

        cid = f"bday-{uuid.uuid4().hex[:12]}"
        first = (person.get("first_name") or "").strip()
        subject = (settings.get("subject_template") or "Happy Birthday, {first_name}!").format(
            first_name=first, last_name=(person.get("last_name") or "").strip(), name=name)
        html = build_html(person, settings, note, cid)
        recipient = test_recipient if test_mode else person["email"]
        if test_mode:
            subject = f"[TEST → {person['email']}] {subject}"
        # never cc the recipient onto their own birthday email
        cc = [a for a in base_cc if a.lower() != (recipient or "").lower()]
        # same for the blind copy, and never duplicate something already on cc
        _cc_l = [c.lower() for c in cc]
        bcc = [a for a in base_bcc
               if a.lower() != (recipient or "").lower() and a.lower() not in _cc_l]

        entry = {
            "date": date_str, "contact_id": cid_, "name": name,
            "intended_email": person.get("email"), "sent_to": recipient,
            "cc": cc, "bcc": bcc,
            "subject": subject, "card": str(card) if card else None,
            "note": note, "test_mode": bool(test_mode),
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }

        if dry_run:
            entry["status"] = "dry-run"
            result["sent"].append({**record, "status": "dry-run", "subject": subject,
                                   "sent_to": recipient, "cc": cc, "bcc": bcc,
                                   "note": note,
                                   "card": str(card) if card else None})
            if verbose:
                print(f"[dry-run] would send '{subject}' → {recipient} "
                      f"(cc: {cc or 'none'}; bcc: {bcc or 'none'}; card: {card})")
            continue

        # inline CID must match the token referenced in the HTML body
        res = send_card(recipient, subject, html, card, cc=cc, cid=cid,
                        bcc=bcc or None)
        if res.get("successful"):
            entry["status"] = "test-sent" if test_mode else "sent"
            result["sent"].append({**record, "status": entry["status"], "subject": subject,
                                   "sent_to": recipient, "cc": cc, "bcc": bcc,
                                   "note": note,
                                   "card": str(card) if card else None})
            if verbose:
                print(f"[sent] {name} → {recipient}")
        else:
            entry["status"] = "failed"
            entry["error"] = res.get("error")
            result["failed"].append({**record, "error": res.get("error")})
            if verbose:
                print(f"[FAIL] {name}: {res.get('error')}", file=sys.stderr)

        append_log(entry)

    settings["last_run"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    save_settings(settings)
    return result


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

def _print_upcoming(days: int) -> None:
    rows = upcoming(days)
    today = local_today()
    print(f"Upcoming birthdays — next {days} days (as of {today.strftime('%Y-%m-%d %H:%M %Z')})")
    if not rows:
        print("  (none)")
        return
    for r in rows:
        when = "TODAY" if r["days_until"] == 0 else f"in {r['days_until']}d"
        print(f"  {r['next_birthday']}  {when:<9} {r['first_name']} {r['last_name']:<20} "
              f"{r['category']:<16} {r['email']}")
    print(f"\n{len(rows)} upcoming · {sum(1 for r in rows if r['days_until'] == 0)} today")


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Agentic OS birthday email engine")
    p.add_argument("--list", action="store_true", help="list upcoming birthdays")
    p.add_argument("--days", type=int, default=60, help="window for --list (default 60)")
    p.add_argument("--today", action="store_true", help="show today's birthdays")
    p.add_argument("--run", action="store_true", help="generate and send for the target date")
    p.add_argument("--date", help="target date YYYY-MM-DD (default: today)")
    p.add_argument("--dry-run", action="store_true", help="full pipeline, no email sent")
    p.add_argument("--test", action="store_true", help="force test mode (route to test_recipient)")
    p.add_argument("--live", action="store_true", help="force live send to the real recipient")
    p.add_argument("--person", help="only this person (email fragment or name)")
    p.add_argument("--preview", action="store_true", help="generate a card only, never send")
    p.add_argument("--force", action="store_true", help="re-send even if already sent today")
    p.add_argument("--note-source", choices=["template", "llm"], help="note text source")
    p.add_argument("--regen-art", action="store_true", help="force new base artwork")
    p.add_argument("--design", help="card design: a key (midnight-gold, ivory-press, "
                                    "clinical-modern, emerald-brass, sunrise, confetti, "
                                    "ai-artwork), a number 1-7, or 'auto' to rotate")
    p.add_argument("--designs", action="store_true", help="list available card designs")
    p.add_argument("--design-gallery", action="store_true",
                   help="render every design for --name (default the next birthday person) and "
                        "publish a review page")
    p.add_argument("--name", help="name to render in the design gallery")
    p.add_argument("--exclude", help="comma-separated designs to bench (with --design-gallery)")
    p.add_argument("--handoff", action="store_true",
                   help="build send-ready Outlook compose links (the delivery path "
                        "that actually reaches @montefiore.org) instead of emailing directly")
    p.add_argument("--notify", action="store_true",
                   help="email the user a report: with --handoff, the compose links; "
                        "with --run, what was sent plus a per-person fallback link")
    p.add_argument("--email-preview", action="store_true",
                   help="render the exact resident-facing email to a public preview URL")
    p.add_argument("--send-preview", action="store_true",
                   help="with --person: send the exact resident-facing email (real subject) to "
                        "the reviewer address for format approval — never to the resident")
    p.add_argument("--at-hour", type=int, metavar="H",
                   help="scheduled mode: only proceed when the local (ET) hour == H, "
                        "otherwise exit quietly. Lets a fixed UTC cron cover 9am ET "
                        "year-round across DST.")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    args = p.parse_args(argv)

    if args.at_hour is not None and (args.run or args.handoff):
        now = local_today()
        if now.hour != args.at_hour:
            print(f"[skip] local hour {now.hour} != {args.at_hour} — waiting for the "
                  f"{args.at_hour}:00 ET window")
            return 0

    if args.design:
        global _DESIGN_OVERRIDE
        _DESIGN_OVERRIDE = args.design

    if args.designs:
        import card_designs
        print(f"Card designs ({len(card_designs.DESIGNS)}):")
        for i, key in enumerate(card_designs.design_names(), 1):
            spec = card_designs.DESIGNS[key]
            rot = "" if key in card_designs.ROTATION else "  (opt-in, not in rotation)"
            print(f"  {i}. {key:<18} {spec['label']:<20} {spec['blurb']}{rot}")
        print("\nRotation is stable per person per year. Use --design <key|number> to pin one.")
        return 0

    if args.list:
        _print_upcoming(args.days)
        return 0

    if args.today:
        t = local_today()
        people = birthdays_on(t.month, t.day)
        if not people:
            print(f"No birthdays on {t.strftime('%Y-%m-%d')}.")
            return 0
        for c in people:
            print(f"  {c['first_name']} {c['last_name']:<20} {c['category']:<16} "
                  f"{c['email']:<32} bday {c['birthday']}")
        return 0

    if args.preview:
        if not args.person:
            print("--preview needs --person <email|name>", file=sys.stderr)
            return 2
        settings = load_settings()
        contacts = fetch_contacts()
        frag = args.person.lower()
        match = [c for c in contacts
                 if frag in (c.get("email") or "").lower()
                 or frag in f"{c.get('first_name')} {c.get('last_name')}".lower()]
        if not match:
            print(f"No contact matched {args.person!r}", file=sys.stderr)
            return 1
        art = generate_base_art(settings, force=args.regen_art)
        card = prepare_card(match[0], settings, reuse_art=art)
        print(json.dumps({"ok": True, "person": f"{match[0]['first_name']} {match[0]['last_name']}",
                          "card": str(card)}, indent=2))
        return 0

    if args.design_gallery:
        settings = load_settings()
        name = args.name
        if not name:
            # default to the next person with a birthday so the sample is realistic
            up = upcoming(365)
            if up:
                name = f"{up[0].get('first_name','')} {up[0].get('last_name','')}".strip()
            else:
                name = "John Hordines"
        excl = None
        if args.exclude:
            excl = [x.strip() for x in args.exclude.split(",") if x.strip()]
        url = publish_design_gallery(name=name, exclude=excl, settings=settings)
        print(json.dumps({"ok": True, "name": name, "gallery_url": url,
                          "benched": excl if excl is not None
                          else (settings.get("design_exclude") or [])}, indent=2))
        return 0

    if args.send_preview:
        if not args.person:
            print("--send-preview needs --person <email|name>", file=sys.stderr)
            return 2
        contacts = fetch_contacts()
        frag = args.person.lower()
        match = [c for c in contacts
                 if frag in (c.get("email") or "").lower()
                 or frag in f"{c.get('first_name')} {c.get('last_name')}".lower()]
        if not match:
            print(f"No contact matched {args.person!r}", file=sys.stderr)
            return 1
        res = send_format_preview(match[0])
        print(json.dumps(res, indent=2))
        return 0 if res.get("successful") else 1

    if args.email_preview:
        if not args.person:
            print("--email-preview needs --person <email|name>", file=sys.stderr)
            return 2
        contacts = fetch_contacts()
        frag = args.person.lower()
        match = [c for c in contacts
                 if frag in (c.get("email") or "").lower()
                 or frag in f"{c.get('first_name')} {c.get('last_name')}".lower()]
        if not match:
            print(f"No contact matched {args.person!r}", file=sys.stderr)
            return 1
        url = publish_email_preview(match[0])
        out = {"ok": True, "person": f"{match[0]['first_name']} {match[0]['last_name']}",
               "preview_url": url, "email": _email_summary(match[0])}
        print(json.dumps(out, indent=2))
        return 0

    if args.handoff:
        res = handoff(target_date=args.date, only=args.person, notify=args.notify,
                      regen_art=args.regen_art, note_source=args.note_source)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            n = len(res.get("items", []))
            print(f"\nOutlook handoff for {res['date']}: {n} greeting(s) ready to send.")
            if res.get("notified"):
                ok = res["notified"].get("successful")
                print(f"Notification email: {'sent' if ok else 'FAILED — ' + str(res['notified'].get('error'))}")
            if n:
                print("Open a link above (or the Birthdays page) → press Send in Outlook.")
        return 0

    if args.run:
        test_mode = None
        if args.test:
            test_mode = True
        if args.live:
            test_mode = False
        res = run(target_date=args.date, dry_run=args.dry_run, test_mode=test_mode,
                  force=args.force, only=args.person, note_source=args.note_source,
                  regen_art=args.regen_art)
        # Safety net: after a LIVE send, report what went out and attach a per-person
        # fallback link. Direct delivery is intermittent, so a clean send is not proof
        # the card arrived — this is what lets the user recover the same morning.
        if args.notify and not args.dry_run and res.get("sent"):
            try:
                res["notified"] = notify_send_result(res)
            except Exception as e:
                print(f"[warn] send notification failed: {e}", file=sys.stderr)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            mode = "LIVE" if not res["test_mode"] else "TEST"
            verb = "dry-run" if res["dry_run"] else "send"
            print(f"\n{mode} {verb} for {res['date']}: "
                  f"{len(res['sent'])} sent, {len(res['skipped'])} skipped, "
                  f"{len(res['failed'])} failed "
                  f"(CRM: {res['crm_with_birthdays']} contacts with birthdays, from {res['source']})")
            if res["failed"]:
                return 1
        return 0

    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
