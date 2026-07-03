"""
Patch for vapi_bridge.py — replaces stub weather/news handlers with real APIs
and adds emailDirections + emailWeather + emailNews tools.

Import this from vapi_bridge.py or apply manually.
"""
import json
import os
import sys
from modules import vapi_realtime
from modules.smtp_sender import send_email

# --- Replace stub handlers with real ones ---
# In vapi_bridge.py, the _handle_weather and _handle_news functions are stubs.
# The tool dispatch calls them. We override them here.

def _real_handle_weather(location: str = "Bronx, NY"):
    """Real weather via NWS weather.gov API."""
    return vapi_realtime.handle_weather(location)

def _real_handle_news(topic: str = ""):
    """Real news via Google News RSS."""
    return vapi_realtime.handle_news(topic)

def _real_handle_directions(origin: str, destination: str):
    """Real directions via Mapbox Directions API with traffic."""
    return vapi_realtime.handle_directions(origin, destination)


def _send_directions_email(email: str, origin: str, destination: str) -> dict:
    """Get directions and email them as formatted HTML."""
    directions = vapi_realtime.handle_directions(origin, destination)
    
    if "error" in directions:
        return {"success": False, "message": directions.get("brief", "Directions unavailable")}
    
    html_body = vapi_realtime.format_directions_email(directions)
    subject = f"Directions: {origin} → {destination} ({directions['miles']} mi, {directions['minutes']} min)"
    
    result = send_email(
        to=email,
        subject=subject,
        body=html_body,
        is_html=True,
    )
    
    return {
        "success": result.get("successful", False),
        "message": "Directions emailed successfully" if result.get("successful") else f"Email failed: {result.get('error', 'unknown')}",
        "brief": directions.get("brief", ""),
        "miles": directions.get("miles", ""),
        "minutes": directions.get("minutes", ""),
        "traffic": directions.get("traffic", ""),
    }


def _send_weather_email(email: str, location: str = "Bronx, NY") -> dict:
    """Get weather and email it as formatted HTML."""
    weather = vapi_realtime.handle_weather(location)
    
    if "error" in weather and not weather.get("forecast"):
        return {"success": False, "message": "Weather unavailable"}
    
    html_body = vapi_realtime.format_weather_email(weather)
    subject = f"Bronx Weather Forecast — {os.environ.get('SMTP_FROM_NAME', 'Urology Residency Program')}"
    
    result = send_email(
        to=email,
        subject=subject,
        body=html_body,
        is_html=True,
    )
    
    return {
        "success": result.get("successful", False),
        "message": "Weather forecast emailed" if result.get("successful") else f"Email failed: {result.get('error', 'unknown')}",
        "brief": weather.get("brief", ""),
    }


def _send_news_email(email: str, topic: str = "") -> dict:
    """Get news and email it as formatted HTML."""
    news = vapi_realtime.handle_news(topic)
    
    if not news.get("headlines"):
        return {"success": False, "message": "No news available"}
    
    html_body = vapi_realtime.format_news_email(news)
    subject = f"Medical/Urology News — {topic or 'Today'}"
    
    result = send_email(
        to=email,
        subject=subject,
        body=html_body,
        is_html=True,
    )
    
    return {
        "success": result.get("successful", False),
        "message": f"{len(news.get('headlines', []))} stories emailed" if result.get("successful") else f"Email failed: {result.get('error', 'unknown')}",
        "brief": news.get("brief", ""),
    }


# === TOOL DEFINITIONS FOR VAPI ASSISTANT ===
# These define the tool schemas that get registered with the Vapi assistant

EMAIL_DIRECTIONS_TOOL = {
    "name": "emailDirections",
    "description": "Get real-time driving directions with traffic and email them. Use when caller asks for directions, traffic, or commute info. Do NOT read turn-by-turn aloud — email it.",
    "parameters": {
        "type": "object",
        "properties": {
            "origin": {"type": "string", "description": "Starting location (address, place name, or resident name)"},
            "destination": {"type": "string", "description": "Destination (address, place name, or Montefiore campus name)"},
            "email": {"type": "string", "description": "Email address to send the directions to"},
        },
        "required": ["origin", "destination", "email"],
    },
}

EMAIL_WEATHER_TOOL = {
    "name": "emailWeather",
    "description": "Get the weather forecast and email it. Use when caller asks for weather. Say the brief summary aloud, then email the full forecast.",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {"type": "string", "description": "Location (default: Bronx, NY)"},
            "email": {"type": "string", "description": "Email address to send the forecast to"},
        },
        "required": ["email"],
    },
}

EMAIL_NEWS_TOOL = {
    "name": "emailNews",
    "description": "Get medical/urology news and email it. Use when caller asks for news. Say the top headline aloud, then email the full list.",
    "parameters": {
        "type": "object",
        "properties": {
            "topic": {"type": "string", "description": "Topic to search for (default: urology/medical education)"},
            "email": {"type": "string", "description": "Email address to send the news to"},
        },
        "required": ["email"],
    },
}

GET_DIRECTIONS_TOOL = {
    "name": "getDirections",
    "description": "Get real-time driving directions with traffic. Returns a brief summary (distance, time, traffic) for voice + full steps for email. ALWAYS offer to email — do NOT read all steps aloud.",
    "parameters": {
        "type": "object",
        "properties": {
            "origin": {"type": "string", "description": "Starting location (address, place name, or resident name)"},
            "destination": {"type": "string", "description": "Destination (address, place name, or Montefiore campus name)"},
        },
        "required": ["origin", "destination"],
    },
}

ALL_NEW_TOOLS = [EMAIL_DIRECTIONS_TOOL, EMAIL_WEATHER_TOOL, EMAIL_NEWS_TOOL, GET_DIRECTIONS_TOOL]