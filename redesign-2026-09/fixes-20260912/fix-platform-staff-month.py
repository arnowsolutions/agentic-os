#!/usr/bin/env python3
"""Fix /api/v1/staff-schedule/month — clamp end date to the month's real last day.

Bug: end = f"{month}-31" -> '2026-09-31'::date throws for any month shorter than
31 days (Sep/Feb/Apr/Jun/Nov) -> HTTP 500 on the Staff Schedule month view.

Run ON THE VPS:  python3 /tmp/fix-platform-staff-month.py
Idempotent: re-running after a successful patch prints "already patched".
"""
import pathlib
import shutil

P = pathlib.Path('/var/www/unified/server/routes/staff-schedule.ts')
src = P.read_text()

OLD = """    const month = (req.query.month as string) || new Date().toISOString().slice(0, 7);
    const start = `${month}-01`;
    const end = `${month}-31`;"""

NEW = """    const month = (req.query.month as string) || new Date().toISOString().slice(0, 7);
    const [yy, mm] = month.split('-').map(Number);
    if (!yy || !mm || mm < 1 || mm > 12) {
      return sendError(res, 'BAD_REQUEST', 'month must be YYYY-MM');
    }
    const lastDay = new Date(Date.UTC(yy, mm, 0)).getUTCDate();
    const start = `${month}-01`;
    const end = `${month}-${String(lastDay).padStart(2, '0')}`;"""

if NEW.split('\n')[1] in src:
    print('already patched — nothing to do')
    raise SystemExit(0)

assert OLD in src, 'old month block not found — inspect manually'

bak = P.with_name(P.name + '.bak-20260912')
shutil.copy2(P, bak)
P.write_text(src.replace(OLD, NEW, 1))
print('patched OK; backup at', bak)
