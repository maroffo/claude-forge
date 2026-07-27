# ABOUTME: Change contract for the new issue-loop-wishew skill (autonomous issue-to-PR loop, Wishew monorepo)
# ABOUTME: Six fields per harness-changes rule; authored with the change, append-only after merge

# Harness Change Contract: add `issue-loop-wishew` skill (autonomous issue → plan → worktree impl → PR, full-auto)

## Component

New skill `issue-loop-wishew` (SKILL.md + references/pr-template.md + loop.py) in the private `claude-skills-wishew` repo, symlinked as `skills/issue-loop-wishew` per the `skills/*-wishew` gitignore convention, plus registration rows in `skills/_INDEX.md` and `CLAUDE.md.example`. Port of `issue-loop-hikma` (contract 2026-07-19_issue-loop-hikma-skill.md) onto the Wishew Projects v2 board substrate.

## Failure mode targeted

Assigned, well-specified Wishew issues sit in the board's Ready column without progressing, because every issue requires a manually driven session per stage (plan-forge, fresh implementation session, PR authoring), and the resulting PRs carry no structured human-QA handoff. Anticipated failure, requested by Max on 2026-07-19 (same class as the hikma contract, different substrate and gate policy).

## Predicted improvement

Over the first 10 eligible Ready issues: at least 7 reach an open PR meeting the DoD (SCORE >= 90, gate pr) with a derivable Manual QA checklist, with zero human intervention beyond board curation (moving issues to Ready and assigning). Escalations (`agent:blocked`) are expected and count as correct behavior, not failures. Note the deliberate divergence from hikma: no plan-approval gate for `complex` verdicts (Max, this session); the counterweights are the mandatory second opinion, the complex-plan audit comment, and escalate-on-all-reviewers-down.

## Invariants preserved

- No auto-merge, ever; PRs are opened, never merged or auto-merge-enabled by the loop.
- Push restricted to `agent/issue-<N>-<slug>` branches; main/master untouched; no force-push.
- No `--no-verify` or hook bypass paths introduced; pre-commit-gate, main-branch-guard, score-evidence-guard all stay active in worktrees.
- plan-forge quality bar unchanged (second opinion mandatory, DoD threshold 90 gate pr, 5-round ceiling with escalation).
- Strictly one issue in flight; the board's In progress status is the lock, and the loop never claims over it (including human-set In progress).
- The loop only picks issues Max curated into Ready and assigned to him; `agent:human` is a permanent veto only a human removes.
- `work-next-wishew` keeps its manual single-shot semantics (its dev→main staleness fix ships alongside, as a plain bugfix commit, not part of this contract).

## Falsification

Any of the following within the first 10 loop-produced PRs means the change made things worse:
- 2 or more PRs closed unmerged because the implementation was wrong or out of scope: the full-auto bet failed; do not revert wholesale, write a superseding contract re-introducing the hikma `complex`→human gate.
- Any push to a non-`agent/*` branch, any merge, or any hook bypass performed by the loop (rail breach: revert immediately, sample size 1).
- More than 4 of 10 iterations end in `agent:blocked` or `agent:needs-spec` (the loop generates triage noise instead of PRs; redesign the eligibility bar).

## Rollback

`git revert <commit>` on claude-forge (index rows) and on claude-skills-wishew (skill commit), remove the `~/.claude/skills/issue-loop-wishew` symlink. Affects: claude-skills-wishew/issue-loop-wishew/{SKILL.md,references/pr-template.md,loop.py}, skills/_INDEX.md, CLAUDE.md.example. GitHub-side labels (`agent:*`) are inert without the skill and can stay.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| 2026-07-27 | 1 attributable PR of the 10-PR window (pilot #3485, 2026-07-19) | insufficient data: the pilot PR wishew-monorepo#3485 merged at SCORE 97/100 and 0 PRs closed unmerged, but only 1 of 10 datapoints exists and the 4 later agent/* PRs in that repo (#3646 open, #3653, #3661, #3673, all 2026-07-24) use agent/fix-* naming rather than the loop's agent/issue-N-slug so they cannot be attributed; separately the component is currently unreachable on this machine, no claude-skills-wishew repo exists anywhere under /Users/maroffo and no issue-loop-wishew symlink exists in ~/.claude/skills or skills/, while skills/_INDEX.md line 31 still advertises it | kept |
