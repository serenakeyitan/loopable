"""Deterministic loop suggester. No LLM calls. Fail-open: never raises to callers.

Contract (DESIGN.md):
  suggest(payload) -> str        rendered suggestion or "" (no match / deduped / error)
  payload: {prompt, last_assistant_message, cwd, platform, session_id}
"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any

from core.repetition import observe as _observe_repetition

# Backtick/code spans and double-quoted spans; single quotes excluded (apostrophes).
_QUOTED_SPAN = re.compile(r"```.*?```|`[^`]*`|\"[^\"]*\"", re.DOTALL)

_ROOT = Path(__file__).resolve().parent.parent
_CATALOG = _ROOT / "data" / "catalog.json"
_TEMPLATES = {
    "claude": _ROOT / "core" / "context_template_claude.txt",
    "codex": _ROOT / "core" / "context_template_codex.txt",
}
_TEMPLATES_REPETITION = {
    "claude": _ROOT / "core" / "context_template_claude_repetition.txt",
    "codex": _ROOT / "core" / "context_template_codex_repetition.txt",
}
_REPETITION_ID = "repetition"
SCHEMA_VERSION = 1
STATE_TTL_DAYS = 7


def _state_dir() -> Path:
    base = os.environ.get("XDG_STATE_HOME") or os.path.join(
        os.path.expanduser("~"), ".local", "state"
    )
    return Path(base) / "loopable"


def _load_catalog() -> list[dict[str, Any]]:
    data = json.loads(_CATALOG.read_text(encoding="utf-8"))
    if data.get("schema_version") != SCHEMA_VERSION:
        return []  # version mismatch degrades to no-op (DESIGN: fail open)
    entries = data.get("entries", [])
    return entries if isinstance(entries, list) else []


def _match(text: str, platform: str, entries: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Return best entry + matched trigger, or None.

    Rank by longest matched trigger (specificity), tie-break by id.
    """
    candidates: list[tuple[int, str, str, dict[str, Any]]] = []
    for entry in entries:
        command = entry.get("command", {}).get(platform)
        if not command:
            continue
        if any(ex in text for ex in entry.get("exclude", [])):
            continue
        hits = [t for t in entry.get("triggers", []) if t in text]
        if len(hits) < int(entry.get("min_confidence", 1)):
            continue
        if not hits:
            continue
        best_trigger = max(hits, key=len)
        candidates.append((len(best_trigger), entry.get("id", ""), best_trigger, entry))
    if not candidates:
        return None
    candidates.sort(key=lambda c: (-c[0], c[1]))
    _, _, trigger, entry = candidates[0]
    return {"entry": entry, "trigger": trigger}


def _already_suggested(session_id: str, entry_id: str) -> bool:
    path = _state_dir() / f"suggested-{session_id}.json"
    try:
        return entry_id in json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return False


def _record_suggested(session_id: str, entry_id: str) -> None:
    state = _state_dir()
    state.mkdir(parents=True, exist_ok=True)
    path = state / f"suggested-{session_id}.json"
    try:
        seen = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        seen = []
    if entry_id not in seen:
        seen.append(entry_id)
    path.write_text(json.dumps(seen), encoding="utf-8")


def _disabled(session_id: str) -> bool:
    state = _state_dir()
    return (
        (state / "disabled-global").exists()
        or (state / f"disabled-{session_id}").exists()
        or (state / f"muted-{session_id}").exists()
    )


def _render(platform: str, trigger: str, command: str) -> str:
    template = _TEMPLATES[platform].read_text(encoding="utf-8")
    return template.replace("{trigger_phrase}", trigger).replace("{loop_command}", command)


def _render_repetition(platform: str, signal: str) -> str:
    template = _TEMPLATES_REPETITION[platform].read_text(encoding="utf-8")
    return template.replace("{signal}", signal)


def cleanup_state(now: float | None = None) -> None:
    """Delete state files older than STATE_TTL_DAYS. Called on SessionStart."""
    cutoff = (now or time.time()) - STATE_TTL_DAYS * 86400
    try:
        for f in _state_dir().iterdir():
            if f.is_file() and f.stat().st_mtime < cutoff:
                f.unlink(missing_ok=True)
    except Exception:
        pass


def suggest(payload: dict[str, Any]) -> str:
    try:
        platform = payload.get("platform", "")
        if platform not in _TEMPLATES:
            return ""
        text = (payload.get("prompt") or payload.get("last_assistant_message") or "").lower()
        if not text.strip() or text.strip().startswith("/"):
            return ""
        # Quoted/backticked spans are mentions, not work being done. Found live:
        # the Stop hook matched the assistant's own example '"tests keep flaking"'.
        text = _QUOTED_SPAN.sub(" ", text)
        session_id = str(payload.get("session_id") or "nosession")
        if _disabled(session_id):
            return ""
        is_prompt = bool(payload.get("prompt"))
        match = _match(text, platform, _load_catalog())
        if match is not None:
            entry_id = match["entry"].get("id", "")
            if not _already_suggested(session_id, entry_id):
                if is_prompt:  # keep retry history complete even when catalog wins
                    _observe_repetition(_state_dir(), session_id, text)
                rendered = _render(platform, match["trigger"], match["entry"]["command"][platform])
                _record_suggested(session_id, entry_id)
                return rendered
        # Repetition trigger: prompt path only — the assistant's own Stop-hook
        # text is not evidence the user is retrying anything.
        if not is_prompt:
            return ""
        signal = _observe_repetition(_state_dir(), session_id, text)
        if not signal or _already_suggested(session_id, _REPETITION_ID):
            return ""
        rendered = _render_repetition(platform, signal)
        _record_suggested(session_id, _REPETITION_ID)
        return rendered
    except Exception:
        return ""  # fail open, always
