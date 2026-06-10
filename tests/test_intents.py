"""INTENTS.md is the natural-language semantic layer: the host model reads
it at SessionStart and matches intent in any language. These tests keep it
consistent with the generated catalog and safe to inject."""

import json
from pathlib import Path

from core.suggest import session_context

ROOT = Path(__file__).resolve().parent.parent
INTENTS = (ROOT / "INTENTS.md").read_text(encoding="utf-8")

# Same denylist as the context templates (DESIGN constraint 2).
DENYLIST = [
    "tell the user",
    "must",
    "critical",
    "important",
    "always",
    "never",
    "you should",
    "usually",
    "find it helpful",
    "system:",
]


def test_every_catalog_command_appears_in_intents_md():
    catalog = json.loads((ROOT / "data" / "catalog.json").read_text(encoding="utf-8"))
    for entry in catalog["entries"]:
        command = entry["command"]["claude"]
        assert command in INTENTS, entry["id"]


def test_intents_md_has_no_denied_tokens():
    lower = INTENTS.lower()
    for token in DENYLIST:
        assert token not in lower, token


def test_session_context_wraps_rules():
    out = session_context()
    assert out.startswith("<loopable-rules>")
    assert out.endswith("</loopable-rules>")
    assert "any language" in out


def test_session_context_respects_mute(isolated_state):
    state = isolated_state / "loopable"
    state.mkdir(parents=True, exist_ok=True)
    (state / "disabled-global").touch()
    assert session_context() == ""
