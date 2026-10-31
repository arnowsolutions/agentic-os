#!/usr/bin/env bash
# Arnow Solutions — Portfolio publish
# Rebuilds the HTML report from notes/projects and deploys it to the live URL:
#   https://unified.srv1738752.hstgr.cloud/portfolio.html
#
# Usage:  bin/publish_portfolio.sh   (or  ./publish_portfolio.sh from agentic-os root)
set -euo pipefail

cd "$(dirname "$0")/.."   # agentic-os root

VPS_HOST="root@147.93.113.241"
VPS_PATH="/var/www/unified/dist/portfolio.html"
PUBLIC_URL="https://unified.srv1738752.hstgr.cloud/portfolio.html"

echo "[1/4] Rebuilding markdown report…"
python3 portfolio_report.py >/dev/null

echo "[2/4] Building HTML…"
python3 portfolio_html.py

HTML="data/portfolio/reports/portfolio.html"
if [ ! -f "$HTML" ]; then
  echo "ERROR: $HTML not found" >&2
  exit 1
fi

echo "[3/4] Deploying to VPS…"
ssh -o BatchMode=yes -o ConnectTimeout=12 -o StrictHostKeyChecking=no "$VPS_HOST" \
  "cat > $VPS_PATH" < "$HTML"

echo "[4/4] Verifying…"
CODE=$(curl -s -o /dev/null -m 20 -w "%{http_code}" "$PUBLIC_URL")
if [ "$CODE" = "200" ]; then
  echo "✅ Live: $PUBLIC_URL  (HTTP $CODE)"
else
  echo "⚠️  Deployed but verification returned HTTP $CODE" >&2
  exit 1
fi
