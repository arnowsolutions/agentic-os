#!/usr/bin/env python3
"""Rebuild parsed roster cache from raw files (run on VPS where write access works)"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from modules.roster_parser import rebuild_parsed_cache

result = rebuild_parsed_cache()
print(json.dumps(result, indent=2))
