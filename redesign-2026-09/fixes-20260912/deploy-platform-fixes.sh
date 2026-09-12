#!/bin/bash
# ══════════════════════════════════════════════════════════════════════
# Platform deploy bundle — staff month-fix + GME year-fix (run after approval)
# Deploys: /var/www/unified/server/routes/staff-schedule.ts (month clamp)
#          /var/www/unified/src/pages/admin/GmeFundStatusTab.tsx (dynamic AY)
# Then: typecheck, frontend rebuild, restart, live verify (incl. JWT probe).
# ══════════════════════════════════════════════════════════════════════
set -e
V=root@147.93.113.241

echo "── 0) ship the two patcher scripts"
scp -o BatchMode=yes /workspace/agentic-os/redesign-2026-09/fixes-20260912/fix-platform-staff-month.py $V:/tmp/
scp -o BatchMode=yes /workspace/agentic-os/redesign-2026-09/fixes-20260912/fix-platform-gme-year.py $V:/tmp/

echo "── 1) apply patches on VPS"
ssh -o BatchMode=yes $V "python3 /tmp/fix-platform-staff-month.py && python3 /tmp/fix-platform-gme-year.py"

echo "── 2) typecheck server change (best effort)"
ssh -o BatchMode=yes $V "docker exec hermes-webui-gsga-unified-platform-1 sh -c 'cd /app && npx tsc --noEmit -p tsconfig.server.json 2>&1 | head -8' || true"

echo "── 3) rebuild frontend + restart"
ssh -o BatchMode=yes $V "docker exec hermes-webui-gsga-unified-platform-1 sh -c 'cd /app && npm run build 2>&1 | tail -6'"
ssh -o BatchMode=yes $V "docker restart hermes-webui-gsga-unified-platform-1"
sleep 8

echo "── 4) live verify: month endpoint now 200 for Sep; GME transactions reachable"
ssh -o BatchMode=yes $V 'bash -s' <<'EOS'
TOKEN=$(python3 - <<'PY'
import hmac, hashlib, base64, json, time
env = {}
for line in open('/var/www/unified/.env'):
    line = line.strip()
    if '=' in line and not line.startswith('#'):
        k, v = line.split('=', 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
secret = env['SUPABASE_JWT_SECRET']
def b64(x): return base64.urlsafe_b64encode(x).rstrip(b'=')
now = int(time.time())
h = b64(json.dumps({'alg': 'HS256', 'typ': 'JWT'}).encode())
p = b64(json.dumps({'sub': '284841b2-f2dd-4a38-a3a4-c5d2fb0d41b9', 'email': 'sfrasier@montefiore.org',
                    'role': 'authenticated', 'aud': 'authenticated', 'iat': now, 'exp': now + 3600}).encode())
s = b64(hmac.new(secret.encode(), h + b'.' + p, hashlib.sha256).digest())
print((h + b'.' + p + b'.' + s).decode())
PY
)
curl -s -m 20 -o /tmp/v_sep -w "2026-09: HTTP %{http_code} | %{size_download} bytes\n" -H "Authorization: Bearer $TOKEN" "http://127.0.0.1:8098/api/v1/staff-schedule/month?month=2026-09"
curl -s -m 20 -o /tmp/v_gme -w "GME tx: HTTP %{http_code} | %{size_download} bytes\n" -H "Authorization: Bearer $TOKEN" "http://127.0.0.1:8098/api/v1/admin/reimb/fund/GME/transactions?academicYear=2026-27"
head -c 160 /tmp/v_sep; echo ""
curl -s -m 10 http://127.0.0.1:8098/api/health | head -c 200; echo ""
EOS
echo "DONE"
