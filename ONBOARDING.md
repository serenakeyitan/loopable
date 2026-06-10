# ONBOARDING.md — agent install guide

You are an AI coding agent. The user asked you to install **loopable**: two small
hooks that suggest `/loop` and `/goal` commands when the user's message is
loop-shaped. Follow these steps exactly. Show the user what you changed.

## Rules

- **Merge, never overwrite.** Read every settings file before editing. Existing
  hooks must survive untouched. After merging, verify each pre-existing event
  array kept all its entries, plus exactly one appended loopable entry.
- **Idempotent.** Before appending to an event array, skip that event if any
  existing entry's command contains `adapters/claude.py` (or `adapters/codex.py`
  for Codex) — re-running this guide must never duplicate hooks.
- **Hooks must be synchronous.** Never add `async: true` — async hook output is
  not injected and loopable would silently do nothing.
- **Never** wire anything that blocks: no `decision:block`, no exit-2 paths.
  loopable is fail-open by design.
- Use **absolute paths**. `$REPO` below means the absolute path of this clone.

## Step 1 — clone and self-test

```bash
git clone https://github.com/serenakeyitan/loopable ~/loopable   # or user's preferred location
# if the directory already exists from a prior run: git -C ~/loopable pull
cd ~/loopable
python3 --version   # needs >= 3.10
echo '{"session_id":"onboard","prompt":"the tests keep flaking","cwd":"/tmp"}' \
  | python3 adapters/claude.py userpromptsubmit
```

Expected: a `<loop-match-context>` block containing `/goal all tests pass and
lint is clean`. Empty output or non-zero exit → stop and report.

Note: this test records a dedupe entry under
`${XDG_STATE_HOME:-~/.local/state}/loopable/` — repeating it with the **same**
`session_id` is expectedly silent (suggestions fire once per loop per session).

## Step 2 — detect hosts

- Claude Code: the `~/.claude/` directory exists → do Step 3.
- Codex CLI: the `~/.codex/` directory exists → do Step 4.
- Both present → do both.

## Step 3 — Claude Code

Read `~/.claude/settings.json`. If the file is absent, create it as
`{"hooks": {}}`. If it exists without a `hooks` object, add one. Then merge
these three entries (append to each event's array; if an event key is absent,
add it with a one-element array; apply the idempotency rule above). Replace
`$REPO` with the absolute clone path:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      { "hooks": [ { "type": "command",
        "command": "python3 $REPO/adapters/claude.py userpromptsubmit",
        "timeout": 5, "statusMessage": "loopable" } ] }
    ],
    "Stop": [
      { "hooks": [ { "type": "command",
        "command": "python3 $REPO/adapters/claude.py stop", "timeout": 5 } ] }
    ],
    "SessionStart": [
      { "hooks": [ { "type": "command",
        "command": "python3 $REPO/adapters/claude.py session_start", "timeout": 5 } ] }
    ]
  }
}
```

(`adapters/claude.py` takes a subcommand; `adapters/codex.py` in Step 4 takes none.
The same three entries, pre-written, are in `settings/claude.settings.json`.)

Validate: `python3 -c "import json;json.load(open('$HOME/.claude/settings.json'))"`.

Show the user a short summary of what was appended (three entries), not a
full-file dump.

Install the control command — create `~/.claude/commands/` if missing and copy
the repo's `commands/loopable.md` there, replacing `$REPO` with the clone path.
Leave `$ARGUMENTS` literal — it is a Claude Code runtime placeholder.

**Tell the user:** hooks are snapshotted at session start — run `/hooks` once
(or start a new session) to activate.

## Step 4 — Codex CLI

Read `~/.codex/hooks.json`; if absent, create it as `{}`. Merge (append; create
the array if the event key is absent; skip if an entry already references
`adapters/codex.py`):

```json
{
  "UserPromptSubmit": [
    { "command": ["python3", "$REPO/adapters/codex.py"] }
  ],
  "Stop": [
    { "command": ["python3", "$REPO/adapters/codex.py"] }
  ]
}
```

Validate: `python3 -c "import json;json.load(open('$HOME/.codex/hooks.json'))"`.

Pipe-test the Codex adapter:

```bash
echo '{"session_id":"onboard-codex","prompt":"the tests keep flaking"}' \
  | python3 $REPO/adapters/codex.py
```

Expected (one line, no markup):
`loopable: "tests keep flaking" matches a saved loop. Consider running: /goal all tests pass and lint is clean, stop after 20 turns`

**Tell the user:** Codex skips untrusted hooks — they must trust it once via
`/hooks` inside Codex.

## Step 5 — verify and hand off

1. Re-run the Step 1 pipe test **with a fresh session id**, e.g.
   `{"session_id":"onboard-verify", ...}`. (Reusing `"onboard"` is expectedly
   silent — that's the once-per-session dedupe working, not a failure.)
2. Tell the user, in one short block:
   - activation: `/hooks` (Claude) / trust via `/hooks` (Codex)
   - live test: say **"the tests keep flaking"** → the agent should mention
     `/goal all tests pass and lint is clean, stop after 20 turns`
   - it fires once per loop per session; second mention stays silent
   - mute: `python3 $REPO/core/ctl.py off` (or `/loopable off`)
3. Do not run `/loop` or `/goal` yourself. Installation ends here.

## Uninstall

1. Remove the three loopable entries from `~/.claude/settings.json` and the two
   from `~/.codex/hooks.json` (drop any event key left with an empty array; if
   loopable created `hooks.json` and nothing else remains, delete the file).
2. Delete `~/.claude/commands/loopable.md`.
3. `rm -rf $REPO "${XDG_STATE_HOME:-$HOME/.local/state}/loopable"`.
4. Tell the user: a live session keeps running the old hook snapshot until they
   run `/hooks` or restart — same as install activation, in reverse.
