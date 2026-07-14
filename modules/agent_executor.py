"""
Agentic OS — Agent Executor
Extracted from server.py Phase 9 module extraction.
Handles execution of agent CLI commands (opencode, hermes, gemini).
"""
import json
import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from modules.config import get_settings

logger = logging.getLogger("agentic_os.agent_executor")

# ─── CLI Helpers ─────────────────────────────────────────────────

def run_cli(args: list, timeout: int = 30) -> tuple:
    """Run a CLI command and return (returncode, stdout, stderr)."""
    r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout, r.stderr


def _resolve_hermes_bin() -> Optional[str]:
    """Return the first existing Hermes CLI binary path, or None."""
    candidates = [
        shutil.which("hermes"),
        "/app/venv/bin/hermes",
        str(Path.home() / ".hermes" / "venv" / "bin" / "hermes"),
    ]
    for p in candidates:
        if p and os.path.isfile(p):
            return p
    return None


def clean_hermes_output(raw: str) -> str:
    """Strip CLI metadata from Hermes output, returning only the AI response."""
    if not raw:
        return ""
    lines = raw.split("\n")
    in_box = False
    content_lines = []
    for line in lines:
        if "╭─" in line:
            in_box = True
            continue
        if "╰─" in line:
            in_box = False
            continue
        if in_box:
            cleaned = line.strip()
            if cleaned:
                content_lines.append(cleaned)
    if content_lines:
        return "\n".join(content_lines)
    non_meta = [
        l.strip()
        for l in lines
        if l.strip()
        and not l.startswith(
            (
                "Query:",
                "Initializing",
                "──",
                "Resume",
                "Session:",
                "Duration:",
                "Messages:",
            )
        )
    ]
    return "\n".join(non_meta[-5:]) or raw


# ─── Fallback ────────────────────────────────────────────────────

def _llm_fallback(agent: str, message: str) -> Optional[str]:
    """OpenRouter fallback used when a CLI agent is unavailable."""
    settings = get_settings()
    if not settings.OPENROUTER_API_KEY:
        return None
    try:
        from modules import llm_client
        from modules import cost_tracker

        messages = [
            {
                "role": "system",
                "content": (
                    "You are Agentic OS, a helpful assistant. The primary agent "
                    f"CLI ('{agent}') was unavailable, so this response was "
                    "produced by the OpenRouter fallback model."
                ),
            },
            {"role": "user", "content": message},
        ]
        data = llm_client.chat_completion(messages)
        content = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )
        if not content:
            return None
        labelled = (
            f"*[Fallback: {settings.OPENROUTER_MODEL} — agent '{agent}' unavailable]*\n\n"
            f"{content}"
        )
        try:
            cost_tracker.record_agent_usage(
                agent="fallback",
                model=settings.OPENROUTER_MODEL,
                message=message,
                response_text=labelled,
                provider="openrouter",
            )
        except Exception:
            pass
        return labelled
    except Exception as e:
        logger.warning("LLM fallback failed for agent '%s': %s", agent, str(e))
        return None


def _agent_unavailable(agent: str, message: str, friendly: str) -> str:
    """Return fallback response or friendly error when agent CLI is unavailable."""
    fb = _llm_fallback(agent, message)
    return fb if fb is not None else friendly


# ─── Main Entry Point ────────────────────────────────────────────

def execute_agent(agent: str, message: str) -> str:
    """Execute a message through the specified agent CLI."""
    try:
        if agent == "opencode":
            try:
                code, out, err = run_cli(
                    ["opencode", "run", "--format", "json", message], timeout=30
                )
            except subprocess.TimeoutExpired:
                return _agent_unavailable(
                    "opencode",
                    message,
                    f"⏱ Agent 'opencode' timed out.\n\n"
                    f'Try running `opencode run "{message[:60]}"` directly.\n\n'
                    f"**Message:** {message[:100]}",
                )
            if code == 0:
                response_text = ""
                for line in (out or "").split("\n"):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        event = json.loads(line)
                        if event.get("type") == "text":
                            text = event.get("part", {}).get("text", "")
                            if text:
                                response_text += text + "\n"
                    except (json.JSONDecodeError, KeyError):
                        continue
                result = (
                    response_text.strip()
                    if response_text
                    else f"**opencode**\n\nProcessed your message.\n\n**Message:** {message[:100]}"
                )
                try:
                    from modules import cost_tracker
                    cost_tracker.record_agent_usage(
                        agent="opencode",
                        model="opencode-go",
                        message=message,
                        response_text=result,
                        provider="opencode",
                    )
                except Exception:
                    pass
                return result
            err_msg = (err or "").strip()
            return err_msg or f"opencode returned exit code {code}"

        elif agent == "hermes":
            hermes_bin = _resolve_hermes_bin()
            if not hermes_bin or not os.path.isfile(hermes_bin):
                return _agent_unavailable(
                    "hermes",
                    message,
                    "⚠ Hermes Agent CLI not found. Run `pip install hermes-agent` or check the install.",
                )
            try:
                code, out, err = run_cli(
                    [hermes_bin, "chat", "-q", message], timeout=180
                )
            except subprocess.TimeoutExpired:
                return _agent_unavailable(
                    "hermes",
                    message,
                    f"⏱ Hermes timed out.\n\nTry a shorter query or check your OpenRouter rate limits.\n\n**Message:** {message[:100]}",
                )
            if code == 0:
                cleaned = clean_hermes_output(out or "")
                result = (
                    cleaned
                    if cleaned
                    else f"**Hermes**\n\nReceived your message but the model returned an empty response. Try rephrasing.\n\n**Message:** {message}"
                )
                try:
                    from modules import cost_tracker
                    cost_tracker.record_agent_usage(
                        agent="hermes",
                        model="hermes-agent",
                        message=message,
                        response_text=result,
                    )
                except Exception:
                    pass
                return result
            err_msg = (err or "").strip()
            if "invalid choice" in err_msg or "usage:" in err_msg:
                return f"**Hermes needs setup**\n\nRun `hermes setup` or check your config.\n\n**Details:** {err_msg[:200]}"
            return err_msg or f"hermes returned exit code {code}"

        elif agent == "gemini":
            for attempt, (args, to) in enumerate(
                [(["-y", "-m", "gemini-2.5-flash"], 60), (["-y"], 40)]
            ):
                try:
                    code, out, err = run_cli(
                        ["gemini", *args, message], timeout=to
                    )
                except subprocess.TimeoutExpired:
                    if attempt == 0:
                        continue
                    return _agent_unavailable(
                        "gemini",
                        message,
                        f"⏱ Gemini timed out.\n\nTry running `gemini \"{message[:60]}\"` directly.\n\n**Message:** {message[:100]}",
                    )
                if code == 0:
                    result = (out or "").strip() or f"**Gemini CLI**\n\nProcessed your query.\n\n**Message:** {message}"
                    try:
                        from modules import cost_tracker
                        cost_tracker.record_agent_usage(
                            agent="gemini",
                            model=args[1] if len(args) > 1 else "gemini-flash",
                            message=message,
                            response_text=result,
                            provider="gemini",
                        )
                    except Exception:
                        pass
                    return result
                err_msg = (err or "").strip()
                if attempt == 0 and (
                    "model" in err_msg.lower() or "not found" in err_msg.lower()
                ):
                    continue
                if "auth" in err_msg.lower() or "login" in err_msg.lower():
                    return f"**Gemini needs re-auth**\n\nRun `gemini auth login` to re-authenticate.\n\n**Details:** {err_msg[:200]}"
                return err_msg or f"gemini returned exit code {code}"
            return "Gemini CLI did not return a response."

        else:
            return f"Unknown agent: {agent}"

    except subprocess.TimeoutExpired:
        return _agent_unavailable(
            agent,
            message,
            f"⏱ Agent '{agent}' timed out.\n\nRun `{agent} --help` for CLI usage.\n\n**Message:** {message[:100]}",
        )
    except FileNotFoundError:
        return _agent_unavailable(
            agent,
            message,
            f"⚠ Agent '{agent}' CLI not installed. Install it and try again.",
        )
    except Exception as e:
        return f"⚠ Error communicating with {agent}: {str(e)}"
