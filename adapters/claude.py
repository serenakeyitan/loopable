"""Claude Code adapter. Wire in settings.json (see settings/claude.settings.json).

Modes: userpromptsubmit | stop | session_start
Every path exits 0 with empty output on error (DESIGN: fail open, never block a prompt).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.suggest import cleanup_state, suggest  # noqa: E402


def _last_assistant_message(transcript_path: str) -> str:
    try:
        lines = Path(transcript_path).read_text(encoding="utf-8").splitlines()
        for line in reversed(lines[-200:]):
            try:
                rec: dict[str, Any] = json.loads(line)
            except Exception:
                continue
            if rec.get("type") == "assistant":
                content = rec.get("message", {}).get("content", [])
                texts = [b.get("text", "") for b in content if b.get("type") == "text"]
                if texts:
                    return "\n".join(texts)
        return ""
    except Exception:
        return ""


def main() -> int:
    try:
        mode = sys.argv[1] if len(sys.argv) > 1 else "userpromptsubmit"
        if mode == "session_start":
            cleanup_state()
            return 0
        payload: dict[str, Any] = json.load(sys.stdin)
        base = {
            "platform": "claude",
            "session_id": payload.get("session_id"),
            "cwd": payload.get("cwd", ""),
        }
        if mode == "stop":
            text = _last_assistant_message(payload.get("transcript_path", ""))
            out = suggest({**base, "prompt": None, "last_assistant_message": text})
            if out:
                print(
                    json.dumps(
                        {
                            "hookSpecificOutput": {
                                "hookEventName": "Stop",
                                "additionalContext": out,
                            }
                        }
                    )
                )
        else:
            out = suggest(
                {
                    **base,
                    "prompt": payload.get("prompt", ""),
                    "last_assistant_message": None,
                }
            )
            if out:
                print(out)
        return 0
    except Exception:
        return 0


if __name__ == "__main__":
    sys.exit(main())
