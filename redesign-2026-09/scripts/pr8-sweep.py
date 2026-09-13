#!/usr/bin/env python3
"""PR8 sweep — emoji + purple + rgba across pages HTML (2026-09-12).

1. Emoji → approved glyph set / removal (52 JS + 4 HTML files).
2. Purple/pink hex → teal palette (6 files + 2 HTML).
3. rgba(255,255,255,α) → theme tokens (13 JS files).
Excluded: calendar.js (functional emoji), cal-new.js + calendar2.js (pending
archive PR9), grand-rounds.js.bak (moved in PR9).

Assertions everywhere; leftover scan must end clean.
"""
import re
import pathlib
import subprocess
import sys
import colorsys

BASE = pathlib.Path('/workspace/agentic-os/dashboard')
PAGES = BASE / 'pages'

TARGETS = ['agent-health','audit','backups','calendar-invites','chat','chief-meetings',
    'claude-code','compliance','conference-email','cost','crm-audit','distribution',
    'drive-sync','email-groups','email-send-log','email-templates','eval-dashboard',
    'eval-portal','gme-detail','gme-tracker','goals','grand-rounds-attendance','grand-rounds',
    'health','images-to-pdf','journal','kanban','learning-analytics','mass-email','memory',
    'morning-briefing','notifications','pdf-archive','people','pin-manager','platforms',
    'plugins','prompts','reports','resident-letters','resident-roster','scheduler',
    'session-replay','settings','setup-wizard','standards','subi-exit-interviews','tasks',
    'telegram-logs','telegram','unified-dashboard','user']

HTML_TARGETS = ['prompt-image.html','prompt-video.html','omniroute-chat.html','login.html']

ICON_FILES = ['mass-email.js','resident-letters.js','gme-tracker.js']

GLOBAL = [
    ('\u26AB','●'),                              # ⚫
    ('🟢','●'),('🟡','●'),('🔵','●'),('🔴','●'),('⚪','○'),('⬜','○'),('⬤','●'),('◉','●'),
    ('✅','✓'),('✔','✓'),('❌','✕'),('✖','✕'),('✗','✕'),('🚫','✕'),('🗑','✕'),
    ('➕','+'),('⚠','!'),('🔄','↻'),('🔍','⌕'),('🖼','▣'),
    ('⬆','↑'),('⬇','↓'),('⬅','←'),('➡','→'),('➤','→'),('▶','▸'),('❓','?'),
    ('✏','✎'),('⬡','○'),('🔓','○'),
    ('🤖','◆'),('👤','▸'),('☰','▤'),
]

REMOVE = ['📋','📅','📊','📈','📉','📝','💰','📧','📱','📦','📄','📓','📚','📥','📤','📨',
    '📭','📂','📁','🎨','📸','🗓','🔑','💾','📜','🔧','💬','💻','🌐','🔌','⚙','⏰','⏱',
    '✉','🏥','👶','🎓','📌','🩺','👥','🎂','🚀','⚡','🧠','⏳','🔗','👁','📡','☕','🤒',
    '👨','👩','🔬','🕐','⚕','🎤','🎮','📖','🆕','🏆','🆓','🛡','🏷','👍','♻','🎯','💼',
    '✨','📐','📇','🎬','🗂','🧭','🔷','🖥','📎','⭐','🎁','📍','🔺','🔻','🔔','🚨','📢',
    '🕹','💡','🧪','🆔','😕','✈','🔤','🚗','🖱','🎥','📺','🔊','👑','🧒','🏦','💳','💸',
    '📞','🏖','🎙','🎚','💭','🖇','🗄','🖨','⌨','🪟','🧾','📑','🗃','🈳','🈚','❗','⁉','‼',
    '🈁','🔊','🔉','🔈','🎵','🎶','🎼','📻','⏯','⏸','⏹','⏺','⏭','⏮','🔁','🔂','🔀',
    '🟠','🟣','🟤']

PRE = {
    'agent-health.js': [
        ("{ opencode: '🔧', hermes: '⚡', gemini: '🧠' }", "{ opencode: '◆', hermes: '●', gemini: '○' }"),
        ("|| '🤖'", "|| '▸'"),
    ],
    'people.js': [
        ('title="Table view">☰</button>', 'title="Table view">▤</button>'),
    ],
    'kanban.js': [
        ('>☰</button>', '>▤</button>'),
    ],
}

WL = set('✓✕↻⌕●◐▸▣◆○▤▦↗↑↓→←✎↩☰‹›')
EMOJI_RE = re.compile(r'[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0000FE0F\u2B00-\u2BFF]')
HEX_RE = re.compile(r'#([0-9a-fA-F]{6})')

fails = []

def sweep_text(t, name, is_js):
    t = t.replace('\uFE0F', '').replace('\u200D', '')
    for old, new in PRE.get(name, []):
        c = t.count(old)
        if c == 0:
            fails.append(f"{name}: PRE not found: {old[:60]!r}")
        t = t.replace(old, new)
    if name in ICON_FILES:
        t, k = re.subn(r"icon: '[^']*'", "icon: '▸'", t)
        if k == 0:
            fails.append(f"{name}: icon: rows expected ≥1, found 0")
    for old, new in GLOBAL:
        t = t.replace(old, new)
    for tok in REMOVE:
        t = re.sub(re.escape(tok) + r'\s?', '', t)
    return t

def leftovers(t):
    return sorted({c for c in EMOJI_RE.findall(t) if c not in WL})

def purple_hexes(t):
    bad = []
    for m in HEX_RE.finditer(t):
        r, g, b = (int(m.group(1)[i:i+2], 16) / 255 for i in (0, 2, 4))
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        deg = h * 360
        if s > 0.25 and 250 <= deg <= 330:   # purple/pink/magenta family
            bad.append(m.group(0))
    return sorted(set(bad))

print('═══ 1. EMOJI SWEEP ═══')
for name in TARGETS:
    p = PAGES / f"{name}.js"
    t = p.read_text()
    t = sweep_text(t, f"{name}.js", True)
    left = leftovers(t)
    p.write_text(t)
    r = subprocess.run(['node', '--check', str(p)], capture_output=True, text=True)
    status = 'OK' if r.returncode == 0 else 'FAIL'
    if r.returncode != 0:
        fails.append(f"{name}.js node --check: {r.stderr.strip()[:100]}")
    flag = '  LEFT:' + ''.join(left) if left else ''
    if left:
        fails.append(f"{name}.js leftover: {left}")
    if status != 'OK' or left:
        print(f"  {name+'.js':30s} {status}{flag}")

for name in HTML_TARGETS:
    p = BASE / name
    t = p.read_text()
    t = sweep_text(t, name, False)
    left = leftovers(t)
    p.write_text(t)
    if left:
        fails.append(f"{name} leftover: {left}")
    print(f"  {name:30s} html  {'LEFT:' + ''.join(left) if left else 'clean'}")

print('═══ 2. PURPLE/PINK HEX ═══')
PURPLE_FIX = {
    'pages/contacts.js': [("#6c5ce7", "#14b8a6")],
    'pages/gme-tracker.js': [("#6c5ce715", "#14b8a615"), ("#6c5ce730", "#14b8a630"), ("#6c5ce7", "#14b8a6")],
    'pages/morning-briefing.js': [
        ("rgba(162,155,254,0.15); color:#a29bfe", "rgba(20,184,166,0.15); color:#14b8a6"),
        ("rgba(108,92,231,0.2); color:#6c5ce7", "rgba(20,184,166,0.25); color:#0d9488")],
    'pages/resident-roster.js': [
        ("rgba(108,92,231,0.15); color: #6c5ce7", "rgba(20,184,166,0.15); color: #14b8a6"),
        ("rgba(162,155,254,0.15); color: #a29bfe", "rgba(20,184,166,0.10); color: #0d9488")],
    'pages/social-media-hub.js': [("#6c5ce7", "#14b8a6"), ("#a29bfe", "#2dd4bf"), ("#fd79a8", "#0d9488")],
    'login.html': [("#6c5ce7", "#14b8a6"), ("#a855f7", "#0d9488")],
    'omniroute-chat.html': [("#667eea", "#14b8a6"), ("#764ba2", "#0d9488")],
}
for rel, pairs in PURPLE_FIX.items():
    p = BASE / rel
    t = p.read_text()
    for old, new in pairs:
        c = t.count(old)
        if c == 0:
            fails.append(f"{rel}: purple '{old}' not found")
        t = t.replace(old, new)
    p.write_text(t)
    rem = purple_hexes(t)
    print(f"  {rel:32s} fixed  {'STILL:' + str(rem) if rem else ''}")
    if rem:
        fails.append(f"{rel} still purple: {rem}")

print('═══ 3. rgba(255,255,255) → tokens (pages) ═══')
RGBA_FILES = ['compliance.js','crm-audit.js','data-gaps.js','eval-dashboard.js','eval-portal.js',
              'file-browser.js','gme-detail.js','morning-briefing.js','resident-roster.js',
              'script-runner.js','staff-schedule.js','telegram-logs.js','user.js']
RULES = [
    (r'(border[a-z-]*:\s*1px solid )rgba\(255,\s*255,\s*255,\s*0\.0[34]\)', r'\1var(--border-soft)'),
    (r'var\(--border-light, rgba\(255,\s*255,\s*255,\s*0\.05\)\)', 'var(--border-light, var(--border-soft))'),
    (r'rgba\(255,\s*255,\s*255,\s*0\.02\)', 'var(--hover-bg)'),
    (r'rgba\(255,\s*255,\s*255,\s*0\.03\)', 'var(--hover-bg)'),
    (r'rgba\(255,\s*255,\s*255,\s*0\.04\)', 'var(--hover-bg-strong)'),
    (r'rgba\(255,\s*255,\s*255,\s*0\.05\)', 'var(--hover-bg-strong)'),
    (r'rgba\(255,\s*255,\s*255,\s*0\.06\)', 'var(--fill-muted)'),
    (r'rgba\(255,\s*255,\s*255,\s*0\.08\)', 'var(--fill-muted)'),
]
total = 0
for fn in RGBA_FILES:
    p = PAGES / fn
    t = p.read_text()
    n = 0
    for pat, rep in RULES:
        t, k = re.subn(pat, rep, t)
        n += k
    total += n
    left = len(re.findall(r'rgba\(255,\s*255,\s*255', t))
    p.write_text(t)
    r = subprocess.run(['node', '--check', str(p)], capture_output=True, text=True)
    if r.returncode != 0:
        fails.append(f"{fn} node check after rgba: {r.stderr[:80]}")
    print(f"  {fn:26s} {n} replaced, {left} left")
    if left:
        fails.append(f"{fn}: {left} rgba remains")
print(f"  total rgba replaced: {total}")

print()
if fails:
    print(f"FAILURES ({len(fails)}):")
    for f in fails[:40]:
        print('  -', f)
    sys.exit(1)
print('PR8 SWEEP PASS — emoji clean, purple clean, rgba → tokens')
