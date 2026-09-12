#!/usr/bin/env python3
"""Fix GmeFundStatusTab DEFAULT_YEAR — use the CURRENT academic year dynamically.

Bug: const DEFAULT_YEAR = '2025-26' hardcoded -> the GME Fund Status tab opens on
last year's data while today (Sep 2026) the current AY is 2026-27, so recent
submissions appear "missing" until the year is switched manually.

Run ON THE VPS:  python3 /tmp/fix-platform-gme-year.py
Idempotent. Also prints where the year TAB list comes from (check that 2026-27
is selectable; extend the list if it is hardcoded).
"""
import pathlib
import shutil
import re

P = pathlib.Path('/var/www/unified/src/pages/admin/GmeFundStatusTab.tsx')
src = P.read_text()

OLD = "const DEFAULT_YEAR = '2025-26';"
NEW = ("// Dynamic default: current academic year (Jul 1 - Jun 30)\n"
       "const DEFAULT_YEAR = (() => {\n"
       "  const d = new Date();\n"
       "  const y = d.getMonth() >= 6 ? d.getFullYear() : d.getFullYear() - 1;\n"
       "  return `${y}-${String(y + 1).slice(2)}`;\n"
       "})();")

if 'const DEFAULT_YEAR = (()' in src:
    print('already patched — nothing to do')
    raise SystemExit(0)

assert OLD in src, f"'{OLD}' not found — inspect manually"

bak = P.with_name(P.name + '.bak-20260912')
shutil.copy2(P, bak)
P.write_text(src.replace(OLD, NEW, 1))
print('patched OK; backup at', bak)

# Print the YearTabs component source (if any) so the caller can verify the
# selectable year list includes the current year.
m = re.search(r"import\s+\{([^}]*YearTabs[^}]*)\}\s+from\s+'([^']+)'", src)
if m:
    imp = m.group(1).strip()
    print(f'YearTabs import: {imp} from {m.group(2)} (check its year list includes 2026-27)')
else:
    print('YearTabs import not found via regex — check the tab list manually:')
    for i, line in enumerate(src.splitlines(), 1):
        if 'Year' in line and ('years' in line or 'Tabs' in line or '[' in line):
            print(f'  {i}: {line.strip()[:120]}')
