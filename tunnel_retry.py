#!/usr/bin/env python3
"""Persistent tunnel retry — runs until tunnel is established and verified."""
import paramiko, json, time, sys, os

config = json.load(open('/workspace/agentic-os/data/vps_config.json'))

MAX_RETRIES = 30
for attempt in range(1, MAX_RETRIES + 1):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect('147.93.113.241', username='root', password=config['password'], timeout=15)
        
        # Check current state
        stdin, stdout, stderr = ssh.exec_command('systemctl is-active vapi-tunnel.service')
        status = stdout.read().decode().strip()
        
        if status != 'active':
            # Reset and start
            ssh.exec_command('systemctl reset-failed vapi-tunnel.service')
            ssh.exec_command('systemctl start vapi-tunnel.service')
        
        # Wait for tunnel
        time.sleep(15)
        
        # Check tunnel log for URL
        stdin, stdout, stderr = ssh.exec_command('grep -o "https://[a-z0-9.-]*\\.trycloudflare\\.com" /tmp/vapi_tunnel.log 2>/dev/null | tail -1')
        url = stdout.read().decode().strip()
        
        stdin, stdout, stderr = ssh.exec_command('systemctl is-active vapi-tunnel.service')
        status = stdout.read().decode().strip()
        
        if url and status == 'active':
            # Write URL
            with open('/workspace/agentic-os/tunnel_url.txt', 'w') as f:
                f.write(url + '\n')
            
            # Test from container
            import subprocess
            r = subprocess.run(['curl', '-s', '--max-time', '10', f'{url}/vapi/auth',
                              '-H', 'Content-Type: application/json',
                              '-d', '{"name":"Shareef Frasier","pin":"1279"}'],
                             capture_output=True, text=True, timeout=15)
            
            if '"verified":true' in r.stdout:
                # Deploy
                os.system('/app/venv/bin/python3 /workspace/agentic-os/deploy_vapi_v5.py')
                print(f'TUNNEL_OK: {url}')
                sys.exit(0)
            elif '1033' in r.stdout:
                print(f'Attempt {attempt}: tunnel active but CF not propagated yet ({url})')
            else:
                print(f'Attempt {attempt}: unexpected response from {url}')
        else:
            stdin, stdout, stderr = ssh.exec_command('tail -3 /tmp/vapi_tunnel.log 2>/dev/null')
            log = stdout.read().decode().strip()
            if '429' in log:
                print(f'Attempt {attempt}: rate limited (429), waiting...')
            else:
                print(f'Attempt {attempt}: {status} - no URL yet')
        
        ssh.close()
    except Exception as e:
        print(f'Attempt {attempt}: error: {e}')
    
    time.sleep(20)

print('TUNNEL_FAILED: max retries exceeded')
sys.exit(1)
