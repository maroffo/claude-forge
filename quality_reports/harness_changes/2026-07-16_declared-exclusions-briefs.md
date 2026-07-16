# ABOUTME: Change-contract for declared exclusions (page faults) in subagent briefs
# ABOUTME: Briefs state what was cut and how to recover it, instead of leaving omissions implicit

# Harness Change Contract: subagent briefs declare exclusions as recoverable page faults

## Component

rule (`rules/orchestrator-protocol.md`), Implementation (Step 1): one paragraph on declared exclusions in scoped briefs (`excluded: <files/areas>; read on demand from <path>`). Idea imported from context-kernel §06 (page fault: no inverse of a projection, only declared, targeted recovery).

## Failure mode targeted

Briefs scope context implicitly: the agent receives files A and B and nothing says C was deliberately cut. An implicit omission reads as "does not exist": the agent concludes from absence, guesses, or halts (LOCALIZE mismatches on planned-but-unlisted files, reviewers judging without the context that was trimmed for budget), instead of fetching the missing piece.

## Predicted improvement

Qualitative, sample 10 orchestrated multi-agent sessions: scoped briefs carry an `excluded:` line; agents recover cut material by reading it on demand instead of concluding from absence. Expected visible effect: fewer DRIFT/LOCALIZE mismatches attributable to missing context.

## Invariants preserved

- Briefs stay lean: the exclusion line lists only deliberate cuts, never an inventory of everything untouched.
- No change to parallelism limits, permission scoping (reviewers read-only), or the LOCALIZE/DRIFT protocol itself.
- Subagents were always allowed to read on demand; this only makes the cut surface explicit.

## Falsification

Over the next 10 sessions: exclusion lists grow longer than the included scope (brief bloat), or agents systematically read everything declared excluded (token cost rises with no precision gain). Either pattern twice → revert.

## Rollback

`git revert <this commit>`. Affects: rules/orchestrator-protocol.md.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
