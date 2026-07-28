# ABOUTME: ExecPlan closing the measurement and autonomy loops on the harness built 2026-07-28.
# ABOUTME: Makes the contracts falsifiable, derives the counts we currently assert, and schedules the hunter.

# Harness loop closure: make today's machinery verifiable (in-session analysis)

**Repo:** claude-forge, branch `feat/harness-loop-closure` off `main` | **Issue:** in-session analysis 2026-07-28 | **Refs:** PR #114 (merged), plan `2026-07-28_real-evidence-pipeline.md`, the five contracts dated 2026-07-28
**Origin:** Max asked for a plan covering everything non-wasit that is still open after a day that shipped an evidence pipeline, an executable DoD, a bug-hunter and a review-budget gate. The unifying gap: several of those mechanisms **assert numbers they could derive**, and every contract written today has a Result row that nothing currently computes.

**Second opinion: deliberately skipped.** Per plan-forge's own escape hatch, this is mechanical plumbing with one obvious shape (four scripts/targets and a cron line, each with a known consumer). The one design question that is not mechanical, where the round-count integrity check belongs, is resolved in decision 4 with the reasoning stated. The two changes that DID need adversarial review this week got it and are planned separately (`2026-07-29_reviewer-isolation.md`, `2026-07-30_review-wave-budget.md`).

## Analysis (verified 2026-07-28, do not re-derive)

- **Five contracts written today each carry an empty Result row** (`quality_reports/harness_changes/2026-07-28_*.md`: dod-executable-table, score-evidence-path, score-guard-fs-validation, followups-agent-ready, hunted-issue-fastpath), plus three more from PR #114. `rules/harness-changes.md` says to append a Result after 10-20 sessions and revert if falsification fired. **Nothing computes those numbers**, so the honest default outcome is that they are never filled and the contracts become decoration. This is the single highest-leverage gap on this list.
- **Two gates verify numbers the loop itself produces.** `review-budget-guard` reads `agents=<returned>/<launched>` and `n=` from the transcript; both are printed by the session being gated. The roster file (`quality_reports/reviews/<slug>/000-roster.md`) already exists and holds the ground truth, but nothing reads it. Live evidence from the PR #114 round: the count was correct only because the orchestrator chose to derive it by hand.
- **Forge has no `make evidence`.** `Makefile` has `check` (line 24) and `test-e2e` (line 29); the evidence-bundle machinery shipped for wasit only. So the harness that now requires an `evidence:` path from other repos cannot produce one for itself, and its own SCORE lines cannot carry the field it invented.
- **The `claude -p` cron pattern is already proven in this repo**, contrary to the assumption in the real-evidence-pipeline plan that it was pending: `crontab -l` shows a monthly knowledge-sync entry (`23 9 1 * *`) invoking `claude -p` with a scoped prompt and appending to `~/.claude/logs/`. Phase 4 of that plan is therefore an addition to a working mechanism, not a bootstrap.
- **The bug-hunter's main path has never been exercised.** Its first supervised run produced a real finding via static reading (wasit#452) but zero e2e-confirmed bugs, so "failing test → issue with repro" and the fingerprint dedup are both untested in practice. A second run is execution, not implementation, and belongs in this plan only as a gated step.

Out-of-scope neighbors: everything in hikma-wasit (Max's explicit boundary, including wasit#452); the frontend/Playwright phase (phase 5 of the real-evidence-pipeline plan), which needs its own refinement because it is a different repo, a different stack, and turns on decisions I cannot make alone (which flows are worth visual regression, how much trace to retain, whether the frontend gets its own bundle or shares wasit's); the two already-planned harness changes.

## Design decisions (locked)

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 1 | Priority | The measurement script (W1) lands FIRST and alone if the plan is cut short | Without it, eight contracts stay unfalsifiable and every other change here ships unmeasured |
| 2 | Measurement scope | One script, `scripts/harness_report.py`, covering reviewer cost, round counts, background adoption, SCORE/evidence-field usage, and hunted-issue outcomes | The five 2026-07-28 contracts and the three from PR #114 need overlapping numbers; one reader over `~/.claude/projects` serves all of them |
| 3 | `agents=` derivation | `scripts/review_roster.py` prints the count from the roster file; the skill instructs the orchestrator to use its output | A gate that reads a self-produced number verifies nothing; the roster is already written at launch |
| 4 | Round-count integrity | Extend `review-budget-guard.py` rather than adding a hook | The data (`REVIEW-ROUND` lines and their count) is already parsed there and turn-scoped; a second hook would duplicate the scanner and the turn-scoping logic that has already drifted once between three Stop hooks |
| 5 | `make evidence` for forge | Port the wasit shape (fmt/lint-equivalent, both suites, metadata.json written last), not the Go specifics | The bundle contract is the manifest and the per-step exit codes, not the language |
| 6 | Hunter cron | Add to the existing crontab pattern, weekly, with the backpressure preflight from the real-evidence-pipeline plan | The pattern is proven in this repo; a new mechanism would be invention where imitation works |
| 7 | Follow-up filing | File FU-1..FU-4 as issues in claude-forge with triage labels, then implement them here | They were drafted and never filed at PR #114 time, which is the failure the followups-agent-ready contract predicts; filing them is also its first live test |
| 8 | Deferred items stay deferred | Stage B of the evidence field, the fate of the Stop-side round branch, and scoped re-review are Result-row questions, not workstreams | Each is explicitly conditioned on measurement that W1 makes possible; deciding them now would be guessing |

## Workstreams & tasklist

### W1 - Measurement (gates the contracts; lands first)
- [ ] W1.1 `scripts/harness_report.py`: read `~/.claude/projects/**/*.jsonl` and report, per period: reviewer launches (count, sync/background split, per-agent median and p90, true blocking minutes as an **interval union**, never a sum of concurrent durations), review rounds per session and sessions over budget, SCORE events with and without the `evidence:` field, and hunted-issue counts. `--since <date>`, `--json` for machine use.
- [ ] W1.2 `scripts/tests/test_harness_report.py`: fixture transcripts covering the union-vs-sum distinction (the error this plan's own analysis made and corrected), background/sync classification, and an empty corpus.
- [ ] W1.3 Append Result rows to the eight open contracts where the data already supports one; where it does not yet, record the exact number needed and the date to re-check.

### W2 - Derive what we assert
- [ ] W2.1 `scripts/review_roster.py` + tests: parse the roster file, print `agents=<returned>/<launched>`, exit non-zero on a malformed roster (a broken roster must not silently produce a passing count).
- [ ] W2.2 `skills/orchestrator/SKILL.md` Finding Consolidation: obtain `agents=` from the script, not by hand.
- [ ] W2.3 `hooks/review-budget-guard.py`: block when the declared `n=` is lower than the count of `REVIEW-ROUND` lines in the same turn (the round-budget contract's own falsification clause), with tests for match, under-report and legacy.

### W3 - Forge produces its own evidence
- [ ] W3.1 `scripts/evidence.sh` + `make evidence` for forge: `make check`, `make test-e2e`, the hook and script suites, each captured with its exit code; `metadata.json` written last as the freshness anchor; `raw/` gitignored.
- [ ] W3.2 `.gitignore`: curated-artefact allowlist under `quality_reports/evidence/`, matching the wasit shape (including the child-exclusion fix, since forge's `/quality_reports/` rule has the same dead-negation bug wasit had).
- [ ] W3.3 One forge SCORE line carrying `evidence: <bundle>`, accepted by `score-evidence-guard` (the field the harness invented, used on itself).

### W4 - Hunter schedule (gated on a successful second run)
- [ ] W4.1 Second supervised hunter run on wasit, targeting a different area, to exercise the untested path (failing test → issue with repro) and the fingerprint dedup. **If it produces no e2e-confirmed bug again, STOP: schedule nothing** and record the verdict, because scheduling a hunter whose main path has never fired would automate a no-op.
- [ ] W4.2 On success only: crontab entry following the existing knowledge-sync pattern (weekly, `claude -p`, log to `~/.claude/logs/`), with the backpressure preflight (dirty tree, >5 open `agent:hunted`, uncleaned worktree) and a push digest.
- [ ] W4.3 Change contract for the scheduled run.

### W5 - Follow-ups + docs
- [ ] W5.1 File FU-1..FU-4 as claude-forge issues with triage labels (the first live exercise of the followups-agent-ready contract), then close the ones this plan implements.
- [ ] W5.2 `quality_reports/plans/tech-debt.md`: record that the frontend/Playwright phase needs its own plan and why it is not in this one.

## E2E matrix

| # | Surface | Scenario | Assertion | Depth |
|---|---------|----------|-----------|-------|
| 1 | harness_report | Corpus with two concurrent reviewer runs in one round | blocking time reported as the interval UNION, not the sum | 3★ (also: fully serial round sums correctly; empty corpus reports zero, not a crash) |
| 2 | harness_report | Corpus with background and sync launches | classified correctly by `run_in_background` | 2★ |
| 3 | harness_report | `--since` filter | events before the date excluded | 2★ |
| 4 | review_roster | Roster with 2 returned, 1 truncated, 1 launched-only | prints `agents=3/4` (truncated counts as returned only with its finding) | 3★ (also: malformed roster exits non-zero; missing file exits non-zero) |
| 5 | review-budget-guard | Declared `n=1` with 8 REVIEW-ROUND lines in the turn | blocks, reason naming both numbers | 3★ (also: declared matches counted = allow; legacy transcript = allow) |
| 6 | make evidence (forge) | Clean tree | bundle with metadata.json, all steps exit 0 | 2★ |
| 7 | make evidence (forge) | One deliberately failing test | bundle records the failure, overall exit != 0 | 2★ |
| 8 | gitignore | Bundle written | curated files committable, `raw/` and stray files ignored, plans/reviews still local | 3★ (the dead-negation bug wasit had) |
| 9 | SCORE with evidence | Forge SCORE citing a fresh bundle | accepted by score-evidence-guard; a fabricated path blocks | 2★ |
| 10 | Hunter run | Second supervised run | either ≥1 e2e-confirmed bug with a repro, or an explicit clean report gating W4.2 | 1★ |

Depth: 3★ = behavior + edge + error, 2★ = happy path, 1★ = smoke.

COVERAGE: 10/10 paths (100%)

### Exhaustiveness note
The union is: the report's three axes (cost, rounds, evidence-field usage) times their edge cases, the two derivation surfaces (roster, round count), the bundle lifecycle (green, red, gitignore, consumption), and one gated live run. Contract Result rows are not a test row: they are an output of W1.3, verified by reading them.

## DoD

| # | Criterion | Command | Expected | Auto |
|---|-----------|---------|----------|------|
| 1 | Measurement suite green | `uv run --no-project python3 scripts/tests/test_harness_report.py` | exit 0 | yes |
| 2 | Roster script suite green | `uv run --no-project python3 scripts/tests/test_review_roster.py` | exit 0 | yes |
| 3 | Guard suite green (round-integrity added) | `uv run --no-project python3 hooks/tests/test_review_budget_guard.py` | exit 0 | yes |
| 4 | Forge bundle produced and green | `make evidence` | exit 0, metadata.json present | yes |
| 5 | Fresh pristine VERIFY after the LAST edit | `make check` | exit 0 | yes |
| 6 | Full suites | `make test-e2e` | exit 0 | yes |
| 7 | Contract Result rows appended or a re-check date recorded for each of the eight | - | no contract left with an empty Result and no date | no |
| 8 | Hunter second run verdict recorded; W4.2 skipped if it was clean | - | verdict in Progress, cron only on success | no |
| 9 | FU-1..FU-4 filed with triage labels | - | four issues, links in the PR body | no |
| 10 | Review fleet: security + architecture + test | - | CRITICAL/MAJOR fixed, re-verified | no |
| 11 | PR to main open, NOT merged | - | `SCORE: <n>/100 (threshold: 90, gate: pr, evidence: <bundle>)` | no |
| 12 | Plan updated after every task | - | Progress, Surprises, Decisions | no |

## Progress
- [x] Analysis + plan (2026-07-28)
- [ ] W1 measurement (lands first)
- [ ] W2 derivation
- [ ] W3 forge evidence
- [ ] W4 hunter schedule (gated)
- [ ] W5 follow-ups + docs
- [ ] Review round + fixes
- [ ] PR + SCORE

## Surprises & Discoveries
- (planning) The `claude -p` crontab pattern is already live in this repo (monthly knowledge-sync), so phase 4 of the real-evidence-pipeline plan was never blocked on a bootstrap, only on someone checking. Recorded because the earlier plan asserted the opposite.

## Decisions
(append-only)

## Outcomes & Retrospective
(fill at close)
