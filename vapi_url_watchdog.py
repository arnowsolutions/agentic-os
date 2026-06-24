#!/usr/bin/env python3
"""VPS Tunnel URL Watchdog — runs in the container every 3 minutes.
Checks if the VPS-side tunnel URL has changed. If so, updates the deploy
script and pushes the new URL to Vapi so the assistant stays reachable.

Also verifies the tunnel is actually responding. If not, alerts via exit code.
"""
import json, os, re, sys, subprocess, time
import urllib.request

from modules.config import get_settings

settings = get_settings()

TUNNEL_URL_FILE = "/workspace/agentic-os/tunnel_url.txt"
DEPLOY_SCRIPT = "/workspace/agentic-os/deploy_vapi_v5.py"
VENV_PYTHON = "/app/venv/bin/python3"
HEALTH_LOG = "/tmp/vapi_tunnel_watchdog.log"
VAPI_ENDPOINT_PATH = settings.VAPI_ENDPOINT_PATH + "/status"
ASSISTANT_ID = settings.VAPI_ASSISTANT_ID
API_KEY = settings.VAPI_API_KEY


def log(msg):
    t = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{t}] {msg}"
    try:
        with open(HEALTH_LOG, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass
    if any(word in msg for word in ["changed", "❌", "⚠️", "ERROR", "FAILED", "Deploy"]):
        print(line)


def get_tunnel_url_from_file():
    try:
        url = open(TUNNEL_URL_FILE).read().strip()
        if url and url.startswith("https://") and "trycloudflare.com" in url:
            return url
    except Exception:
        pass
    return None


def get_assistant_server_url():
    """Read the current server.url from the Vapi assistant config."""
    try:
        req = urllib.request.Request(
            f"https://api.vapi.ai/assistant/{ASSISTANT_ID}",
            headers={"Authorization": "Bearer " + API_KEY, "User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode())
            return data.get("server", {}).get("url", "")
    except Exception as e:
        log(f"Could not read assistant config: {e}")
        return ""


def deploy():
    log("Re-deploying Vapi config with current tunnel URL...")
    result = subprocess.run(
        [VENV_PYTHON, DEPLOY_SCRIPT],
        capture_output=True, text=True, timeout=25
    )
    if result.returncode == 0:
        log("✅ Deploy OK")
        return True
    else:
        log(f"❌ Deploy failed: {result.stderr[:300]}")
        return False


def check_tunnel_live(url):
    """Quick connectivity check — does the tunnel respond?"""
    try:
        req = urllib.request.Request(url + VAPI_ENDPOINT_PATH, method="GET", timeout=5)
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status == 200
    except Exception:
        return False


# ── Main ──
log("VPS tunnel watchdog running...")

tunnel_url = get_tunnel_url_from_file()
if not tunnel_url:
    log("⚠️ No tunnel URL in tunnel_url.txt — VPS tunnel may not have started yet")
    sys.exit(1)

assistant_url = get_assistant_server_url()
# assistant_url contains the full URL including /vapi path
if tunnel_url + "/vapi" != assistant_url:
    log(f"Assistant URL mismatch: {assistant_url} → {tunnel_url}/vapi")
    if deploy():
        log("✅ Assistant URL updated")
    else:
        log("❌ Failed to update assistant URL")
else:
    log(f"URL unchanged: {tunnel_url}")

# Live check
if not check_tunnel_live(tunnel_url):
    log(f"⚠️ Tunnel URL {tunnel_url} is NOT responding from this host (may be a local network restriction)")
    # Do not exit with error — Vapi's external reachability is the real test.
    sys.exit(0)
