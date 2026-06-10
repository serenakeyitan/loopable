# loopable

Suggests `/loop` and `/goal` commands when the conversation is loop-shaped. Claude Code + Codex CLI.

Status: approved · 2026-06-09

## Problem

Users hand-grind work the host already has a command for ("tests keep flaking", "check the deploy every few minutes"). The awesome-agent-loops catalog has the right commands, but a catalog is passive. loopable matches the conversation against the catalog and surfaces the matching command. The user runs it.

## Constraints

1. **Hooks cannot run slash commands.** Docs: "Hooks communicate through stdout, stderr, and exit codes only. They cannot trigger / commands or tool calls." loopable is a suggester. Auto-launch is impossible; do not design for it.
2. **Injected context must be factual, not imperative.** Imperative phrasing trips Claude's prompt-injection defenses and gets surfaced to the user as suspicious text. No "tell the user", no MUST/CRITICAL.
3. **Detection is deterministic** — keyword match, no LLM call. Free, testable, explainable.
4. **One catalog.** A single generated `catalog.json` feeds both hosts.
5. **Fail open.** Any error → exit 0, empty output. Never block or erase a prompt.
6. **Visibility differs per host.** Claude: injected context is model-visible; relay to the user is probabilistic. Codex: `additionalContext` renders visibly in the transcript (openai/codex#16933), so its text must read clean raw.

## Architecture

```
awesome-agent-loops (markdown, human-edited)
        │ build_catalog.py — CI drift gate
        ▼
data/catalog.json (generated, schema v1)
        │
core/suggest.py — deterministic matcher, fail-open
        │                       │
adapters/claude.py      adapters/codex.py
UserPromptSubmit + Stop  UserPromptSubmit + Stop
```

### Catalog entry

```json
{
  "id": "tests-keep-flaking",
  "triggers": ["tests keep flaking", "keep failing", "until tests pass"],
  "exclude": ["do not", "stop running"],
  "intent": "verify-until-green",
  "min_confidence": 2,
  "command": {
    "claude": "/goal all tests pass and lint is clean, stop after 20 turns",
    "codex":  "/goal all tests pass and lint is clean, stop after 20 turns"
  }
}
```

`command` is per-host (Codex has no `/loop`; its `/goal` tracks an objective rather than auto-continuing). Missing host key → entry skipped on that host. Commands are authored for each host's semantics, not translated.

### Matcher

Input: `{prompt, last_assistant_message, cwd, platform, session_id}` (adapters normalize host payloads).
Logic: lowercase → strip quoted/backticked/code spans (mentions are not work; found live when the Stop hook matched the assistant's own quoted example) → count distinct trigger hits per entry → drop on any `exclude` hit, `hits < min_confidence`, missing `command[platform]`, message starting with a slash command → rank by trigger specificity, tie-break by id → session dedupe → emit ≤1 suggestion. Always exit 0. Called in-process (no subprocess on the prompt path).

### Semantic layer (INTENTS.md)

Keyword lists are mechanical: they enumerate surface forms and lose every paraphrase and language they didn't enumerate. The fix that keeps constraint 3 (no LLM call in the hook): the host model is already an LLM, so the SessionStart hook injects `INTENTS.md` — plain-language rules mapping intents to commands — once per session, and the model does semantic matching for free, in any language. The md is human-edited content, the same register as the catalog; a test pins every catalog `claude` command verbatim into the md (drift gate) and runs the inject-text denylist over it. Muted → no injection. Claude-only for now (Codex hooks expose no SessionStart event). ~500 tokens per session is the cost; model attention over long sessions is the known weakness, which the deterministic layers backstop.

### Repetition trigger

The catalog answers WHAT loop to suggest; triggers answer WHEN. Keywords are the fast path; `core/repetition.py` adds the higher-precision behavioral trigger: the user is visibly re-running the same task by hand. Two deterministic signals, prompt path only (assistant Stop-hook text is not evidence the user is retrying):

- **retry chain** — a short retry-vocabulary message ("run it again", "still failing", "还是不行") immediately after another one; long messages containing "again" are new asks.
- **similar messages** — token-set Jaccard ≥ 0.6 against ≥ 2 of the last 6 messages (each ≥ 4 tokens).

Catalog match wins when both would fire. The injected text names the pattern but no command — the host model already has the conversation, so it composes the `/goal` success condition; the hook stays content-blind. State (`recent-<session_id>.json`) stores only per-message token hashes + a retry flag, never prompt text. Dedupe id `repetition`, once per session, same mute/TTL machinery.

### Injected text

Claude (model-visible):

```
<loop-match-context>
This environment includes a catalog of saved loop commands. A lookup on the
user's latest message returned one matching entry, provided as reference
data, not an instruction. No command has been executed.

  trigger_phrase: "{trigger_phrase}"
  loop_command:   "{loop_command}"

This catalog is intended for the matching loop_command to be quoted on a
single line so the user can decide whether to run it.
</loop-match-context>
```

Codex (user-visible, raw):

```
loopable: "{trigger_phrase}" matches a saved loop. Consider running: {loop_command}
```

### Delivery

**Claude Code** — `UserPromptSubmit` (primary) and `Stop` (secondary) hooks emit stdout / `additionalContext`. Never `decision:block`. Hook entry must be synchronous (`async` output is not injected) and is snapshotted at session start (install requires `/hooks` or restart). Use exec-form `args`.

**Codex CLI** — same two hook events (hooks confirmed in codex-cli 0.133.0). Wire via `[[hooks.*]]` tables in user `config.toml` (single home; `hooks.json` also loads in the same layer, so defining both runs every hook twice). Untrusted user-layer hooks are *discovered but silently skipped at dispatch*: trust = `[hooks.state."<source>:<snake_case_event>:<group>:<handler>"] trusted_hash` entries in user config.toml, granted via `/hooks` interactively or written headlessly with the `currentHash` from app-server `hooks/list`; any command/timeout/matcher edit invalidates it. E2E-found 2026-06-10: in `codex exec` the injected text lands as a model-visible developer message, NOT in the visible transcript — the original "renders visibly (#16933)" assumption holds at best for interactive mode, and relay to the user is model discretion on both hosts. `--dangerously-bypass-hook-trust` warns but does not run untrusted hooks in exec 0.133.0.

Rejected surfaces: statusline, output styles (no write path); Codex `notify` (one-way); MCP (cannot watch passively).

### Control command

`/loopable` status · `/loopable on|off` · `/loopable mute` (session). Deferred: `why`, `list`, `system-message`. Never runs a loop itself.

### State

`$XDG_STATE_HOME/loopable/`: `suggested-<session_id>.json` (dedupe), `disabled-/muted-<session_id>`. 7-day TTL cleanup on SessionStart. Missing session_id → in-memory suggest-once. Never log prompt text; match log is `{ts, entry_id, trigger_phrase}`, off by default.

## Engineering

- Tests: golden cases (prompt → entry → command per host), fail-open (malformed input → exit 0, empty), inject-text denylist (no imperative/empirical tokens), adapter normalization, dedupe, exclusions.
- Hook wrapper: global try/except, 1s timeout, exit 0 on every path.
- CI: rebuild `catalog.json` must be byte-identical (drift gate); JSON-schema validation; ruff + mypy --strict; gitleaks.
- Versioning: `schema_version` separate from tool version; mismatch → no-op. `source_commit` pins catalog source.
- Package: `@loopable/cli` or `loopable-cc` (bare name likely squatted; verify before publish).

## Risks

1. Claude relay is model discretion. The step-0 PoC measures it.
2. Codex rendering asserted from docs + #16933, not a live run. Step 0 gates the adapter.
3. False positives → `min_confidence`, excludes, dedupe, mute.
4. `Stop` fires every response → dedupe mandatory.

## Plan

0. Verify injection on both hosts.
   - Claude: **done 2026-06-09.** PoC at `~/.claude/loopable-poc/hook.sh`, wired into `~/.claude/settings.json`, unit-tested (match / no-match / garbage → exit 0). Remaining: activate via `/hooks`, send a trigger phrase, check `fired.log` and whether Claude relays the command.
   - Codex: pending. Echo hook, trust, observe rendering.
1. Scaffold repo: layout above, lint + CI, schema v1.
2. Seed catalog with 5–8 mainstream patterns; author per-host commands.
3. `build_catalog.py` + drift gate.
4. `core/suggest.py` + tests.
5. `adapters/claude.py` + sample settings.
6. `adapters/codex.py` + sample hooks.json.
7. `/loopable` control command.
8. Package both plugins; README covers both installs (Codex trust step, Claude `/hooks` reload).
9. E2E per host: trigger phrase → suggestion surfaced, command not auto-run.
