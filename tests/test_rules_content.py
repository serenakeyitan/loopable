"""loopable.md is the product: judgment rules the agent interprets. These tests
gate its structure and injection safety, not its judgment (that's the
model's)."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RULES = (ROOT / "loopable.md").read_text(encoding="utf-8")
REMINDER = (ROOT / "core" / "reminder_claude.txt").read_text(encoding="utf-8")
DIGEST = (ROOT / "core" / "digest_codex.txt").read_text(encoding="utf-8")

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


def test_no_denied_tokens_in_injected_text():
    for name, text in (("RULES", RULES), ("REMINDER", REMINDER), ("DIGEST", DIGEST)):
        lower = text.lower()
        for token in DENYLIST:
            assert token not in lower, (name, token)


def test_rules_structure():
    for section in ("## The decision", "## What to offer", "## Reference library"):
        assert section in RULES
    assert "any language" in RULES
    # the etiquette that keeps it un-Clippy
    assert "once per session" in RULES
    assert "stay quiet" in RULES


def test_reference_library_keeps_core_loops():
    for fragment in (
        "/goal all tests pass and lint is clean, stop after 20 turns",
        "/goal the production build exits 0",
        "/loop 10m run `gh pr checks`",
        "/goal all database migrations apply cleanly",
    ):
        assert fragment in RULES, fragment


def test_codex_digest_is_single_clean_line():
    assert "\n" not in DIGEST.strip()
    assert "<" not in DIGEST
    assert "/loop" not in DIGEST  # codex has no /loop
    assert "/goal" in DIGEST
