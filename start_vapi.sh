#!/bin/bash
# Vapi Voice System — Container-side startup (VPS handles server + tunnel)
# The server and tunnel now run on the VPS via systemd (vapi-server + vapi-tunnel).
# This script is kept for reference but the container no longer needs a local
# server or tunnel — all traffic routes through the VPS tunnel.
#
# Run this only if you need a local instance for development/testing:
#   bash /workspace/agentic-os/start_vapi.sh --local

set -e

WITH_LOCAL=false
if [ "${1:-}" = "--local" ]; then
    WITH_LOCAL=true
fi

ASSISTANT_ID="9b00342e-1951-4bd0-b4a5-5ca4c9827bd0"

echo "=== Vapi Voice System Status ==="
echo ""
echo "Architecture: VPS-managed (systemd)"
echo "  Server:     vapi-server.service (VPS)"
echo "  Tunnel:     vapi-tunnel.service (VPS)"
echo ""
echo "Tunnel URL: $(cat /workspace/agentic-os/tunnel_url.txt 2>/dev/null || echo 'unknown')"
echo ""
echo "The Vapi assistant is configured to route through the VPS tunnel."
echo "Call +1 (971) 382-0498 and say your name + PIN to test."
echo ""
echo "=== Status Check ==="

# Quick check — is the tunnel reachable from here?
URL=$(cat /workspace/agentic-os/tunnel_url.txt 2>/dev/null)
if [ -n "$URL" ]; then
    CODE=$(curl -s -o /dev/null -w "%{http_code}" "$URL/api/vapi" 2>/dev/null || echo "000")
    if [ "$CODE" = "405" ]; then
        echo "✅ Tunnel reachable from container"
    else
        echo "⚠️ Tunnel responded with HTTP $CODE"
    fi
else
    echo "⚠️ No tunnel URL file found"
fi

if [ "$WITH_LOCAL" = true ]; then
    echo ""
    echo "--- Local mode ---"
    echo "Starting local server + tunnel for development..."
    # Kill old processes
    pkill -f "server.py --port 8090" 2>/dev/null || true
    sleep 1
    # Start server
    nohup /app/venv/bin/python3 /workspace/agentic-os/server.py --port 8090 --host 0.0.0.0 > /tmp/agentic-os.log 2>&1 &
    echo "Server started (PID $!)"
    # Start tunnel
    nohup /tmp/cloudflared tunnel --url http://localhost:8090 > /tmp/cloudflared.log 2>&1 &
    echo "Tunnel started (PID $!)"
    echo "Waiting for URL..."
    sleep 10
    TUNNEL_URL=$(grep -o 'https://[a-z0-9.-]*\.trycloudflare\.com' /tmp/cloudflared.log 2>/dev/null | head -1)
    echo "Local tunnel: ${TUNNEL_URL:-unknown}"
fi

echo ""
echo "PIN for Shareef Frasier: 1279"
