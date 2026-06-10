"""Delivery mechanics — the only decisions code still makes: has this
session got the rules yet, and is a reminder due."""

import time
import uuid
from pathlib import Path

import core.suggest as s
from core.suggest import cleanup_state, mark_injected, prompt_context, session_context


def _payload(prompt, platform="claude", session=None):
    return {
        "platform": platform,
        "prompt": prompt,
        "session_id": session or uuid.uuid4().hex,
    }


def test_first_message_gets_full_rules():
    out = prompt_context(_payload("please fix the login bug"))
    assert out.startswith("<loopable-rules>")
    assert out.endswith("</loopable-rules>")


def test_second_message_is_silent():
    sid = uuid.uuid4().hex
    assert prompt_context(_payload("first", session=sid)) != ""
    assert prompt_context(_payload("second", session=sid)) == ""


def test_session_start_prevents_duplicate_injection():
    sid = uuid.uuid4().hex
    assert session_context().startswith("<loopable-rules>")
    mark_injected(sid)
    assert prompt_context(_payload("first message after start", session=sid)) == ""


def test_reminder_fires_every_refresh_interval(monkeypatch):
    monkeypatch.setattr(s, "REFRESH_EVERY", 3)
    sid = uuid.uuid4().hex
    assert prompt_context(_payload("msg 1", session=sid)).startswith("<loopable-rules>")
    assert prompt_context(_payload("msg 2", session=sid)) == ""
    assert prompt_context(_payload("msg 3", session=sid)) == ""
    out = prompt_context(_payload("msg 4", session=sid))
    assert out.startswith("<loopable-rules-reminder>")
    assert prompt_context(_payload("msg 5", session=sid)) == ""


def test_codex_first_message_gets_digest_then_silence():
    sid = uuid.uuid4().hex
    out = prompt_context(_payload("fix the flaky parser", platform="codex", session=sid))
    assert out.startswith("loopable rules:")
    assert "<" not in out
    assert prompt_context(_payload("thanks", platform="codex", session=sid)) == ""


def test_slash_commands_and_empty_skipped():
    sid = uuid.uuid4().hex
    assert prompt_context(_payload("/loopable status", session=sid)) == ""
    assert prompt_context(_payload("   ", session=sid)) == ""
    # the skipped messages did not consume the first-injection slot
    assert prompt_context(_payload("real message", session=sid)) != ""


def test_mute_suppresses_everything(isolated_state):
    state = Path(isolated_state) / "loopable"
    state.mkdir(parents=True, exist_ok=True)
    (state / "disabled-global").touch()
    assert session_context() == ""
    assert prompt_context(_payload("fix the tests please")) == ""


def test_unknown_platform_and_garbage_payloads():
    assert prompt_context({}) == ""
    assert prompt_context({"platform": "cursor", "prompt": "hi", "session_id": "x"}) == ""
    assert prompt_context({"platform": "claude", "prompt": None, "session_id": None}) == ""


def test_ttl_cleanup(isolated_state):
    state = Path(isolated_state) / "loopable"
    state.mkdir(parents=True, exist_ok=True)
    old = state / "rules-old.json"
    old.write_text("{}")
    cleanup_state(now=time.time() + 8 * 86400)
    assert not old.exists()
