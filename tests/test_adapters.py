import json
import os
import subprocess
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _run(adapter, payload, args=(), state_dir="/tmp/loopable-test-state"):
    return subprocess.run(
        ["python3", str(ROOT / "adapters" / adapter), *args],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=10,
        env={**os.environ, "XDG_STATE_HOME": state_dir},
    )


def test_claude_userpromptsubmit(tmp_path):
    r = _run(
        "claude.py",
        {
            "session_id": uuid.uuid4().hex,
            "prompt": "the tests keep flaking",
            "cwd": "/tmp",
        },
        args=["userpromptsubmit"],
        state_dir=str(tmp_path),
    )
    assert r.returncode == 0
    assert "<loop-match-context>" in r.stdout
    assert "/goal all tests pass" in r.stdout


def test_claude_stop_reads_transcript(tmp_path):
    transcript = tmp_path / "t.jsonl"
    transcript.write_text(
        json.dumps(
            {
                "type": "assistant",
                "message": {
                    "content": [{"type": "text", "text": "the build keeps failing, retrying"}]
                },
            }
        )
        + "\n"
    )
    r = _run(
        "claude.py",
        {"session_id": uuid.uuid4().hex, "transcript_path": str(transcript)},
        args=["stop"],
        state_dir=str(tmp_path),
    )
    assert r.returncode == 0
    out = json.loads(r.stdout)
    assert out["hookSpecificOutput"]["hookEventName"] == "Stop"
    assert "/goal the production build exits 0" in out["hookSpecificOutput"]["additionalContext"]


def test_codex_userpromptsubmit(tmp_path):
    r = _run(
        "codex.py",
        {"session_id": uuid.uuid4().hex, "prompt": "the tests keep flaking"},
        state_dir=str(tmp_path),
    )
    assert r.returncode == 0
    assert r.stdout.startswith("loopable:")
    assert "/goal all tests pass" in r.stdout


def test_claude_session_start_cleanup(tmp_path):
    r = _run("claude.py", {}, args=["session_start"], state_dir=str(tmp_path))
    assert r.returncode == 0
    assert r.stdout == ""
