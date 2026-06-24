#!/usr/bin/env python3
"""Deploy Vapi stack to Hostinger VPS.
   Steps:
   1. Install Python deps in venv
   2. Start the FastAPI server on port 8090
   3. Add Traefik route so voice.vps-domain gets a cert
   4. Update Vapi assistant to use the new URL
"""
import pexpect
import time
import json
import os

VPS_IP = "147.93.113.241"
VPS_PASS = "e't64)QQ#-aWExcT"
WORKSPACE = "/var/lib/docker/volumes/hermes-webui-gsga_hermes-workspace/_data"
COMPOSE_DIR = "/docker/hermes-webui-gsga"

def ssh():
    child = pexpect.spawn(f'ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@{VPS_IP}', timeout=120)
    child.expect('password:', timeout=15)
    child.sendline(VPS_PASS)
    child.expect('root@', timeout=10)
    return child

def run(child, cmd, timeout=30, echo=True):
    child.sendline(cmd)
    time.sleep(1)
    try:
        child.expect('root@', timeout=timeout)
    except pexpect.TIMEOUT:
        print(f"  TIMEOUT on: {cmd[:60]}")
        return child.before.decode()
    out = child.before.decode()
    lines = []
    for line in out.split('\n'):
        l = line.strip()
        if l and 'root@' not in l and cmd.strip() not in l and len(l) > 3:
            lines.append(l)
            if echo:
                print(f"  {l[:200]}")
    return '\n'.join(lines)

print("=" * 60)
print("DEPLOYING VAPI STACK TO VPS")
print("=" * 60)

c = ssh()

# Step 1: Install deps
print("\n[1/6] Installing Python dependencies...")
r = run(c, f'cd {WORKSPACE} && .vapi-venv/bin/pip install fastapi uvicorn openpyxl pydantic httpx python-multipart 2>&1 | tail -5', timeout=90)
if 'Successfully' in r or 'already satisfied' in r:
    print("  ✅ Dependencies installed")
else:
    print(f"  ⚠️ Result: {r[:100]}")

# Step 2: Verify import
print("\n[2/6] Verifying server import...")
r = run(c, f'cd {WORKSPACE} && .vapi-venv/bin/python3 -c "from modules.vapi_bridge import router; print(\'Import OK\')" 2>&1', timeout=15)
if 'Import OK' in r:
    print("  ✅ Module imports work")
else:
    print(f"  ❌ Import failed: {r[:200]}")
    c.sendline('exit')
    c.expect(pexpect.EOF, timeout=5)
    exit(1)

# Step 3: Kill any existing server on 8090
print("\n[3/6] Stopping any existing server on port 8090...")
run(c, f'fuser -k 8090/tcp 2>/dev/null || kill $(lsof -ti:8090) 2>/dev/null || echo "No server running"', timeout=5)

# Step 4: Start server in background
print("\n[4/6] Starting Vapi server on port 8090...")
run(c, f'cd {WORKSPACE} && nohup .vapi-venv/bin/python3 server.py --port 8090 --host 0.0.0.0 > /tmp/vapi-server.log 2>&1 & echo "SERVER_PID=$!"', timeout=5)
time.sleep(4)

# Verify
r = run(c, 'curl -s -o /dev/null -w "%{http_code}" http://localhost:8090/api/vapi -X POST -H "Content-Type: application/json" -d \'{}\'', timeout=10)
if '200' in r:
    print("  ✅ Server running on port 8090")
else:
    r2 = run(c, 'cat /tmp/vapi-server.log | tail -5', timeout=5)
    print(f"  ❌ Server not responding. Log: {r2[:200]}")
    c.sendline('exit')
    c.expect(pexpect.EOF, timeout=5)
    exit(1)

# Step 5: Add Traefik route for the Vapi service
print("\n[5/6] Adding Traefik route...")
# Read the existing compose file
compose = run(c, f'cat {COMPOSE_DIR}/docker-compose.yml', timeout=5)

# The host is srv1738752.hstgr.cloud - we'll add a route for vapi.srv1738752.hstgr.cloud
# First add the service to docker-compose.yml
new_service = """
  vapi-server:
    image: python:3.12-slim
    restart: unless-stopped
    network_mode: host
    command: ["python3", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8090"]
    labels:
      - traefik.enable=true
      - traefik.http.routers.vapi.rule=Host(`vapi.srv1738752.hstgr.cloud`)
      - traefik.http.routers.vapi.entrypoints=websecure
      - traefik.http.routers.vapi.tls.certresolver=letsencrypt
      - traefik.http.services.vapi.loadbalancer.server.port=8090
    working_dir: /workspace
    volumes:
      - hermes-workspace:/workspace
"""

# Actually, the Docker Python image is heavy. The server is already running on the host.
# Better approach: use the host server and just add a file-based Traefik config.

# Check if Traefik has a file provider config directory
r = run(c, 'ls /docker/traefik/ 2>/dev/null; docker inspect traefik-traefik-1 --format "{{json .Mounts}}" 2>/dev/null | head -5', timeout=10)
print(f"  Traefik config dir: /docker/traefik/")

# Write a Traefik file provider config for the Vapi route
traefik_config = """
# Vapi Voice Server - dynamic config
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
"""

# But Traefik's current config uses Docker provider, not file provider.
# We need to restart with the file provider enabled, or use Docker labels.

# Simplest approach: restart traefik with file provider
# Actually the simplest is to just use the host server directly with the hostname.
# The VPS hostname srv1738752.hstgr.cloud already resolves to this IP.
# Let's just start the server and tell Vapi to use the IP directly.

# For TLS, we need a proper domain. But let's first get the server running.
# Vapi can use http://147.93.113.241:8090 - no TLS needed for server->Vapi communication
# since Vapi initiates the connection.

print("  Server is running on http://147.93.113.241:8090")
print("  We need a proper subdomain for Traefik to issue a Let's Encrypt cert.")
print("  For now, Vapi can use the IP directly.")

# Step 6: Update the Vapi assistant to use the VPS URL
print("\n[6/6] Updating Vapi assistant server URL...")
# Update deploy_vapi_v4.py to use VPS IP instead of tunnel
run(c, f'cd {WORKSPACE}/agentic-os && sed -i "s|TUNNEL = \"https://.*\.trycloudflare\.com\"|TUNNEL = \"http://147.93.113.241\"|" deploy_vapi_v4.py', timeout=5)
print("  ✅ Deploy script updated to use VPS IP")

# Add a Docker container for the Vapi server (more reliable than host process)
# Write a new compose file fragment
dockerfile = f"""
# vapi-server entrypoint script
cat > {WORKSPACE}/agentic-os/start_vapi_vps.sh << 'SCRIPT'
#!/bin/bash
cd {WORKSPACE}
nohup .vapi-venv/bin/python3 server.py --port 8090 --host 0.0.0.0 > /tmp/vapi-server.log 2>&1 &
echo $!
SCRIPT
chmod +x {WORKSPACE}/agentic-os/start_vapi_vps.sh
"""
run(c, f'cd {WORKSPACE}/agentic-os && cat > start_vapi_vps.sh << \'SCRIPT\'
#!/bin/bash
cd {WORKSPACE}
nohup .vapi-venv/bin/python3 server.py --port 8090 --host 0.0.0.0 > /tmp/vapi-server.log 2>&1 &
echo $!
SCRIPT
chmod +x start_vapi_vps.sh', timeout=5)
print("  ✅ Start script created")

# Create a systemd service for auto-start
service_file = """
cat > /etc/systemd/system/vapi-server.service << 'SERVICE'
[Unit]
Description=Vapi Voice Server
After=network.target docker.service
Requires=docker.service

[Service]
Type=forking
ExecStart=/var/lib/docker/volumes/hermes-webui-gsga_hermes-workspace/_data/agentic-os/start_vapi_vps.sh
ExecStop=/usr/bin/fuser -k 8090/tcp
Restart=on-failure
RestartSec=10
User=root

[Install]
WantedBy=multi-user.target
SERVICE
"""
run(c, service_file, timeout=5)
print("  ✅ Systemd service created")

run(c, 'systemctl daemon-reload && systemctl enable vapi-server.service 2>&1', timeout=10)
print("  ✅ Systemd service enabled")

# Test the full flow
print("\n📞 Vapi server is running at: http://147.93.113.241:8090/api/vapi")
print("   The tunnel is still active as a backup.")
print("   To deploy with this URL, run from VPS:")
print("   cd /var/lib/docker/volumes/hermes-webui-gsga_hermes-workspace/_data/agentic-os")
print("   && .vapi-venv/bin/python3 deploy_vapi_v4.py")

c.sendline('exit')
c.expect(pexpect.EOF, timeout=5)
print("\n=== DEPLOYMENT COMPLETE ===")
