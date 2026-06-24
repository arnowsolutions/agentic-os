#!/usr/bin/env bash
# Start Agentic OS Dashboard
set -euo pipefail

cd /workspace/agentic-os

# Get port from settings
PORT=$(python3 -c "
import json
d = json.load(open('data/settings.json'))
print(d.get('dashboard', {}).get('port', 8081))
" 2>/dev/null || echo "8081")

echo "Starting Agentic OS Dashboard on port ${PORT}..."
echo "Dashboard: http://172.16.1.3:${PORT}"
echo ""

exec python3 server.py --port "${PORT}"
