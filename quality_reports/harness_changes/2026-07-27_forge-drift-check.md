# ABOUTME: Change contract for the forge drift check (SessionStart scan of ~/.claude against the checkout)
# ABOUTME: Borrowed from gstack's auto-update defensive patterns, stripped of the update itself

# Harness Change Contract: SessionStart drift check between the checkout and ~/.claude

## Component

- `hooks/forge-drift-check.sh` (new): SessionStart hook, matcher `startup|resume`, timeout 10.
- `hooks/settings.example.json`: one entry appended to the existing `startup|resume` block.
- `hooks/tests/test_forge_drift_check.py` (new): matrix rows 10-16 of
  `quality_reports/plans/active/2026-07-27_gstack-borrowings.md`.
- `README.md`, enforcement-layer section: the bootstrap caveat (the check cannot see its own
  missing installation).

## Failure mode targeted

Post-merge install drift surviving undetected across sessions: stale copies, missing symlinks, and
hooks installed but never registered in `settings.json`. Two documented incidents, both silent for
weeks. (1) `~/.claude/agents/` held stale *copies* of the forge agent definitions; two manual audits
(2026-07-04 and 2026-07-05) walked past them, and the divergence was only found on 2026-07-23.
(2) Every PR adding a hook file needs a manual post-merge `ln -s`, which is remembered by habit
alone. `install.sh:211-233` guards existing symlinks at install time; nothing looks at the installed
tree afterwards, so a session runs with a half-installed harness and behaves as if the rules simply
did not exist.

## Predicted improvement

Time-to-detection for an install drift event drops from weeks (two incidents, both found by
unrelated manual inspection) to the first session after the merge that caused it. Sample needed:
the next 2 merges that add or rename a hook, agent, or rule file. Numeric side of the same claim:
in sessions with no drift the hook prints 0 lines, so the cost of the guarantee is 0 tokens in the
steady state, and at most 3 lines when it fires.

## Invariants preserved

- **Read-only.** No writes anywhere, no network, no git invocation, no auto-fix, no throttle file.
  Every finding is reported with the exact `ln -s` (or "register in settings.json") the human runs.
- **Exit 0 on every path.** `set +e`, the scan runs inside a command substitution, and a failure
  inside it truncates output instead of failing the session.
- **Silent when clean.** Zero output, zero stderr. This is what buys the right to run unthrottled;
  if the clean case ever prints, the change has become noise.
- **Non-forge components are invisible to it.** `notify.sh` and `herdr-agent-state.sh` live in the
  same `~/.claude/hooks/` and must never be flagged. This holds by construction, not by an
  exclusion list: an entry counts only when it resolves into the checkout the hook itself was
  installed from.
- **Output budget of 3 lines**, aggregated with a `+N more` tail beyond that.
- **`~/.claude/.forge-omit` always wins**, so a deliberately partial install on a second machine
  stays quiet.

## Falsification

Either of these reverts the change:

1. A **third stale-install incident on a machine where the check runs**: drift of a class the check
   claims to cover (dangling symlink, missing entry in a managed category, unregistered hook, stale
   regular-file copy, forge-named live symlink repointed outside the checkout) that is discovered by
   hand rather than by the hook. The fifth class was added in review fix round 1 (plan decision 27);
   it is also the class most exposed to falsification #2 below, since a deliberate local override
   emits a line every session until the name lands in `.forge-omit`.
2. **Recurring false positives**: any `[forge-drift]` line, in 20 sessions, reporting something Max
   then chooses not to fix and does not silence via `.forge-omit`. That is the state that trains him
   to skim past the prefix, at which point the check costs attention and buys nothing.

Not falsification: silence on a machine that installed forge by copy rather than by symlink. The
category gate (a category with zero forge symlinks is not scanned) is a deliberate false-positive
tradeoff, and copies are what `install.sh` produces by default.

## Rollback

`git revert <commit>`, then remove the `~/.claude/hooks/forge-drift-check.sh` symlink and the
`forge-drift-check.sh` entry from the `SessionStart` `startup|resume` block in
`~/.claude/settings.json`. Affects: `hooks/forge-drift-check.sh`, `hooks/settings.example.json`,
`hooks/tests/test_forge_drift_check.py`, `README.md`.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|

Verdict: **kept** / **reverted** / **modified** (link to follow-up contract). If reverted, write one line on why the prediction missed.
