# ABOUTME: Change contract — /goal as mechanical enforcement of the orchestrator quality gate
# ABOUTME: Targets premature loop exit on "good enough" judgment before SCORE threshold is met

# Harness Change Contract: Goal-Backed Runs section in orchestrator-protocol

## Component

Rule: `rules/orchestrator-protocol.md`, new "Goal-Backed Runs (optional)" section before Score Reporting.

## Failure mode targeted

The orchestrator loop stops early because the working model judges the result "good enough" before the SCORE threshold is met: the 5-round ceiling and the ≥80 gate live only in prose, and prose does not prevent a turn from ending. `score-evidence-guard` blocks *false* SCORE claims but cannot force the loop to continue toward the gate. Anticipated failure; mechanism confirmed by /goal docs (evaluator = session-scoped prompt-based Stop hook, CLI 2.1.202 installed ≥ 2.1.139 required).

## Predicted improvement

Over the next 10 orchestrator sessions with deterministic criteria: every plan-approval message includes a proposed `/goal` line (compliance observable in traces). Qualitative: sessions where Max sets the goal reach the SCORE threshold or escalate explicitly, with zero silent sub-threshold stops.

## Invariants preserved

- `/goal` proposal only; Claude never claims to have set a goal it cannot set.
- Turn-cap clause always present and equal to the global 5-round ceiling (no unbounded loops).
- SKIP_SET tasks and human-judgment criteria stay out (UAT unchanged).
- `score-evidence-guard` behavior unchanged (the two are complementary, not overlapping).

## Falsification

If over 10 sessions the proposed conditions are consistently wrong-grained (evaluator loops on met conditions, or clears on unmet ones) — observable as goal churn in transcripts — the condition template is bad: revert or rewrite. Also revert if token spend per session grows >10% attributable to goal-forced extra turns that produce no score delta.

## Rollback

`git revert <commit>`. Affects: `rules/orchestrator-protocol.md` (one section).

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
