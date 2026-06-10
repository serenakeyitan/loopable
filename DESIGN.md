# loopable

Delivers rules of judgment so the host agent suggests `/loop` and `/goal` commands when the conversation is loop-shaped. Claude Code + Codex CLI.

Status: approved · 2026-06-09 · **v2 pivot 2026-06-10** (judgment moved from code to the agent)

## Problem

Users hand-grind work the host already has a command for ("tests keep flaking", "check the deploy every few minutes"). The awesome-agent-loops catalog has the right commands, but a catalog is passive. loopable puts the judgment rules — what counts as loop-shaped, what single command to offer — into the agent's context, and the agent judges every message. The user runs the command, or doesn't.

## The v2 pivot

v0.1–0.5 decided yes/no in code: keyword trigger lists, retry-phrase tables, token-hash similarity. Live use showed the flaw three times in one day — "make sure all tests pass", "ensure all tests pass", "fix bug for me" each missed the lists, and each patch grew the enumeration without closing the gap. Enumerated surface forms can never cover paraphrase or other languages; that's whack-a-mole by construction (机械化, not agentic). The fix: the host model already reads every message, so it makes the match decision. Code keeps only what code is good at — reliable delivery, mute, state, fail-open.

## Constraints

1. **Hooks cannot run slash commands.** Docs: "Hooks communicate through stdout, stderr, and exit codes only. They cannot trigger / commands or tool calls." loopable is a suggester. Auto-launch is impossible; do not design for it.
2. **Injected context must be factual, not imperative.** Imperative phrasing trips Claude's prompt-injection defenses and gets surfaced to the user as suspicious text. No "tell the user", no MUST/CRITICAL.
3. **Judgment is the model's; delivery is deterministic.** (Reversed 2026-06-10 — was "detection is deterministic".) Code makes no decision about message content: it answers only "has this session got the rules?", "is a reminder due?", "is loopable muted?". Those delivery decisions stay deterministic, testable, free.
4. **One rules file.** `RULES.md` is the single source for both hosts (Codex receives a condensed one-line digest of it).
5. **Fail open.** Any error → exit 0, empty output. Never block or erase a prompt.
6. **Visibility differs per host.** Claude: injected context is model-visible; relay to the user is probabilistic. Codex: hook output lands as a model-visible developer message (in `codex exec` it is NOT shown in the transcript; interactive mode may render it), so its text must read clean raw either way.

## Architecture

```
RULES.md (judgment rules + reference library, human-edited,
          seeded from awesome-agent-loops)
        │
core/suggest.py — delivery + state only, fail-open
  session_context()   full rules           (SessionStart, Claude)
  prompt_context()    full rules on a session's first sighting,
                      short reminder every REFRESH_EVERY msgs
        │                          │
adapters/claude.py          adapters/codex.py
SessionStart +              UserPromptSubmit (no SessionStart
UserPromptSubmit            event on Codex — rules ride msg 1)
(stop = no-op, back-compat)
```

### Rules delivery

The whole runtime decision tree, none of it about message content:

- `SessionStart` (Claude): cleanup TTL state, inject `<loopable-rules>` wrapping RULES.md, mark the session injected.
- `UserPromptSubmit` (both hosts): skip empty/slash messages → if the session was never injected (Codex always; Claude resumed/pre-install sessions) deliver the full rules → else count messages and deliver a short reminder every `REFRESH_EVERY` (20) — countering model attention fade and context compaction in long sessions.
- Muted → nothing. Errors → nothing (fail open). `stop` mode is a kept-for-compat no-op.

Claude gets the full md (`<loopable-rules>` / `<loopable-rules-reminder>` blocks); Codex gets a one-line digest (`core/digest_codex.txt`) since its hook output may render in the visible transcript and Codex has no `/loop`.

### RULES.md shape

Three sections, all judgment guidance, no enumerations: **The decision** (verify-until-green, watch-until-done, manual-retry-in-progress — and what is NOT loop-shaped, with "when unsure, stay quiet"), **What to offer** (one command, one line, composed: concrete artifact, verifiable-not-opinion success condition, proportional turn cap 5-30, once per session, user decides), **Reference library** (proven shapes seeded from awesome-agent-loops, marked adapt-don't-recite; Codex offers /goal shapes only). Tests gate structure, the inject-text denylist, and the library's core commands — judgment quality itself is the model's and is validated by live E2E, not unit tests.

### Delivery

**Claude Code** — `UserPromptSubmit` (primary) and `Stop` (secondary) hooks emit stdout / `additionalContext`. Never `decision:block`. Hook entry must be synchronous (`async` output is not injected) and is snapshotted at session start (install requires `/hooks` or restart). Use exec-form `args`.

**Codex CLI** — same two hook events (hooks confirmed in codex-cli 0.133.0). Wire via `[[hooks.*]]` tables in user `config.toml` (single home; `hooks.json` also loads in the same layer, so defining both runs every hook twice). Untrusted user-layer hooks are *discovered but silently skipped at dispatch*: trust = `[hooks.state."<source>:<snake_case_event>:<group>:<handler>"] trusted_hash` entries in user config.toml, granted via `/hooks` interactively or written headlessly with the `currentHash` from app-server `hooks/list`; any command/timeout/matcher edit invalidates it. E2E-found 2026-06-10: in `codex exec` the injected text lands as a model-visible developer message, NOT in the visible transcript — the original "renders visibly (#16933)" assumption holds at best for interactive mode, and relay to the user is model discretion on both hosts. `--dangerously-bypass-hook-trust` warns but does not run untrusted hooks in exec 0.133.0.

Rejected surfaces: statusline, output styles (no write path); Codex `notify` (one-way); MCP (cannot watch passively).

### Control command

`/loopable` status · `/loopable on|off` · `/loopable mute` (session). Deferred: `why`, `list`, `system-message`. Never runs a loop itself.

### State

`$XDG_STATE_HOME/loopable/`: `rules-<session_id>.json` (`{injected, count}` delivery state), `disabled-global`, `disabled-/muted-<session_id>`. 7-day TTL cleanup on SessionStart. Missing session_id → keyed as `nosession`. No message text is ever read into state — the delivery layer never inspects content.

## Engineering

- Tests (20): delivery mechanics (first-message injection, SessionStart dedupe, reminder cadence, mute, TTL, slash/empty skip), fail-open (malformed input → exit 0, empty), rules-content gates (structure, inject-text denylist, core library commands pinned, codex digest single clean line), adapter subprocess contracts.
- Hook wrapper: global try/except, exit 0 on every path.
- CI: pytest; ruff check + format; mypy --strict on core.
- Judgment quality is not unit-testable — validate via live E2E sessions per host (claude -p / codex exec), as on 2026-06-10.
- Package: `@loopable/cli` or `loopable-cc` (bare name likely squatted; verify before publish).

## Risks

1. Claude relay is model discretion. The step-0 PoC measures it.
2. Codex rendering asserted from docs + #16933, not a live run. Step 0 gates the adapter.
3. False positives → judgment etiquette in RULES.md (once per session, stay quiet when unsure) + mute. Over-suggesting is a rules-wording bug; fix the md, verify by live E2E.
4. Long sessions fade the rules from attention → REFRESH_EVERY reminder cadence; compaction loses them entirely → first-sighting re-injection on the prompt path.

## Plan

(Historical — v0.1 build plan, completed 2026-06-09/10; superseded by the v2 pivot above. Kept for the record.)

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
