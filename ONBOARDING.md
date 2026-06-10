# ONBOARDING.md — agent install guide

You are an AI coding agent. The user asked you to install **loopable**: small
hooks that deliver RULES.md — rules of judgment for spotting loop-shaped
moments and offering one `/loop` or `/goal` command — into each session's
context. The hooks decide nothing about content; the agent reading the rules
does the judging. Follow these steps exactly. Show the user what you changed.

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
echo '{"session_id":"onboard","prompt":"hello","cwd":"/tmp"}' \
  | python3 adapters/claude.py userpromptsubmit
```

Expected: a `<loopable-rules>` block containing the contents of RULES.md.
Empty output or non-zero exit → stop and report.

Note: this test records delivery state under
`${XDG_STATE_HOME:-~/.local/state}/loopable/` — repeating it with the **same**
`session_id` is expectedly silent (the rules are delivered once per session,
then refreshed as a short reminder every ~20 messages).

## Step 2 — detect hosts

- Claude Code: the `~/.claude/` directory exists → do Step 3.
- Codex CLI: the `~/.codex/` directory exists → do Step 4.
- Both present → do both.

## Step 3 — Claude Code

Read `~/.claude/settings.json`. If the file is absent, create it as
`{"hooks": {}}`. If it exists without a `hooks` object, add one. Then merge
these two entries (append to each event's array; if an event key is absent,
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
    "SessionStart": [
      { "hooks": [ { "type": "command",
        "command": "python3 $REPO/adapters/claude.py session_start", "timeout": 5 } ] }
    ]
  }
}
```

(`adapters/claude.py` takes a subcommand; `adapters/codex.py` in Step 4 takes none.
The same two entries, pre-written, are in `settings/claude.settings.json`. A
`Stop` entry from a pre-v2 install is a harmless no-op — leave or remove it.)

Validate: `python3 -c "import json;json.load(open('$HOME/.claude/settings.json'))"`.

Show the user a short summary of what was appended (two entries), not a
full-file dump.

Install the control command — create `~/.claude/commands/` if missing and copy
the repo's `commands/loopable.md` there, replacing `$REPO` with the clone path.
Leave `$ARGUMENTS` literal — it is a Claude Code runtime placeholder.

**Tell the user:** hooks are snapshotted at session start — run `/hooks` once
(or start a new session) to activate.

## Step 4 — Codex CLI

Wire the hooks in `~/.codex/config.toml` — not `hooks.json`. Codex 0.133.0
loads both from the same user layer; defining both duplicates every hook
execution (with only a log warning), and trust state has to live in
config.toml anyway. If a previous loopable install left entries in
`~/.codex/hooks.json`, remove them.

Append to `~/.codex/config.toml` (skip any block whose command already
references `adapters/codex.py`; replace `$REPO` with the absolute clone
path — the same snippet is pre-written in `settings/codex.config.toml`):

```toml
[[hooks.UserPromptSubmit]]
[[hooks.UserPromptSubmit.hooks]]
type = "command"
command = "python3 $REPO/adapters/codex.py"

[[hooks.Stop]]
[[hooks.Stop.hooks]]
type = "command"
command = "python3 $REPO/adapters/codex.py"
```

Pipe-test the Codex adapter:

```bash
echo '{"session_id":"onboard-codex","prompt":"hello"}' \
  | python3 $REPO/adapters/codex.py
```

Expected: one line, no markup, starting with `loopable rules:` (the condensed
rules digest — Codex has no SessionStart event, so the first message of each
session carries the rules instead).

### Step 4b — trust (required; untrusted hooks are silently skipped)

Codex lists untrusted user-layer hooks but skips them at dispatch with no
error. Grant trust one of two ways:

- **Interactive:** the user runs `/hooks` once inside Codex → "Trust all and
  continue". Tell them this is the activation step.
- **Headless:** talk to `codex app-server` over stdio JSON-RPC: send
  `initialize`, the `initialized` notification, then
  `{"method":"hooks/list","params":{}}` (`params` is required — omitting it
  errors with -32600, which is not the same as "0 hooks"). For each of the
  two hooks take `key` and `currentHash` and append:

```toml
[hooks.state."<key for user_prompt_submit>"]
trusted_hash = "<currentHash>"

[hooks.state."<key for stop>"]
trusted_hash = "<currentHash>"
```

Keys embed the absolute config path and snake_case event labels (e.g.
`/home/u/.codex/config.toml:user_prompt_submit:0:0`). The hash covers the
hook's command/timeout/matcher, so any edit invalidates trust — re-trust
after edits. Do not rely on `--dangerously-bypass-hook-trust`; in exec mode
0.133.0 it warns but does not actually run untrusted hooks.

Verify: re-run hooks/list and check both hooks show `trustStatus: "trusted"`
— presence alone does not mean they will run.

## Step 5 — verify and hand off

1. Re-run the Step 1 pipe test **with a fresh session id**, e.g.
   `{"session_id":"onboard-verify", ...}`. (Reusing `"onboard"` is expectedly
   silent — rules deliver once per session, not per message.)
2. Tell the user, in one short block:
   - activation: `/hooks` (Claude) / trust via `/hooks` (Codex)
   - live test: in a new session, describe something loop-shaped in ANY
     phrasing or language — *"make sure the tests go green"*, *"测试老是挂"* —
     and the agent (judging by RULES.md, not keywords) offers a fitted
     `/goal` on one line
   - the rules land once per session plus a short reminder every ~20 messages
   - mute: `python3 $REPO/core/ctl.py off` (or `/loopable off`)
3. Do not run `/loop` or `/goal` yourself. Installation ends here.

## Uninstall

1. Remove the two loopable entries (plus any legacy `Stop` entry) from
   `~/.claude/settings.json`, and from
   `~/.codex/config.toml` the two `[[hooks.*]]` blocks plus their
   `[hooks.state."…"]` trust entries. Legacy installs may also have entries in
   `~/.codex/hooks.json` — remove those too (delete the file if loopable
   created it and nothing else remains).
2. Delete `~/.claude/commands/loopable.md`.
3. `rm -rf $REPO "${XDG_STATE_HOME:-$HOME/.local/state}/loopable"`.
4. Tell the user: a live session keeps running the old hook snapshot until they
   run `/hooks` or restart — same as install activation, in reverse.
