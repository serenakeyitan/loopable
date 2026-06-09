import time
import uuid
from pathlib import Path

from core.suggest import cleanup_state, suggest


def _payload(session_id):
    return {
        "platform": "claude",
        "prompt": "the tests keep flaking",
        "last_assistant_message": None,
        "cwd": "/tmp",
        "session_id": session_id,
    }


def test_fires_once_per_session():
    sid = uuid.uuid4().hex
    assert suggest(_payload(sid)) != ""
    assert suggest(_payload(sid)) == ""


def test_different_sessions_independent():
    assert suggest(_payload(uuid.uuid4().hex)) != ""
    assert suggest(_payload(uuid.uuid4().hex)) != ""


def test_disable_flag(isolated_state):
    state = Path(isolated_state) / "loopable"
    state.mkdir(parents=True, exist_ok=True)
    (state / "disabled-global").touch()
    assert suggest(_payload(uuid.uuid4().hex)) == ""


def test_ttl_cleanup(isolated_state):
    state = Path(isolated_state) / "loopable"
    state.mkdir(parents=True, exist_ok=True)
    old = state / "suggested-old.json"
    old.write_text("[]")
    cleanup_state(now=time.time() + 8 * 86400)
    assert not old.exists()
