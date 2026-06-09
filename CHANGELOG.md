# Changelog

## 0.1.0 — 2026-06-09

- Deterministic matcher (`core/suggest.py`): trigger phrases, excludes, per-entry confidence, specificity ranking, session dedupe, fail-open.
- Catalog: 7 entries seeded from awesome-agent-loops; `build_catalog.py` with validation + CI drift gate.
- Claude Code adapter: `UserPromptSubmit` (context inject), `Stop` (additionalContext), `SessionStart` (state TTL cleanup).
- Codex CLI adapter: `UserPromptSubmit` + `Stop`, user-visible one-line output.
- Control: `core/ctl.py status|on|off`, `/loopable` command wrapper.
- Tests: matcher goldens, fail-open, inject-text denylist, adapter subprocess contracts, dedupe/TTL. ruff + mypy --strict clean.
