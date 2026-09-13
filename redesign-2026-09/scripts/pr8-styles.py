#!/usr/bin/env python3
"""PR8 styles.css — light-mode tokens + rgba sweep + mobile nav fixes."""
import re
import pathlib
import sys

p = pathlib.Path('/workspace/agentic-os/dashboard/styles.css')
t = p.read_text()
fails = []

def rep(old, new, n=1, label=None):
    global t
    c = t.count(old)
    if c != n:
        fails.append(f"{label or old[:50]}: expected {n}, found {c}")
        return
    t = t.replace(old, new)

# ── 1. tokens: dark block ──
rep("  --border: rgba(255, 255, 255, 0.06);\n  --border-hover: rgba(255, 255, 255, 0.10);\n",
"""  --border: rgba(255, 255, 255, 0.06);
  --border-hover: rgba(255, 255, 255, 0.10);
  /* PR8 — hover/fill/soft tokens (light-mode hardened) */
  --hover-bg: rgba(255, 255, 255, 0.03);
  --hover-bg-strong: rgba(255, 255, 255, 0.05);
  --fill-muted: rgba(255, 255, 255, 0.06);
  --border-soft: rgba(255, 255, 255, 0.04);
  --scrollbar: rgba(255, 255, 255, 0.08);
  --scrollbar-hover: rgba(255, 255, 255, 0.14);
""", 1, 'dark tokens')

# ── 2. tokens: light block ──
rep("  --border: rgba(0, 0, 0, 0.06);\n  --border-hover: rgba(0, 0, 0, 0.10);\n",
"""  --border: rgba(0, 0, 0, 0.06);
  --border-hover: rgba(0, 0, 0, 0.10);
  /* PR8 — hover/fill/soft tokens */
  --hover-bg: rgba(0, 0, 0, 0.03);
  --hover-bg-strong: rgba(0, 0, 0, 0.05);
  --fill-muted: rgba(0, 0, 0, 0.06);
  --border-soft: rgba(0, 0, 0, 0.05);
  --scrollbar: rgba(0, 0, 0, 0.15);
  --scrollbar-hover: rgba(0, 0, 0, 0.25);
""", 1, 'light tokens')

# ── 3. scrollbar ──
rep("::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.08);",
    "::-webkit-scrollbar-thumb { background: var(--scrollbar);", 1, 'scrollbar')
rep("::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.14);",
    "::-webkit-scrollbar-thumb:hover { background: var(--scrollbar-hover);", 1, 'scrollbar-hover')

# ── 4. targeted replacements (specific before generic) ──
rep("  background: rgba(255, 255, 255, 0.05);", "  background: var(--hover-bg-strong);", 1, 'btn-ghost')
rep("var(--border-color, rgba(255,255,255,0.12))", "var(--border-color, var(--border))", 1, 'border-color fallback 12')
rep("border-color: rgba(255,255,255,0.06);", "border-color: var(--border);", 1, 'border-color 06')
rep("border-color: rgba(255,255,255,0.15);", "border-color: var(--border-hover);", 1, 'border-color 15')
rep("var(--border-color, rgba(255,255,255,0.08))", "var(--border-color, var(--border))", 2, 'border-color fallback 08')
rep("var(--event-bg, rgba(255,255,255,0.02))", "var(--event-bg, var(--hover-bg))", 1, 'event-bg')

# ── 5. generic remaining (counts asserted) ──
for alpha, token, expect in [('0.02','var(--hover-bg)',1), ('0.03','var(--hover-bg)',4),
                             ('0.04','var(--hover-bg-strong)',3), ('0.05','var(--hover-bg-strong)',1),
                             ('0.06','var(--fill-muted)',3), ('0.08','var(--fill-muted)',1)]:
    pat = f"rgba(255,255,255,{alpha})"
    c = t.count(pat)
    if c != expect:
        fails.append(f"generic {alpha}: expected {expect}, found {c}")
    t = t.replace(pat, token)

# ── 6. mobile nav fixes ──
rep("  .sidebar-overlay { display: block; }",
    "  .sidebar { max-width: 85vw; }\n\n  .sidebar-overlay.active { display: block; }\n\n  .tabs { max-width: 100%; overflow-x: auto; -webkit-overflow-scrolling: touch; }",
    1, 'mobile overlay/tabs')

p.write_text(t)

# verify
left_sp = len(re.findall(r'rgba\(255,\s*255,\s*255', t))
left_ns = len(re.findall(r'rgba\(255,255,255', t))
print(f"rgba(255, 255, 255 remaining: {left_sp} (expect 2 = dark tokens), no-space: {left_ns} (expect 0)")
print(f"new tokens present: --hover-bg:{'--hover-bg:' in t} --fill-muted:{'--fill-muted:' in t} --border-soft:{'--border-soft:' in t} --scrollbar:{'--scrollbar:' in t}")
print(f"mobile: overlay.active:{'.sidebar-overlay.active' in t} tabs-scroll:{'.tabs { max-width: 100%' in t} max-width:{'max-width: 85vw' in t}")

if left_sp != 2 or left_ns != 0:
    fails.append('rgba leftovers')
if fails:
    print('\nFAILURES:')
    for f in fails:
        print('  -', f)
    sys.exit(1)
print('\nPR8 STYLES PASS')
