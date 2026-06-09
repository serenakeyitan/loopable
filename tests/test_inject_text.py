from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLAUDE = (ROOT / "core" / "context_template_claude.txt").read_text()
CODEX = (ROOT / "core" / "context_template_codex.txt").read_text()

# Imperative / empirical phrasing trips Claude's prompt-injection defenses
# or smuggles invented claims (DESIGN constraint 2).
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


def test_claude_template_has_no_denied_tokens():
    lower = CLAUDE.lower()
    for token in DENYLIST:
        assert token not in lower, token


def test_placeholders_present():
    for template in (CLAUDE, CODEX):
        assert "{trigger_phrase}" in template
        assert "{loop_command}" in template


def test_codex_template_is_single_line_no_markup():
    assert "\n" not in CODEX.strip()
    assert "<" not in CODEX
