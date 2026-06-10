# loopable

**`/loop` and `/goal` suggestions matched from your conversation — never auto-run.**

The librarian for [**awesome-agent-loops**](https://github.com/serenakeyitan/awesome-agent-loops), the library of copy-paste `/loop`, `/goal`, and `/schedule` prompts these suggestions come from.

### check out my latest work, and run `/loop` in [first-tree](https://github.com/agent-team-foundation/first-tree) free :D

## The pain

Claude Code already ships the commands that kill repetitive work: `/goal` keeps going until tests *actually* pass, `/loop` re-checks a PR every 10 minutes. The problem is remembering they exist **in the moment** — you're three "run it again"s deep before it occurs to you that a loop would have done this. The catalog of good loops is a page you have to go read; nobody does mid-task.

## What loopable is

A **hook** — two tiny scripts your agent host runs automatically around each message (`UserPromptSubmit` + `Stop`). On every message it keyword-matches your words against the catalog. On a hit, your agent surfaces the matching command:

```
you:     ugh, the tests keep flaking again
claude:  that matches a saved loop — you can run:
         /goal all tests pass and lint is clean, stop after 20 turns
```

- **Never auto-runs.** Hooks physically cannot trigger slash commands; you always press enter yourself.
- **Deterministic.** Plain keyword match against `data/catalog.json` — no LLM call, zero latency, zero cost.
- **Fail-open.** Any error exits silent; it can never block or eat a prompt.
- **Not naggy.** Fires once per loop per session; quoted/backticked mentions don't trigger it.

## Install

Paste this into Claude Code (or Codex):

```
clone https://github.com/serenakeyitan/loopable and follow its ONBOARDING.md to install it
```

Your agent reads [ONBOARDING.md](ONBOARDING.md) and wires the hooks itself — it merges your settings (never overwrites), validates, and tells you the one activation step (`/hooks` on Claude; trust-once via `/hooks` on Codex). Prefer doing it by hand? Every manual step is in the same file.

Then say something loop-shaped — *"the tests keep flaking"* — and watch.

## Control

```
/loopable            status
/loopable off | on   mute / unmute everywhere
```

(or `python3 core/ctl.py status|on|off` directly)

## How it works

```
your message ──▶ hook ──▶ keyword match vs catalog ──▶ one factual note to the agent ──▶ agent suggests the command
```

Catalog source of truth is [`build/entries.json`](build/entries.json); `build_catalog.py` generates `data/catalog.json` (CI fails on drift). Codex entries never use `/loop` (Codex doesn't have it). Full architecture, invariants, and the prompt-injection-safe wording: [DESIGN.md](DESIGN.md).

## Dev

```
python3 -m pytest tests/        # 28 tests
ruff check . && mypy --strict core/suggest.py core/ctl.py
```

MIT
