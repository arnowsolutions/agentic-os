#!/bin/bash
# Deploy Vapi VPS setup - Traefik + systemd service
# Run on VPS as root: bash /root/vps_setup.sh

set -e
WS="/var/lib/docker/volumes/hermes-webui-gsga_hermes-workspace/_data"
TRAEFIK_DIR="/docker/traefik"

echo "=== Step 1: Write Traefik dynamic config ==="
mkdir -p $TRAEFIK_DIR

cat > $TRAEFIK_DIR/vapi.yml << 'CONF'
http:
  routers:
    vapi:
      rule: "Host(`vapi.srv1738752.hstgr.cloud`)"
      entrypoints:
        - websecure
      tls:
        certresolver: letsencrypt
      service: vapi-backend
  services:
    vapi-backend:
      loadBalancer:
        servers:
          - url: "http://127.0.0.1:8090"
CONF
echo "  Config written"

echo "=== Step 2: Update Traefik compose ==="
cd $TRAEFIK_DIR

# Check if file provider is already in compose
if grep -q "providers.file" docker-compose.yml; then
    echo "  File provider already configured"
else
    # Add file provider flag
    sed -i 's|--entrypoints.web.http.redirections.entrypoint.scheme=https|--entrypoints.web.http.redirections.entrypoint.scheme=https\n    - --providers.file.filename=/docker/traefik/vapi.yml|' docker-compose.yml
    echo "  Added file provider to compose"
fi

echo "=== Step 3: Restart Traefik ==="
docker compose up -d --force-recreate traefik 2>&1 | tail -3
echo "  Traefik restarted"

echo "=== Step 4: Wait for Let's Encrypt cert ==="
sleep 12

echo "=== Step 5: Test HTTPS ==="
curl -sk -o /dev/null -w "HTTPS: %{http_code}\n" https://vapi.srv1738752.hstgr.cloud/api/vapi \
    -X POST -H "Content-Type: application/json" -d '{}'

echo "=== Step 6: Test auth ==="
curl -sk "https://vapi.srv1738752.hstgr.cloud/api/vapi" \
    -X POST -H "Content-Type: application/json" \
    -d '{"message":{"type":"tool-calls","toolCalls":[{"function":{"name":"authUser","arguments":{"name":"Shareef Frasier","pin":"3195"}}}]}}'

echo ""
echo "=== DONE ==="
echo "Permanent URL: https://vapi.srv1738752.hstgr.cloud/api/vapi"
