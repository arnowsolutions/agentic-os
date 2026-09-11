#!/usr/bin/env python3
"""
Importable wrapper around `send-report.py` (which contains a hyphen, so it
cannot be `import`ed by name directly).

Exposes:
    send_individual(resident_name, recipient) -> str
    get_resident_data(resident_name)          -> dict | None
    generate_pdf(data)                        -> str (path)

Used by the Telegram bot (telegram_reimb_bot.py) and any future VoIP/HTTP
trigger without duplicating the send logic.
"""
import importlib.util
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# Ensure the agentic-os SMTP credentials are in the process environment BEFORE
# smtp_sender.py runs its own load_dotenv(). This is CRITICAL: smtp_sender's
# load_dotenv() may pick up a stale/different SMTP_APP_PASSWORD (e.g. from
# ~/.hermes/.env) that Gmail rejects. We force the agentic-os value so it wins.
_AGENV = HERE / ".env"
if _AGENV.exists():
    for _line in _AGENV.read_text().splitlines():
        _line = _line.strip()
        if "=" in _line and not _line.startswith("#"):
            _k, _, _v = _line.partition("=")
            if _k.strip() in ("SMTP_USER", "SMTP_APP_PASSWORD", "SMTP_HOST", "SMTP_PORT"):
                os.environ[_k.strip()] = _v.strip().strip('"').strip("'")


def _load():
    path = HERE / "send-report.py"
    spec = importlib.util.spec_from_file_location("send_report_engine", path)
    mod = importlib.util.module_from_spec(spec)
    # Ensure sys.path has the agentic-os dir so its local imports resolve
    sys.path.insert(0, str(HERE))
    sys.path.insert(0, str(HERE.parent))
    spec.loader.exec_module(mod)
    return mod


_engine = _load()

send_individual = _engine.send_individual
get_resident_data = _engine.get_resident_data
generate_pdf = _engine.generate_pdf


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--resident", required=True)
    ap.add_argument("--email", default="sfrasier@montefiore.org")
    ap.add_argument("--year", default=None, help="Academic year (e.g. 2025-26) or 'all'")
    ap.add_argument("--dry-run", action="store_true", help="build PDF but don't send")
    a = ap.parse_args()

    data = get_resident_data(a.resident, a.year if a.year and a.year.lower() != "all" else None)
    if data is None:
        print(f"❌ Resident '{a.resident}' not found")
        sys.exit(1)
    scope = data.get('requested_year') or ("all years" if data.get('years') else "")
    print(f"Resident: {data['name']} ({data.get('cls','')})  GME remaining: ${data['gme_remaining']:,.2f}  scope: {scope}")
    if a.dry_run:
        pdf = generate_pdf(data)
        print(f"DRY-RUN pdf: {pdf}")
    else:
        print(send_individual(a.resident, a.email, a.year if a.year and a.year.lower() != "all" else None))
