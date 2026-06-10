# ONBOARDING.md — agent install guide

You are an AI coding agent. The user asked you to install **loopable**: two small
hooks that suggest `/loop` and `/goal` commands when the user's message is
loop-shaped. Follow these steps exactly. Show the user what you changed.

## Rules

- **Merge, never overwrite.** Read every settings file before editing. Existing
  hooks must survive untouched.
- **Hooks must be synchronous.** Never add `async: true` — async hook output is
  not injected and loopable would silently do nothing.
- **Never** wire anything that blocks: no `decision:block`, no exit-2 paths.
  loopable is fail-open by design.
- Use **absolute paths**. `$REPO` below means the absolute path of this clone.

## Step 1 — clone and self-test

```bash
git clone https://github.com/serenakeyitan/loopable ~/loopable   # or user's preferred location
cd ~/loopable
python3 --version   # needs >= 3.10
echo '{"session_id":"onboard","prompt":"the tests keep flaking","cwd":"/tmp"}' \
  | python3 adapters/claude.py userpromptsubmit
```

Expected: a `<loop-match-context>` block containing `/goal all tests pass and
lint is clean`. Empty output or non-zero exit → stop and report.

## Step 2 — detect hosts

- Claude Code: `~/.claude/settings.json` exists → do Step 3.
- Codex CLI: `~/.codex/` exists → do Step 4.
- Both present → do both.

## Step 3 — Claude Code

Read `~/.claude/settings.json`. Merge these three entries into the existing
`hooks` object (append to each event's array; create the array if missing).
Replace `$REPO` with the absolute clone path:

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

Validate: `python3 -c "import json;json.load(open('$HOME/.claude/settings.json'))"`.

Optionally install the control command — write `~/.claude/commands/loopable.md`:

```markdown
---
description: Control the loopable suggester
argument-hint: "[status|on|off]"
---
Run `python3 $REPO/core/ctl.py $ARGUMENTS` and show the output verbatim.
Never run /loop or /goal yourself from this command.
```

**Tell the user:** hooks are snapshotted at session start — run `/hooks` once
(or start a new session) to activate.

## Step 4 — Codex CLI

Read `~/.codex/hooks.json` (create `{}` if absent). Merge:

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

**Tell the user:** Codex skips untrusted hooks — they must trust it once via
`/hooks` inside Codex.

## Step 5 — verify and hand off

1. Re-run the Step 1 pipe test.
2. Tell the user, in one short block:
   - activation: `/hooks` (Claude) / trust via `/hooks` (Codex)
   - live test: say **"the tests keep flaking"** → the agent should mention
     `/goal all tests pass and lint is clean, stop after 20 turns`
   - it fires once per loop per session; second mention stays silent
   - mute: `python3 $REPO/core/ctl.py off` (or `/loopable off`)
3. Do not run `/loop` or `/goal` yourself. Installation ends here.

## Uninstall

Remove the three loopable entries from `~/.claude/settings.json` (and the two
from `~/.codex/hooks.json`), delete `~/.claude/commands/loopable.md`, then
`rm -rf $REPO ~/.local/state/loopable`.
