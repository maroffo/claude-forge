# ABOUTME: Change-contract template for harness mutations (hooks, rules, skills, settings)
# ABOUTME: Six fields from arxiv 2605.18747 §5.2.3 (treat harness edits like safety-critical code)

# Harness Change Contract: <one-line description>

Filename convention: `quality_reports/harness_changes/YYYY-MM-DD_<short-slug>.md`. Authored before the change lands. Linked from the commit body. Append-only after merge (add a Result section, do not edit the contract).

## Component

What part of the harness is being modified. One of: hook (`hooks/*.py|*.sh`), rule (`rules/*.md`), skill (`skills/<name>/`), settings fragment (`settings.json` or `settings.local.json`), agent definition (`agents/*.md`), or other (specify).

> e.g. `rules/orchestrator-protocol.md`, step LOCALIZE: adding `scope_reduction_rationale` escape hatch.

## Failure mode targeted

The specific observed (or anticipated) failure this change is meant to prevent. Cite a session log, trace, or incident if one exists. **One change = one failure mode.** Bundling multiple targets makes falsification (below) ambiguous.

> e.g. "Agent halted LOCALIZE on a planned-but-not-needed file because the protocol had no way to record 'turned out unnecessary'. Observed in session 2026-04-18, halted at step 4 of 7."

## Predicted improvement

What metric should move, by how much, in which direction. Prefer numeric predictions (rates, counts, ratios) over adjectives. If you cannot predict a number, write the qualitative outcome AND the smallest sample needed to detect it.

> e.g. "LOCALIZE_halts_per_session drops from ~0.3 to ~0.05 over next 20 sessions." | "After 5 bug-fix tasks, fewer than 1 mistakes REPRODUCE→FIX cycle."

## Invariants preserved

Properties this change MUST NOT break. List the boundary conditions that, if violated, would make the change a regression even if the predicted improvement happened.

> e.g. "No `--no-verify` paths added." | "REVIEW agents stay read-only." | "Token cost per round does not grow >5%." | "All v1 traces still parse."

## Falsification

The concrete observation that would tell us this change made things worse. Must be checkable without rerunning every prior task. Prefer: a trace assertion, a test, a regression suite item, or a counted-event threshold.

> e.g. "If LOCALIZE_halts_per_session goes UP over the next 10 sessions, revert." | "If a session emits more than 2 scope_reduction_rationale entries, the change is being abused, revert."

## Rollback

One-liner: how to undo. Include the git ref to revert OR the explicit file/line to restore. If the change touches multiple files, list all of them.

> e.g. "`git revert <commit>`. Affects: rules/orchestrator-protocol.md, skills/harness-trace/src/harness_trace/models.py."

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|

Verdict: **kept** / **reverted** / **modified** (link to follow-up contract). If reverted, write one line on why the prediction missed.
