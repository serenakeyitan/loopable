"""Codex CLI adapter. Wire in hooks.json (see settings/codex.hooks.json).

Codex renders injected context visibly (openai/codex#16933), so output is the
clean one-line template. Every path exits 0 with empty output on error.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.suggest import suggest  # noqa: E402


def main() -> int:
    try:
        payload: dict[str, Any] = json.load(sys.stdin)
        out = suggest(
            {
                "platform": "codex",
                "session_id": payload.get("session_id"),
                "cwd": payload.get("cwd", ""),
                "prompt": payload.get("prompt"),
                "last_assistant_message": payload.get("last_assistant_message"),
            }
        )
        if out:
            print(out, end="")
        return 0
    except Exception:
        return 0


if __name__ == "__main__":
    sys.exit(main())
