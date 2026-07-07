# ABOUTME: Change contract — /loop post-PR babysitting pattern in source-control skill
# ABOUTME: Targets PR feedback (CI failures, review comments) sitting unaddressed until manual polling

# Harness Change Contract: Post-PR Loop section in source-control

## Component

Skill: `skills/source-control/SKILL.md`, new "Post-PR Loop (babysitting)" section.

## Failure mode targeted

After a PR opens, CI failures and review comments sit unaddressed until Max manually checks: the harness has no pattern for interfacing with external systems on an interval. Anticipated failure, imported from the ClaudeDevs loops article (time-based loops for external environments).

## Predicted improvement

Qualitative, sample = next 5 PRs where the loop is offered and used: time from CI failure/review comment to addressed fix drops from "next manual check" (hours) to ≤ 2 loop intervals (~20 min). Observable: loop-driven fix commits on PR branches.

## Invariants preserved

- Push scope: only the loop's PR branch, only during that loop session. NEVER-push everywhere else (decision #4 in plan 2026-07-07_loop-primitives-integration).
- No `--force` (bare) ever; no hook bypass (`--no-verify` family stays forbidden) under loop pressure.
- Pre-commit gate runs on every loop commit.
- Loop stops at merge; no idle recurring runs.

## Falsification

If a loop pushes outside its PR branch even once, revert the push-authorization clause immediately (keep the read-only monitoring variant). If over 5 PRs the loop mostly burns turns on "no change" checks (interval mismatch), tighten the guidance or revert.

## Rollback

`git revert <commit>`. Affects: `skills/source-control/SKILL.md` (one section).

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
