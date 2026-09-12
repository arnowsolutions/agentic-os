#!/bin/bash
# PR: therec / tc-report / ce-full routing fix — run on the VPS as root.
#   ssh root@147.93.113.241 'bash -s' < deploy-fixes-20260912.sh
# Reversible: backups of all three traefik files are kept as *.bak-20260912.
set -e

echo "=== backups ==="
cd /docker/traefik && for f in therec tc-report ce-full; do cp -n $f.yml $f.yml.bak-20260912 || true; done && ls -la *.bak-20260912 | tail -5

echo "=== tc-report content dir ==="
mkdir -p /var/www/tc-report
cp -n /var/www/ce-full-report/trade-compass-index.html /var/www/tc-report/index.html
ls -la /var/www/tc-report/

echo "=== write units ==="
cat > /etc/systemd/system/static-therec.service <<'U'
[Unit]
Description=The Rec static site (port 8145)
After=network.target

[Service]
Type=simple
WorkingDirectory=/var/www/therec
ExecStart=/usr/bin/python3 /opt/scripts/static-server.py 8145 /var/www/therec
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
U
cat > /etc/systemd/system/static-tc-report.service <<'U'
[Unit]
Description=Trade Compass report (port 8146)
After=network.target

[Service]
Type=simple
WorkingDirectory=/var/www/tc-report
ExecStart=/usr/bin/python3 /opt/scripts/static-server.py 8146 /var/www/tc-report
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
U
cat > /etc/systemd/system/static-ce-full.service <<'U'
[Unit]
Description=CE:FULL report (port 8147)
After=network.target

[Service]
Type=simple
WorkingDirectory=/var/www/ce-full-report
ExecStart=/usr/bin/python3 /opt/scripts/static-server.py 8147 /var/www/ce-full-report
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
U

systemctl daemon-reload
systemctl enable --now static-therec.service static-tc-report.service static-ce-full.service
sleep 2
echo "units:"; systemctl is-active static-therec static-tc-report static-ce-full

echo "=== local checks ==="
for p in 8145 8146 8147; do curl -s -o /dev/null -w "port $p -> %{http_code}\n" http://127.0.0.1:$p/; done

echo "=== traefik rewrites ==="
cat > /docker/traefik/therec.yml <<'Y'
http:
  routers:
    therec:
      rule: "Host(`therec.srv1738752.hstgr.cloud`)"
      entrypoints:
        - websecure
      tls:
        certresolver: letsencrypt
      service: therec-backend
    therec-http:
      rule: "Host(`therec.srv1738752.hstgr.cloud`)"
      entrypoints:
        - web
      service: therec-backend
  services:
    therec-backend:
      loadBalancer:
        servers:
          - url: "http://127.0.0.1:8145"
Y
cat > /docker/traefik/tc-report.yml <<'Y'
http:
  routers:
    tradecompass-report:
      rule: "Host(`tc-report.srv1738752.hstgr.cloud`)"
      entrypoints:
        - websecure
      tls:
        certresolver: letsencrypt
      service: tradecompass-report-backend
  services:
    tradecompass-report-backend:
      loadBalancer:
        servers:
          - url: "http://127.0.0.1:8146"
Y
cat > /docker/traefik/ce-full.yml <<'Y'
http:
  routers:
    ce-full:
      rule: "Host(`ce-full.srv1738752.hstgr.cloud`)"
      entrypoints:
        - websecure
      tls:
        certresolver: letsencrypt
      service: ce-full
  services:
    ce-full:
      loadBalancer:
        servers:
          - url: "http://127.0.0.1:8147"
Y

echo "=== wait for traefik file-watch, then domain checks ==="
sleep 6
for h in therec tc-report ce-full; do echo "-- $h:"; curl -sk -m 8 "https://$h.srv1738752.hstgr.cloud" | grep -o -i "<title>[^<]*" | head -1; done

echo "=== if titles are still wrong, reload traefik once: ==="
echo "  docker restart traefik-traefik-1 && sleep 6"
echo "=== done ==="
