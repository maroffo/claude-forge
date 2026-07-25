# ABOUTME: Living plan for re-engineering the always-on harness context per Claude 5 guidance + graph-engineering note
# ABOUTME: Four independent changes (A dedup, B progressive disclosure, C artifact contracts, D complexity budget), each with its own change contract

# Context Engineering for Claude 5 — harness rework

**Branch:** `feat/context-engineering-claude5`
**Started:** 2026-07-25
**Complexity:** complex (cross-cutting: CLAUDE.md + rules/ + agents/ + skills/, touches the substrate every session loads)

## Sources

| Source | Where | What we take from it |
|---|---|---|
| "The new rules of context engineering for Claude 5 generation models" | claude.com/blog | ~80% system-prompt cut; judgment over rules; progressive disclosure; no duplication; interfaces over examples; rich references over specs |
| @trq212 tweet | x.com/trq212/status/2080710971228918066 | Announcement of the same blog post (WebFetch 402 on x.com; recovered via mirror). No independent content |
| "Graph Engineering — The Karpathy Loop, Improved 1000x by Itself" | local PDF, July 2026 | Ratchet loop (measure/keep/revert); artifact contract on every handoff; reviewer returns criterion-level defects; complexity budget declared per run; memory outside the transcript |

## Problem (measured, 2026-07-25, pre-change)

```
rules/orchestrator-protocol.md   2264 words   loaded always, applies after plan approval on non-SKIP_SET tasks
rules/plan-first-workflow.md      788
CLAUDE.md (installed)             938
rules/quality-gates.md            355
rules/verification-protocol.md    290
rules/harness-changes.md          276
rules/response-shape.md           148
                                 -----
                                 5059 words ~= 6.7k tokens of always-on context, every session, including one-line fixes
```

Claude Code auto-discovers `~/.claude/rules/*.md` (no `@import` anywhere in CLAUDE.md; verified). So rules/ is unconditional.

Install layout (matters for every edit below):
- `~/.claude/rules` -> repo `rules/` (symlink, dir-level): repo edit lands immediately
- `~/.claude/skills` -> repo `skills/` (symlink, dir-level): a new skill dir lands immediately
- `~/.claude/agents`: directory of per-file symlinks; a NEW agent needs `ln -s` post-merge
- `~/.claude/CLAUDE.md`: a **copy**, not a symlink, and it has already drifted from `CLAUDE.md.example` (installed has `mauro-blogger`, example has `issue-loop-wishew`). Both must be edited, or the copy re-synced.

## Decisions

| # | Decision | Choice | Rationale | Revisit if |
|---|---|---|---|---|
| 1 | Scope | All four changes A+B+C+D | Max, 2026-07-25 | — |
| 2 | pi executor role | Mechanical subtasks only (inventory, text moves, cross-references, indexes); judgment cuts stay native | `orchestrator-protocol.md` already forbids routing spec/review roles to pi; a low-thinking flash model deciding which safety invariant survives a cut is the worst case | pi's mechanical output proves unreliable -> drop pi entirely |
| 3 | Falsification instrument | The existing trace corpus: literal `SCORE:` / `DRIFT:` / `LOCALIZE:` / `BLAST-RADIUS:` / `EXECUTOR:` lines per session, pre vs post | This is the PDF's ratchet loop applied to the harness: the metric already exists and is machine-readable | Extractor stops keying on those lines |
| 4 | B's failure mode is silent degradation | The always-on spine keeps an explicit "load the orchestrator skill before step 1" instruction, so the trigger never depends on the model inferring relevance | Moving the loop into a skill that may not auto-trigger would degrade contractor mode invisibly | Traces show the skill not loading on non-SKIP_SET tasks |
| 5 | CLAUDE.md copy vs symlink | Out of scope for this plan: edit both copies, flag the drift as an open item | Scope discipline; symlinking the installed CLAUDE.md is a separate decision for Max | Max approves the symlink separately |

## Budget

| Limit | This run |
|-------|----------|
| Fix rounds | 5, then escalate |
| Concurrent write agents | 1 (all four changes touch the same substrate; no disjoint scopes worth parallelising) |
| Sub-agents for the whole run | 4 (pi mechanical subtasks) + the review fleet at step 3 |
| Minimum evidence to finalize | `make check` and `hooks/tests` green, plus a word-count diff of the always-on context |

## Work

### A. Deduplicate CLAUDE.md  (`harness_changes/2026-07-25_claude-md-dedup.md`)
Failure mode: instructions repeated across CLAUDE.md, skill descriptions and hook messages consume always-on context and dilute attention.
- [ ] Skills table (~350 words) removed: the harness already injects every skill name + description
- [ ] "Enforcement Layer (hooks)" inventory removed: hooks state their rule when they fire
- [ ] "Second Opinion (auto-trigger)" moved into the second-opinion SKILL.md description/body
- [ ] "Knowledge Capture" compressed to pointers (lifecycle detail lives in plan-first-workflow)
- [ ] Both `~/.claude/CLAUDE.md` and repo `CLAUDE.md.example` updated (drift resolved in passing)
- Observable outcome: `wc -w ~/.claude/CLAUDE.md` <= 400; every removed instruction is still reachable from a skill description or hook message (checked one by one, listed in the contract)

### B. Orchestrator progressive disclosure  (`harness_changes/2026-07-25_orchestrator-progressive-disclosure.md`)
Failure mode: 2264 words of loop detail loaded on every session, including sessions that never enter the loop.
- [ ] `rules/orchestrator-protocol.md` reduced to a spine (<= 300 words): the 10 steps, the literal report formats, SKIP_SET, the escalation ceiling, executor selection invariants, and the instruction to load the full protocol before step 1
- [ ] `skills/orchestrator/SKILL.md` + reference files carry the detail (sub-protocol tables, blast radius, UAT, parallelism, effort table, goal-backed runs)
- [ ] Every cross-reference from other rules/skills to `orchestrator-protocol.md` sections repointed
- Observable outcome: always-on word count of rules/ drops below 2000; a fresh session asked to run a non-SKIP_SET task loads the skill and still emits LOCALIZE/DRIFT/SCORE lines

### C. Reviewer artifact contract  (`harness_changes/2026-07-25_reviewer-artifact-contract.md`)
Failure mode: reviewers return prose; findings without `required_evidence` cannot be mechanically checked, so the fix loop argues instead of verifying.
- [ ] Review agents return per-finding `{decision, claim, reason, required_evidence}` alongside the existing severity
- [ ] `quality-gates.md` severity table stays the single source of the vocabulary (no re-inlining)
- Observable outcome: a review run produces findings each carrying a `required_evidence` list; score-evidence-guard's gate has something machine-checkable to key on

### D. Complexity budget declared per run  (`harness_changes/2026-07-25_complexity-budget.md`)
Failure mode: budgets are implicit and scattered (5-round ceiling in one place, parallelism caps in another, no token/sub-agent ceiling at all), so a run cannot state what it spent against what it was allowed.
- [ ] One budget line proposed at plan approval: max sub-agents, max fix rounds, max wall-clock/token, minimum evidence for finalization
- [ ] The existing 5-round ceiling becomes one row of that budget, not a separate rule
- Observable outcome: the plan file of a new run carries a budget block; exhaustion returns best-artifact + open issues + reason, never a fluent partial success

## Progress

- [x] 2026-07-25 — sources read, harness measured, scope decided with Max (A+B+C+D, pi mechanical only)
- [x] 2026-07-25 — branch `feat/context-engineering-claude5` created, plan written
- [x] 2026-07-25 — CE#1-inventory (pi, mechanical): citation-backed duplication inventory. Headline: CLAUDE.md is 73.2% duplicated (691/944 words); orchestrator-protocol 43.9%
- [x] 2026-07-25 — C: Finding Contract in quality-gates.md + evidence field in all 7 review agents (native)
- [x] 2026-07-25 — D: `## Budget` in plan-first-workflow.md, fix-round ceiling restated as a budget default (native)
- [x] 2026-07-25 — B: spine 2264 -> 465 words, detail moved verbatim to `skills/orchestrator/SKILL.md` (native)
- [x] 2026-07-25 — A: CLAUDE.md 944 -> 475 words, both copies now byte-identical (drift resolved)
- [x] 2026-07-25 — CE#2-xref (pi, mechanical): 6 files repointed, skill registered in `_INDEX.md` and README. DRIFT: minor (nested parentheses in every repoint, two README rows left stale), fixed natively
- [x] 2026-07-25 — 4 change contracts written
- [x] 2026-07-25 — `make check` + `make test-e2e` green
- [x] 2026-07-25 — BLAST-RADIUS: 2 Major found and fixed (skill-forge told authors to add new skills to a CLAUDE.md table that no longer exists; plan-forge template called the fix-round ceiling "the orchestrator's global ceiling")
- [ ] Independent review fleet: NOT run (session constraint: subagents only where Max asked for them). Offered as `/pr-review` at PR time

Always-on context: **5059 -> 3055 words (-40%)**, and CLAUDE.md alone -50%.

## Surprises & Discoveries

- `~/.claude/CLAUDE.md` is a copy, not a symlink, and has already drifted from the repo's `CLAUDE.md.example`. Every prior "harness change" that edited only the repo copy never reached the running agent.
- WebFetch on x.com returns HTTP 402; tweets need a mirror or a paste from Max.

## Outcomes & Retrospective

_(filled at close)_
