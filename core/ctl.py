"""Deterministic control CLI: python3 core/ctl.py status|on|off

The /loopable slash command wraps this. Session-scoped mute is deferred until
hosts expose a session id to slash commands (DESIGN: control command v0.1).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.suggest import _CATALOG, _state_dir  # noqa: E402


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    state = _state_dir()
    flag = state / "disabled-global"
    if cmd == "off":
        state.mkdir(parents=True, exist_ok=True)
        flag.touch()
        print("loopable: off (global)")
    elif cmd == "on":
        flag.unlink(missing_ok=True)
        print("loopable: on")
    elif cmd == "status":
        try:
            n = len(json.loads(_CATALOG.read_text(encoding="utf-8"))["entries"])
        except Exception:
            n = 0
        print(f"loopable: {'off' if flag.exists() else 'on'} · {n} catalog entries")
    else:
        print(f"unknown subcommand: {cmd}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
