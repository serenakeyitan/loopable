import json
import os
import subprocess
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _run(adapter, payload, args=(), state_dir="/tmp/loopable-test-state"):
    return subprocess.run(
        ["python3", str(ROOT / "adapters" / adapter), *args],
        input=payload if isinstance(payload, str) else json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=10,
        env={**os.environ, "XDG_STATE_HOME": state_dir},
    )


def test_claude_session_start_injects_rules(tmp_path):
    r = _run(
        "claude.py",
        {"session_id": uuid.uuid4().hex},
        args=["session_start"],
        state_dir=str(tmp_path),
    )
    assert r.returncode == 0
    out = json.loads(r.stdout)
    assert out["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    ctx = out["hookSpecificOutput"]["additionalContext"]
    assert ctx.startswith("<loopable-rules>")
    assert "## The decision" in ctx


def test_claude_session_start_muted_is_silent(tmp_path):
    state = tmp_path / "loopable"
    state.mkdir(parents=True)
    (state / "disabled-global").touch()
    r = _run("claude.py", {}, args=["session_start"], state_dir=str(tmp_path))
    assert r.returncode == 0
    assert r.stdout == ""


def test_claude_prompt_injects_when_session_start_missed(tmp_path):
    sid = uuid.uuid4().hex
    r = _run(
        "claude.py",
        {"session_id": sid, "prompt": "the tests keep flaking", "cwd": "/tmp"},
        args=["userpromptsubmit"],
        state_dir=str(tmp_path),
    )
    assert r.returncode == 0
    assert r.stdout.startswith("<loopable-rules>")
    # second message: rules already delivered
    r2 = _run(
        "claude.py",
        {"session_id": sid, "prompt": "and the build too", "cwd": "/tmp"},
        args=["userpromptsubmit"],
        state_dir=str(tmp_path),
    )
    assert r2.returncode == 0
    assert r2.stdout == ""


def test_claude_session_start_then_prompt_no_duplicate(tmp_path):
    sid = uuid.uuid4().hex
    _run("claude.py", {"session_id": sid}, args=["session_start"], state_dir=str(tmp_path))
    r = _run(
        "claude.py",
        {"session_id": sid, "prompt": "hello there", "cwd": "/tmp"},
        args=["userpromptsubmit"],
        state_dir=str(tmp_path),
    )
    assert r.stdout == ""


def test_claude_stop_is_noop(tmp_path):
    r = _run("claude.py", {"session_id": uuid.uuid4().hex}, args=["stop"], state_dir=str(tmp_path))
    assert r.returncode == 0
    assert r.stdout == ""


def test_codex_first_message_digest(tmp_path):
    sid = uuid.uuid4().hex
    r = _run(
        "codex.py", {"session_id": sid, "prompt": "fix my flaky tests"}, state_dir=str(tmp_path)
    )
    assert r.returncode == 0
    assert r.stdout.startswith("loopable rules:")
    assert "<" not in r.stdout
    r2 = _run("codex.py", {"session_id": sid, "prompt": "thanks"}, state_dir=str(tmp_path))
    assert r2.stdout == ""


def test_adapters_fail_open_on_garbage(tmp_path):
    for adapter in ("claude.py", "codex.py"):
        for stdin in ["not json", "", "[1,2,3]"]:
            r = _run(adapter, stdin, state_dir=str(tmp_path))
            assert r.returncode == 0, (adapter, stdin, r.stderr)
            assert r.stdout == ""
