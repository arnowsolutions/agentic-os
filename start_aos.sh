#!/usr/bin/env bash
# Agentic OS auto-restart wrapper — keeps the server alive.
# Usage: bash start_aos.sh [port] [host]
# If the server crashes, it restarts after a 3-second delay.
# Logs go to /tmp/agentic-os.log

PORT="${1:-8090}"
HOST="${2:-0.0.0.0}"
LOGFILE="/tmp/agentic-os.log"
RESTART_DELAY=3

cd /workspace/agentic-os

echo "[$(date -Iseconds)] Agentic OS starting on ${HOST}:${PORT}" | tee -a "$LOGFILE"

while true; do
  /app/venv/bin/python3 -B server.py --port "$PORT" --host "$HOST" >> "$LOGFILE" 2>&1
  EXIT_CODE=$?
  echo "[$(date -Iseconds)] Server exited with code ${EXIT_CODE}. Restarting in ${RESTART_DELAY}s..." | tee -a "$LOGFILE"
  sleep $RESTART_DELAY
done
