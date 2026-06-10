# Changelog

## 0.5.0 — 2026-06-10

- INTENTS.md: the catalog is no longer a ceiling. New "Composing a loop when no entry matches" rules — when an ask has a checkable success condition and plausible iteration ("fix this bug" about a crashing parser), the agent composes a fitted `/goal <verifiable condition>, stop after N turns` from conversation context. Guard rails: concrete artifact, verifiable-not-opinion condition, proportional turn cap (5-30), skip one-shot asks, offer once.

## 0.4.2 — 2026-06-10

- Stop-path echo guard (found by live E2E): the assistant's own prose could re-match the catalog right after it surfaced a suggestion, re-injecting the same command and burning the entry's once-per-session dedupe slot. The Stop path now skips an entry when the assistant message already contains its command (checked before quoted-span stripping, since commands are usually shown in backticks) — without recording, so a later legitimate match still fires. 5 new tests (48 total).

## 0.4.1 — 2026-06-10

- Fix Codex install (found by real-session E2E): hooks belong in `~/.codex/config.toml` `[[hooks.*]]` tables, and untrusted user-layer hooks are discovered but *silently skipped* — ONBOARDING now covers headless trust via `[hooks.state]` + app-server `hooks/list`, the `/hooks` interactive path, and warns that hooks.json+config.toml double-wiring runs every hook twice. `settings/codex.hooks.json` → `settings/codex.config.toml`. DESIGN corrected: in `codex exec` the suggestion is a model-visible developer message, not transcript-visible.

## 0.4.0 — 2026-06-10

- Semantic layer: `INTENTS.md` — plain-language intent→command rules, injected once per session by the Claude SessionStart hook. The host model matches meaning, not substrings, so any phrasing in any language works ("测试又挂了" ≙ "tests keep flaking"). Deterministic keyword + retry layers stay as the zero-cost floor. Tests pin md↔catalog consistency and the denylist; mute suppresses injection. 43 tests total.

## 0.3.0 — 2026-06-10

- Repetition trigger (`core/repetition.py`): detects manual retry loops — two retry-style messages in a row ("run it again" → "still failing") or three similar messages per session (token-hash Jaccard ≥ 0.6). Deterministic, prompt-path only, no message text stored. Catalog match takes precedence; the injected note names the pattern and lets the host model compose the `/goal`. New templates pass the inject-text denylist; 10 new tests (38 total).

## 0.2.0 — 2026-06-10

- Catalog: expanded triggers across all 7 entries (32 → 98) to catch natural phrasings — "make sure all tests pass", "the build won't compile", "keep an eye on the pr", "wait for the deploy", "increase test coverage", "migrations won't apply". Kept intent-shaped wording; avoided success-state phrases ("all tests pass" alone) that the Stop hook would match in the assistant's own summaries.

## 0.1.0 — 2026-06-09

- Deterministic matcher (`core/suggest.py`): trigger phrases, excludes, per-entry confidence, specificity ranking, session dedupe, fail-open.
- Catalog: 7 entries seeded from awesome-agent-loops; `build_catalog.py` with validation + CI drift gate.
- Claude Code adapter: `UserPromptSubmit` (context inject), `Stop` (additionalContext), `SessionStart` (state TTL cleanup).
- Codex CLI adapter: `UserPromptSubmit` + `Stop`, user-visible one-line output.
- Control: `core/ctl.py status|on|off`, `/loopable` command wrapper.
- Tests: matcher goldens, fail-open, inject-text denylist, adapter subprocess contracts, dedupe/TTL. ruff + mypy --strict clean.
