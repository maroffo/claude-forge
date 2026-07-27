# ABOUTME: Change contract for orchestrator-side finding consolidation between REVIEW (step 3) and FIX (step 4)
# ABOUTME: Source: 2026-07-27 swarm-forge borrowings analysis, second opinion by Gemini + DeepSeek (unanimous: dedup at the orchestrator, not per-agent negative scope)

# Harness Change Contract: one defect, one deduction at SCORE

## Component

`skills/orchestrator/SKILL.md` (new `### Finding Consolidation (step 3 → 4)` subsection under Review Routing), `rules/orchestrator-protocol.md` (loop step 3 gains one clause pointing at that subsection), `rules/quality-gates.md` (`## How to Score` now scores the consolidated list).

Zero edits to `agents/`: the seven reviewer prompts are untouched by design.

## Failure mode targeted

One defect reported by two agents is subtracted twice at SCORE. The routing table maps file patterns to agents and never defect classes to owners, so scopes overlap (verified 2026-07-27: architecture-reviewer "Silent success / fail-open" vs security-reviewer "Fail-open enforcement"; architecture-reviewer "Build-time / baked-in values" vs dx-reviewer "Build-time config chain"), and nothing between step 3 and step 6 merges reports. `rules/quality-gates.md` then subtracts per finding with no uniqueness constraint: two Majors for the same fail-open at `x.go:42` is -20 for one problem. This is a scoring arithmetic bug, not noise.

## Predicted improvement

Qualitative, detectable on the first traced session that runs REVIEW with two or more agents: SCORE arithmetic counts each defect once, so the score reflects the number of defects rather than the number of reviewers that happened to match the file pattern. Secondary and previously invisible: the duplicate rate across the seven reviewers becomes readable from the `reported_by` fields (smallest useful sample: 5 REVIEW-running sessions), where before it silently inflated penalties.

## Invariants preserved

- Consolidation never lowers the highest severity in a group: a Minor and a Major describing the same defect merge to Major.
- Agent prompts are unchanged (zero edits under `agents/`), so no reviewer's scope narrows as a result of this change.
- The two existing inline depth-gradient deferrals stay untouched: security-reviewer defers deep CVE analysis to dependency-reviewer, database-reviewer defers complex N+1 to performance-reviewer.
- Distinct defects at the same location are never merged: an N+1 and a god-object both filed at `y.go:10` remain two findings.
- Review agents stay read-only; consolidation is orchestrator work between step 3 and step 4.

## Falsification

If a traced session shows a defect that NO agent reported because consolidation was read as permission to narrow reviewer scope (an agent's report citing "another agent owns this", or a post-hoc bug traced to a class every reviewer punted), the change converted visible duplicates into silent seam-loss: revert.

## Rollback

`git revert <commit>`. Affects: `skills/orchestrator/SKILL.md`, `rules/orchestrator-protocol.md`, `rules/quality-gates.md`.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
