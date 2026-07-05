# ABOUTME: Change contract for the score-evidence-guard Stop hook (two-confirmation gate import)
# ABOUTME: SCORE claims must carry fresh computational evidence; judge-only green is blocked

# Harness Change Contract: score-evidence-guard — SCORE requires fresh computational evidence

## Component

- Hook: `hooks/score-evidence-guard.py` + `hooks/score-evidence-guard.sh` (new, Stop event)
- Settings fragment: `hooks/settings.example.json` (Stop registration)
- Rule: `rules/orchestrator-protocol.md`, Score Reporting section (one line: evidence requirement)

Concept imported from `hikmaai-io/hikma-bringles` decision #2 (two-confirmation gate: no green
without a computational tool exit AND a judge verdict; "the loop trusts evidence, not prose").

## Failure mode targeted

The orchestrator reports `SCORE: <n>/100` (step 6) as a judge-only verdict: nothing verifies
mechanically that VERIFY/RE-VERIFY (steps 2/5) actually ran in the same round. A turn can claim
"92, PR ready" with stale or absent test evidence. The commit gate is covered downstream by
`pre-commit-gate.sh` (re-runs the tools independently), but the PR gate (>= 90) never passes
through any hook because pushes are manual, and just-do-it mode trusts the reported score.
This is the same self-grading-loop failure Bringles lists as its own M0 tech-debt ("gate
enforcement trusts the turn to run the tool").

## Predicted improvement

Over the next 10 traced sessions, 100% of turns emitting a `SCORE:` line contain a successful
verification command (verify-before-stop's `VERIFY_RE`) issued AFTER the last source edit of the
session (baseline: unmeasured, presumed non-compliant in FIX->SCORE rounds where RE-VERIFY gets
skipped). Blocks fire < 1 per session on average.

## Invariants preserved

- Fail-open: any parse/IO error exits 0 silently; hook never breaks a session.
- One nudge per turn via `stop_hook_active` guard (same contract as verify-before-stop).
- Read-only: no state files written; the transcript is the only input.
- Turns without a `SCORE:` line are never blocked (zero cost for normal turns).
- No `--no-verify`-style bypass added; escape hatch is stating explicitly that verification
  happened in a subagent/sidechain, after which the second stop is not blocked.
- Sidechain events ignored, consistent with verify-before-stop.

## Known false-allow residuals (accepted, measured at Result time)

Evidence freshness is computed from the main transcript only. Two edit channels stay invisible
and can let stale evidence pass: (a) file mutations via Bash (`sed -i`, `git apply`,
`git checkout`); (b) `pip install ruff`-style commands matching `VERIFY_RE` without verifying
anything. Write-class subagent launches ARE handled: a `Task`/`Agent` call with
`subagent_type: software-engineer` invalidates earlier evidence (read-only reviewers do not,
since REVIEW legitimately runs after VERIFY). A verify with no `tool_result` gets the benefit
of the doubt; `git commit` counts as evidence because pre-commit-gate re-runs the suite on it.

## Falsification

If over the next 10 traced sessions the hook blocks legitimately-scored turns more than 2 times
per session (false positives, e.g. verification delegated to subagents whose commands are
sidechain-invisible), the freshness heuristic is wrong: revert or supersede with a stamp-based
design. Also revert if any session shows the hook firing on a turn with no `SCORE:` line.
The false-allow direction must be measured too: at Result time, spot-check traces for SCORE
events whose nearest preceding verify predates a Bash-mediated file mutation; if that residual
shows up in practice (> 1 occurrence across the sample), supersede with a stamp-based design
rather than widening this heuristic.

## Rollback

`git revert <commit>`; remove `~/.claude/hooks/score-evidence-guard.sh` symlink and the Stop
entry from `~/.claude/settings.json`. Affects: hooks/score-evidence-guard.py,
hooks/score-evidence-guard.sh, hooks/tests/test_score_evidence_guard.py,
hooks/settings.example.json, rules/orchestrator-protocol.md.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
