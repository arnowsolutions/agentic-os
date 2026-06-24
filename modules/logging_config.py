"""Structured JSON logging setup used across the Agentic OS voice stack."""
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from modules.config import get_settings


class _JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "extra"):
            payload.update(record.extra)
        return json.dumps(payload, default=str)


def setup_logging() -> logging.Logger:
    """Configure root application logging to file and stderr."""
    settings = get_settings()
    settings.LOG_DIR.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger("agentic_os")
    root.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    if root.handlers:
        return root

    # Structured file handler (rotated by logrotate/external)
    file_handler = logging.FileHandler(settings.APP_LOG_FILE)
    file_handler.setFormatter(_JSONFormatter())
    root.addHandler(file_handler)

    # Human-readable stderr handler
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )
    root.addHandler(stderr_handler)

    return root


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def audit_record(event_type: str, **fields):
    """Append a structured audit record to the audit log file."""
    settings = get_settings()
    settings.LOG_DIR.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event_type,
        **fields,
    }
    try:
        with open(settings.AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=str) + "\n")
    except Exception as e:
        logging.getLogger("agentic_os").error("audit write failed", extra={"error": str(e)})
