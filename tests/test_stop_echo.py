"""Stop-path echo guard (found live 2026-06-10): after the model surfaces a
loop suggestion, its own prose can keyword-match the catalog via the Stop
hook — re-injecting the same suggestion and burning the dedupe slot."""

import uuid

from core.suggest import suggest

COMMAND = "/goal all tests pass and lint is clean, stop after 20 turns"


def _stop(message, session=None):
    return {
        "platform": "claude",
        "prompt": None,
        "last_assistant_message": message,
        "cwd": "/tmp",
        "session_id": session or uuid.uuid4().hex,
    }


def _prompt(message, session=None):
    return {
        "platform": "claude",
        "prompt": message,
        "last_assistant_message": None,
        "cwd": "/tmp",
        "session_id": session or uuid.uuid4().hex,
    }


def test_stop_silent_when_command_already_surfaced():
    msg = f"You mentioned tests keep failing. To drive the suite green you can run: `{COMMAND}`"
    assert suggest(_stop(msg)) == ""


def test_stop_silent_when_command_surfaced_unquoted():
    msg = f"since the tests keep failing, consider {COMMAND} to grind it out"
    assert suggest(_stop(msg)) == ""


def test_echo_does_not_burn_dedupe_slot():
    s = uuid.uuid4().hex
    echo = f"tests keep failing here — you could run `{COMMAND}`"
    assert suggest(_stop(echo, session=s)) == ""
    # a later legitimate user prompt in the same session still fires
    assert COMMAND in suggest(_prompt("ugh the tests keep flaking again", session=s))


def test_stop_still_fires_without_command():
    # the legitimate Stop-hook case: trigger phrase in prose, command absent
    out = suggest(_stop("the build keeps failing, retrying"))
    assert "/goal the production build exits 0" in out


def test_prompt_path_unaffected_by_command_presence():
    msg = f"the tests keep flaking — should I run {COMMAND} ?"
    assert COMMAND in suggest(_prompt(msg))
