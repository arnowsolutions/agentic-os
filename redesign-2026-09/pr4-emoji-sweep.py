#!/usr/bin/env python3
"""PR4 emoji sweep — dashboard/pages worst-10 files (2026-09-12).

Replaces decorative emoji with the approved glyph set (▸ ● ◆ ○ ✓ ✕ ↻ ⌕) or
plain text. Calendars are EXCLUDED on purpose: their emoji occurrences are
functional regexes/keywords (title cleanup, event search).

Backups: redesign-2026-09/backup-pre-pr4/
"""
import re
import pathlib
import subprocess

BASE = pathlib.Path('/workspace/agentic-os/dashboard/pages')
FILES = ['manager.js', 'manager-command-center.js', 'social-media-hub.js',
         'voice-commands.js', 'tools.js', 'contacts.js', 'smart-router.js',
         'omniroute.js', 'ai-builder.js', 'quick-actions.js']

# Specific sequences handled BEFORE the global map.
PRE = {
    'smart-router.js': [
        ("{ opencode: '🔧', hermes: '⚡', gemini: '🧠' }",
         "{ opencode: '◆', hermes: '●', gemini: '○' }"),
        ("|| '🤖'", "|| '▸'"),
    ],
    'omniroute.js': [
        ("const avatar = isUser ? '👤' : '🤖';", "const avatar = isUser ? '▸' : '◆';"),
        ("12px\">🚀</div>", "12px\">◆</div>"),
        ("linear-gradient(135deg, #667eea 0%, #764ba2 100%)", "var(--accent-dim)"),
        ("background:#667eea;background:linear-gradient(135deg,#667eea,#764ba2)", "background:var(--accent-dim)"),
    ],
    'social-media-hub.js': [
        ('<span style="filter:none">📱</span> ', ''),
    ],
}

# Global glyph mappings (applied everywhere in the 10 files).
GLOBAL = [
    ('✅', '✓'), ('✔️', '✓'), ('✔', '✓'),
    ('❌', '✕'), ('✖', '✕'), ('✗', '✕'),
    ('➕', '+'),
    ('⚠️', '!'), ('⚠', '!'),
    ('🔄', '↻'), ('🔍', '⌕'),
    ('✏️', '✎'), ('✏', '✎'),
    ('↩️', '↩'), ('⬤', '●'),
    ('🟢', '●'), ('🟡', '●'), ('🔵', '●'), ('🔴', '●'),
    ('🗑', '✕'), ('🚫', '✕'),
    ('🖼️', '▣'), ('🖼', '▣'),
    ('👆', '▸'), ('🌙', '◐'),
    ('❓', '?'), ('➤', '→'),
]

# Decorative emoji removed outright (with one trailing space).
REMOVE = ['📋', '📅', '📊', '📈', '📉', '📝', '💰', '📧', '📱', '📦', '📄',
          '📓', '📚', '📥', '📤', '📨', '📭', '📂', '📁', '🎨', '📸', '🗓️',
          '🗓', '🔑', '💾', '📜', '🔧', '💬', '🤖', '💻', '🌐', '🔌', '⚙️',
          '⚙', '⏰', '⏱', '✉', '☰', '🏥', '👶', '🎓', '📌', '🩺', '👥',
          '👤', '🎂', '🚀', '⚡', '🧠', '⏳', '🔗', '✍️', '✍', '👁', '🔓',
          '📡', '☕', '🤒', '👨', '👩', '🔬', '🕐', '⚕', '🎤', '🎮', '📖',
          '🆕', '🎛️', '🎛', '🏆', '🆓', '🛡️', '🛡', '🏷️', '🏷', '👍', '♻️',
          '♻', '🎯', '💼', '✨', '📐', '📇', '🎬', '🗂', '🧭', '🔷', '🖥️',
          '🖥', '📎', '⭐', '🎁', '📍', '🔺', '🔻', '🔔', '🚨', '📢', '🕹️',
          '🗨️', '↗️', '◉', '◆', '💡']

KEEP = set('✓✕✎↩↻⌕●◐▸▣')  # glyphs we intentionally produce

LEFT_RE = re.compile(r'[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0000FE0F\u2B00-\u2BFF]')


def main():
    total_left = 0
    for fn in FILES:
        p = BASE / fn
        t = p.read_text()
        orig = t
        for old, new in PRE.get(fn, []):
            t = t.replace(old, new)
        for old, new in GLOBAL:
            t = t.replace(old, new)
        for tok in REMOVE:
            t = re.sub(re.escape(tok) + r'\s?', '', t)
        if fn in ('social-media-hub.js', 'quick-actions.js'):
            t = re.sub(r"icon: '[^']*'", "icon: '▸'", t)
        if fn == 'quick-actions.js':
            t = re.sub(r"color: '#[0-9a-fA-F]{6}'", "color: 'var(--accent)'", t)
        left = sorted(set(c for c in LEFT_RE.findall(t) if c not in KEEP))
        total_left += len(left)
        p.write_text(t)
        r = subprocess.run(['node', '--check', str(p)], capture_output=True, text=True)
        status = 'OK ' if r.returncode == 0 else 'FAIL'
        changed = sum(1 for a, b in zip(orig.split('\n'), t.split('\n')) if a != b)
        print(f"{fn:34s} {status} lines~{changed:2d} leftover={len(left)} {''.join(left)[:40]}")
    print('TOTAL leftover:', total_left)
    return 1 if total_left else 0


if __name__ == '__main__':
    raise SystemExit(main())
