# ABOUTME: Change contract for the new issue-loop-hikma skill (autonomous issue-to-PR loop, hikmaAI repos)
# ABOUTME: Six fields per harness-changes rule; authored with the change, append-only after merge

# Harness Change Contract: add `issue-loop-hikma` skill (autonomous issue → plan → worktree impl → PR)

## Component

New skill `issue-loop-hikma` (SKILL.md + references/pr-template.md) in the private `claude-hikma-skills` repo, symlinked as `skills/issue-loop-hikma` per the client-skills convention (untracked here via the `.gitignore` `skills/*-hikma` rule), plus registration rows in `skills/_INDEX.md` and `CLAUDE.md.example`.

## Failure mode targeted

Triaged, well-specified GitHub issues in the hikmaAI repos (mirsad/wasit/frontend) sit idle because every issue requires a manually driven session for each stage (plan-forge, fresh implementation session, PR authoring). Anticipated failure, requested by Max on 2026-07-19: eligible issues do not progress without hand-orchestrated sessions, and PRs arrive without a structured human-QA handoff.

## Predicted improvement

Over the first 10 issues labeled `agent:ready`: at least 7 reach an open PR meeting the DoD (SCORE >= 90, gate pr) with a derivable Manual QA checklist, with zero human intervention beyond (a) triage labeling and (b) plan approval for `complex` verdicts. Escalations (`agent:blocked`) are expected and count as correct behavior, not failures.

## Invariants preserved

- No auto-merge, ever; PRs are opened, never merged or auto-merge-enabled by the loop.
- Push restricted to `agent/issue-<N>-<slug>` branches; dev/main/master untouched; no force-push.
- No `--no-verify` or hook bypass paths introduced; pre-commit-gate, main-branch-guard, score-evidence-guard all stay active in worktrees.
- plan-forge quality bar unchanged (second opinion mandatory, DoD threshold 90 gate pr, 5-round ceiling with escalation).
- Strictly one issue in flight across all repos (anti-collision, incident #569).
- The loop only ever touches issues Max labeled `agent:ready`; it never self-selects work.

## Falsification

Any of the following within the first 10 loop-produced PRs means the change made things worse; revert:
- 2 or more PRs closed unmerged because the implementation was wrong or out of scope (plan gate insufficient).
- Any push to a non-`agent/*` branch, any merge, or any hook bypass performed by the loop (rail breach: revert immediately, sample size 1).
- More than 4 of 10 iterations end in `agent:blocked` (the loop generates triage noise instead of PRs; redesign the eligibility bar).

## Rollback

`git revert <commit>` on claude-forge (index rows), `git revert` the skill commit in claude-hikma-skills, and remove the `~/.claude/skills/issue-loop-hikma` and `skills/issue-loop-hikma` symlinks. Affects: claude-hikma-skills/issue-loop-hikma/{SKILL.md,references/pr-template.md}, skills/_INDEX.md, CLAUDE.md.example. GitHub-side labels (`agent:*`, `plan:approved`) are inert without the skill and can stay.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| 2026-07-27 | 33 agent-branch PRs across 4 hikmaAI repos, 2026-07-19 to 07-26, against a 10-PR prediction window | prediction beaten: the first 10 by date all merged against a bar of 7 of 10 reaching an open PR at DoD, and all 33 are merged with 0 closed unmerged; agent:blocked is 0 across all four repos against a falsifier of more than 4 of 10; no push outside agent/* observed, though one branch (hikma-mirsad #757 agent/topical-ml-control) departs from the mandated agent/issue-N-slug form while staying inside the agent/ rail | kept |
