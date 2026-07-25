# ABOUTME: Change contract for splitting the orchestrator protocol into an always-on spine plus an on-demand skill
# ABOUTME: Source: "The new rules of context engineering for Claude 5 generation models" (claude.com blog), rule 3, progressive disclosure

# Harness Change Contract: orchestrator spine always on, detail on demand

## Component

`rules/orchestrator-protocol.md` (2264 -> 465 words) and the new `skills/orchestrator/SKILL.md`, which receives the moved sections verbatim: Research + Complexity, Implementation and Executor selection, the sub-protocol table, VERIFY, Review Routing, Blast Radius, UAT, Parallelism, Effort assignment, Escalation, Just-do-it, Goal-Backed Runs, Trace Capture.

The spine keeps what must survive without a skill load: the 10 loop steps, SKIP_SET, the literal report lines the trace extractor keys on, the read-only/committer/pi invariants, and an explicit instruction to load the skill at the first step actually run.

That load point was written as "before step 1" in the first draft of this change and corrected during PR review: the skill also owns the step 0 complexity verdict and the `/goal` proposal made at plan approval, so "before step 1" left two always-on gates in `plan-first-workflow` (Living Plans, Annotation Cycle) keyed on a term whose definition was not yet loaded.

## Failure mode targeted

The full contractor-mode protocol was in context on every session, including the ones that never enter the loop. At 2264 words it was the single heaviest always-on file (the July token baseline already flagged it as the heaviest, at 1075 tokens), and most of it applies only after plan approval on a non-SKIP_SET task. Anthropic's Claude 5 guidance calls this the case for progressive disclosure: move the detail into a skill the model loads when it reaches the step that needs it.

## Predicted improvement

Always-on rules drop by roughly 1800 words (measured: total always-on context 5059 -> 3055 words including the CLAUDE.md change). Over the next 10 non-SKIP_SET sessions, the loop still runs identically: LOCALIZE / DRIFT / SCORE / BLAST-RADIUS lines appear at the same rate per session as in the pre-change trace corpus, and the `orchestrator` skill is loaded in at least 8 of those 10.

## Invariants preserved

- The literal report lines stay always-on, in `rules/`: telemetry must not depend on a skill being loaded.
- SKIP_SET stays always-on: the decision NOT to enter the loop must be makeable without loading anything.
- The pi executor constraints (never commits, never takes a review or spec role, DRIFT mandatory) stay stated in the spine as well as in the skill: they are safety boundaries, not detail.
- No section content is reworded during the move, with three declared exceptions: pointers to "the global 5-round ceiling" now read as the plan's Budget (see the complexity-budget contract), severity words follow the canonical Critical/Major/Minor casing, and two em dashes carried over from the old file were replaced with a colon to satisfy `make check`.
- A fresh session can still run the loop end to end from the spine plus the skill, with no chat history.

## Falsification

If, over the next 10 non-SKIP_SET sessions, the `orchestrator` skill is loaded in fewer than 8, or the per-session rate of LOCALIZE / DRIFT / BLAST-RADIUS lines drops below the pre-change baseline, the detail is not arriving when it is needed: revert to the single always-on file.

Second falsifier: any session that reaches step 4 (FIX) having invented its own review routing or parallelism limits, rather than the ones in the skill, means the load happened too late: move those two tables back into the spine.

## Rollback

`git revert <commit>`. Affects: `rules/orchestrator-protocol.md`, `skills/orchestrator/SKILL.md`, plus the cross-reference repoints in `README.md`, `skills/_INDEX.md` and `agents/software-engineer-pi/AGENT.md`.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
