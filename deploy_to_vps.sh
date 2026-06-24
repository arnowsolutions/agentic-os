#!/bin/bash
# Deploy Vapi server to VPS - run from the container
# This script SSHs into the VPS and sets up the Vapi FastAPI server

VPS_IP="147.93.113.241"
VPS_PASS="e't64)QQ#-aWExcT"
WORKSPACE="/var/lib/docker/volumes/hermes-webui-gsga_hermes-workspace/_data"

python3 -c "
import pexpect, time, sys

child = pexpect.spawn('ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@${VPS_IP}', timeout=120)
child.expect('password:', timeout=15)
child.sendline('${VPS_PASS}')
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

# Step 1: Install pip deps
print('Step 1: Installing Python packages...')
run('cd ${WORKSPACE} && .vapi-venv/bin/pip install fastapi uvicorn openpyxl pydantic httpx python-multipart 2>&1 | tail -3', timeout=60)

# Step 2: Test the server starts
print('Step 2: Testing server import...')
run('cd ${WORKSPACE} && .vapi-venv/bin/python3 -c \"from modules.vapi_bridge import router; print(\\\"Import OK\\\")\" 2>&1', timeout=15)

# Step 3: Start the server in background
print('Step 3: Starting Vapi server on port 8090...')
run('cd ${WORKSPACE} && nohup .vapi-venv/bin/python3 server.py --port 8090 --host 0.0.0.0 > /tmp/vapi-server.log 2>&1 &
echo \"PID: \$!\"', timeout=5)

# Step 4: Check if it's running
print('Step 4: Verifying server...')
time.sleep(3)
run('curl -s -o /dev/null -w \"%{http_code}\" http://localhost:8090/api/vapi -X POST -H \"Content-Type: application/json\" -d \\\"{}\\\" 2>/dev/null || echo \"NOT_YET\"', timeout=10)

child.sendline('exit')
child.expect(pexpect.EOF, timeout=5)
print('=== DONE ===')
" 2>&1