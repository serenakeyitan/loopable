"""Codex CLI adapter. Wire in ~/.codex/config.toml (see settings/codex.config.toml)
and grant trust — ONBOARDING.md Step 4/4b.

Codex has no SessionStart event, so the UserPromptSubmit hook delivers the
rules digest on each session's first message and re-delivers it every ~20
messages. Output is one clean line: it lands as a model-visible developer
message (in exec mode it is not shown in the transcript, so it must read
clean either way). Every path exits 0 with empty output on error.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.suggest import prompt_context  # noqa: E402


def main() -> int:
    try:
        payload: dict[str, Any] = json.load(sys.stdin)
        out = prompt_context(
            {
                "platform": "codex",
                "session_id": payload.get("session_id"),
                "prompt": payload.get("prompt"),
            }
        )
        if out:
            print(out, end="")
        return 0
    except Exception:
        return 0


if __name__ == "__main__":
    sys.exit(main())
