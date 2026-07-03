"""
Real-time data handlers for Vapi voice assistant.
Replaces the stub weather/news handlers with live API calls.
Adds directions/traffic via Mapbox + email delivery via SMTP.

Used by vapi_bridge.py tool dispatcher.
"""
import json
import os
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

# --- Config ---
MAPBOX_TOKEN_FILE = "/home/hermeswebui/.hermes/profiles/opencode-acct2/.mapbox_token"
RESIDENTS_FILE = "/workspace/scripts/resident_addresses.json"

KNOWN_LOCATIONS = {
    "montefiore medical center": ("Montefiore Medical Center (111 E 210th St, Bronx)", -73.8790, 40.8762),
    "montefiore": ("Montefiore Medical Center (111 E 210th St, Bronx)", -73.8790, 40.8762),
    "montefiore moses": ("Montefiore Moses Campus (111 E 210th St, Bronx)", -73.8790, 40.8762),
    "moses": ("Montefiore Moses Campus (111 E 210th St, Bronx)", -73.8790, 40.8762),
    "montefiore weiler": ("Montefiore Weiler Campus (1825 Eastchester Rd, Bronx)", -73.8435, 40.8527),
    "weiler": ("Montefiore Weiler Campus (1825 Eastchester Rd, Bronx)", -73.8435, 40.8527),
    "montefiore wakefield": ("Montefiore Wakefield Campus (600 E 233rd St, Bronx)", -73.8550, 40.8927),
    "wakefield": ("Montefiore Wakefield Campus (600 E 233rd St, Bronx)", -73.8550, 40.8927),
    "montefiore allen pavilion": ("Montefiore Allen Pavilion (3140 Bainbridge Ave, Bronx)", -73.8923, 40.8745),
    "einstein college of medicine": ("Einstein College of Medicine (1300 Morris Park Ave, Bronx)", -73.8448, 40.8510),
    "einstein": ("Einstein College of Medicine (1300 Morris Park Ave, Bronx)", -73.8448, 40.8510),
    "yankee stadium": ("Yankee Stadium (1 E 161st St, Bronx)", -73.9282, 40.8296),
    "lincoln hospital": ("Lincoln Hospital (234 E 149th St, Bronx)", -73.9183, 40.8123),
    "bronx lebanon hospital": ("Bronx Lebanon Hospital (1650 Grand Concourse, Bronx)", -73.9207, 40.8338),
    "north central bronx hospital": ("North Central Bronx Hospital (3424 Bainbridge Ave, Bronx)", -73.8923, 40.8747),
}


def _get_mapbox_token() -> str:
    """Load Mapbox token from env or file."""
    token = os.environ.get("MAPBOX_TOKEN", "")
    if not token and os.path.exists(MAPBOX_TOKEN_FILE):
        with open(MAPBOX_TOKEN_FILE) as f:
            token = f.read().strip()
    return token


def _load_residents() -> List[dict]:
    """Load resident address data."""
    if os.path.exists(RESIDENTS_FILE):
        with open(RESIDENTS_FILE) as f:
            return json.load(f)
    return []


def handle_weather(location: str = "Bronx, NY") -> Dict[str, Any]:
    """
    REAL weather via NWS weather.gov API.
    Returns current conditions + next 4 forecast periods.
    """
    try:
        # Bronx coordinates
        lat, lon = 40.8448, -73.8648
        point_url = f"https://api.weather.gov/points/{lat},{lon}"
        req = urllib.request.Request(
            point_url,
            headers={"User-Agent": "HermesAgent/1.0", "Accept": "application/geo+json"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            point_data = json.loads(resp.read())

        forecast_url = point_data["properties"]["forecast"]
        req2 = urllib.request.Request(
            forecast_url,
            headers={"User-Agent": "HermesAgent/1.0", "Accept": "application/geo+json"}
        )
        with urllib.request.urlopen(req2, timeout=15) as resp2:
            forecast_data = json.loads(resp2.read())

        periods = forecast_data["properties"]["periods"][:4]

        # Build brief summary for voice + detailed for email
        current = periods[0] if periods else {}
        brief = f"{current.get('name', 'Today')}: {current.get('temperature', '?')} degrees, {current.get('shortForecast', 'unknown')}"

        forecast_list = []
        for p in periods:
            forecast_list.append({
                "name": p.get("name", ""),
                "temperature": p.get("temperature", ""),
                "unit": p.get("temperatureUnit", "F"),
                "shortForecast": p.get("shortForecast", ""),
                "detailedForecast": p.get("detailedForecast", ""),
            })

        return {
            "location": "Bronx, NY",
            "brief": brief,
            "forecast": forecast_list,
            "source": "NWS weather.gov",
        }
    except Exception as e:
        return {
            "location": location,
            "brief": f"Weather unavailable right now.",
            "error": str(e),
        }


def handle_news(topic: str = "") -> Dict[str, Any]:
    """
    REAL news via Google News RSS.
    Returns top 5 urology/medical education headlines.
    """
    try:
        query = "urology OR medical education OR residency"
        if topic:
            query = topic
        rss_url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=en-US&gl=US&ceid=US:en"
        req = urllib.request.Request(rss_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            rss_raw = resp.read().decode("utf-8")

        root = ET.fromstring(rss_raw)
        items = root.findall(".//item")[:5]

        headlines = []
        seen = set()
        for item in items:
            title = item.findtext("title", default="")
            source = item.findtext("source", default="")
            if title in seen:
                continue
            seen.add(title)
            headlines.append({"title": title, "source": source})

        brief = f"{len(headlines)} stories today. Top: {headlines[0]['title']}" if headlines else "No news found."

        return {
            "topic": topic or "urology/medical education",
            "brief": brief,
            "headlines": headlines,
            "source": "Google News RSS",
        }
    except Exception as e:
        return {
            "topic": topic,
            "brief": "News unavailable right now.",
            "error": str(e),
        }


def _geocode(place_name: str) -> Optional[List[float]]:
    """Geocode a place name or address to [lon, lat]. Checks known locations + residents first."""
    token = _get_mapbox_token()
    if not token:
        return None

    key = place_name.lower().strip()

    # Check known landmarks
    if key in KNOWN_LOCATIONS:
        name, lon, lat = KNOWN_LOCATIONS[key]
        return [lon, lat]

    # Check resident addresses
    residents = _load_residents()
    for r in residents:
        full_name = r["name"].lower()
        last_name = r["lastName"].lower()
        first_name = r["firstName"].lower()
        if key == full_name or key == last_name or key == first_name:
            return _geocode_address(r["address"], token)

    # Fall back to Mapbox geocoding
    return _geocode_address(place_name, token)


def _geocode_address(address: str, token: str) -> Optional[List[float]]:
    """Geocode a raw address via Mapbox."""
    encoded = urllib.parse.quote(address)
    bbox = "-74.05,40.65,-73.75,40.95"
    url = (
        f"https://api.mapbox.com/geocoding/v5/mapbox.places/{encoded}.json?"
        f"access_token={token}&limit=1&bbox={bbox}&proximity=-73.866,40.837"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "HermesAgent/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
    if not data["features"]:
        return None
    return data["features"][0]["center"]


def handle_directions(origin: str, destination: str) -> Dict[str, Any]:
    """
    Real-time driving directions via Mapbox Directions API.
    Returns brief summary for voice + full turn-by-turn for email.
    """
    token = _get_mapbox_token()
    if not token:
        return {"error": "Mapbox token not configured", "brief": "Directions unavailable."}

    origin_coords = _geocode(origin)
    dest_coords = _geocode(destination)

    if not origin_coords:
        return {"error": f"Could not find origin: {origin}", "brief": f"I couldn't find {origin}."}
    if not dest_coords:
        return {"error": f"Could not find destination: {destination}", "brief": f"I couldn't find {destination}."}

    coord_str = f"{origin_coords[0]},{origin_coords[1]};{dest_coords[0]},{dest_coords[1]}"
    params = {
        "access_token": token,
        "steps": "true",
        "overview": "full",
        "geometries": "geojson",
        "language": "en",
    }
    url = f"https://api.mapbox.com/directions/v5/mapbox/driving-traffic/{coord_str}?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "HermesAgent/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read())

    if data.get("code") != "Ok" or not data.get("routes"):
        return {"error": "No route found", "brief": "I couldn't find a driving route for that."}

    route = data["routes"][0]
    leg = route["legs"][0]
    miles = route["distance"] * 0.000621371
    minutes = route["duration"] / 60
    weight = route.get("weight", route["duration"])
    traffic_ratio = weight / route["duration"] if route["duration"] > 0 else 1
    if traffic_ratio > 1.3:
        traffic = "heavy"
    elif traffic_ratio > 1.1:
        traffic = "moderate"
    else:
        traffic = "normal"

    # Brief for voice (1 sentence)
    brief = f"{miles:.1f} miles, about {minutes:.0f} minutes, traffic is {traffic}."

    # Full turn-by-turn for email
    steps = []
    step_num = 1
    for step in leg["steps"]:
        maneuver = step["maneuver"]
        m_type = maneuver["type"]
        m_mod = maneuver.get("modifier", "")
        road_name = step.get("name", "") or "(unnamed road)"
        step_dist = step["distance"] * 0.000621371

        if step_dist < 0.005 and m_type not in ("depart", "arrive"):
            continue

        if m_type == "depart":
            instruction = f"Head {m_mod} on {road_name}" if m_mod else f"Start on {road_name}"
        elif m_type == "arrive":
            instruction = f"Arrive at destination ({road_name})"
        elif m_type == "turn":
            instruction = f"Turn {m_mod} onto {road_name}"
        elif m_type == "continue":
            instruction = f"Continue {m_mod} on {road_name}"
        elif m_type == "merge":
            instruction = f"Merge onto {road_name}"
        elif m_type == "on ramp":
            instruction = f"Take ramp onto {road_name}"
        elif m_type == "off ramp":
            instruction = f"Take exit onto {road_name}"
        elif m_type == "fork":
            instruction = f"Keep {m_mod} at fork onto {road_name}"
        else:
            instruction = f"{m_type} {m_mod} onto {road_name}".strip()

        if step_dist >= 0.1:
            dist_str = f"{step_dist:.1f} mi"
        else:
            dist_str = f"{step_dist * 5280:.0f} ft"

        steps.append({"step": step_num, "instruction": instruction, "distance": dist_str})
        step_num += 1

    return {
        "origin": origin,
        "destination": destination,
        "miles": round(miles, 1),
        "minutes": round(minutes),
        "traffic": traffic,
        "brief": brief,
        "steps": steps,
        "source": "Mapbox Directions API (real-time traffic)",
    }


def format_directions_email(directions_data: dict, recipient_name: str = "") -> str:
    """Format directions data as HTML email body."""
    if "error" in directions_data:
        return f"<p>Sorry, couldn't get directions: {directions_data['error']}</p>"

    html = f"""
    <html><body style="font-family: Arial, sans-serif; color: #333;">
    <h2 style="color: #1a3a5c;">Driving Directions — Real-Time Traffic</h2>
    <table style="border-collapse: collapse; width: 100%; max-width: 600px;">
        <tr><td style="padding: 4px 0; font-weight: bold;">From:</td><td>{directions_data['origin']}</td></tr>
        <tr><td style="padding: 4px 0; font-weight: bold;">To:</td><td>{directions_data['destination']}</td></tr>
        <tr><td style="padding: 4px 0; font-weight: bold;">Distance:</td><td>{directions_data['miles']} miles</td></tr>
        <tr><td style="padding: 4px 0; font-weight: bold;">Duration:</td><td>{directions_data['minutes']} min (with traffic)</td></tr>
        <tr><td style="padding: 4px 0; font-weight: bold;">Traffic:</td><td style="text-transform: capitalize;">{directions_data['traffic']}</td></tr>
    </table>
    <h3 style="color: #1a3a5c; margin-top: 20px;">Turn-by-Turn</h3>
    <ol style="line-height: 1.6;">
    """
    for step in directions_data.get("steps", []):
        html += f"<li>{step['instruction']} ({step['distance']})</li>\n"
    html += """
    </ol>
    <p style="margin-top: 20px; font-size: 12px; color: #999;">Powered by Mapbox Directions API with real-time traffic. ETA may change based on live conditions.</p>
    </body></html>
    """
    return html


def format_weather_email(weather_data: dict) -> str:
    """Format weather data as HTML email body."""
    html = '<html><body style="font-family: Arial, sans-serif; color: #333;">'
    html += '<h2 style="color: #1a3a5c;">Bronx Weather Forecast</h2>'
    html += '<table style="border-collapse: collapse; width: 100%; max-width: 600px;">'
    for p in weather_data.get("forecast", []):
        html += f"""
        <tr style="border-bottom: 1px solid #eee;">
            <td style="padding: 8px 0; font-weight: bold;">{p['name']}</td>
            <td style="padding: 8px 0;">{p['temperature']}°{p['unit']}</td>
            <td style="padding: 8px 0;">{p['shortForecast']}</td>
        </tr>
        <tr><td colspan="3" style="padding: 4px 0 12px; color: #666; font-size: 13px;">{p.get('detailedForecast', '')}</td></tr>
        """
    html += '</table>'
    html += '<p style="margin-top: 16px; font-size: 12px; color: #999;">Source: NWS weather.gov</p>'
    html += '</body></html>'
    return html


def format_news_email(news_data: dict) -> str:
    """Format news data as HTML email body."""
    html = '<html><body style="font-family: Arial, sans-serif; color: #333;">'
    html += '<h2 style="color: #1a3a5c;">Medical / Urology News</h2>'
    html += '<ol style="line-height: 1.8;">'
    for h in news_data.get("headlines", []):
        html += f'<li><strong>{h["title"]}</strong><br><span style="color: #999; font-size: 13px;">{h.get("source", "")}</span></li>'
    html += '</ol>'
    html += '<p style="margin-top: 16px; font-size: 12px; color: #999;">Source: Google News RSS</p>'
    html += '</body></html>'
    return html