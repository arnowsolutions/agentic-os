#!/bin/bash
# Vapi VPS Deployment Script
# Run this on the VPS as root

set -e

WORKSPACE="/var/lib/docker/volumes/hermes-webui-gsga_hermes-workspace/_data"
cd "$WORKSPACE"

echo "[1] Installing Python dependencies..."
.vapi-venv/bin/pip install fastapi uvicorn openpyxl pydantic httpx python-multipart -q 2>&1 | tail -2

echo "[2] Testing import..."
.vapi-venv/bin/python3 -c "from modules.vapi_bridge import router; print('Import OK')"

echo "[3] Stopping old server..."
fuser -k 8090/tcp 2>/dev/null || true
sleep 1

echo "[4] Starting server..."
systemd-run --unit=vapi-server --same-dir --working-dir="$WORKSPACE" \
    "$WORKSPACE/.vapi-venv/bin/python3" "$WORKSPACE/server.py" --port 8090 --host 0.0.0.0
sleep 4

echo "[5] Testing..."
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:8090/api/vapi \
    -X POST -H "Content-Type: application/json" -d '{}'

echo "[6] Creating systemd service..."
cat > /etc/systemd/system/vapi-server.service << 'SERVICE'
[Unit]
Description=Vapi Voice Server
After=network.target

[Service]
Type=simple
ExecStart=PATH_PLACEHOLDER/.vapi-venv/bin/python3 PATH_PLACEHOLDER/server.py --port 8090 --host 0.0.0.0
Restart=on-failure
RestartSec=10
User=root
WorkingDirectory=PATH_PLACEHOLDER

[Install]
WantedBy=multi-user.target
SERVICE
sed -i "s|PATH_PLACEHOLDER|$WORKSPACE|g" /etc/systemd/system/vapi-server.service
systemctl daemon-reload
systemctl enable vapi-server.service

echo "[7] Testing via tunnel..."
curl -s "https://membrane-distributors-rebel-globe.trycloudflare.com/api/vapi" \
    -X POST -H "Content-Type: application/json" \
    -d '{"message":{"type":"tool-calls","toolCalls":[{"function":{"name":"authUser","arguments":{"name":"Shareef Frasier","pin":"3195"}}}]}}'

echo ""
echo "=== VAPI SERVER DEPLOYED ON VPS ==="
echo "Local:  http://localhost:8090"
echo "Public: http://147.93.113.241:8090 (no TLS)"
echo ""
echo "Next: update Vapi assistant URL to use this server"
