#!/bin/bash
# Convert bare-nohup static servers to supervised systemd units (Restart=always).
# Run on the VPS as root:
#   ssh root@147.93.113.241 'bash -s' < deploy-static-units.sh
# Ports/services: 8140 nursing-videos, 8141 manim-demos, 8142 masterb-pilot,
# 8143 animation-studio. Kills the session-scoped processes and lets systemd own them.
set -e

write_unit() {  # name, desc, port, root, script
  cat > /etc/systemd/system/$1.service <<U
[Unit]
Description=$2 (port $3)
After=network.target

[Service]
Type=simple
WorkingDirectory=$4
ExecStart=/usr/bin/python3 $5 $3 $4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
U
}

write_unit static-nursing-videos "Nursing Video Archive" 8140 /var/www/nursing-videos /opt/nursing-videos/range_server.py
write_unit static-manim-demos    "Manim test renders"   8141 /var/www/manim-demos    /opt/nursing-videos/range_server.py
write_unit static-masterb-pilot  "Master B pilot"       8142 /var/www/masterb-pilot  /opt/spa-range/spa_range_server.py
write_unit static-animation-studio "Animation Studio"   8143 /var/www/animation-studio /opt/spa-range/spa_range_server.py

systemctl daemon-reload

for port in 8140 8141 8142 8143; do
  PID=$(ss -tlnp 2>/dev/null | grep ":$port " | grep -o -E 'pid=[0-9]+' | head -1 | cut -d= -f2)
  if [ -n "$PID" ]; then
    echo "stopping existing process on $port (pid $PID)"
    kill "$PID" 2>/dev/null || true
    sleep 1
  fi
done

systemctl enable --now static-nursing-videos static-manim-demos static-masterb-pilot static-animation-studio
sleep 2
echo "=== status ==="
systemctl is-active static-nursing-videos static-manim-demos static-masterb-pilot static-animation-studio
echo "=== port checks ==="
for p in 8140 8141 8142 8143; do curl -s -o /dev/null -w "port $p -> %{http_code}\n" http://127.0.0.1:$p/; done
echo "=== domains ==="
for h in nursing-videos manim masterb-pilot animation-studio; do echo "-- $h:"; curl -sk -m 8 "https://$h.srv1738752.hstgr.cloud" | grep -o -i "<title>[^<]*" | head -1; done
echo "=== done ==="
