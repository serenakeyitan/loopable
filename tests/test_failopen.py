import json
import os
import subprocess
from pathlib import Path

import core.suggest as s
from core.suggest import suggest

ROOT = Path(__file__).resolve().parent.parent
ADAPTERS = [ROOT / "adapters" / "claude.py", ROOT / "adapters" / "codex.py"]


def test_empty_payload():
    assert suggest({}) == ""


def test_none_fields():
    assert suggest({"platform": "claude", "prompt": None, "session_id": None}) == ""


def test_missing_catalog(monkeypatch):
    monkeypatch.setattr(s, "_CATALOG", Path("/nonexistent/catalog.json"))
    assert suggest({"platform": "claude", "prompt": "tests keep flaking", "session_id": "x"}) == ""


def test_schema_mismatch(tmp_path, monkeypatch):
    bad = tmp_path / "catalog.json"
    bad.write_text(json.dumps({"schema_version": 99, "entries": []}))
    monkeypatch.setattr(s, "_CATALOG", bad)
    assert suggest({"platform": "claude", "prompt": "tests keep flaking", "session_id": "x"}) == ""


def _run(adapter, stdin, args=()):
    return subprocess.run(
        ["python3", str(adapter), *args],
        input=stdin,
        capture_output=True,
        text=True,
        timeout=10,
        env={**os.environ, "XDG_STATE_HOME": "/tmp/loopable-test-state"},
    )


def test_adapters_fail_open_on_garbage():
    for adapter in ADAPTERS:
        for stdin in ["not json", "", "[1,2,3]"]:
            r = _run(adapter, stdin)
            assert r.returncode == 0, (adapter.name, stdin, r.stderr)
            assert r.stdout == ""
