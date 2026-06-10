from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLAUDE = (ROOT / "core" / "context_template_claude.txt").read_text()
CODEX = (ROOT / "core" / "context_template_codex.txt").read_text()
CLAUDE_REPETITION = (ROOT / "core" / "context_template_claude_repetition.txt").read_text()
CODEX_REPETITION = (ROOT / "core" / "context_template_codex_repetition.txt").read_text()

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


def test_claude_templates_have_no_denied_tokens():
    for template in (CLAUDE, CLAUDE_REPETITION):
        lower = template.lower()
        for token in DENYLIST:
            assert token not in lower, token


def test_placeholders_present():
    for template in (CLAUDE, CODEX):
        assert "{trigger_phrase}" in template
        assert "{loop_command}" in template
    for template in (CLAUDE_REPETITION, CODEX_REPETITION):
        assert "{signal}" in template


def test_codex_templates_are_single_line_no_markup():
    for template in (CODEX, CODEX_REPETITION):
        assert "\n" not in template.strip()
        assert "<" not in template
