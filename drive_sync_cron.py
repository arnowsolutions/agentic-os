#!/usr/bin/env python3
"""Daily Drive Sync — called by Hermes cron at 5:00 AM ET.
Syncs location-roster files from Google Drive to local cache.
Silent on success, prints only on failure.
"""
import json, os, sys

# Path resolution
HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(HERE)

sys.path.insert(0, os.path.join(WORKSPACE, "agentic-os"))
try:
    from modules import drive_sync
except ImportError:
    # Try alternate path
    sys.path.insert(0, os.path.join(WORKSPACE))
    from agentic_os.modules import drive_sync  # noqa: F811

result = drive_sync.sync_location_rosters()

if result.get("success"):
    synced = result.get("synced", 0)
    skipped = result.get("skipped", 0)
    errors = result.get("errors", [])
    if errors:
        print(f"Drive sync: {synced} synced, {skipped} skipped, {len(errors)} errors")
        for e in errors:
            print(f"  - {e}")
    # Silent on clean success
else:
    reason = result.get("reason", "unknown")
    print(f"Drive sync FAILED: {reason}")
    print(result.get("action", ""))
    print(result.get("error", ""))
