# Agentic OS — DESIGN.md

Design token spec for the AOS dashboard (2026-09 redesign). This is the contract:
pages and suites consume these tokens; nothing hardcodes colors outside them.

## Color

Tokens live in `dashboard/styles.css` under `[data-theme="dark"]` / `[data-theme="light"]`.

| Token | Dark | Light | Use |
|---|---|---|---|
| `--accent` | teal `#14b8a6` | teal | primary actions, active states |
| `--bg-primary/secondary/card` | near-blacks | whites | surfaces |
| `--border` / `--border-hover` | white α .06/.10 | black α .06/.10 | hairlines |
| `--hover-bg` | white α .03 | black α .03 | row/item hover |
| `--hover-bg-strong` | white α .05 | black α .05 | button hover, active chips |
| `--fill-muted` | white α .06 | black α .06 | bars, tracks, code chips, badges |
| `--border-soft` | white α .04 | black α .05 | subtle separators |
| `--scrollbar` / `--scrollbar-hover` | white α .08/.14 | black α .15/.25 | scrollbars |

**Banned:** purple (`#6c5ce7`, `#a29bfe`, `#667eea`, `#764ba2`, …) and pink
(`#fd79a8`, `#f093fb`, `#a855f7`) anywhere — chrome, pages, standalone HTML.
Badge/stat palettes run teal family (`#14b8a6` / `#0d9488` / `#2dd4bf`) plus
functional red/orange/green only for error/warning/success semantics.

## Typography

- Font: **Inter** (`--font`), mono for data (`--font-mono`).
- h1 20px/600 · stat value 24px/700 · body 13.5px · labels 11–12px muted.
- `font-feature-settings: "tnum"` on stat/table values (digits align).
- Table row rhythm: 32px — data pages must not exceed it.

## Glyphs

Approved decorative glyph set: `▸ ● ◆ ○ ✓ ✕ ↻ ⌕ ! △ ◐ → ▣ ↗` (plus `↑ ↓ ← ▤ ▦` for
view toggles). **No emoji in UI.** `☰` is allowed only as the mobile-menu icon.
Exception: `calendar.js` emoji are FUNCTIONAL (event keyword classification and
title-cleaning regexes) — never sweep them.

## Components

- **Cards:** thin `1px solid var(--border)`, no shadow, hover = border-only change.
- **Stat strip:** horizontal label-left/value-right pill rows, not 4-up card stacks.
- **Tabs/suites:** `.tabs` + `.tab` with hash-driven state (`#suite?tab=key`);
  tab content delegates to original modules or embeds standalone pages
  (`.suite-embed` iframe). See `agentic-os-dashboard/references/suite-merges.md`.
- **Empty states:** `.empty-state` with glyph icon + title + desc + single action.
- **No emoji buttons.** Icon slots use the glyph set or plain text.

## Layout

- Sidebar 250px (`--sidebar-width`), zones with collapsible trays; ≤768px it
  becomes an off-canvas drawer (`.sidebar.open` + `.sidebar-overlay.active`
  are the ONLY visibility switches — never inline styles on the toggles).
- Page content: `.page-header` (≤1 primary action) → stat strip → content;
  two-column ≥1280px, single column mobile.
- Suite embeds: `height: calc(100vh - 190px)`, min 480px.

## Deploy conventions

- Static edits deploy instantly (workspace = Docker volume). Bump `?v=` on
  `utils.js/api.js/app.js/styles.css` in index.html per rollout (`v=20260919` current).
- `utils.js` is root-owned: edit a copy, deploy via SSH as root, md5-compare.
- Re-run `redesign-2026-09/scripts/pr9-audit.js` after any nav/page change
  (parity + redirects + inventory).
