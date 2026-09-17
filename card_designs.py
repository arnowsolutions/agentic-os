#!/usr/bin/env python3
"""
Birthday card design system — Agentic OS
========================================

Six rotating art directions plus one opt-in AI-artwork design, rendered as real
HTML/CSS through headless Chromium at 2x.

DESIGN PHILOSOPHY (revised 2026-09-16)
--------------------------------------
The first cut of these designs was too *thin* — flat background, one line of type,
nothing to reward a second look. Each design now builds in layers:

  1. ground   — base colour/gradient, then a light rig (multiple soft glows)
  2. texture  — fine grain and/or a pattern (rays, guilloche, deco fans)
  3. ornament — a monogram medallion, frame work, art-deco detailing
  4. type     — the name, metallic foil or engraved, with real hierarchy

A card should survive being looked at twice: the first look reads the name, the
second notices the craft.

WHY CHROMIUM: real design needs gradient meshes, blend modes, background-clip
foil, letter-spacing and variable fonts. PIL compositing cannot do this.
"""
from __future__ import annotations

import asyncio
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parent
FONT_DIR = BASE_DIR / "assets" / "fonts"

CARD_W, CARD_H = 1600, 900
SCALE = 2  # -> 3200x1800 output

FONTS = {
    "playfair": "playfair.ttf",
    "fraunces": "fraunces.ttf",
    "inter": "inter.ttf",
    "cormorant": "cormorant.ttf",
    "outfit": "outfit.ttf",
    "dmserif": "dmserif.ttf",
    "spacegrotesk": "spacegrotesk.ttf",
}

# Fine film grain — the single cheapest upgrade to perceived quality. Flat vector
# gradients read as "template"; grain reads as "printed".
_GRAIN_URI = (
    "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='220' height='220'>"
    "<filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.82' numOctaves='4' "
    "stitchTiles='stitch'/></filter>"
    "<rect width='220' height='220' filter='url(%23n)'/></svg>"
)

# Shared CSS injected once per document — texture, foil, monogram chrome.
COMMON_CSS = f"""
.grain {{ position:absolute; inset:0; pointer-events:none;
  background-image:url("{_GRAIN_URI}"); opacity:.15; mix-blend-mode:overlay; }}
/* Light cards band badly in large soft gradients; a stronger multiply grain dithers
   the ramps and reads as paper. */
.grain-dark {{ mix-blend-mode:multiply; opacity:.19; }}
.foil {{ background:linear-gradient(104deg,#7d5f26 0%,#e8c77a 18%,#fff6dc 34%,#d9b25f 50%,
  #f2dda6 64%,#8a6a2f 84%,#c9a24e 100%);
  -webkit-background-clip:text; background-clip:text; color:transparent; }}
.mono {{ display:flex; align-items:center; justify-content:center; }}
.mono-ring {{ display:flex; align-items:center; justify-content:center;
  border-radius:50%; }}
.shadow-soft {{ box-shadow:0 30px 80px rgba(0,0,0,.45); }}
"""


def _font_css() -> str:
    out = []
    for fam, file in FONTS.items():
        p = FONT_DIR / file
        if p.exists():
            out.append(
                f"@font-face{{font-family:'{fam}';src:url('{p.as_uri()}');"
                f"font-weight:100 900;font-display:block;}}")
    return "\n".join(out)


def _fit(name: str, base: int, min_size: int = 54, per_char: float = 4.6) -> int:
    """Shrink the name face for long names so it never crowds the frame."""
    n = len(name)
    if n <= 14:
        return base
    return max(min_size, int(base - (n - 14) * per_char))


def _esc(s: str) -> str:
    return (str(s or "")
            .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _initials(first: str, last: str) -> str:
    a = (first or "").strip()[:1]
    b = (last or "").strip()[:1]
    return (a + b).upper() or "•"


def _note_size(note: str, base: int = 31) -> int:
    """Scale the message line so it stays on one or two lines in every layout.

    Bases sit around 31 design px. The card is 1600 design px wide but displays in
    the email at 640, so the on-screen scale is 0.4 — a 31px line reads ~12px in
    the inbox. Below ~29 it stops being comfortably legible at that size.
    """
    n = len(note or "")
    if n <= 48:
        return base + 2
    if n <= 70:
        return base
    return max(26, base - 4)


def _note_html(note: str, cls: str = "note") -> str:
    return f'<div class="{cls}">{_esc(note)}</div>' if (note or "").strip() else ""


# ─────────────────────────────────────────────────────────────
# Design registry — each entry is a full art direction
# ─────────────────────────────────────────────────────────────

def _midnight_gold(name: str, first: str, last: str, dept: str, year: int,
                   note: str = "") -> str:
    """Art-deco grandeur: navy ground, fan corners, metallic foil name, monogram."""
    size = _fit(name, 110)
    nsize = _note_size(note, 31)
    mono = _initials(first, last)
    fans = "".join(
        f'<g transform="translate({x},{y}) rotate({r})">'
        f'<path d="M0 0 L64 0 M0 0 L59 -22 M0 0 L50 -42 M0 0 L37 -59 M0 0 L20 -70" '
        f'stroke="#e8c77a" stroke-width="1.1" fill="none" opacity=".55"/></g>'
        for x, y, r in [(64, 64, 0), (1536, 64, 90), (1536, 836, 180), (64, 836, 270)])
    return f"""
    <div class="card">
      <div class="light"></div><div class="light2"></div><div class="light3"></div>
      <svg class="rays" viewBox="0 0 1600 900" preserveAspectRatio="none">
        <defs><radialGradient id="rg" cx="50%" cy="0%" r="78%">
          <stop offset="0%" stop-color="#e8c77a" stop-opacity=".16"/>
          <stop offset="100%" stop-color="#e8c77a" stop-opacity="0"/>
        </radialGradient></defs>
        <rect width="1600" height="900" fill="url(#rg)"/>
        <g stroke="#e8c77a" stroke-width="1" opacity=".10">
          {"".join(f'<line x1="800" y1="0" x2="{x}" y2="900"/>' for x in range(0, 1601, 100))}
        </g>
      </svg>
      <svg class="fans" viewBox="0 0 1600 900">{fans}</svg>
      <div class="frame"></div><div class="frame2"></div>
      <div class="grain"></div>
      <div class="inner">
        <div class="mono"><div class="mono-ring"><span class="foil">{mono}</span></div></div>
        <div class="name foil">{_esc(name)}</div>
        <div class="rule"><i></i><b></b><i></i></div>
        {_note_html(note)}
        <div class="dept">{_esc(dept)}</div>
      </div>
    </div>
    <style>
      .card {{ position:relative; width:{CARD_W}px; height:{CARD_H}px; overflow:hidden;
        background:
          radial-gradient(120% 95% at 50% 2%, #20304f 0%, #101a30 42%, #070c17 100%); }}
      .light {{ position:absolute; width:1400px; height:1000px; left:100px; top:-620px;
        background:radial-gradient(circle, rgba(232,199,122,.26) 0%, rgba(232,199,122,0) 62%); }}
      .light2 {{ position:absolute; width:1000px; height:1000px; left:-380px; top:420px;
        background:radial-gradient(circle, rgba(96,140,214,.20) 0%, rgba(96,140,214,0) 70%); }}
      .light3 {{ position:absolute; width:900px; height:900px; right:-320px; bottom:-420px;
        background:radial-gradient(circle, rgba(232,199,122,.14) 0%, rgba(232,199,122,0) 70%); }}
      .rays,.fans {{ position:absolute; inset:0; }}
      .frame {{ position:absolute; inset:40px; border:1px solid rgba(232,199,122,.46); }}
      .frame2 {{ position:absolute; inset:50px; border:1px solid rgba(232,199,122,.14); }}
      .inner {{ position:absolute; inset:0; display:flex; flex-direction:column;
        align-items:center; justify-content:center; }}
      .mono-ring {{ width:96px; height:96px; border:1px solid rgba(232,199,122,.55);
        box-shadow:0 0 0 6px rgba(232,199,122,.07), inset 0 0 30px rgba(232,199,122,.10); }}
      .mono-ring span {{ font-family:'playfair'; font-size:34px; font-weight:700;
        letter-spacing:.06em; }}
      .name {{ font-family:'playfair'; font-weight:700; font-size:{size}px; line-height:1.04;
        margin-top:34px; text-align:center; padding:0 120px;
        filter:drop-shadow(0 4px 34px rgba(0,0,0,.60)); }}
      .rule {{ display:flex; align-items:center; gap:14px; margin:30px 0 26px; }}
      .rule i {{ display:block; width:110px; height:1px;
        background:linear-gradient(90deg, transparent, rgba(232,199,122,.75)); }}
      .rule i:last-child {{ background:linear-gradient(90deg, rgba(232,199,122,.75), transparent); }}
      .rule b {{ display:block; width:7px; height:7px; background:#e8c77a; transform:rotate(45deg); }}
      .note {{ font-family:'inter'; font-weight:300; font-size:{nsize}px; color:#b6c0d2;
        text-align:center; padding:0 210px; line-height:1.5; margin-bottom:26px; }}
      .dept {{ font-family:'inter'; font-weight:400; font-size:21px; letter-spacing:.36em;
        text-transform:uppercase; color:#93a0b8; padding-left:.36em; }}
    </style>"""


def _ivory_press(name: str, first: str, last: str, dept: str, year: int,
                 note: str = "") -> str:
    """Letterpress: cotton paper, engraved ink, deckled rules, medallion monogram."""
    size = _fit(name, 116)
    nsize = _note_size(note, 31)
    mono = _initials(first, last)
    return f"""
    <div class="card">
      <div class="wash"></div>
      <div class="deckle top"></div><div class="deckle bottom"></div>
      <div class="guilloche"></div>
      <div class="grain grain-dark"></div>
      <div class="inner">
        <div class="kicker">Happy Birthday</div>
        <div class="name">{_esc(name)}</div>
        <div class="medallion">
          <span class="line"></span>
          <span class="seal"><b>{mono}</b></span>
          <span class="line"></span>
        </div>
        {_note_html(note)}
        <div class="dept">{_esc(dept)}</div>
      </div>
      <div class="corner tl"></div><div class="corner tr"></div>
      <div class="corner bl"></div><div class="corner br"></div>
    </div>
    <style>
      .card {{ position:relative; width:{CARD_W}px; height:{CARD_H}px; overflow:hidden;
        background:
          radial-gradient(130% 120% at 50% 32%, #fffdf8 0%, #f8f2e7 52%, #ece2d1 100%); }}
      .wash {{ position:absolute; inset:0;
        background:radial-gradient(80% 60% at 50% 108%, rgba(176,141,63,.16) 0%, rgba(176,141,63,0) 70%); }}
      .deckle {{ position:absolute; left:70px; right:70px; height:7px; }}
      .deckle.top {{ top:66px; }}
      .deckle.bottom {{ bottom:66px; }}
      .deckle::before {{ content:''; position:absolute; inset:0 0 auto 0; height:2px; background:#22201c; }}
      .deckle::after {{ content:''; position:absolute; inset:5px 0 auto 0; height:1px;
        background:rgba(34,32,28,.38); }}
      .guilloche {{ position:absolute; inset:0; opacity:.5;
        background-image:repeating-linear-gradient(90deg, rgba(34,32,28,.055) 0 1px, transparent 1px 9px); }}
      .inner {{ position:absolute; inset:0; display:flex; flex-direction:column;
        align-items:center; justify-content:center; }}
      .kicker {{ font-family:'inter'; font-weight:600; font-size:23px; letter-spacing:.44em;
        text-transform:uppercase; color:#9a875f; padding-left:.44em; }}
      .name {{ font-family:'fraunces'; font-weight:600; font-size:{size}px; color:#1d1b18;
        text-align:center; padding:0 130px; line-height:1.06; letter-spacing:-.018em;
        margin-top:22px;
        text-shadow:0 1px 0 rgba(255,255,255,.9), 0 -1px 0 rgba(34,32,28,.16); }}
      .medallion {{ display:flex; align-items:center; gap:18px; margin:36px 0 26px; }}
      .medallion .line {{ display:block; width:96px; height:1px; background:rgba(34,32,28,.30); }}
      .seal {{ display:flex; align-items:center; justify-content:center; width:52px; height:52px;
        border-radius:50%; border:1px solid rgba(176,141,63,.75);
        box-shadow:inset 0 1px 0 rgba(255,255,255,.9), 0 2px 6px rgba(34,32,28,.10); }}
      .seal b {{ font-family:'fraunces'; font-weight:600; font-size:19px; color:#8d6f2c;
        letter-spacing:.04em; }}
      .note {{ font-family:'fraunces'; font-weight:400; font-size:{nsize}px; color:#4a4438;
        text-align:center; padding:0 230px; line-height:1.5; margin-bottom:24px;
        font-style:italic; }}
      .dept {{ font-family:'inter'; font-weight:500; font-size:20px; letter-spacing:.32em;
        text-transform:uppercase; color:#786d5b; padding-left:.32em; }}
      .corner {{ position:absolute; width:26px; height:26px; border:0 solid rgba(34,32,28,.35); }}
      .corner.tl {{ top:38px; left:38px; border-top-width:1px; border-left-width:1px; }}
      .corner.tr {{ top:38px; right:38px; border-top-width:1px; border-right-width:1px; }}
      .corner.bl {{ bottom:38px; left:38px; border-bottom-width:1px; border-left-width:1px; }}
      .corner.br {{ bottom:38px; right:38px; border-bottom-width:1px; border-right-width:1px; }}
    </style>"""


def _clinical_modern(name: str, first: str, last: str, dept: str, year: int,
                     note: str = "") -> str:
    """Institutional-modern, enriched: colour field, watermark monogram, foil sheen.

    Shipped nearly empty at first (white + one rule) and read as a template — a
    reviewer called it "a corporate presentation slide". Now it layers a depth
    colour field, an inset hairline frame system, an oversized watermark monogram,
    a gloss sweep and paper grain, while staying deliberately clean.
    """
    size = _fit(name, 118, per_char=5.6)
    nsize = _note_size(note, 31)
    mono = _initials(first, last)
    return f"""
    <div class="card">
      <div class="field"></div>
      <div class="orb o1"></div><div class="orb o2"></div><div class="orb o3"></div>
      <div class="watermark">{mono}</div>
      <div class="gridfine"></div>
      <div class="sheen"></div>
      <div class="frame"></div><div class="frame2"></div>
      <div class="grain grain-dark"></div>
      <div class="inner">
        <div class="topline">
          <span class="mark"></span>
          <span class="kicker">Happy Birthday</span>
          <span class="ref">{year}</span>
        </div>
        <div class="name">{_esc(name)}</div>
        <div class="rule"></div>
        {_note_html(note)}
      </div>
      <div class="foot">
        <span class="dept">{_esc(dept)}</span>
        <span class="seal"><b>{mono}</b></span>
      </div>
    </div>
    <style>
      .card {{ position:relative; width:{CARD_W}px; height:{CARD_H}px; overflow:hidden;
        background:#fdfdfe; }}
      .field {{ position:absolute; inset:0;
        background:
          linear-gradient(180deg, rgba(11,79,138,.06) 0%, rgba(11,79,138,0) 44%),
          linear-gradient(115deg, rgba(10,15,26,.04) 0%, rgba(10,15,26,0) 58%); }}
      .orb {{ position:absolute; border-radius:50%; filter:blur(72px); }}
      .o1 {{ width:860px; height:860px; right:-280px; top:-340px; background:rgba(11,79,138,.17); }}
      .o2 {{ width:680px; height:680px; left:-260px; bottom:-320px; background:rgba(0,124,138,.13); }}
      .o3 {{ width:540px; height:540px; right:100px; bottom:-280px; background:rgba(196,132,58,.13); }}
      .watermark {{ position:absolute; right:-124px; top:50%; transform:translateY(-50%);
        font-family:'inter'; font-weight:800; font-size:620px; letter-spacing:-.06em;
        line-height:1; color:rgba(11,79,138,.038); }}
      /* Measured column rules — architectural texture for the empty right half.
         Faded out on the left so it never competes with the name. */
      .gridfine {{ position:absolute; inset:0;
        background-image:linear-gradient(90deg, rgba(10,15,26,.05) 1px, transparent 1px);
        background-size:80px 100%;
        -webkit-mask-image:linear-gradient(90deg, transparent 46%, #000 100%);
        mask-image:linear-gradient(90deg, transparent 46%, #000 100%); }}
      .sheen {{ position:absolute; inset:0;
        background:linear-gradient(112deg, rgba(255,255,255,0) 34%, rgba(255,255,255,.55) 47%,
          rgba(255,255,255,0) 60%); }}
      .frame {{ position:absolute; inset:34px; border:1px solid rgba(10,15,26,.10); }}
      .frame2 {{ position:absolute; inset:42px; border:1px solid rgba(10,15,26,.05); }}
      .inner {{ position:absolute; left:136px; right:150px; top:238px; }}
      .topline {{ display:flex; align-items:center; gap:14px; }}
      .mark {{ display:block; width:56px; height:5px;
        background:linear-gradient(90deg, #0b4f8a, #2b7fc4); }}
      .kicker {{ font-family:'inter'; font-weight:700; font-size:21px; letter-spacing:.34em;
        text-transform:uppercase; color:#0b4f8a; }}
      .ref {{ margin-left:auto; font-family:'inter'; font-weight:500; font-size:16px;
        letter-spacing:.2em; color:#aab4c0; }}
      .name {{ font-family:'inter'; font-weight:800; font-size:{size}px; color:#070c14;
        letter-spacing:-.042em; line-height:1.0; margin-top:26px; }}
      .rule {{ width:620px; height:1px; margin:40px 0 24px;
        background:linear-gradient(90deg, rgba(10,15,26,.28), rgba(10,15,26,.02)); }}
      .note {{ font-family:'inter'; font-weight:400; font-size:{nsize}px; color:#55606d;
        letter-spacing:-.012em; line-height:1.5; max-width:1060px; }}
      .foot {{ position:absolute; left:136px; right:150px; bottom:96px;
        display:flex; align-items:center; }}
      .dept {{ font-family:'inter'; font-weight:600; font-size:18px; letter-spacing:.26em;
        text-transform:uppercase; color:#8f9baa; }}
      .seal {{ margin-left:auto; width:58px; height:58px; border-radius:50%;
        border:1px solid rgba(11,79,138,.32); background:rgba(255,255,255,.70);
        display:flex; align-items:center; justify-content:center;
        box-shadow:0 4px 16px rgba(11,79,138,.10), inset 0 1px 0 rgba(255,255,255,.9); }}
      .seal b {{ font-family:'inter'; font-weight:700; font-size:18px; letter-spacing:.06em;
        color:#0b4f8a; }}
    </style>"""


def _emerald_brass(name: str, first: str, last: str, dept: str, year: int,
                   note: str = "") -> str:
    """Quiet luxury: emerald ground, brass deco arch, foil name, monogram."""
    size = _fit(name, 116)
    nsize = _note_size(note, 32)
    mono = _initials(first, last)
    return f"""
    <div class="card">
      <div class="light"></div><div class="light2"></div>
      <svg class="arch" viewBox="0 0 1600 900">
        <g stroke="#c9a227" fill="none" opacity=".55">
          <path d="M300 742 V430 a500 500 0 0 1 1000 0 V742" stroke-width="1.2"/>
          <path d="M322 742 V432 a478 478 0 0 1 956 0 V742" stroke-width=".8" opacity=".6"/>
        </g>
        <g fill="#c9a227" opacity=".5">
          <circle cx="300" cy="742" r="3.5"/><circle cx="1300" cy="742" r="3.5"/>
          <circle cx="800" cy="182" r="3.5"/>
        </g>
      </svg>
      <div class="grain"></div>
      <div class="inner">
        <div class="kicker">Happy Birthday</div>
        <div class="orn">
          <i></i><b></b><i></i>
        </div>
        <div class="name">{_esc(name)}</div>
        {_note_html(note)}
        <div class="dept">{_esc(dept)}</div>
      </div>
      <div class="seal"><span class="foil">{mono}</span></div>
    </div>
    <style>
      .card {{ position:relative; width:{CARD_W}px; height:{CARD_H}px; overflow:hidden;
        background:
          radial-gradient(115% 105% at 50% -6%, #10493c 0%, #08281f 46%, #03130d 100%); }}
      .light {{ position:absolute; width:1300px; height:950px; left:150px; top:-420px;
        background:radial-gradient(circle, rgba(201,162,39,.24) 0%, rgba(201,162,39,0) 66%); }}
      .light2 {{ position:absolute; width:900px; height:900px; left:-300px; bottom:-460px;
        background:radial-gradient(circle, rgba(46,140,116,.22) 0%, rgba(46,140,116,0) 70%); }}
      .arch,.grain {{ position:absolute; inset:0; }}
      .inner {{ position:absolute; inset:0; display:flex; flex-direction:column;
        align-items:center; justify-content:center; padding-bottom:78px; }}
      .kicker {{ font-family:'inter'; font-weight:500; font-size:24px; letter-spacing:.42em;
        text-transform:uppercase; color:#c9a227; padding-left:.42em; }}
      .orn {{ display:flex; align-items:center; gap:14px; margin:24px 0 30px; }}
      .orn i {{ display:block; width:104px; height:1px;
        background:linear-gradient(90deg, transparent, rgba(201,162,39,.7)); }}
      .orn i:last-child {{ background:linear-gradient(90deg, rgba(201,162,39,.7), transparent); }}
      .orn b {{ display:block; width:8px; height:8px; background:#c9a227; transform:rotate(45deg); }}
      .name {{ font-family:'cormorant'; font-weight:600; font-size:{size}px; color:#f7f4ea;
        text-align:center; padding:0 150px; line-height:1.03; letter-spacing:.005em;
        text-shadow:0 4px 30px rgba(0,0,0,.45); }}
      .dept {{ font-family:'inter'; font-weight:400; font-size:20px; letter-spacing:.32em;
        text-transform:uppercase; color:#82a094; margin-top:40px; padding-left:.32em; }}
      .note {{ font-family:'cormorant'; font-weight:500; font-size:{nsize}px; color:#c1d4c8;
        text-align:center; padding:0 200px; line-height:1.5; margin-top:32px;
        font-style:italic; }}
      .seal {{ position:absolute; bottom:44px; left:50%; transform:translateX(-50%);
        width:58px; height:58px; border-radius:50%; border:1px solid rgba(201,162,39,.45);
        display:flex; align-items:center; justify-content:center; }}
      .seal span {{ font-family:'cormorant'; font-weight:600; font-size:21px; letter-spacing:.05em; }}
    </style>"""


def _sunrise(name: str, first: str, last: str, dept: str, year: int,
             note: str = "") -> str:
    """Warm optimism: sunburst rays, layered light, editorial serif, monogram sun."""
    size = _fit(name, 114)
    nsize = _note_size(note, 31)
    mono = _initials(first, last)
    rays = "".join(
        f'<line x1="800" y1="150" x2="{x}" y2="980" stroke="#c05a34" stroke-width="1" '
        f'opacity="{0.028 + (abs(800-x)/800)*0.030:.3f}"/>'
        for x in range(-420, 2400, 62))
    return f"""
    <div class="card">
      <div class="sky"></div>
      <svg class="rays" viewBox="0 0 1600 900">{rays}</svg>
      <div class="sun"></div><div class="warm"></div>
      <div class="grain grain-dark"></div>
      <div class="inner">
        <div class="pill">Happy Birthday</div>
        <div class="name">{_esc(name)}</div>
        {_note_html(note)}
      </div>
      <div class="foot">
        <span class="mono"><b>{mono}</b></span>
        <span class="dept">{_esc(dept)}</span>
      </div>
    </div>
    <style>
      .card {{ position:relative; width:{CARD_W}px; height:{CARD_H}px; overflow:hidden;
        background:linear-gradient(158deg, #fffcf7 0%, #fdf1e2 42%, #f8e0c9 72%, #f0cfae 100%); }}
      .rays {{ position:absolute; inset:0; }}
      .sun {{ position:absolute; width:1200px; height:1200px; left:200px; top:-660px;
        background:radial-gradient(circle, rgba(255,255,255,.95) 0%, rgba(255,252,240,.55) 34%,
          rgba(255,255,255,0) 68%); }}
      .warm {{ position:absolute; width:1000px; height:1000px; right:-320px; bottom:-500px;
        background:radial-gradient(circle, rgba(176,84,52,.18) 0%, rgba(176,84,52,0) 70%); }}
      .sky {{ position:absolute; inset:0;
        background:linear-gradient(180deg, rgba(255,255,255,.55) 0%, rgba(255,255,255,0) 46%); }}
      .inner {{ position:absolute; inset:0; display:flex; flex-direction:column;
        align-items:center; justify-content:center; }}
      .pill {{ font-family:'outfit'; font-weight:600; font-size:20px; letter-spacing:.26em;
        text-transform:uppercase; color:#8a4f36; background:rgba(255,255,255,.58);
        border:1px solid rgba(138,79,54,.22); padding:11px 30px 9px; border-radius:999px;
        box-shadow:0 6px 20px rgba(176,84,52,.10); }}
      .name {{ font-family:'dmserif'; font-weight:400; font-size:{size}px; color:#33201a;
        text-align:center; padding:0 120px; line-height:1.03; margin-top:34px;
        text-shadow:0 2px 24px rgba(255,255,255,.7); }}
      .note {{ font-family:'outfit'; font-weight:400; font-size:{nsize}px; color:#8a5c48;
        margin-top:30px; letter-spacing:.005em; text-align:center; padding:0 200px;
        line-height:1.5; }}
      .foot {{ position:absolute; bottom:74px; left:118px; right:118px;
        display:flex; align-items:center; gap:16px; }}
      .mono {{ width:46px; height:46px; border-radius:50%; border:1px solid rgba(138,79,54,.30);
        background:rgba(255,255,255,.45); display:flex; align-items:center; justify-content:center; }}
      .mono b {{ font-family:'dmserif'; font-weight:400; font-size:17px; color:#8a4f36;
        letter-spacing:.05em; }}
      .dept {{ font-family:'outfit'; font-weight:600; font-size:18px; letter-spacing:.32em;
        text-transform:uppercase; color:#9a6b55; }}
    </style>"""


def _confetti(name: str, first: str, last: str, dept: str, year: int,
              note: str = "") -> str:
    """Celebration with depth: blurred foreground confetti, layered fields, frame.

    The first version was sparse — "pleasant but ungrounded". The fix is depth of
    field: large out-of-focus confetti at the edges reads as shot-through-a-lens
    and grounds the composition, so there is something to discover on a second look.
    """
    size = _fit(name, 110)
    nsize = _note_size(note, 30)
    mono = _initials(first, last)
    blobs = [
        (-160, -180, 660, "#e8735a", 90, .30), (1160, -240, 740, "#d9a441", 100, .32),
        (-220, 540, 720, "#2f7f7a", 110, .20), (1220, 500, 680, "#e8735a", 100, .22),
        (540, 690, 560, "#d9a441", 110, .20), (280, -140, 440, "#2f7f7a", 90, .16),
    ]
    blob_html = "\n".join(
        f'<div class="blob" style="left:{l}px;top:{t}px;width:{s}px;height:{s}px;'
        f'background:radial-gradient(circle, {c} 0%, rgba(255,255,255,0) 70%);'
        f'filter:blur({b}px);opacity:{o};"></div>'
        for l, t, s, c, b, o in blobs)

    # Depth of field: out-of-focus pieces IN FRONT of the card. Kept smaller and
    # less blurred than a pure bokeh blob — at 200px+/26px blur these read as
    # smudges rather than foreground confetti.
    foreground = [
        (-46, 700, 118, "#e8735a", .52), (1452, 150, 132, "#d9a441", .48),
        (1224, 806, 106, "#2f7f7a", .44), (196, -34, 100, "#d9a441", .42),
        (1552, 588, 96, "#e8735a", .40), (688, 866, 104, "#e8735a", .34),
    ]
    fg_html = "\n".join(
        f'<div class="fg" style="left:{x}px;top:{y}px;width:{s}px;height:{s}px;'
        f'background:radial-gradient(circle, {c} 0%, {c}66 58%, {c}00 78%);'
        f'filter:blur(13px);opacity:{o};"></div>'
        for x, y, s, c, o in foreground)

    # Mixed crisp geometry — identical dots read as a pattern, mixed shapes read as confetti.
    shapes = []
    for x, y, kind, c, o, rot, r in [
        (252, 206, "dot", "#d9a441", .60, 0, 6), (1364, 296, "bar", "#e8735a", .55, 24, 0),
        (430, 700, "ring", "#2f7f7a", .48, 0, 9), (1176, 646, "dot", "#d9a441", .52, 0, 5),
        (762, 148, "bar", "#e8735a", .48, -18, 0), (988, 764, "dot", "#2f7f7a", .44, 0, 7),
        (1520, 560, "ring", "#d9a441", .42, 0, 11), (96, 420, "dot", "#e8735a", .44, 0, 4),
        (640, 838, "bar", "#2f7f7a", .40, 12, 0), (1420, 120, "dot", "#2f7f7a", .46, 0, 6),
        (330, 372, "bar", "#d9a441", .40, -32, 0), (1268, 452, "dot", "#e8735a", .38, 0, 4),
        (556, 322, "ring", "#e8735a", .34, 0, 7), (1080, 250, "bar", "#2f7f7a", .34, 40, 0),
    ]:
        if kind == "dot":
            shapes.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{c}" opacity="{o}"/>')
        elif kind == "ring":
            shapes.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="none" stroke="{c}" '
                          f'stroke-width="1.7" opacity="{o}"/>')
        else:
            shapes.append(f'<rect x="{x}" y="{y}" width="4" height="16" rx="2" fill="{c}" '
                          f'opacity="{o}" transform="rotate({rot} {x} {y})"/>')

    return f"""
    <div class="card">
      {blob_html}
      <svg class="flecks" viewBox="0 0 1600 900">{''.join(shapes)}</svg>
      {fg_html}
      <div class="ground"></div>
      <div class="frame"></div>
      <div class="grain grain-dark"></div>
      <div class="inner">
        <div class="kicker">Happy Birthday</div>
        <div class="rule"></div>
        <div class="name">{_esc(name)}</div>
        {_note_html(note)}
        <div class="dept">{_esc(dept)}</div>
      </div>
      <div class="seal"><b>{mono}</b></div>
    </div>
    <style>
      .card {{ position:relative; width:{CARD_W}px; height:{CARD_H}px; overflow:hidden;
        background:linear-gradient(152deg, #fffdf9 0%, #fbf5ea 55%, #f6ece0 100%); }}
      .blob {{ position:absolute; border-radius:50%; }}
      .fg {{ position:absolute; border-radius:50%; }}
      .flecks {{ position:absolute; inset:0; }}
      .ground {{ position:absolute; inset:0;
        background:radial-gradient(78% 62% at 50% 52%, rgba(255,255,255,.55) 0%,
          rgba(255,255,255,0) 62%); }}
      .frame {{ position:absolute; inset:40px; border:1px solid rgba(161,118,47,.28); }}
      .inner {{ position:absolute; inset:0; display:flex; flex-direction:column;
        align-items:center; justify-content:center; }}
      .kicker {{ font-family:'inter'; font-weight:600; font-size:23px; letter-spacing:.46em;
        text-transform:uppercase; color:#a1762f; padding-left:.46em; }}
      .rule {{ width:170px; height:1px; margin:28px 0 32px;
        background:linear-gradient(90deg, transparent, rgba(161,118,47,.62), transparent); }}
      .name {{ font-family:'fraunces'; font-weight:600; font-size:{size}px; color:#221d18;
        text-align:center; padding:0 130px; line-height:1.05; letter-spacing:-.02em;
        text-shadow:0 1px 34px rgba(255,255,255,.95), 0 1px 2px rgba(255,255,255,.9); }}
      .dept {{ font-family:'inter'; font-weight:500; font-size:20px; letter-spacing:.32em;
        text-transform:uppercase; color:#8a7f70; margin-top:50px; padding-left:.32em; }}
      .note {{ font-family:'fraunces'; font-weight:400; font-size:{nsize}px; color:#5d5346;
        text-align:center; padding:0 220px; line-height:1.5; margin-top:26px; }}
      .seal {{ position:absolute; top:56px; left:50%; transform:translateX(-50%);
        width:56px; height:56px; border-radius:50%; border:1px solid rgba(161,118,47,.45);
        background:rgba(255,255,255,.62); display:flex; align-items:center;
        justify-content:center; box-shadow:0 6px 20px rgba(161,118,47,.14),
        inset 0 1px 0 rgba(255,255,255,.95); }}
      .seal b {{ font-family:'inter'; font-weight:700; font-size:17px; letter-spacing:.06em;
        color:#a1762f; }}
    </style>"""


def _ai_artwork(name: str, first: str, last: str, dept: str, year: int,
                note: str = "", art: str = "") -> str:
    """AI-generated background with CSS typography over a scrim (opt-in)."""
    size = _fit(name, 110)
    nsize = _note_size(note, 31)
    mono = _initials(first, last)
    bg = f"url('{art}')" if art else "none"
    return f"""
    <div class="card">
      <div class="art" style="background-image:{bg};"></div>
      <div class="scrim"></div>
      <div class="frame"></div><div class="frame2"></div>
      <div class="grain"></div>
      <div class="inner">
        <div class="mono-ring"><span class="foil">{mono}</span></div>
        <div class="name foil">{_esc(name)}</div>
        <div class="rule"><i></i><b></b><i></i></div>
        {_note_html(note)}
        <div class="dept">{_esc(dept)}</div>
      </div>
    </div>
    <style>
      .card {{ position:relative; width:{CARD_W}px; height:{CARD_H}px; overflow:hidden;
        background:#070b16; }}
      .art {{ position:absolute; inset:0; background-size:cover; background-position:center;
        filter:brightness(.58) saturate(1.15) blur(2px); }}
      .scrim {{ position:absolute; inset:0;
        background:
          radial-gradient(120% 100% at 50% 50%, rgba(4,8,18,.62) 0%, rgba(4,8,18,.28) 38%,
            rgba(4,8,18,.90) 100%),
          linear-gradient(180deg, rgba(4,8,18,.55) 0%, rgba(4,8,18,.16) 45%, rgba(4,8,18,.74) 100%); }}
      .frame {{ position:absolute; inset:38px; border:1px solid rgba(232,199,122,.42); }}
      .frame2 {{ position:absolute; inset:48px; border:1px solid rgba(232,199,122,.13); }}
      .inner {{ position:absolute; inset:0; display:flex; flex-direction:column;
        align-items:center; justify-content:center; }}
      .mono-ring {{ width:92px; height:92px; border:1px solid rgba(232,199,122,.55);
        box-shadow:0 0 0 6px rgba(232,199,122,.07); }}
      .mono-ring span {{ font-family:'playfair'; font-size:32px; font-weight:700; }}
      .name {{ font-family:'playfair'; font-weight:700; font-size:{size}px; line-height:1.04;
        margin-top:32px; text-align:center; padding:0 120px;
        filter:drop-shadow(0 6px 40px rgba(0,0,0,.75)); }}
      .rule {{ display:flex; align-items:center; gap:14px; margin:30px 0 26px; }}
      .rule i {{ display:block; width:110px; height:1px;
        background:linear-gradient(90deg, transparent, rgba(232,199,122,.75)); }}
      .rule i:last-child {{ background:linear-gradient(90deg, rgba(232,199,122,.75), transparent); }}
      .rule b {{ display:block; width:7px; height:7px; background:#e8c77a; transform:rotate(45deg); }}
      .note {{ font-family:'inter'; font-weight:300; font-size:{nsize}px; color:#c3cad8;
        text-align:center; padding:0 210px; line-height:1.5; margin-bottom:24px; }}
      .dept {{ font-family:'inter'; font-weight:400; font-size:21px; letter-spacing:.36em;
        text-transform:uppercase; color:#9aa3b6; padding-left:.36em; }}
    </style>"""


DESIGNS: Dict[str, Dict[str, Any]] = {
    "midnight-gold": {
        "label": "Midnight Gold",
        "blurb": "Navy ground, deco fan corners, metallic foil name, monogram.",
        "render": _midnight_gold,
    },
    "ivory-press": {
        "label": "Ivory Letterpress",
        "blurb": "Cotton paper, engraved ink, deckled rules, wax-seal monogram.",
        "render": _ivory_press,
    },
    "clinical-modern": {
        "label": "Clinical Modern",
        "blurb": "Colour depth field, measured rules, monogram mark, tight Inter.",
        "render": _clinical_modern,
    },
    "emerald-brass": {
        "label": "Emerald & Brass",
        "blurb": "Emerald ground, brass deco arch, foil monogram, quiet luxury.",
        "render": _emerald_brass,
    },
    "sunrise": {
        "label": "Sunrise",
        "blurb": "Sunburst rays, layered warm light, editorial serif, monogram sun.",
        "render": _sunrise,
    },
    "confetti": {
        "label": "Confetti",
        "blurb": "Layered colour fields, mixed confetti geometry, restrained cream.",
        "render": _confetti,
    },
    # Opt-in (NOT in the default rotation — depends on the fal image API and a
    # monthly-cached background; a birthday must never degrade because of that).
    "ai-artwork": {
        "label": "AI Artwork",
        "blurb": "fal.ai generated background, foil type over a scrim. Needs FAL_KEY.",
        "render": _ai_artwork,
        "needs_art": True,
    },
}

# Designs offered by automatic rotation — all deterministic, no external calls.
ROTATION: List[str] = [d for d in DESIGNS if not DESIGNS[d].get("needs_art")]


def rotation(exclude: Optional[List[str]] = None) -> List[str]:
    """Designs eligible for rotation, minus any benched via `design_exclude`.

    Benching is a settings operation, not a code change — a design the user
    dislikes should be removable without touching this file. Never returns
    empty: if everything is excluded, fall back to the full set so birthdays
    keep rendering.
    """
    ex = {str(x).strip().lower() for x in (exclude or []) if str(x).strip()}
    out = [d for d in ROTATION if d not in ex]
    return out or list(ROTATION)


def design_names() -> List[str]:
    return list(DESIGNS.keys())


def pick_design(contact_id: str, year: int, override: Optional[str] = None,
                month: Optional[int] = None,
                exclude: Optional[List[str]] = None) -> str:
    """Stable per person per year — same card all year, varies across people.

    `month` (the person's birthday month) is mixed in so designs spread across
    the calendar year rather than clustering: with 15 people an id-only hash can
    leave one design unused for the whole year. Passing it is optional (callers
    that don't have a birthday still get a stable answer).
    """
    if override and override.strip().lower() not in ("auto", "rotate", ""):
        key = override.strip().lower()
        if key in DESIGNS:
            return key
        if key.isdigit() and 1 <= int(key) <= len(DESIGNS):
            return design_names()[int(key) - 1]
    rot = rotation(exclude)
    base = int(hashlib.md5(f"{contact_id or 'x'}{year}".encode()).hexdigest(), 16)
    if month:
        # XOR an independent hash of the month so designs decorrelate instead of
        # drifting together — measured against the real 15-person roster, this is
        # the only blend that used all 6 designs without clustering (max 4, min 1).
        base ^= int(hashlib.md5(f"mon{month}".encode()).hexdigest(), 16)
    return rot[base % len(rot)]


def build_document(design: str, person: Dict[str, Any], dept: str = "Montefiore Urology",
                   year: Optional[int] = None, art_path: Optional[Path] = None,
                   note: str = "") -> str:
    """Full standalone HTML document for one card."""
    import datetime as _dt
    year = year or _dt.date.today().year
    spec = DESIGNS.get(design) or DESIGNS[ROTATION[0]]
    first = (person.get("first_name") or "").strip()
    last = (person.get("last_name") or "").strip()
    full = f"{first} {last}".strip() or "Friend"
    if spec.get("needs_art"):
        art_uri = Path(art_path).as_uri() if art_path and Path(art_path).exists() else ""
        body = spec["render"](full, first, last, dept, year, note, art=art_uri)
    else:
        body = spec["render"](full, first, last, dept, year, note)
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
{_font_css()}
{COMMON_CSS}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html,body {{ width:{CARD_W}px; height:{CARD_H}px; overflow:hidden; background:#000; }}
.card {{ font-kerning:normal; -webkit-font-smoothing:antialiased; }}
</style></head>
<body>{body}</body></html>"""


async def _render_async(html: str, out_path: Path, html_path: Optional[Path] = None) -> Path:
    from playwright.async_api import async_playwright
    tmp_html = html_path or out_path.with_suffix(".html")
    tmp_html.write_text(html, encoding="utf-8")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--no-sandbox", "--font-render-hinting=none"])
        page = await browser.new_page(
            viewport={"width": CARD_W, "height": CARD_H}, device_scale_factor=SCALE)
        # Must load from a real file:// origin — with set_content() the page origin
        # is about:blank and the @font-face file:// sources silently fail.
        await page.goto(tmp_html.as_uri(), wait_until="load")
        await page.evaluate("document.fonts.ready")
        await page.wait_for_timeout(400)
        await page.screenshot(path=str(out_path), type="jpeg", quality=96)
        await browser.close()
    return out_path


def render_card(design: str, person: Dict[str, Any], out_path: Path,
                dept: str = "Montefiore Urology", year: Optional[int] = None,
                keep_html: bool = False, art_path: Optional[Path] = None,
                note: str = "") -> Path:
    """Render one card to a JPEG. Sync wrapper (CLI + cron friendly)."""
    html = build_document(design, person, dept=dept, year=year, art_path=art_path, note=note)
    html_path = out_path.with_suffix(".html") if keep_html else None
    asyncio.run(_render_async(html, out_path, html_path))
    if html_path is None:
        try:
            out_path.with_suffix(".html").unlink(missing_ok=True)
        except Exception:
            pass
    return out_path


if __name__ == "__main__":
    import argparse
    import json

    ap = argparse.ArgumentParser(description="Render sample birthday cards")
    ap.add_argument("--name", default="John Hordines")
    ap.add_argument("--design", default=None, help="design key, 1-7, or 'all'")
    ap.add_argument("--note", default="Wishing you a wonderful year ahead — from all of us in Urology.",
                    help="message line printed on the card ('' to omit)")
    ap.add_argument("--outdir", default="/tmp/card_samples")
    a = ap.parse_args()

    first, _, last = a.name.partition(" ")
    person = {"first_name": first, "last_name": last, "id": "sample"}
    outdir = Path(a.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    if a.design == "all" or a.design is None:
        for key in design_names():
            p = render_card(key, person, outdir / f"{key}.jpg", note=a.note)
            print(f"{key:18} -> {p} ({p.stat().st_size} bytes)  [{DESIGNS[key]['label']}]")
    else:
        key = pick_design("sample", 2026, a.design)
        p = render_card(key, person, outdir / f"{key}.jpg", note=a.note)
        print(json.dumps({"design": key, "path": str(p), "bytes": p.stat().st_size}))
