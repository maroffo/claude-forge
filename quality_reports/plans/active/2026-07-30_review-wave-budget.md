# ABOUTME: ExecPlan for preventing over-budget review waves at launch time, not blessing them at turn end.
# ABOUTME: PreToolUse on Agent launches with file-backed session state; never a hard deny (that wedges sessions).

# Review wave budget: prevent the cost, not just the claim (in-session analysis)

**Repo:** claude-forge, branch `feat/review-wave-budget` off `main` | **Issue:** in-session analysis 2026-07-28, follow-up (B) from PR #114 | **Refs:** PR #114 finding 16 and decision 15, plan `2026-07-28_review-loop-cost.md`
**Origin:** The architecture reviewer of PR #114 argued the shipped Stop hook fires after the rounds are already spent: it prevents the false claim, not the cost. Second opinion (Gemini + DeepSeek surviving; isolated Claude timed out) agreed on the point and killed the obvious implementation.

**Prerequisite:** ship `2026-07-29_reviewer-isolation.md` first. Both reviewers ranked blast radius above cost optimization, and that plan is smaller.

## Analysis (verified 2026-07-28, do not re-derive)

- **The shipped gate is a claim-gate, not a preventer.** `hooks/review-budget-guard.py` runs at `Stop`: it fires once the turn is over, so rounds 6-15 have already been spent by the time it can object. It converts "silently over budget" into "over budget and blocked from claiming success", which is worth having and is not what the measurement asked for. Measured motivation: worst sessions ran 8/13/15 review rounds against a declared budget of 5; 62.7 true blocking minutes in the worst; one pathological reviewer run was 20% of all blocking time in the dataset.
- **The repo's own convention puts preventers at PreToolUse:** `main-branch-guard`, `freeze-guard`, `commit-intent-guard`. Claim-gates are Stop: `verify-before-stop`, `score-evidence-guard`, and now `review-budget-guard`. This change files a process limit under the preventer convention, where it belongs.
- **Transcript-reading to count waves is UNSOUND.** Both surviving reviewers flagged this independently, and it is the finding that would have broken a naive implementation:
  - **Compaction** summarizes earlier messages away. The `Agent` launches from compacted waves vanish from the transcript, so a transcript-counting hook sees zero prior waves and permits unlimited launches. The gate defeats itself exactly in the long sessions it exists for.
  - **Resume** replays or restores history, risking double-counting.
  - The Stop hooks get away with transcript-reading because they judge the CURRENT turn against `last_human`, a local window. A wave counter is cumulative state, which is a different problem.
- **A PreToolUse hard deny wedges the session.** The model cannot un-block itself; in a headless run it retries or loops explaining the failure. Gemini's alternative: return an approval carrying `additionalContext` that directs the model to stop looping and go to PRESENT. DeepSeek states the same principle: the block is information for the orchestrator's policy, not an error for the model to fight.
- **PreToolUse payloads carry no subagent identity** (Gemini): `session_id`, `tool_name`, `tool_input`. This is fine here, because the gate inspects the `Agent` *launch* call itself (whose `tool_input.subagent_type` names the reviewer) rather than trying to attribute a nested Edit.

Out-of-scope neighbors: the `Stop`-side budget check shipped in PR #114 (it stays until this lands and is measured; see decision 6); the per-reviewer time cap (procedure, PR #114); reviewer isolation (its own plan).

### Second-opinion hard requirements folded in

1. **No transcript-derived wave counting** (both, independently): use file-backed state keyed by `session_id`, which survives compaction and resume by construction.
2. **Never a hard deny** (Gemini explicit, DeepSeek in principle): permit the call and inject a directive, or the session wedges.
3. **Reset the counter on a human turn**, not on elapsed time: the budget is per task, and the human message is the task boundary the rest of the harness already uses.
4. **Add a harness-level watchdog** (both, as their "third thing"): a reviewer that exceeds a tool-call count or a wall-clock multiple of its type's median is a runtime failure that neither budget nor isolation catches. Scoped here as W3, because it shares the state file.

## Design decisions (locked)

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 1 | Hook point | `PreToolUse` on `Agent`/`Task` calls whose `subagent_type` is a `*-reviewer` | The only point at which a round can still be NOT spent |
| 2 | Wave counting | File-backed state `~/.claude/state/review-waves/<session_id>.json`, incremented per launch | Transcript counting is defeated by compaction (both reviewers); state survives by construction |
| 3 | Counter reset | On the first reviewer launch after a human turn (the hook stamps `last_human_seen` from the payload's transcript path, read ONLY for the last human index, not for counting) | The budget is per task; the human turn is the boundary the harness already uses |
| 4 | Over-budget behavior | **Permit the call** and return `additionalContext` naming the budget, the count, and the required next step (ESCALATION literal, then PRESENT) | A hard deny wedges a session that cannot un-block itself |
| 5 | Budget source | The hook's own default (5), overridable by `REVIEW_WAVE_BUDGET` in the environment; it does NOT read the plan file | Reading a plan path from a hook couples the gate to plan-file layout and fails on plans that live elsewhere; the declared budget still reaches telemetry via the `REVIEW-ROUND:` literal |
| 6 | Relationship to the Stop gate | Both ship; after 10-20 sessions decide whether the Stop-side round branch is dead code | If the preventer works, no session reaches the Stop check; that is a measurable prediction, so measure it before deleting |
| 7 | Watchdog scope | Tool-call ceiling per reviewer (default 60) recorded in the same state file; exceeding it emits `additionalContext`, never a kill | Killing from a hook is not available; making the runaway visible to the orchestrator is |
| 8 | Failure discipline | Fail-open on every exception, including unreadable/corrupt state; a missing state file means "first wave" | Same discipline as every other hook here: an infra error must never block work |

## Workstreams & tasklist

### W1 - State + hook
- [ ] W1.1 `hooks/_review_wave_state.py` (new, shared): read/increment/reset the per-session JSON, atomic write (tmp + rename), corrupt file treated as absent.
- [ ] W1.2 `hooks/review-wave-guard.py` (new PreToolUse): match `Agent`/`Task` with a `*-reviewer` `subagent_type`; increment; when the wave exceeds budget emit `hookSpecificOutput.additionalContext` per decision 4; always permit.
- [ ] W1.3 Wrapper + registration in `hooks/settings.example.json` under `PreToolUse` with a `Task|Agent` matcher; README row.

### W2 - Tests
- [ ] W2.1 `hooks/tests/test_review_wave_guard.py`: within budget permits silently; wave budget+1 permits WITH additionalContext naming both numbers; non-reviewer subagent types are ignored; human turn resets; corrupt/missing state fails open; concurrent launches in one wave do not double-count.
- [ ] W2.2 Compaction simulation: a transcript truncated to remove earlier launches must NOT reset the counter (the property transcript-counting would fail).

### W3 - Watchdog (shares the state file)
- [ ] W3.1 Tool-call ceiling per reviewer recorded in state; `additionalContext` when exceeded.
- [ ] W3.2 Tests for ceiling reached / not reached / disabled.

### W4 - Contracts + docs
- [ ] W4.1 Contracts `2026-07-30_review-wave-preventer.md` and `2026-07-30_reviewer-watchdog.md` (one failure mode each).
- [ ] W4.2 `skills/orchestrator/SKILL.md`: state that the wave gate exists, that it advises rather than denies, and what the orchestrator must do on receiving the directive.
- [ ] W4.3 Decide and record the fate of the Stop-side round branch (decision 6) as a Result-row question, not now.

## E2E matrix

| # | Surface | Scenario | Assertion | Depth |
|---|---------|----------|-----------|-------|
| 1 | Wave guard | Reviewer launch, wave <= budget | permitted, no additionalContext | 3★ (also: non-reviewer subagent ignored; malformed payload fails open) |
| 2 | Wave guard | Launch at budget+1 | permitted WITH additionalContext naming budget and count | 3★ (also: budget from env override; budget=0 disables) |
| 3 | State | Human turn between waves | counter resets to 1 | 2★ |
| 4 | State | Transcript truncated (compaction sim) | counter NOT reset: the property transcript-counting fails | 3★ (the reason this design was chosen; also: corrupt state = fail open as first wave) |
| 5 | State | Two launches in one message (parallel wave) | counted as one wave, not two | 2★ |
| 6 | Watchdog | Reviewer exceeding the tool-call ceiling | additionalContext emitted, call still permitted | 2★ |
| 7 | Live | One real session crossing the budget | orchestrator escalates instead of launching wave 6; session does not wedge | 1★ (UAT) |

Depth: 3★ = behavior + edge + error, 2★ = happy path, 1★ = smoke.

COVERAGE: 7/7 paths (100%)

### Exhaustiveness note
The union is: gate decision surface (under/over budget x reviewer/non-reviewer x well-formed/malformed), state lifecycle (reset, compaction, concurrency, corruption), watchdog, and one live pass. Session-resume double-counting is covered by row 4's mechanism (state is not derived from the transcript), so it is not a separate row.

## DoD

| # | Criterion | Command | Expected | Auto |
|---|-----------|---------|----------|------|
| 1 | Wave-guard suite green | `uv run --no-project python3 hooks/tests/test_review_wave_guard.py` | exit 0 | yes |
| 2 | Literal/registration sync | `uv run --no-project python3 hooks/tests/test_hook_constants_sync.py` | exit 0 | yes |
| 3 | Hook registered where the harness reads it | `uv run --no-project python3 hooks/tests/test_settings_example.py` | exit 0 | yes |
| 4 | Fresh pristine VERIFY after the LAST edit | `make check` | exit 0 | yes |
| 5 | Full suites | `make test-e2e` | exit 0 | yes |
| 6 | Mutation check on the new hook (the PR #114 lesson) | - | every mutant of the budget comparison and the reset rule is killed | no |
| 7 | Live session crossing the budget does not wedge | - | escalation happens, session continues to PRESENT | no |
| 8 | Review fleet: security + architecture + test | - | CRITICAL/MAJOR fixed, re-verified | no |
| 9 | PR to main open, NOT merged | - | `SCORE: <n>/100 (threshold: 90, gate: pr)` | no |
| 10 | Two change contracts committed | - | six fields each, one failure mode each | no |
| 11 | Plan updated after every task | - | Progress, Surprises, Decisions | no |

## Progress
- [x] Analysis + second opinion + plan (2026-07-28)
- [ ] W1 state + hook
- [ ] W2 tests
- [ ] W3 watchdog
- [ ] W4 contracts + docs
- [ ] Review round + fixes
- [ ] PR + SCORE

## Surprises & Discoveries
- (planning) The obvious implementation (count waves by reading the transcript, like the Stop hooks do) is defeated by compaction: the launches it counts are exactly what compaction removes. Two reviewers found this independently, which is why the design uses file-backed state instead.

## Decisions
(append-only)

## Outcomes & Retrospective
(fill at close)
