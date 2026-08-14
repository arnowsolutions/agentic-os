#!/bin/bash
# Deploy updated Agentic OS to VPS - restart the server on port 8090
# Password read from vps_config.json, NOT hardcoded
VPS_IP="147.93.113.241"
WORKSPACE="/var/lib/docker/volumes/hermes-webui-gsga_hermes-workspace/_data"

VPS_PASS=$(python3 -c "import json; print(json.load(open('/workspace/agentic-os/data/vps_config.json'))['password'])")

python3 << 'PYEOF'
import pexpect, time, sys, os

vps_ip = os.environ.get("VPS_IP", "147.93.113.241")
vps_pass = os.environ.get("VPS_PASS", "")
workspace = "/var/lib/docker/volumes/hermes-webui-gsga_hermes-workspace/_data"

child = pexpect.spawn(f'ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@{vps_ip}', timeout=120)
child.expect('password:', timeout=15)
child.sendline(vps_pass)
child.expect('root@', timeout=10)

def run(cmd, timeout=30):
    child.sendline(cmd)
    time.sleep(1)
    i = child.expect(['root@', pexpect.TIMEOUT], timeout=timeout)
    out = child.before.decode()
    for line in out.split(chr(10)):
        l = line.strip()
        if l and 'root@' not in l and cmd.strip() not in l and len(l) > 3:
            if 'error' in l.lower() or 'Error' in l:
                print(f'  ERROR: {l[:150]}')
    return i == 0

print('Step 1: Stopping old server...')
run(f'fuser -k 8090/tcp 2>/dev/null; sleep 2', timeout=10)

print('Step 2: Starting new server...')
run(f'cd {workspace}/agentic-os && nohup /app/venv/bin/python3 server.py --port 8090 --host 0.0.0.0 > /tmp/aos-server.log 2>&1 &', timeout=5)

print('Step 3: Waiting for server...')
time.sleep(5)

print('Step 4: Verifying endpoints...')
run(f'curl -s http://localhost:8090/api/compliance/overview', timeout=10)
run(f'curl -s http://localhost:8090/api/morning-briefing', timeout=10)
run(f'curl -s http://localhost:8090/api/notifications', timeout=10)

child.sendline('exit')
child.expect(pexpect.EOF, timeout=5)
print('=== RESTART COMPLETE ===')
PYEOF
