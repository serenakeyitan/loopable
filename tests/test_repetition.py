import uuid

from core.repetition import is_retry
from core.suggest import suggest


def _payload(prompt, platform="claude", session=None):
    return {
        "platform": platform,
        "prompt": prompt,
        "last_assistant_message": None,
        "cwd": "/tmp",
        "session_id": session or uuid.uuid4().hex,
    }


def test_is_retry_vocabulary():
    assert is_retry("run it again")
    assert is_retry("still failing")
    assert is_retry("nope still broken")
    assert is_retry("还是不行")
    assert is_retry("rerun tests again")  # bare "again", short message
    assert not is_retry("write me a readme")
    # long messages with "again" are new asks, not retries
    assert not is_retry(
        "the build failed once again because of a flaky network mock in the auth suite"
    )


def test_two_retry_messages_in_a_row_fire():
    s = uuid.uuid4().hex
    assert suggest(_payload("please fix the login redirect bug", session=s)) == ""
    assert suggest(_payload("run it again", session=s)) == ""
    out = suggest(_payload("still broken", session=s))
    assert "<loop-repetition-context>" in out
    assert "/goal" in out


def test_retry_chain_resets_on_normal_message():
    s = uuid.uuid4().hex
    assert suggest(_payload("run it again", session=s)) == ""
    assert suggest(_payload("now refactor the config loader module instead", session=s)) == ""
    assert suggest(_payload("still broken", session=s)) == ""


def test_three_similar_messages_fire():
    s = uuid.uuid4().hex
    assert (
        suggest(_payload("deploy the staging branch to the preview environment", session=s)) == ""
    )
    assert (
        suggest(_payload("deploy the staging branch to the preview environment please", session=s))
        == ""
    )
    out = suggest(_payload("deploy the staging branch to the preview environment now", session=s))
    assert "<loop-repetition-context>" in out
    assert "three similar messages" in out


def test_short_messages_do_not_count_as_similar():
    s = uuid.uuid4().hex
    for _ in range(3):
        assert suggest(_payload("fix it", session=s)) == ""


def test_fires_once_per_session():
    s = uuid.uuid4().hex
    suggest(_payload("please fix the login redirect bug", session=s))
    suggest(_payload("run it again", session=s))
    assert suggest(_payload("still broken", session=s)) != ""
    assert suggest(_payload("try again", session=s)) == ""


def test_catalog_takes_precedence_then_repetition_covers_repeats():
    s = uuid.uuid4().hex
    first = suggest(_payload("the tests keep flaking", session=s))
    assert "<loop-match-context>" in first
    assert suggest(_payload("the tests keep flaking", session=s)) == ""  # catalog deduped
    out = suggest(_payload("the tests keep flaking", session=s))  # third look-alike
    assert "<loop-repetition-context>" in out


def test_stop_path_never_observes():
    s = uuid.uuid4().hex
    stop = {
        "platform": "claude",
        "prompt": None,
        "last_assistant_message": "still failing",
        "cwd": "/tmp",
        "session_id": s,
    }
    assert suggest(stop) == ""
    assert suggest(stop) == ""
    # assistant chatter left no retry history behind
    assert suggest(_payload("still broken", session=s)) == ""


def test_codex_repetition_single_line():
    s = uuid.uuid4().hex
    suggest(_payload("please fix the login redirect bug", platform="codex", session=s))
    suggest(_payload("run it again", platform="codex", session=s))
    out = suggest(_payload("still broken", platform="codex", session=s))
    assert out.startswith("loopable:")
    assert "<" not in out
    assert "/loop" not in out  # codex has no /loop


def test_state_stores_no_prompt_text(isolated_state):
    s = "fixed-session-id"
    suggest(_payload("deploy the staging branch now", session=s))
    content = (isolated_state / "loopable" / f"recent-{s}.json").read_text()
    for word in ("deploy", "staging", "branch"):
        assert word not in content
