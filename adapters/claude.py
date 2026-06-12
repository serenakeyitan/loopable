"""Claude Code adapter. Wire in settings.json (see settings/claude.settings.json).

Modes: userpromptsubmit | stop | session_start
session_start injects loopable.md; userpromptsubmit injects it for sessions
SessionStart never saw (resumed/pre-install) and a short reminder every
~20 messages; stop is a no-op kept for backward-compatible installs.
Every path exits 0 with empty output on error (DESIGN: fail open).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.suggest import cleanup_state, mark_injected, prompt_context, session_context  # noqa: E402


def main() -> int:
    try:
        mode = sys.argv[1] if len(sys.argv) > 1 else "userpromptsubmit"
        if mode == "session_start":
            cleanup_state()
            try:
                payload: dict[str, Any] = json.load(sys.stdin)
            except Exception:
                payload = {}
            rules = session_context()
            if rules:
                session_id = payload.get("session_id")
                if session_id:
                    mark_injected(str(session_id))
                print(
                    json.dumps(
                        {
                            "hookSpecificOutput": {
                                "hookEventName": "SessionStart",
                                "additionalContext": rules,
                            }
                        }
                    )
                )
            return 0
        if mode == "stop":
            return 0  # v2: nothing to judge in code
        payload = json.load(sys.stdin)
        out = prompt_context(
            {
                "platform": "claude",
                "session_id": payload.get("session_id"),
                "prompt": payload.get("prompt", ""),
            }
        )
        if out:
            print(out)
        return 0
    except Exception:
        return 0


if __name__ == "__main__":
    sys.exit(main())
