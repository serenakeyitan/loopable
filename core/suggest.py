"""loopable core: delivers rules of judgment to the host agent. Fail-open.

v2 (2026-06-10): no matchers. Earlier versions decided yes/no in code
(keyword triggers, retry-phrase lists, token-hash similarity) — permanent
whack-a-mole against natural language. Now the agent judges what is
loop-shaped by reading RULES.md; this module only owns delivery and state:

  session_context() -> str        full rules (SessionStart, Claude)
  prompt_context(payload) -> str  full rules on a session's first message,
                                  a short reminder every REFRESH_EVERY
                                  messages after that, otherwise ""
  mark_injected(session_id)       SessionStart bookkeeping
  cleanup_state(now)              TTL cleanup (SessionStart)

Every public function returns "" / no-ops on any error. Never raises.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent.parent
_RULES = _ROOT / "RULES.md"
_REMINDER_CLAUDE = _ROOT / "core" / "reminder_claude.txt"
_DIGEST_CODEX = _ROOT / "core" / "digest_codex.txt"
_PLATFORMS = ("claude", "codex")
STATE_TTL_DAYS = 7
REFRESH_EVERY = 20  # user messages between rule reminders


def _state_dir() -> Path:
    base = os.environ.get("XDG_STATE_HOME") or os.path.join(
        os.path.expanduser("~"), ".local", "state"
    )
    return Path(base) / "loopable"


def _disabled(session_id: str) -> bool:
    state = _state_dir()
    return (
        (state / "disabled-global").exists()
        or (state / f"disabled-{session_id}").exists()
        or (state / f"muted-{session_id}").exists()
    )


def _state_path(session_id: str) -> Path:
    return _state_dir() / f"rules-{session_id}.json"


def _load_state(session_id: str) -> dict[str, Any]:
    try:
        data = json.loads(_state_path(session_id).read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_state(session_id: str, count: int) -> None:
    try:
        path = _state_path(session_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"injected": True, "count": count}), encoding="utf-8")
    except Exception:
        pass


def _full_rules(platform: str) -> str:
    if platform == "codex":
        # Codex output may render in the visible transcript: one clean line.
        return _DIGEST_CODEX.read_text(encoding="utf-8").strip()
    text = _RULES.read_text(encoding="utf-8").strip()
    return f"<loopable-rules>\n{text}\n</loopable-rules>"


def _reminder(platform: str) -> str:
    if platform == "codex":
        return _DIGEST_CODEX.read_text(encoding="utf-8").strip()
    return _REMINDER_CLAUDE.read_text(encoding="utf-8").strip()


def mark_injected(session_id: str) -> None:
    """Record that SessionStart delivered the rules for this session."""
    _save_state(session_id, 0)


def session_context() -> str:
    """Full rules for SessionStart (Claude only — Codex has no such event).

    Empty when muted or on any error.
    """
    try:
        if (_state_dir() / "disabled-global").exists():
            return ""
        return _full_rules("claude")
    except Exception:
        return ""


def prompt_context(payload: dict[str, Any]) -> str:
    """Delivery decision for one user message. No judgment about content —
    the only questions are "has this session got the rules yet?" and
    "is a reminder due?". Slash commands and empty prompts are skipped.
    """
    try:
        platform = payload.get("platform", "")
        if platform not in _PLATFORMS:
            return ""
        prompt = str(payload.get("prompt") or "")
        if not prompt.strip() or prompt.strip().startswith("/"):
            return ""
        session_id = str(payload.get("session_id") or "nosession")
        if _disabled(session_id):
            return ""
        state = _load_state(session_id)
        if not state.get("injected"):
            # First sighting of this session: SessionStart never ran (Codex,
            # resumed/pre-install Claude sessions) — deliver the full rules.
            _save_state(session_id, 0)
            return _full_rules(platform)
        count = int(state.get("count", 0)) + 1
        if count >= REFRESH_EVERY:
            _save_state(session_id, 0)
            return _reminder(platform)
        _save_state(session_id, count)
        return ""
    except Exception:
        return ""


def cleanup_state(now: float | None = None) -> None:
    """Delete state files older than STATE_TTL_DAYS. Called on SessionStart."""
    cutoff = (now or time.time()) - STATE_TTL_DAYS * 86400
    try:
        for f in _state_dir().iterdir():
            if f.is_file() and f.stat().st_mtime < cutoff:
                f.unlink(missing_ok=True)
    except Exception:
        pass
