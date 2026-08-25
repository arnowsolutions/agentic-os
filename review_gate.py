#!/usr/bin/env python3
"""
review_gate.py — Review-before-send gate for ONE-OFF agent-composed outbound emails.

WHY THIS EXISTS (Shareef, 2026-08-21):
An autonomous agent composed and emailed Dr. Schoenberg about a Sub-I exit
interview at ~5am and Shareef never saw the message before it went out. He wants
to review/approve every agent-written one-off outbound email first (student +
Dr. Schoenberg, availability requests, etc.), while automated reports/briefings
stay as-is.

FLOW:
  1. Agent composes the outbound email and calls:
        python3 review_gate.py --draft \
            --to "student@x.edu" --cc "mschoenb@montefiore.org" \
            --subject "..." --body "..." [--html] [--attach FILE ...]
     This ONLY queues the draft (writes data/pending_review/<id>.json) and
     emails Shareef a preview of EXACTLY what will go out. NOTHING is sent to
     the real recipient(s) yet.
  2. Shareef reviews the preview and says "approve".
  3. Then (an agent or Shareef) runs:
        python3 review_gate.py --approve <id>
     Only NOW is the email delivered to the real recipient(s) via SMTP.
  4. Optionally, a pending draft can be cancelled:
        python3 review_gate.py --reject <id>

EVERY delivery (approved sends) is appended to data/outbound_email_log.json.

Modes:
  --draft       queue the email and email Shareef a preview. never sends.
  --approve ID  deliver a queued draft to its real recipients.
  --reject ID   remove a queued draft without sending.
  --list        show pending drafts.
"""
import argparse, json, os, sys, time, uuid
from pathlib import Path

BASE = Path(__file__).resolve().parent
QUEUE_DIR = BASE / "data" / "pending_review"
LOG_FILE = BASE / "data" / "outbound_email_log.json"
PREVIEW_TO = "sfrasier@montefiore.org"  # Shareef's review inbox

sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / "modules"))

# Load SMTP creds into env (single source: ~/.hermes/scripts/.smtp.env),
# stripping the spaces in the Gmail app password (proven fix in task_notifier).
_ENV_CANDIDATES = [
    Path.home() / ".hermes" / "scripts" / ".smtp.env",
    Path("/home/hermeswebui/.hermes/scripts/.smtp.env"),
    Path("/home/hermes/.hermes/scripts/.smtp.env"),
]
for _p in _ENV_CANDIDATES:
    if _p.exists():
        for _line in _p.read_text().splitlines():
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                _v = _v.strip()
                if _k.strip() == "SMTP_APP_PASSWORD":
                    _v = _v.replace(" ", "")
                if _k.strip():
                    os.environ[_k.strip()] = _v
        break


def _load_smtp_env():
    """Read SMTP config the same way smtp_send.py does (single source)."""
    cfg = {}
    candidates = [
        Path.home() / ".hermes" / "scripts" / ".smtp.env",
        Path("/home/hermeswebui/.hermes/scripts/.smtp.env"),
        Path("/home/hermes/.hermes/scripts/.smtp.env"),
    ]
    p = next((c for c in candidates if c.exists()), None)
    if not p:
        return cfg
    for line in p.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip()
    return cfg


def _deliver(to, cc, subject, body, html, attachments):
    """Actually send via SMTP (space-stripped app password — the proven path)."""
    from modules.smtp_sender import send_email
    cc_list = [c for c in (cc or "").split(",") if c.strip()]
    auth_ok = os.environ.get("SMTP_APP_PASSWORD")
    # Strip spaces from the Gmail app password (same fix task_notifier uses)
    if auth_ok:
        os.environ["SMTP_APP_PASSWORD"] = auth_ok.replace(" ", "")
    res = send_email(to=to, subject=subject, body=body,
                     cc=cc_list, attachments=attachments, is_html=html)
    if res.get("successful"):
        return res.get("data", {}).get("id", "sent")
    raise RuntimeError(f"send failed: {res.get('error')}")


def _send_preview(draft):
    """Email Shareef a preview of the queued draft (cc/recipients/body)."""
    from modules.smtp_sender import send_email
    cc = "".join(f"<li>{c.strip()}</li>" for c in (draft.get("cc") or "").split(",") if c.strip())
    att = "".join(f"<li>{a}</li>" for a in (draft.get("attachments") or []))
    preview = f"""
<html><body style="font-family:'Segoe UI',Arial,sans-serif;max-width:640px;">
<h2 style="color:#1a3a5c">📬 REVIEW BEFORE SEND — {draft['id'][:8]}</h2>
<p>An agent drafted this outbound email. It has <b>NOT</b> been sent. Approve it below.</p>
<p><b>To:</b> {draft['to']}<br/><b>Cc:</b> {draft.get('cc') or '(none)'}</p>
<p><b>Subject:</b> {draft['subject']}</p>
<p><b>Attachments:</b> {att or '(none)'}</p>
<hr/>
{body_to_html(draft['body']) if draft.get('html') else draft['body']}
<hr/>
<p style="font-size:12px;color:#666">
To send:  python3 /workspace/agentic-os/review_gate.py --approve {draft['id']}<br/>
To cancel: python3 /workspace/agentic-os/review_gate.py --reject  {draft['id']}
</p>
</body></html>"""
    r = send_email(to=PREVIEW_TO, subject=f"[REVIEW] {draft['subject']}", body=preview, is_html=True)
    return r.get("successful", False)


def body_to_html(text):
    return "<br/>".join(str(text).split("\n"))


def _write_log(entry):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    logs = []
    if LOG_FILE.exists():
        try:
            logs = json.loads(LOG_FILE.read_text())
        except Exception:
            logs = []
    logs.append(entry)
    LOG_FILE.write_text(json.dumps(logs, indent=2))


def do_draft(args):
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    did = time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]
    draft = {
        "id": did, "created": time.time(), "status": "pending",
        "to": args.to, "cc": args.cc or "", "subject": args.subject,
        "body": args.body, "html": args.html, "attachments": args.attach or [],
    }
    q = QUEUE_DIR / f"{did}.json"
    q.write_text(json.dumps(draft, indent=2))
    try:
        ok = _send_preview(draft)
    except Exception as e:
        ok = False
        print(f"[gate] preview email failed: {e}", file=sys.stderr)
    print(f"[gate] DRAFT {did} queued. Preview {'sent to ' + PREVIEW_TO if ok else 'FAILED to send'}. NOTHING delivered to real recipients yet.")
    return did


def do_approve(args):
    q = QUEUE_DIR / f"{args.approve}.json"
    if not q.exists():
        raise SystemExit(f"[gate] no pending draft {args.approve}")
    draft = json.loads(q.read_text())
    if draft.get("status") != "pending":
        raise SystemExit(f"[gate] draft {args.approve} already {draft.get('status')}")
    try:
        mid = _deliver(draft["to"], draft["cc"], draft["subject"], draft["body"],
                       draft["html"], draft["attachments"])
        draft["status"] = "approved"
        draft["approved_at"] = time.time()
        draft["message_id"] = mid
        q.write_text(json.dumps(draft, indent=2))
        _write_log({"action": "approve", "id": args.approve, "to": draft["to"],
                    "cc": draft["cc"], "subject": draft["subject"], "at": draft["approved_at"]})
        print(f"[gate] DELIVERED {args.approve} -> {draft['to']} cc={draft['cc'] or '(none)'} (msgid {mid})")
    except Exception as e:
        print(f"[gate] DELIVERY FAILED {args.approve}: {e}", file=sys.stderr)
        raise SystemExit(1)


def do_reject(args):
    q = QUEUE_DIR / f"{args.reject}.json"
    if q.exists():
        d = json.loads(q.read_text())
        d["status"] = "rejected"
        d["rejected_at"] = time.time()
        q.write_text(json.dumps(d, indent=2))
    print(f"[gate] REJECTED {args.reject} (not sent)")


def do_list():
    if not QUEUE_DIR.exists():
        print("[gate] no pending drafts")
        return
    for q in sorted(QUEUE_DIR.glob("*.json")):
        d = json.loads(q.read_text())
        print(f"{d['id']} [{d['status']}] -> {d['to']} cc={d['cc'] or '(none)'} :: {d['subject']}")


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--draft", action="store_true", help="queue + preview to Shareef, do NOT send")
    g.add_argument("--approve", metavar="ID")
    g.add_argument("--reject", metavar="ID")
    g.add_argument("--list", action="store_true")
    ap.add_argument("--to")
    ap.add_argument("--cc")
    ap.add_argument("--subject")
    ap.add_argument("--body")
    ap.add_argument("--html", action="store_true")
    ap.add_argument("--attach", nargs="*")
    a = ap.parse_args()

    if a.list:
        do_list()
    elif a.approve:
        do_approve(a)
    elif a.reject:
        do_reject(a)
    elif a.draft:
        do_draft(a)


if __name__ == "__main__":
    main()
