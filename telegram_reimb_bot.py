#!/usr/bin/env python3
"""
Telegram trigger for Montefiore Urology reimbursement-summary emails.

RESIDENT-TO-SELF ONLY (PHI/liability-safe policy).
A requested reimbursement summary is emailed ONLY to the resident's own
on-file CRM email address. It can NEVER be sent to an arbitrary/third-party
address. Commands:

    /reimbursement <Resident Name>   -> email that resident their OWN summary,
                                        to their on-file CRM email
    /reimbursement help              -> usage
    /reimbursement <Name> to <email> -> REFUSED (no arbitrary recipients)

Shareef may receive a copy only via the explicit test override (the single
address in REIMB_ADMIN_EMAIL, defaulting to sfrasier@montefiore.org, gated to
authorized Telegram chat IDs in TELEGRAM_ALLOWED_IDS) by appending "--to-admin".

The bot reads the resident summary from the UNIFIED DB and emails it (SMTP)
via the same engine (reimb_email_engine.py).

Setup (one-time):
  - Create a bot via @BotFather, put its token in /workspace/agentic-os/.env
    as  TELEGRAM_BOT_TOKEN=...
  - Set TELEGRAM_ALLOWED_IDS=<comma-separated numeric chat IDs> so only you
    (and anyone you add) can drive it. REQUIRED for production.
  - Optional REIMB_ADMIN_EMAIL (default sfrasier@montefiore.org).
  - Run:  python3 /workspace/agentic-os/telegram_reimb_bot.py
"""
import os
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Load the agentic-os .env from THIS directory (works on VPS volume path and
# local /workspace). SMTP creds + Telegram token come from here.
# ---------------------------------------------------------------------------
_ENV = _HERE / ".env"
if _ENV.exists():
    for line in _ENV.read_text().splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            k = k.strip()
            # Force SMTP_* so smtp_sender doesn't pick up a stale ~/.hermes value;
            # setdefault for the Telegram/email settings so any real process env
            # (set by PM2/systemd) still wins.
            if k in ("SMTP_USER", "SMTP_APP_PASSWORD", "SMTP_HOST", "SMTP_PORT"):
                os.environ[k] = v.strip().strip('"').strip("'")
            elif k in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_ALLOWED_IDS", "REIMB_ADMIN_EMAIL"):
                os.environ.setdefault(k, v.strip().strip('"').strip("'"))

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
ALLOWED_IDS = {int(x.strip()) for x in os.environ.get("TELEGRAM_ALLOWED_IDS", "").split(",") if x.strip().isdigit()}
ADMIN_EMAIL = os.environ.get("REIMB_ADMIN_EMAIL", "sfrasier@montefiore.org").strip().lower()

sys.path.insert(0, str(_HERE.parent))   # parent of agentic-os = workspace root
sys.path.insert(0, str(_HERE))          # agentic-os dir

from reimb_email_engine import (  # noqa: E402
    send_individual,
    get_resident_data,
)

# The single "to <email>" construct is explicitly disallowed (third-party send).
_REFUSE_MSG = ("⛔ Refusing: sending a reimbursement summary to an arbitrary "
               "address is not allowed (PHI/liability policy). "
               "It can only go to the resident's own on-file email.")


def _parse_resident(text: str) -> str:
    """Reduce a command text to just a resident name (year stripped). Returns '' if help."""
    t = text.strip().lstrip("/")
    while True:
        before = t
        t = re.sub(r"^(?:please|kindly|send|email|forward|the|a|for|of)\s+", "", t, flags=re.I)
        t = re.sub(r"^(?:reimbursement[ _-]?summary|reimb(?:ursement)?|summary)\s*", "", t, flags=re.I)
        if t == before:
            break
    return t.strip().strip("'\"")


def _split_year(text: str):
    """Return (resident_text, year_or_None). Recognizes '2025-26', '25/26',
    '2025', or the word 'all' as the requested academic year. The year must be a
    trailing token so a name like 'John Hill' is never mistaken for a year."""
    t = text.strip()
    # end-of-string academic year patterns
    m = re.search(r"(?:^|\s)(all|ALL|(?:19|20)?\d{2}[-/](?:19|20)?\d{2}|(?:19|20)?\d{2})\s*$", t)
    if m:
        tok = m.group(1)
        # a bare 4-digit year is a year only if it's clearly not a name middle (it's trailing)
        if tok.lower() == "all":
            return t[: m.start()].strip(), "all"
        # reject if the token could be part of a last name like '2000'? keep simple:
        return t[: m.start()].strip(), tok
    return t, None


def handle(text: str) -> str:
    """Handle a single command text, return a reply string (may send email)."""
    raw = text.strip()

    # --- refuse any arbitrary-address attempt before doing anything ---
    if re.search(r"\bto\s+[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b", raw, flags=re.I):
        # Allow ONLY the explicit admin copy syntax "--to-admin"
        if "--to-admin" not in raw.lower():
            return _REFUSE_MSG
        # still require the resident, and strip the control token
        raw = raw.lower().replace("--to-admin", " ").strip()

    to_admin = "--to-admin" in text.strip().lower()

    name_part, year = _split_year(raw)
    t = _parse_resident(name_part)
    if not t or t.lower() in ("help", "?", "usage"):
        return ("Usage (resident-to-self only):\n"
                "  /reimbursement <Resident Name>\n"
                "     -> emails that resident their own summary, to their on-file CRM email\n"
                "  /reimbursement <Name> [<Year>|all]\n"
                "     -> optionally filter to an academic year (e.g. 2025-26) or 'all'\n"
                "  /reimbursement <Name> --to-admin\n"
                "     -> also makes a copy to the admin address (REIMB_ADMIN_EMAIL)\n"
                "Arbitrary 'send to <email>' is blocked by policy.")

    resident = t
    data = get_resident_data(resident, year)
    if not data:
        return f"❌ Could not find resident '{resident}' in the system."

    onfile = (data.get("email") or "").strip().lower()
    if not onfile:
        return (f"⛔ No on-file email for {data['name']} in the CRM, so I won't send "
                "(I never guess an address). Ask Shareef to add it first.")

    sends = [onfile]
    if to_admin:
        # Always ALSO send to the admin override so Shareef can preview.
        # The admin address is a fixed, single value — not user-supplied.
        sends.append(ADMIN_EMAIL)

    results = []
    for addr in sends:
        try:
            r = send_individual(data["name"], addr, year)
            results.append(f"{addr}: {r}")
        except Exception as e:
            results.append(f"{addr}: ❌ {type(e).__name__}: {str(e)[:200]}")

    scope = data.get('requested_year') or ("all years" if data.get('years') else "")
    return ("📧 " + "\n".join(results) +
            f"\nResident: {data['name']} ({data.get('cls','')})"
            f"\nGME remaining (requested scope): ${data['gme_remaining']:,.2f}"
            f"\nOn-file email: {onfile}"
            + (f"\nScope: {scope}" if scope else ""))


def main() -> int:
    if not TOKEN:
        print("TELEGRAM_BOT_TOKEN not set in /workspace/agentic-os/.env")
        return 1
    try:
        import telebot
    except Exception as e:
        print("pip install pyTelegramBotAPI (module 'telebot') first.", e)
        return 1

    import telebot as tb
    bot = tb.TeleBot(TOKEN)

    @bot.message_handler(commands=["reimbursement", "reimb", "start", "help"])
    def on_cmd(msg):
        chat_id = msg.chat.id
        if ALLOWED_IDS and chat_id not in ALLOWED_IDS:
            bot.reply_to(msg, "Not authorized.")
            return
        text = (msg.text or "")
        # strip the leading /command
        parts = text.split(None, 1)
        body = parts[1] if len(parts) > 1 else ""
        if parts and parts[0].lstrip("/").lower() in ("start", "help"):
            body = "help"
        reply = handle(body or "help")
        try:
            bot.send_message(chat_id, reply)
        except Exception as e:
            print("send failed:", e)

    print(f"Telegram reimb bot running (allowed={sorted(ALLOWED_IDS) or 'ANY'}) ...")
    bot.infinity_polling(timeout=60)
    return 0


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser("Telegram reimbursement-email bot")
    ap.add_argument("--once", metavar="MSG", help="process one message and exit (for cron/testing)")
    a = ap.parse_args()
    if a.once:
        print(handle(a.once))
        sys.exit(0)
    sys.exit(main())
