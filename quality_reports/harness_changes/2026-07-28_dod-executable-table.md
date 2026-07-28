# ABOUTME: Change contract — plan-forge DoD becomes an executable table (Command/Expected/Auto) run by scripts/dod_run.py
# ABOUTME: One failure mode: DoD items pass as prose claims with no executable check

# Harness Change Contract: executable DoD table + dod_run.py

## Component

Skill reference `skills/plan-forge/references/plan-template.md` (DoD section shape) + new script `scripts/dod_run.py` (+ tests in `scripts/tests/test_dod_run.py`) + the DoD-gate step of `issue-loop-hikma/SKILL.md` (claude-hikma-skills repo), which becomes the enforcement point invoking dod_run against the plan's table.

## Failure mode targeted

DoD items in plans are prose checkboxes; a session can tick them as claims without any executable check having run. Observed: the DoD template's own verify row embeds its command as a placeholder inside prose, and no artifact records which DoD rows were actually verified versus asserted (real-evidence-pipeline plan, decision 6-7).

## Predicted improvement

Every plan emitted by plan-forge after this change carries a DoD table where each `Auto: yes` row has a runnable command; `dod_run.py` executes them and writes `dod-results.json` into the evidence bundle. Measurable: in traced sessions that reach the DoD gate, the fraction of DoD rows backed by a recorded exit code goes from 0 (no mechanism exists) to the table's auto-row share (predicted >= 60% of rows on typical plans).

## Invariants preserved

- Manual judgment rows still exist (`Auto: no`) and are never executed or auto-ticked.
- The script does the work, the model supplies only values (score-log.sh discipline); dod_run.py never edits the plan file.
- Repo-agnostic: commands come from the plan, run in `--repo` cwd; no forge path baked in.
- A failing DoD command reds the run (exit != 0) but still writes dod-results.json: partial failure is recorded, never hidden.
- Existing plans with checkbox DoD remain readable; dod_run.py exits 2 (usage error) on plans without a parseable DoD table, it does not fabricate a pass.

## Falsification

In sessions using the new template, a DoD gate is reported as passed while `dod-results.json` is absent from the evidence bundle or records a non-zero exit for an `Auto: yes` row; or plans regularly mark rows `Auto: no` that have obvious runnable commands (gaming the auto share below 30%).

## Rollback

Revert the DoD section of `plan-template.md` to the checkbox list and delete `scripts/dod_run.py` + its test; no other component depends on them.

## Result

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| (after 10-20 sessions) | | | |
