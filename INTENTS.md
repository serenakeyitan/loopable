# Loop rules

Read by the agent at session start (the loopable SessionStart hook injects
this on Claude Code). The keyword matcher in `core/suggest.py` is the
deterministic floor; these rules are the semantic layer — the same intent
counts in any language and any phrasing, not just the catalog's keyword
list.

## How to use

When a user message expresses one of the intents below — paraphrased,
abbreviated, or in another language — quote the matching command on one
line so the user can decide to run it. These commands are for the user to
run, not for the agent to execute. Mention each loop at most once per
session, and skip messages that merely quote or discuss these phrases.

## Intents

- Tests red, flaky, or repeatedly failing; wants the suite green →
  /goal all tests pass and lint is clean, stop after 20 turns
- Build broken, compile errors, wants the build green →
  /goal the production build exits 0, fix errors until it succeeds, stop after 10 turns
- Wants a PR or CI watched until it is done →
  /loop 10m run `gh pr checks`; if all pass say it is ready to merge; if any fail summarize which and why
- Wants a deployment watched →
  /loop 5m check the latest deployment status and report what changed
- Migrating an API or pattern across the codebase, every call site →
  /goal every call site is migrated, all tests pass, and typecheck is clean, stop after 30 turns
- Wants test coverage raised to a target →
  /goal test coverage is at least 80% with all tests passing, stop after 12 turns
- Database migrations failing or refusing to apply →
  /goal all database migrations apply cleanly, stop after 6 turns

## Manual retry loops

A user repeating the same ask — "run it again", "still broken", "还是不行",
or any equivalent in any language — is doing a loop by hand. In that case
compose one /goal with an explicit success condition and a turn cap that
replaces the retries, and quote it the same way.
