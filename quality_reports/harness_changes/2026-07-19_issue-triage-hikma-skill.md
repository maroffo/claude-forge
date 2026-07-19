# ABOUTME: Change contract for the issue-triage-hikma skill (auto-eligibility for the autonomous loop)
# ABOUTME: Supersedes one invariant of 2026-07-19_issue-loop-hikma-skill.md (manual-only issue selection)

# Harness Change Contract: add `issue-triage-hikma` (auto-triage feeding issue-loop-hikma)

## Component

New skill `issue-triage-hikma` (SKILL.md) in the private `claude-hikma-skills` repo, symlinked as `skills/issue-triage-hikma` (untracked here, `.gitignore` `skills/*-hikma`); edits to `issue-loop-hikma/SKILL.md` in the same repo (label table, selection step c, references); registration rows in `skills/_INDEX.md` and `CLAUDE.md.example`. Supersedes the "the loop only ever touches issues Max labeled agent:ready; it never self-selects work" invariant of `2026-07-19_issue-loop-hikma-skill.md`; every other invariant of that contract stands.

## Failure mode targeted

The loop is not actually autonomous: with `agent:ready` set only by Max, an empty label queue stalls the loop until he triages, so throughput degenerates to his manual triage cadence. Requested by Max on 2026-07-19 ("volevo un loop autonomo").

## Predicted improvement

From a zero-label state, one `/issue-loop-hikma` invocation completes a full iteration (triage, plan, implement, PR) with no human input for at least one simple/moderate issue, provided one exists. Over the first 20 auto-triage verdicts, Max reverses at most 4 (removes `agent:ready` or downgrades to `agent:human`).

## Invariants preserved

- Triage writes labels and comments only: never code, never closes issues, never removes human-set labels.
- `agent:human` is a permanent human veto; triage never overrides or removes it.
- 🔴 classes (security-sensitive core, data-loss migrations, release/infra, unresolved design debates) are never auto-readied.
- All surviving issue-loop-hikma rails unchanged: push only `agent/*`, no merge ever, one issue in flight, DoD threshold 90 gate pr, escalation over bar-lowering.
- Every verdict carries a rationale comment (auditable; no silent labeling).

## Falsification

Within the first 10 auto-readied issues: 3 or more vetoed by Max or ending `agent:blocked` with a "should not have been attempted" root cause means the rubric is too loose; tighten or revert. A single 🔴-class issue auto-readied means the hard rail failed: revert immediately.

## Rollback

`git revert <commit>` on claude-forge (index rows), `git revert` the skill commit in claude-hikma-skills, remove the `issue-triage-hikma` symlinks in `~/.claude/skills` and `skills/`. Affects: claude-hikma-skills/{issue-triage-hikma,issue-loop-hikma}/SKILL.md, skills/_INDEX.md, CLAUDE.md.example. The loop falls back to Max-only `agent:ready` labeling (prior contract behavior). Labels `agent:needs-spec`/`agent:human` are inert and can stay.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
