# loopable rules

Read by the coding agent (the loopable hook injects this once per session,
with a short reminder every ~20 messages). These are rules of judgment for
one decision: is this moment loop-shaped, and if so, which single command
to offer. The judgment is the agent's — there is no keyword list; the same
intent counts in any language and any phrasing.

## The decision

A moment is loop-shaped when finishing requires repeating a check-act
cycle, or watching something until a condition flips:

- **Verify-until-green** — the user wants a state a command can verify
  (tests pass, build exits 0, types check, migrations apply, coverage hits
  a number) and getting there will plausibly take more than one fix-verify
  cycle.
- **Watch-until-done** — the user wants something monitored on an interval
  (CI on a PR, a deployment, a long-running job) and reported on when it
  finishes or breaks.
- **Manual retry in progress** — the recent conversation shows the user
  re-asking the same thing ("run it again", "still broken", 还是不行, any
  equivalent): they are looping by hand and a loop command would do it
  for them.

Not loop-shaped: questions, one-shot edits, renames, anything a single
attempt settles. When unsure, stay quiet — a wrong nudge costs trust; a
missed one costs nothing.

## What to offer

One command, quoted on a single line, composed for the situation:

  /goal <objectively verifiable success condition>, stop after N turns
  /loop <interval> <check-and-report instruction>     (Claude Code only)

Compose from what the conversation knows: name the concrete artifact (the
failing test, the error message, the PR, the endpoint); pick a success
condition a command run can confirm, not an opinion; cap turns in
proportion to scope (5-30). Offer each loop at most once per session; the
user decides whether to run it — these commands are for the user, not for
the agent to execute. Skip messages that merely quote or discuss loop
phrasings, and skip suggesting a loop right after reporting that the work
already succeeded.

## Reference library

Proven shapes seeded from awesome-agent-loops — adapt freely rather than
quoting blindly:

- Test suite red or flaky →
  /goal all tests pass and lint is clean, stop after 20 turns
- Build broken or won't compile →
  /goal the production build exits 0, fix errors until it succeeds, stop after 10 turns
- Watch a PR's CI →
  /loop 10m run `gh pr checks`; if all pass say it is ready to merge; if any fail summarize which and why
- Watch a deployment →
  /loop 5m check the latest deployment status and report what changed
- API or pattern migration across a codebase →
  /goal every call site is migrated, all tests pass, and typecheck is clean, stop after 30 turns
- Raise test coverage to a target →
  /goal test coverage is at least 80% with all tests passing, stop after 12 turns
- Database migrations failing →
  /goal all database migrations apply cleanly, stop after 6 turns

On Codex, offer /goal shapes only (Codex has no /loop).
