"""Generate data/catalog.json from build/entries.json. Deterministic: CI re-runs
this and fails if the committed catalog differs (drift gate)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "build" / "entries.json"
TARGET = ROOT / "data" / "catalog.json"
SCHEMA_VERSION = 1
VALID_PLATFORMS = {"claude", "codex"}


def validate(entries: list[dict]) -> list[str]:
    errors: list[str] = []
    seen_ids: set[str] = set()
    for i, e in enumerate(entries):
        eid = e.get("id")
        if not eid or not isinstance(eid, str):
            errors.append(f"entry {i}: missing id")
            continue
        if eid in seen_ids:
            errors.append(f"{eid}: duplicate id")
        seen_ids.add(eid)
        if not e.get("triggers"):
            errors.append(f"{eid}: no triggers")
        if any(t != t.lower() for t in e.get("triggers", [])):
            errors.append(f"{eid}: triggers must be lowercase")
        cmd = e.get("command", {})
        if not cmd or not set(cmd) <= VALID_PLATFORMS:
            errors.append(f"{eid}: command keys must be subset of {VALID_PLATFORMS}")
        for plat, c in cmd.items():
            if not c.startswith("/"):
                errors.append(f"{eid}: {plat} command must start with /")
        if "/loop" in cmd.get("codex", ""):
            errors.append(f"{eid}: codex has no /loop")
    return errors


def main() -> int:
    src = json.loads(SOURCE.read_text(encoding="utf-8"))
    entries = src["entries"]
    errors = validate(entries)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    catalog = {
        "schema_version": SCHEMA_VERSION,
        "source": src.get("source", str(SOURCE.relative_to(ROOT))),
        "entries": sorted(entries, key=lambda e: e["id"]),
    }
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(
        json.dumps(catalog, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {TARGET.relative_to(ROOT)} ({len(entries)} entries)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
