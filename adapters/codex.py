"""Codex CLI adapter. Wire in ~/.codex/config.toml (see settings/codex.config.toml)
and grant trust — ONBOARDING.md Step 4/4b.

Output is the clean one-line template: it lands as a model-visible developer
message (in exec mode it is not shown in the transcript, so it must read clean
either way). Every path exits 0 with empty output on error.
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
