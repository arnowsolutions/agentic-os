#!/usr/bin/env python3
"""
directions.py — Google Maps Directions + Geocoding for morning briefing.
Uses Google Maps Platform API (Directions + Geocoding).

Routes configured:
  - Shareef's commute: Home to assigned hospital
  - Rutul's commute: Home to assigned hospital

Destinations:
  - Moses:      111 E 210th St, Bronx, NY 10467
  - Hutch:      1250 Waters Pl, Bronx, NY 10461
  - Wakefield:  600 E 233rd St, Bronx, NY 10466

API key stored at ~/.hermes/.env.maps
"""
import json
import os
import urllib.request
import urllib.parse
import sys
from datetime import datetime
from typing import Optional

# CRM data from Supabase Postgres via shared module
try:
    from modules.crm_db import get_contacts, get_contact_by_email
except ImportError:
    get_contacts = lambda: []
    get_contact_by_email = lambda e: None

def get_api_key():
    candidates = [
        os.path.join(os.environ.get("HOME", "/home/hermeswebui"), ".hermes", ".env.maps"),
        "/home/hermeswebui/.hermes/.env.maps",
    ]
    for fp in candidates:
        if os.path.exists(fp):
            with open(fp) as f:
                for line in f:
                    s = line.strip()
                    if s.startswith("GOOGLE_MAPS_API_KEY="):
                        return s.split("=", 1)[1].strip().strip(chr(34)).strip(chr(39))
    return ""

API_KEY = get_api_key()
BASE_URL = "https://maps.googleapis.com/maps/api"

def load_crm_contacts():
    """Load contacts from Supabase Postgres (shared module)."""
    return get_contacts()

def get_address_from_crm(first, last):
    for c in get_contacts():
        if c.get("firstName", "").lower() == first.lower() and c.get("lastName", "").lower() == last.lower():
            a = c.get("homeAddress") or c.get("address") or c.get("workAddress")
            if a:
                return a
    return None

HOSPITALS = {
    "moses": "111 E 210th St, Bronx, NY 10467",
    "hutch": "1250 Waters Pl, Bronx, NY 10461",
    "wakefield": "600 E 233rd St, Bronx, NY 10466",
}

ROUTES = [
    {"key": "shareef", "first": "Shareef", "last": "Frasier",
     "home": "665 Arnow Ave, Bronx, NY 10467", "hospital": "hutch"},
    {"key": "rutul", "first": "Rutul", "last": "Patel",
     "home": "", "hospital": "moses", "hide_from": ["shareef"]},
]

def resolve_origin(cfg):
    a = get_address_from_crm(cfg["first"], cfg["last"])
    return a if a else cfg["home"]

def resolve_destination(cfg):
    return HOSPITALS.get(cfg.get("hospital", "moses"), HOSPITALS["moses"])

def geocode(address):
    url = BASE_URL + "/geocode/json?" + urllib.parse.urlencode({"address": address, "key": API_KEY})
    try:
        data = json.loads(urllib.request.urlopen(urllib.request.Request(url), timeout=10).read())
        if data["status"] == "OK" and data["results"]:
            loc = data["results"][0]["geometry"]["location"]
            return (loc["lat"], loc["lng"])
    except Exception as e:
        print(f"  geocode error: {e}", file=sys.stderr)
    return None

def get_directions(origin, dest, dep="now"):
    params = urllib.parse.urlencode({"origin": origin, "destination": dest, "mode": "driving",
                                      "departure_time": dep, "traffic_model": "best_guess", "key": API_KEY})
    url = BASE_URL + "/directions/json?" + params
    try:
        data = json.loads(urllib.request.urlopen(urllib.request.Request(url), timeout=15).read())
    except Exception as e:
        print(f"  directions error: {e}", file=sys.stderr)
        return None
    if data["status"] != "OK":
        print(f"  directions status: {data['status']}", file=sys.stderr)
        return None
    leg = data["routes"][0]["legs"][0]
    return {
        "origin": leg["start_address"],
        "destination": leg["end_address"],
        "distance": leg["distance"]["text"],
        "duration": leg["duration"]["text"],
        "duration_in_traffic": leg.get("duration_in_traffic", {}).get("text", leg["duration"]["text"]),
    }

def check_route(name, origin, dest, dep="now"):
    print(f"\n{name.title()}'s commute:")
    coords = geocode(origin)
    if coords:
        print(f"   @ {coords[0]:.4f}, {coords[1]:.4f}")
    result = get_directions(origin, dest, dep)
    if not result:
        return {"name": name, "error": "Could not get directions"}
    normal = result["duration"]
    traffic = result["duration_in_traffic"]
    dt = ""
    if normal != traffic:
        try:
            nv = int(normal.split()[0])
            tv = int(traffic.split()[0])
            if "hour" in normal:
                nv = nv * 60 + (int(normal.split()[2]) if len(normal.split()) > 2 else 0)
                tv = tv * 60 + (int(traffic.split()[2]) if len(traffic.split()) > 2 else 0)
            d = tv - nv
            if d > 0:
                dt = f" (+{d} min traffic)"
            elif d < 0:
                dt = f" ({abs(d)} min faster)"
            else:
                dt = " (no delay)"
        except:
            dt = ""
    print(f"   {result['distance']} — normally {normal}, now {traffic}{dt}")
    return {"name": name, "distance": result["distance"], "duration": normal,
            "duration_in_traffic": traffic, "delta_text": dt}

def get_commute_report(dep="now", viewer=None):
    """Get commute report for all routes. If viewer is set, hide routes with hide_from containing viewer key."""
    results = []
    for r in ROUTES:
        hidden = r.get("hide_from", [])
        if viewer and viewer in hidden:
            continue
        o = resolve_origin(r)
        d = resolve_destination(r)
        results.append(check_route(r["key"], o, d, dep))
    return {"routes": results, "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    print("=" * 50)
    print("Commute Check — Morning Briefing")
    print("=" * 50)
    get_commute_report()
