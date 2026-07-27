# ABOUTME: Change contract for the freeze guard (repo-local edit boundary hook + /freeze skill)
# ABOUTME: Borrowed from gstack, redesigned fail-open and repo-local after a 2-lab second opinion

# Harness Change Contract: repo-local freeze boundary for Edit/Write/NotebookEdit

## Component

- `hooks/freeze-guard.sh` (new): PreToolUse hook on Edit, Write, NotebookEdit.
- `hooks/_freeze_boundary.sh` (new): shared basename constant `FREEZE_BOUNDARY_BASENAME` plus the
  git-root / physical-path resolvers.
- `skills/freeze/SKILL.md` (new): `/freeze <dir>`, `/freeze status`, `/freeze off`.
- `hooks/settings.example.json`: three PreToolUse matcher entries, timeout 10.
- `hooks/tests/test_freeze_guard.py` (new) and `hooks/tests/test_hook_constants_sync.py` (extended
  with the skill-quotes-the-constant assertion).

## Failure mode targeted

Edits landing outside the intended work area during focused debugging. The orchestrator invariant
"software-engineer is read-write, **scoped to its assigned files**" (`rules/orchestrator-protocol.md`,
Invariants) has no deterministic enforcement whatsoever: the scope is prose in a prompt, and a long
debugging session drifts out of it without anything noticing. `quality_reports/plans/tech-debt.md:7`
already asks for a PreToolUse write-gate in this family.

## Predicted improvement

In sessions where `/freeze` is active, out-of-boundary Edit/Write/NotebookEdit calls drop to zero
(the hook denies them, by construction), and the model's next action is a visible re-scope rather
than a silent out-of-scope edit. Sample needed to judge the borrow itself: 10 sessions where a
boundary was set at least once. Secondary, unmeasurable-but-stated expectation: fewer than 1 in 10
of those sessions ends with `/freeze off` used as an escape from a boundary that was simply wrong.

## Invariants preserved

- **Fails open, always.** Missing `jq`, garbled hook JSON, missing/empty/newline-bearing
  `tool_input.file_path`, unusable boundary file: every one of these allows the edit and prints at
  most one line to stderr. Exit code is 0 on every path.
- **Inert when unused.** No boundary file at the edited file's git root means zero output, zero
  stderr, no git writes, no network. Every session that never runs `/freeze` is unaffected.
- **Repo-local.** The boundary is resolved from the git root of the *edited file*, never from the
  session cwd, so a freeze in one repo cannot block edits in another (or in another worktree).
- **Not a security boundary, and says so.** `Bash` is not gated; the skill states this in its own
  first section rather than letting the name imply containment.
- **One source of truth for the basename.** The skill and the hook agree by test, not by luck.

## Falsification

Either of these reverts the change:

1. A session where a boundary is active and a **legitimate in-boundary edit is denied** (a false
   block). The fail-open design leaves this as the only unrecoverable outcome, so one occurrence is
   enough.
2. A traced session with a boundary set in which **more than zero out-of-boundary edits pass**
   through Edit/Write/NotebookEdit. That means the resolution logic does not hold and the hook is
   costing a PreToolUse slot for a guarantee it does not provide.

Not falsification: out-of-boundary writes performed through `Bash`. Those are documented as out of
scope, and treating them as a miss would be scoring the change against a claim it never made.

## Rollback

`git revert <commit>`, then remove the `~/.claude/hooks/freeze-guard.sh` and
`~/.claude/hooks/_freeze_boundary.sh` symlinks and the three PreToolUse entries from
`~/.claude/settings.json`. Affects: `hooks/freeze-guard.sh`, `hooks/_freeze_boundary.sh`,
`hooks/settings.example.json`, `hooks/tests/test_freeze_guard.py`,
`hooks/tests/test_hook_constants_sync.py`, `skills/freeze/SKILL.md`.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|

Verdict: **kept** / **reverted** / **modified** (link to follow-up contract). If reverted, write one line on why the prediction missed.
