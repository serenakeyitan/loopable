# loopable

**Don't prompt the loop — the loop prompts you.**

`/loop` and `/goal` suggestions matched from your conversation, never auto-run. Claude Code + Codex CLI.

You say "ugh, the tests keep flaking" — loopable matches it against a catalog of saved loops and surfaces the command:

```
/goal all tests pass and lint is clean, stop after 20 turns
```

It never runs anything. Hooks cannot trigger slash commands; loopable is a suggester by construction. Detection is a deterministic keyword match — no LLM call, no latency, no cost. See [DESIGN.md](DESIGN.md).

## Install — Claude Code

1. Clone this repo.
2. Merge [settings/claude.settings.json](settings/claude.settings.json) into `~/.claude/settings.json`, replacing `REPLACE_WITH_PATH` with the clone path.
3. Run `/hooks` once (or restart) — hooks are snapshotted at session start.

Suggestions are injected as model-visible context; Claude relays them in its reply.

## Install — Codex CLI

1. Clone this repo.
2. Merge [settings/codex.hooks.json](settings/codex.hooks.json) into `~/.codex/hooks.json`, replacing `REPLACE_WITH_PATH`.
3. Trust the hook once via `/hooks` — non-managed Codex hooks are skipped until trusted.

Codex renders the suggestion directly in the transcript as a one-liner.

## Control

```
python3 core/ctl.py status|on|off
```

`/loopable` (commands/loopable.md) wraps this in-session. Per-session mute is deferred until hosts expose a session id to slash commands. Suggestions fire at most once per entry per session.

## Catalog

`build/entries.json` is canonical (seeded from [awesome-agent-loops](https://github.com/serenakeyitan/awesome-agent-loops)). `python3 build/build_catalog.py` regenerates `data/catalog.json`; CI fails if the committed file drifts. Codex entries never use `/loop` (Codex doesn't have it) and its `/goal` tracks an objective rather than auto-continuing.

## Dev

```
python3 -m pytest tests/
ruff check . && ruff format --check .
mypy --strict core/suggest.py core/ctl.py
```

Fail-open invariant: every adapter path exits 0. A broken loopable must never block or erase a prompt.

## License

MIT
