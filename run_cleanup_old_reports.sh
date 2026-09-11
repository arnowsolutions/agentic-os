#!/bin/bash
# Cron wrapper for cleanup_old_reports.py — runs under default Hermes home with correct interpreter
export HERMES_HOME=/home/hermeswebui/.hermes
export HOME=/home/hermeswebui
exec /workspace/.aos-venv/bin/python3 "/home/hermeswebui/.hermes/scripts/cleanup_old_reports.py" "$@"
