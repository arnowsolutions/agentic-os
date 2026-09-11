#!/usr/bin/env python3
"""DEPRECATED (2026-09-09) — Grand Rounds schedule single-source consolidation.

OLD design (WRONG, retired): urology_qgenda.grand_rounds_schedule was treated as
canonical and pushed down to unified.grand_rounds + grand-rounds.js. That
duplicated the schedule in 3+ places and caused stale/conflicting data.

NEW design (LIVE): unified.grand_rounds (postgres DB, schema unified) is the ONE
canonical store. Every consumer reads it:
  - gr_schedule.py          -> shared reader/writer used by all senders + server
  - outlook_deeplink_generator.py (Calendar Invites page)
  - send_grand_rounds_email.py / send_monday_sasp_email.py (bulk senders)
  - server.py /api/conference/* + /api/send-tracker/* + /api/email/send-log
  - dashboard pages fetch those APIs (no embedded schedule arrays)

The old urology_qgenda.grand_rounds_schedule table was renamed to
_archive_grand_rounds_schedule_20260909 (2026-09-09) — see Phase F.

This file must NOT be re-run as-is; it would resurrect the old direction.
If the old table needs inspection: psql -d urology_qgenda
SELECT * FROM _archive_grand_rounds_schedule_20260909;
"""
import sys
print("Deprecated. unified.grand_rounds is the single source of truth. Nothing to do.")
sys.exit(0)
