#!/bin/bash
# VPS Cloudflare Tunnel — started by systemd
# Manages a quick tunnel pointing to the local Vapi server on port 8090.
# Writes the current tunnel URL to the shared volume for the container to read.
# Runs in foreground so systemd can monitor and auto-restart it.

set -e

CLOUDFLARED="/usr/local/bin/cloudflared"
SERVER_URL="http://localhost:8090"
TUNNEL_LOG="/tmp/vapi_tunnel.log"
TUNNEL_URL_FILE="/var/lib/docker/volumes/hermes-webui-gsga_hermes-workspace/_data/agentic-os/tunnel_url.txt"
LOCAL_URL_FILE="/tmp/vapi_tunnel_url.txt"

echo "[vps-tunnel] Starting Cloudflare tunnel -> $SERVER_URL"

# Kill any leftover cloudflared from a previous run that wasn't cleaned up
pkill -f "cloudflared tunnel" 2>/dev/null || true
sleep 1

# Start cloudflared in background, capture output
$CLOUDFLARED tunnel --url "$SERVER_URL" > "$TUNNEL_LOG" 2>&1 &
CF_PID=$!
echo "[vps-tunnel] cloudflared PID: $CF_PID"

# Wait for the tunnel URL to appear in the log
URL=""
for i in $(seq 1 30); do
    URL=$(grep -o 'https://[a-z0-9.-]*\.trycloudflare\.com' "$TUNNEL_LOG" 2>/dev/null | head -1)
    if [ -n "$URL" ]; then
        break
    fi
    sleep 1
done

if [ -z "$URL" ]; then
    echo "[vps-tunnel] ERROR: Could not get tunnel URL after 30s"
    kill $CF_PID 2>/dev/null || true
    exit 1
fi

# Write URL to shared volume for the container
echo "$URL" > "$TUNNEL_URL_FILE"
echo "$URL" > "$LOCAL_URL_FILE"
echo "[vps-tunnel] ✅ Tunnel URL: $URL"
echo "[vps-tunnel] Written to $TUNNEL_URL_FILE"

# Now follow the tunnel process — keep running so systemd knows we're alive
# If cloudflared dies, this script exits and systemd restarts us
wait $CF_PID
EXIT_CODE=$?
echo "[vps-tunnel] cloudflared exited with code $EXIT_CODE"
exit $EXIT_CODE
