# Changelog

## 0.2.0 — 2026-06-10

- Catalog: expanded triggers across all 7 entries (32 → 98) to catch natural phrasings — "make sure all tests pass", "the build won't compile", "keep an eye on the pr", "wait for the deploy", "increase test coverage", "migrations won't apply". Kept intent-shaped wording; avoided success-state phrases ("all tests pass" alone) that the Stop hook would match in the assistant's own summaries.

## 0.1.0 — 2026-06-09

- Deterministic matcher (`core/suggest.py`): trigger phrases, excludes, per-entry confidence, specificity ranking, session dedupe, fail-open.
- Catalog: 7 entries seeded from awesome-agent-loops; `build_catalog.py` with validation + CI drift gate.
- Claude Code adapter: `UserPromptSubmit` (context inject), `Stop` (additionalContext), `SessionStart` (state TTL cleanup).
- Codex CLI adapter: `UserPromptSubmit` + `Stop`, user-visible one-line output.
- Control: `core/ctl.py status|on|off`, `/loopable` command wrapper.
- Tests: matcher goldens, fail-open, inject-text denylist, adapter subprocess contracts, dedupe/TTL. ruff + mypy --strict clean.
