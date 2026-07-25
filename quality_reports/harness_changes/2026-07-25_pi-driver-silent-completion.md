# ABOUTME: Change contract for the pi driver going idle without delivering its report, and for symlink-blind anomaly checks
# ABOUTME: Both failure modes observed live on 2026-07-25 across four driver runs

# Harness Change Contract: the pi driver must deliver its report, and must see out-of-repo edits

## Component

`agents/software-engineer-pi/AGENT.md`: step 5 of the protocol (report delivery on message-initiated runs) and the anomalies line of the report format (symlink boundary check).

## Failure mode targeted

Two failures observed in a single session (2026-07-25), both of which make a pi run look successful when it is not observable:

1. **Silent completion.** Three of four driver runs went idle without their report reaching the orchestrator. The runs that were resumed with a message never delivered anything: a subagent's final text is its return value only on the initial run, and nothing in the driver's protocol told it to reply with SendMessage when resumed. The orchestrator had to reconstruct model id and outcome from `~/.pi/agent/sessions/*.jsonl` and from the diff. Since the driver has no native-implementation fallback by construction, a genuinely failed pi run would have been just as silent as a successful one.
2. **Symlink-blind anomaly check.** A brief named five skills by path; two of them (`skills/advanced-review`, `skills/issue-loop-hikma`) are symlinks into separate repositories. pi edited files in those repos, on their `main` branches, and the driver reported `anomalies: none` because `git status --short` in the workdir shows nothing for a symlinked directory.

## Predicted improvement

Over the next 10 driver runs: every run delivers a report to whoever started it, including message-resumed runs (target 10/10, baseline 1/4 in the observed session). Every run whose brief touches a symlinked path names that path and its owning repository in `anomalies:` instead of `none`.

## Invariants preserved

- The driver still never edits repository files, never commits, and never falls back to implementing natively.
- The report format is unchanged; only the delivery rule and one anomaly check are added.
- The `EXECUTOR:` first line stays exact: it is the carrier for the orchestrator's own trace line.
- Read-only git remains read-only: the symlink check uses `ls -la`, not a git write.

## Falsification

If a driver run delivers a report but the report is fabricated (an `EXECUTOR:` line with no matching session `.jsonl` under `~/.pi/agent/sessions/`), the delivery rule has bought compliance at the cost of truth: revert and prefer silence to invention.

Counted form: over the next 10 runs, more than one report whose claimed session file does not exist means revert.

## Rollback

`git revert <commit>`. Affects: `agents/software-engineer-pi/AGENT.md` (two edits: step 5, and the paragraph after the report format block).

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
