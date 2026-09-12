#!/bin/bash
# ══════════════════════════════════════════════════════════════════════
# AOS restart + verification  (run from the agent after user approval)
# Restarts the agentic-os container (picks up server.py + modules/crm.py
# fixes: staff-schedule endpoint + GME tracker -> unified data).
# The static dashboard files are already live via the shared volume.
# ══════════════════════════════════════════════════════════════════════
set -e
V=root@147.93.113.241

echo "── 1) restart agentic-os"
ssh -o BatchMode=yes $V "docker restart hermes-webui-gsga-agentic-os-1"
sleep 10

echo "── 2) staff-schedule via public domain (was 500)"
curl -sk --max-time 20 "https://os.srv1738752.hstgr.cloud/api/staff-schedule?hospital=Moses" \
  -o /tmp/ss.json -w "staff HTTP %{http_code}\n"
python3 -c "import json; d=json.load(open('/tmp/ss.json')); print('Moses total:', d.get('total'), '| first:', (d.get('staff') or [{}])[0].get('name'))"

echo "── 3) GME endpoints (in-container, real data)"
ssh -o BatchMode=yes $V 'docker exec -i hermes-webui-gsga-agentic-os-1 sh -c "cd /workspace/agentic-os 2>/dev/null || cd /app; python3 -"' < /tmp/verify_gme.py

echo "── 4) container logs tail"
ssh -o BatchMode=yes $V "docker logs --tail 5 hermes-webui-gsga-agentic-os-1 2>&1 | tail -5"
echo "DONE"
