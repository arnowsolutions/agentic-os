#!/usr/bin/env python3
"""Rebuild roster cache on VPS with all file types - uses workspace tokens"""
import sys, os, json

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

from modules.google_workspace import GoogleWorkspace

# Use the workspace data dir paths  
gw = GoogleWorkspace(
    token_path=os.path.join(BASE, "data", "google_token.json"),
    credentials_path=os.path.join(BASE, "data", "google_credentials.json"),
)

raw_dir = os.path.join(BASE, "data", "location_rosters", "raw")
os.makedirs(raw_dir, exist_ok=True)

# Download vacation file  
r = gw.download_drive_file(user_id="urologyresidency", file_id="1gBCGL6gR3Py0kAFDMCmuGkHvI_nSRJqW",
    dest_path=os.path.join(raw_dir, "Urology 2026 Approved Vacation.xlsm"))
print(f"Vacation: {r.get('successful')} ({r.get('size',0)} bytes)")

# Download timeline  
r2 = gw.download_drive_file(user_id="urologyresidency", file_id="1Idt8SsF7DXwdD8KEYaDpSQp1Jw1_7R31",
    dest_path=os.path.join(raw_dir, "Urology Scheduling Timeline.xlsx"))
print(f"Timeline: {r2.get('successful')} ({r2.get('size',0)} bytes)")

# Rebuild with roster_parser
from modules.roster_parser import rebuild_parsed_cache
result = rebuild_parsed_cache()
print(json.dumps(result, indent=2))
