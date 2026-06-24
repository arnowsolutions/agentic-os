#!/usr/bin/env python3
"""Check Vapi server health and restart if down.
   Runs every 5 minutes via cron.
   - Checks if server:8090 is alive
   - Checks if tunnel is alive 
   - Restarts both if needed
"""
import os, sys, subprocess, json, re, time

from modules.config import get_settings

settings = get_settings()

SERVER_PORT = settings.PORT
SERVER_DIR = "/workspace/agentic-os"
VENV_PYTHON = "/app/venv/bin/python3"
CLOUDFLARED = "/tmp/cloudflared"
TUNNEL_URL_FILE = "/workspace/agentic-os/tunnel_url.txt"
VAPI_ENDPOINT_PATH = settings.VAPI_ENDPOINT_PATH + "/status"
API_KEY = settings.VAPI_API_KEY
ASSISTANT_ID = settings.VAPI_ASSISTANT_ID


def check_server():
    """Check if server is responding on port."""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3)
    try:
        s.connect(("127.0.0.1", SERVER_PORT))
        s.close()
        return True
    except Exception:
        return False


def check_tunnel():
    """Check if tunnel URL is reachable."""
    if not os.path.exists(TUNNEL_URL_FILE):
        return False
    url = open(TUNNEL_URL_FILE).read().strip()
    if not url:
        return False
    import urllib.request
    try:
        req = urllib.request.Request(url + VAPI_ENDPOINT_PATH, method="GET", timeout=5)
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status == 200
    except Exception:
        return False


def kill_processes(port=None, name=None):
    """Kill processes by port or name."""
    for pid_dir in os.listdir("/proc"):
        if not pid_dir.isdigit():
            continue
        try:
            cmdline = open(f"/proc/{pid_dir}/cmdline").read()
            if port and f":{port}" in cmdline and "server.py" in cmdline:
                os.kill(int(pid_dir), 9)
            if name and name in cmdline:
                os.kill(int(pid_dir), 9)
        except Exception:
            pass


def start_server():
    kill_processes(port=SERVER_PORT)
    log = open("/tmp/agentic-os.log", "w")
    subprocess.Popen(
        [VENV_PYTHON, "server.py", "--port", str(SERVER_PORT), "--host", "0.0.0.0"],
        cwd=SERVER_DIR, stdout=log, stderr=subprocess.STDOUT
    )
    for i in range(10):
        time.sleep(1)
        if check_server():
            return True
    return False


def start_tunnel():
    kill_processes(name="cloudflared")
    log = open("/tmp/cloudflared.log", "w")
    proc = subprocess.Popen(
        [CLOUDFLARED, "tunnel", "--url", f"http://localhost:{SERVER_PORT}"],
        stdout=log, stderr=subprocess.STDOUT
    )
    for i in range(15):
        time.sleep(1)
        try:
            output = open("/tmp/cloudflared.log").read()
            urls = re.findall(r'https://[a-z0-9.-]*\.trycloudflare\.com', output)
            if urls:
                url = urls[0]
                open(TUNNEL_URL_FILE, "w").write(url)
                return url
        except Exception:
            pass
    return None


# ── MAIN ──
status = {"server": check_server(), "tunnel": check_tunnel()}
actions = []

if not status["server"]:
    actions.append("server was down")
    if start_server():
        actions.append("server restarted OK")
    else:
        actions.append("server FAILED to restart")
        print("CRITICAL: Vapi server could not be restarted")
        sys.exit(1)

if not status["tunnel"]:
    actions.append("tunnel was down")
    tunnel_url = start_tunnel()
    if tunnel_url:
        actions.append(f"tunnel restarted: {tunnel_url}")
    else:
        actions.append("tunnel FAILED to restart")

if actions:
    print(f"Actions taken: {'; '.join(actions)}")
else:
    print("All systems healthy")
