# ABOUTME: ExecPlan for cutting review-loop blocking cost without cutting review coverage.
# ABOUTME: Round-budget enforcement first (dominant driver), then bg+cap for the pathological tail; scoped re-review deferred.

# Review loop cost: enforce the budget, cap the tail (in-session analysis)

**Repo:** claude-forge, branch `feat/review-loop-cost` off `main` | **Issue:** in-session analysis 2026-07-28 | **Refs:** `rules/orchestrator-protocol.md`, `skills/orchestrator/SKILL.md`, contract 2026-07-27_score-history (literal+hook precedent)
**Origin:** Max observed "reviewers take over 45 minutes in some tasks" (2026-07-28). Measurement + 3-lab second opinion (Claude/Gemini/DeepSeek, unanimous against one of my three proposals), then a second measurement round that corrected my own metric.

## Analysis (verified 2026-07-28 over 420 reviewer launches / 78 sessions, do not re-derive)

Method: raw transcripts `~/.claude/projects/**/*.jsonl`, pairing each reviewer `Task` tool_use with its `tool_result` (the traces in `quality_reports/traces/` record only the spawn, so they cannot answer this).

- **Per-agent latency is not the problem.** Synchronous runs: median 2.0 min, p75 3.2, p90 6.1. Only 9 of 134 exceed 10 min.
- **My first metric was wrong and I corrected it.** "142.9 blocking minutes" in the worst session was the SUM of durations; the true blocking wall-clock (union of intervals) is **62.7 min**. Across 65 sessions the naive sum overstates by **37%** (412 vs 301 true minutes). Median session blocks **0.2 min**.
- **Reviewers already run concurrently.** 14 of 16 multi-reviewer rounds have overlapping intervals; only 2 rounds were serial, costing ~6 min total. The "launch them in one batch" lever proposed by isolated Claude is therefore already ~satisfied: refuted by measurement.
- **The dominant driver is round count, not agent speed.** Worst sessions: 8 rounds (62.7 min), 13 rounds (39.6), 15 rounds (37.3). The declared fix-round budget is **5, then escalate** (`rules/orchestrator-protocol.md:29`, Budget in plan-first-workflow). Those sessions ran 60-200% past the ceiling. The budget is prose; nothing counts rounds.
- **The single worst blocking event is one pathological agent.** A 58.0-min architecture-reviewer (2026-07-05) is 62 of the 301 total blocking minutes across the whole dataset: **20% of all blocking time is one run**.
- **Four of the six "slowest runs" are `[Request interrupted by user for tool use]`** — time-to-interrupt, not work. Interruption was the only control available during a silent block.
- **Prompt size does not predict duration** (fast runs median 1666 chars, slow 1634): there is no evidence that trimming reviewer context speeds them up.
- **Background adoption is 84/420 (20%)**, and nothing in the harness mentions backgrounding review agents: `rules/orchestrator-protocol.md:24` (step 3 REVIEW) and the Parallelism table (`skills/orchestrator/SKILL.md:163`) cover routing and concurrency only. Reviewers are read-only by charter (`agents/security-reviewer/AGENT.md`: "never edits files"), i.e. read-only for permissions but not for scheduling.
- **Implementation constraint (verified):** the `Agent` tool exposes no timeout parameter (`description, prompt, subagent_type, model, run_in_background, isolation, name, team_name, mode`). A per-agent cap is therefore **not expressible on a synchronous launch**; it requires a backgrounded launch plus `TaskStop` at the deadline. Backgrounding is a prerequisite for the cap, not an alternative to it.

Out-of-scope neighbors: `/pr-review` (composes the same fleet plus gemini-review plus second-opinion: more fan-out, not less — rejected); reviewer `effort` downgrade (no evidence, see prompt-size finding); cutting the fleet to one generalist (this session alone: 6 Major found across two rounds, including a leaked local PATH in a committable artifact and a missing command allowlist on a script executing untrusted-reachable strings).

### Second-opinion hard requirements folded in

1. **Scoped re-review is the highest quality risk — all three reviewers, unanimous, against my proposal.** It is the only change that removes eyes from code, and its failure mode (fix-induced regression in an untouched caller) is exactly what inline review exists to catch. Deferred out of this plan (decision 5).
2. **The join barrier is consolidation, not FIX** (Claude, must-fix; Gemini and DeepSeek concur with different placements). FIX is skippable: zero Critical/Major routes straight to SCORE, which is precisely the path where a missing reviewer reads as "clean".
3. **A prose instruction will regress; only a hook is durable** (Claude, citing this repo's own telemetry: free-form phrasing produced 0 SCORE events across 6 sessions until the literal line plus hook landed).
4. **A truncated review must be structurally un-mistakable for a completed one** (all three). Claude/Gemini: it must flow into the existing FIX/escalation path as a finding, not as prose.
5. **The cap must be enforced harness-side, never announced to the reviewer in its prompt** (Claude): an agent told about its deadline satisfices, returning shallow findings fast — worse than truncation, because it is indistinguishable from diligence.
6. **Enforce the fix-round budget: "the worst session in your data wasn't slow, it was disobedient"** (Claude); "convergence detection is a higher-priority problem than shaving minutes off each round" (DeepSeek). Two of three independently ranked this above my three proposals.
7. **Audit the 84 background runs before defaulting to background** (Claude): if any findings were fire-and-forgotten, that is direct evidence the join hook must land first.

## Design decisions (locked)

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 1 | Priority order | Round-budget enforcement FIRST, then background+cap, scoped re-review deferred | Measurement: round count drives the worst sessions (8/13/15 rounds vs budget 5); 2 of 3 reviewers ranked it above my proposals |
| 2 | Round counting | New literal `REVIEW-ROUND: n=<n> budget=<b> scope=<full\|fix-diff>` + a Stop hook that blocks a SCORE claimed past budget without an escalation line | Hard requirement 3: prose invariants regress, hooks do not (score-history contract precedent) |
| 3 | Backgrounding | Read-only review agents launch with `run_in_background: true`; the orchestrator does non-conflicting work meanwhile | Read-only for permissions must mean read-only for scheduling; also the only way to express a cap (Agent has no timeout) |
| 4 | Join barrier | At **Finding Consolidation**, not at FIX. Roster of launched agents recorded in the round's findings file; `REVIEW-ARTIFACT` gains `agents=<returned>/<launched>`; hook blocks SCORE while launched<returned | Hard requirement 2: FIX is skippable, consolidation is not |
| 5 | Scoped re-review | **Deferred**, not shipped. Tech-debt entry with the unanimous rationale and the expansion rule the reviewers specified, for a future plan | Hard requirement 1: unanimous highest-risk verdict; and its motivating problem (many rounds) is better addressed by decision 1 |
| 6 | Cap value | 15 min per reviewer, harness-side via `TaskStop`, never mentioned in the reviewer prompt | Hard requirement 5; 15 min is above p90 (6.1) with margin, below the 58-min pathology |
| 7 | Truncation representation | A truncated reviewer auto-files a **Major** finding ("review incomplete: covered X, uncovered Y") and sets per-agent status `truncated`; `converged=yes` requires every routed agent `completed` | Hard requirement 4; Major (not Critical) keeps it inside the fix-round budget instead of forcing score 0 on an infra event |
| 8 | Stale-findings guard | Consolidation verifies the working tree still matches the reviewed SHA; mismatch is reported loudly, findings re-anchored or the round re-run | Claude's snapshot hazard: line-anchored findings go stale if the tree moves while a backgrounded reviewer runs |
| 9 | Background audit | W0 audits the 84 historical background runs for dropped findings BEFORE the default flips | Hard requirement 7: natural experiment already in the data |
| 10 | Progress visibility | The orchestrator states which reviewers are running and what it is doing meanwhile | The 4 interrupts are an experience failure: interruption was the only control during a silent block |

Append-only after this point. The implementing session does NOT relitigate; execution-time decisions get NEW rows in `## Decisions`.

## Workstreams & tasklist

### W0 - Background-run audit (gate for W2, mandatory first)
- [x] W0.1 (2026-07-28, verdict GO) Over the 84 historical background reviewer launches, determine for each whether its findings were collected (a later task-notification / TaskOutput / findings-file entry referencing it) or dropped. Record the ratio in `## Surprises`. Dropped > 0 means the join hook (W1.2) MUST land before the background default (W2) — the plan already orders them that way; a dropped-rate above ~20% additionally requires a `converged` recount on affected sessions.

### W1 - Round-budget enforcement + join barrier (the load-bearing workstream)
- [x] W1.1 `rules/orchestrator-protocol.md`: add `REVIEW-ROUND: n=<n> budget=<b> scope=<full|fix-diff>` to the literal report lines; extend `REVIEW-ARTIFACT:` with `agents=<returned>/<launched>`; state that step 3 launches reviewers in background and step 4 consumes them at consolidation.
- [x] W1.2 `hooks/review-budget-guard.py` (new Stop hook): from the transcript, count `REVIEW-ROUND:` lines this turn/session and reviewer launches vs returns. BLOCK a `SCORE:` claim when (a) round count exceeds the stated budget without an escalation line, or (b) `agents=<returned>/<launched>` shows unreturned reviewers. Fail-open on any exception, `stop_hook_active` short-circuit, one nudge per turn — same discipline as `score-evidence-guard.py`.
- [x] W1.3 Register in `hooks/settings.example.json` (Stop array, after score-evidence-guard) + README row.
- [x] W1.4 `skills/orchestrator/SKILL.md`: Finding Consolidation gains the join step (roster recorded, `agents=` computed, SHA-match check per decision 8); Parallelism table gains a Scheduling column stating read-only agents launch backgrounded.

### W2 - Background default + cap (depends on W0 verdict and W1.2)
- [x] W2.1 `skills/orchestrator/SKILL.md` REVIEW step: launch routed reviewers with `run_in_background: true`, name them, state the running roster to the user (decision 10), and do non-conflicting work while they run (contract/plan/commit-message prep — never edits to files under review).
- [x] W2.2 Cap procedure: poll with `TaskList`/`Monitor`; at 15 min per agent issue `TaskStop`, record per-agent status `completed|truncated`, and synthesize the truncation Major finding per decision 7. The cap value lives in ONE place in the skill text, quoted by the hook test.
- [x] W2.3 `hooks/tests/test_review_budget_guard.py`: synthetic transcripts covering the matrix below.

### W3 - docs + follow-ups
- [x] W3.1 Three change contracts (one failure mode each): `2026-07-28_review-round-budget.md`, `_review-join-barrier.md`, `_review-background-cap.md`.
- [x] W3.2 `quality_reports/plans/tech-debt.md`: scoped re-review deferred, carrying the reviewers' expansion rule verbatim (interface point touched => expand to depth-1 importers via the existing ast-grep pre-filter; scope and non-reviewed remainder written into the findings file's Verification gaps).
- [ ] W3.3 Follow-up issues drafted here, filed at PR time with triage labels per the follow-ups-agent-ready contract.

## E2E matrix

| # | Surface | Scenario | Assertion | Depth |
|---|---------|----------|-----------|-------|
| 1 | review-budget-guard hook | SCORE after rounds within budget, all reviewers returned | allow (exit 0, no block JSON) | 3★ (also: no REVIEW-ROUND line at all = legacy transcript, allow) |
| 2 | review-budget-guard hook | SCORE with round count > budget and no escalation line | block, reason names the budget and the count | 3★ (also: budget respected but escalation present = allow; malformed n=/budget= = fail-open) |
| 3 | review-budget-guard hook | SCORE while `agents=2/3` (a reviewer never returned) | block, reason names the missing count | 3★ (also: agents=3/3 allows; absent agents= field = legacy, allow) |
| 4 | review-budget-guard hook | Corrupt/poisoned transcript lines | fail-open (exit 0), logic intact on the good lines | 2★ |
| 5 | review-budget-guard hook | `stop_hook_active` set | allow unconditionally (no double-block) | 2★ |
| 6 | Literal sync | The `REVIEW-ROUND:` form in the rule, the hook regex, and the skill text agree | constants-sync test asserts equivalence on fixtures | 2★ |
| 7 | Truncation path | A reviewer marked `truncated` in a round | consolidation emits a Major finding; `converged=yes` impossible with a truncated agent | 2★ |
| 8 | Background audit (W0) | 84 historical background runs classified | every run classified collected/dropped, ratio recorded in the plan | 1★ (data analysis, verified by re-run) |
| 9 | Live loop | One real forge task run under the new REVIEW step | reviewers backgrounded, roster stated, join at consolidation, SCORE accepted | 1★ (UAT, human-observed) |

Depth: 3★ = behavior + edge + error, 2★ = happy path, 1★ = smoke.

COVERAGE: 9/10 paths (90%)   <!-- the 10th path, TaskStop actually killing a >15min agent, is [GAP]: it needs a pathological agent to reproduce, ~0.7% of runs -->

| # | Surface | Scenario | Assertion | Depth |
|---|---------|----------|-----------|-------|
| 10 | Cap enforcement | An agent genuinely exceeding 15 min is TaskStop-ped | [GAP] not reproducible on demand; the truncation REPRESENTATION is covered by row 7 | [GAP] |

### Exhaustiveness note
The matrix is the union of: hook decision surface (allow/block × budget/join × legacy/malformed), literal-sync surface, consolidation behavior on truncation, and one live loop pass. Anything beyond is covered by the existing score-evidence-guard suite (shared transcript-scanning machinery, already tested) and by the constants-sync test; do not enumerate reviewer types combinatorially — the hook is agent-agnostic by construction.

## DoD

| # | Criterion | Command | Expected | Auto |
|---|-----------|---------|----------|------|
| 1 | Hook suite green (new + existing) | `uv run --no-project python3 hooks/tests/test_review_budget_guard.py` | exit 0 | yes |
| 2 | Literal sync pinned across rule/hook/skill | `uv run --no-project python3 hooks/tests/test_hook_constants_sync.py` | exit 0 | yes |
| 3 | Fresh pristine VERIFY after the LAST edit | `make check` | exit 0 | yes |
| 4 | Full hook + script suites | `make test-e2e` | exit 0 | yes |
| 5 | Hook registered where the harness reads it | `uv run --no-project python3 hooks/tests/test_settings_example.py` | exit 0 | yes |
| 6 | W0 audit recorded before the background default lands | - | dropped-findings ratio in ## Surprises, with the W2 go/no-go stated | no |
| 7 | Review fleet: architecture + security + test (hook = harness code) | - | CRITICAL/MAJOR fixed, re-verified | no |
| 8 | PR to main open, NOT merged | - | `SCORE: <n>/100 (threshold: 90, gate: pr, evidence: <bundle-path>)` | no |
| 9 | Three change contracts committed with the change | - | one failure mode each, six fields filled | no |
| 10 | Follow-ups filed with triage labels; scoped re-review in tech-debt | - | links in PR body | no |
| 11 | This plan updated after every task | - | Progress ticked, Surprises with evidence, Decisions appended | no |

## Progress
- [x] Measurement + 3-lab second opinion + plan (2026-07-28, planning session)
- [x] W0 background-run audit (gates W2) — 84/84 collected, 0 dropped, strict-verified
- [x] W1 round budget + join barrier
- [x] W2 background default + cap
- [x] W3 contracts, tech-debt (follow-ups at PR time)
- [ ] Review round + fixes
- [ ] PR + SCORE
- [ ] Close-out (plan -> completed/, retrospective)

## Surprises & Discoveries
- **W0 verdict (2026-07-28): 84/84 background reviewer launches had their findings collected, 0% dropped — W2 is GO.** Measured twice: a generous heuristic (any task-notification within 400 following lines) and a strict one (the launch's OWN tool_use_id or its unique agent name reappearing later). Both returned 100%. The strict pass exists because the generous one would have credited a notification belonging to an unrelated background task; the verdict gates the background default, so a false green there would have been the expensive kind of wrong.
- (planning) My own headline metric was inflated 2.3x: "142.9 blocking minutes" was a sum of concurrent durations; the true union is 62.7. Recorded here because the corrected number changed the plan's priority order.
- (planning) Isolated Claude's serial-launch hypothesis was refuted by measurement (14/16 rounds already overlap), which is why "batch the launches" is not a workstream.

## Decisions
| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 11 | Which violation blocks first when both fire | Join before round budget | The join is the more specific signal (a named count) and its fix is mechanical; the budget block asks for a judgment call (escalate or justify), so it should not mask a missing reviewer |
| 12 | Escalation recognition | Loose regex (escalat*, budget exhausted/spent/reached, stopping here, fix-round budget/ceiling), and it must appear AFTER the offending round | An escalation is prose by design, so a narrow pattern would block honest ones; requiring it after the round stops stale earlier mentions from satisfying the gate |
| 13 | Cap has no hook | Procedure in the skill, not enforcement | The Agent tool has no timeout and a Stop hook cannot interrupt a running tool call; the enforceable part (a truncated agent must not read as clean) IS hooked, via the join count |

## Outcomes & Retrospective
(fill at close: shipped, gaps, lessons)
