import uuid

from core.suggest import suggest


def _payload(prompt, platform="claude"):
    return {
        "platform": platform,
        "prompt": prompt,
        "last_assistant_message": None,
        "cwd": "/tmp",
        "session_id": uuid.uuid4().hex,
    }


GOLDEN = [
    (
        "ugh the tests keep flaking again",
        "claude",
        "/goal all tests pass and lint is clean",
    ),
    (
        "ugh the tests keep flaking again",
        "codex",
        "/goal all tests pass and lint is clean",
    ),
    ("the build keeps failing on ci", "claude", "/goal the production build exits 0"),
    ("can you watch the pr for me", "claude", "/loop 10m run `gh pr checks`"),
    (
        "check the deploy every few minutes",
        "claude",
        "/loop 5m check the latest deployment",
    ),
    (
        "migrate every call site to the new api",
        "claude",
        "/goal every call site is migrated",
    ),
]


def test_golden_cases():
    for prompt, platform, expected_fragment in GOLDEN:
        out = suggest(_payload(prompt, platform))
        assert expected_fragment in out, (prompt, platform)


def test_no_match_is_silent():
    assert suggest(_payload("write me a readme please")) == ""


def test_exclude_suppresses():
    assert suggest(_payload("do not keep failing me here")) == ""


def test_slash_command_skipped():
    assert suggest(_payload("/goal all tests pass until tests pass")) == ""


def test_codex_never_gets_loop_entries():
    assert suggest(_payload("can you watch the pr for me", platform="codex")) == ""


def test_unknown_platform():
    assert suggest(_payload("tests keep flaking", platform="cursor")) == ""


def test_claude_template_shape():
    out = suggest(_payload("the tests keep flaking"))
    assert out.startswith("<loop-match-context>")
    assert 'trigger_phrase: "tests keep flaking"' in out


def test_codex_template_shape():
    out = suggest(_payload("the tests keep flaking", platform="codex"))
    assert out.startswith("loopable:")
    assert "<" not in out


def test_quoted_mention_does_not_fire():
    # Found live: Stop hook matched the assistant's own quoted example.
    assert suggest(_payload('type something like "ugh the tests keep flaking"')) == ""


def test_backticked_mention_does_not_fire():
    assert suggest(_payload("the phrase `tests keep flaking` is a trigger")) == ""


def test_code_block_mention_does_not_fire():
    assert suggest(_payload("example:\n```\ntests keep flaking\n```\nsee?")) == ""


def test_unquoted_still_fires():
    assert "/goal all tests pass" in suggest(_payload("the tests keep flaking again"))
