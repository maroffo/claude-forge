# ABOUTME: ExecPlan for isolating review subagents so their writes cannot reach the main tree.
# ABOUTME: Uses the Agent tool's existing isolation:"worktree", not a tools: allowlist (which both reviewers called theatre).

# Reviewer isolation: worktree, not a tools allowlist (in-session analysis)

**Repo:** claude-forge, branch `feat/reviewer-isolation` off `main` | **Issue:** in-session analysis 2026-07-28, follow-up (A) from PR #114 | **Refs:** PR #114 findings 15, `quality_reports/reviews/2026-07-28_review-loop-cost/001-findings.md`
**Origin:** A security reviewer found that all 13 agent definitions declare read-only in prose with no enforcement, and that PR #114 widened the blast radius by running reviewers concurrently with the writer. Second opinion (Gemini + DeepSeek surviving; isolated Claude timed out at 5 min) rejected the obvious fix and proposed a better one.

## Analysis (verified 2026-07-28, do not re-derive)

- **No enforcement exists.** All 13 `agents/*/AGENT.md` files carry `name`/`description`/`effort` and **zero** `tools:` keys (verified by grep over the directory). The protocol asserts "Review agents are read-only" (`rules/orchestrator-protocol.md` Invariants) and each reviewer's prose says "never edits files"; the agent roster shows them with "All tools".
- **A `tools:` allowlist is the wrong fix, on two independent grounds.** Both surviving reviewers said so:
  - Allowing `Bash` makes the allowlist theatre (Bash writes files); denying `Bash` kills empirical review.
  - **Empirical review is where this harness's value came from.** In the PR #114 round, the test-reviewer performed mutation testing (11 mutants applied to the hook source, suite run against each) and the security reviewer ran executable probes and ReDoS timing. Those reviews found the Critical. A Read/Grep/Glob-only allowlist would have prevented them.
- **The property we actually want is not "read-only", it is "cannot contaminate the main tree".** Gemini's counterfactual is the concrete risk and it is not hypothetical: a mutation run that crashes before restoring leaves surviving mutants on disk, and subsequent implementation steps build and test against corrupted source. (Checked after this session's own mutation runs: tree clean, both restored. It worked by luck of no crash, not by design.)
- **The harness already has the mechanism.** The `Agent` tool exposes `isolation: "worktree"`: "creates a temporary git worktree so the agent works on an isolated copy of the repo… auto-cleaned if unchanged". Gemini independently proposed dedicated temporary worktrees as its sixth option without knowing the parameter exists. This makes the change a one-parameter edit plus documentation, not a new subsystem.
- **PreToolUse cannot distinguish a reviewer's Edit from the main loop's.** Gemini states the payload carries `session_id`/`tool_name`/`tool_input` and no subagent identity; correlating by PID or timestamp is race-prone under concurrent reviewers. This kills option (4) from the original list and is why isolation-by-construction beats interception.

Out-of-scope neighbors: the `software-engineer` agent (write-capable by design, scoped to assigned files, already worktree-isolated when the orchestrator says so); `research-analyst` and `Explore` (read-heavy, same argument applies, but they do not run concurrently with the writer today).

### Second-opinion hard requirements folded in

1. **Do not ship a `tools:` allowlist** (Gemini and DeepSeek, independently): theatre if Bash is allowed, capability-destroying if it is not.
2. **Isolate by worktree** (Gemini, sixth option): reviewers keep full write capability inside a copy; leakage into the main tree becomes impossible rather than forbidden.
3. **Ship this before the wave-budget gate** (both): blast radius before cost optimization. A prompt-injected reviewer with write access to the real tree is a live exposure; an over-budget loop is expensive, not dangerous.
4. **Add a harness-level per-reviewer timeout** (both, as their "third thing"): the 58-minute pathology is a runtime failure that neither isolation nor budget addresses. Partly covered by PR #114's 15-min cap procedure; this plan makes it a checked precondition rather than re-implementing it.

## Design decisions (locked)

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 1 | Mechanism | `isolation: "worktree"` on every review-agent launch | The property wanted is non-contamination, not tool denial; the harness already provides it |
| 2 | `tools:` allowlist | **Not shipped** | Theatre with Bash, capability-destroying without it (both reviewers) |
| 3 | Scope | Review agents only (the 7 `*-reviewer` types), not research-analyst or software-engineer | Reviewers are the ones now running concurrently with the writer; the others keep their current behavior until measured |
| 4 | Findings anchoring | Reviewer briefs must state that the worktree is a copy at a named SHA, and cite `file:line` against that SHA | A finding anchored in a copy must still apply to the main tree; naming the SHA makes a stale anchor detectable at consolidation (the snapshot check already exists) |
| 5 | Cleanup | Rely on auto-clean for unchanged worktrees; the orchestrator removes changed ones after consolidation, and reports a leftover rather than silently deleting findings-bearing state | A reviewer that mutated its copy has evidence in it; deleting it before its report is consolidated destroys the evidence |
| 6 | Prose invariant | Keep "review agents are read-only" but restate it as "read-only with respect to the main tree; writes are confined to their own worktree copy" | The old wording is now false in a way that matters: reviewers DO write, and the review quality depends on it |
| 7 | Enforcement honesty | Document that this is isolation, not permission: a reviewer can still write inside its copy and can still be prompt-injected | Same discipline as PR #114: never claim enforcement the mechanism does not provide |

## Workstreams & tasklist

### W1 - Launch-side change
- [ ] W1.1 `skills/orchestrator/SKILL.md` Review Scheduling: every review-agent launch carries `isolation: "worktree"` alongside `run_in_background: true`; state the cost (~200-500ms plus disk per agent) and that it is paid because reviewers write by design.
- [ ] W1.2 Same section: reviewer briefs state the worktree SHA and require `file:line` citations against it.
- [ ] W1.3 `rules/orchestrator-protocol.md` Invariants: restate the read-only invariant per decision 6.

### W2 - Agent definitions
- [ ] W2.1 Each `agents/*-reviewer/AGENT.md`: one line stating writes are confined to the agent's own worktree copy and must never target the main tree; empirical verification (probes, mutation runs) is explicitly encouraged there.
- [ ] W2.2 No `tools:` key is added (decision 2). Record the rejection in the file's prose so a future reader does not "fix" it.

### W3 - Test + docs
- [ ] W3.1 `hooks/tests/test_agent_definitions.py` (new): assert every `agents/*-reviewer/AGENT.md` parses, carries the worktree-confinement line, and does NOT carry a `tools:` key (pinning the locked rejection).
- [ ] W3.2 Change contract `2026-07-29_reviewer-worktree-isolation.md`.
- [ ] W3.3 Update the PR #114 follow-up issue with the outcome.

## E2E matrix

| # | Surface | Scenario | Assertion | Depth |
|---|---------|----------|-----------|-------|
| 1 | Agent definitions | Every `*-reviewer` definition | carries the confinement line, no `tools:` key | 3★ (also: a new reviewer added without the line fails the test) |
| 2 | Live launch | One review wave with `isolation: "worktree"` | each reviewer reports from its own worktree; `git status` in the main tree is unchanged throughout | 2★ |
| 3 | Contaminating reviewer | A reviewer that writes a file in its worktree | the main tree is unaffected; the worktree is not auto-cleaned (it changed) and the orchestrator reports it | 2★ |
| 4 | Findings anchoring | A finding cited at `file:line` from a worktree copy | the same line exists at the named SHA in the main tree (snapshot check) | 2★ |
| 5 | Cleanup | After consolidation | no leftover review worktrees; a leftover is reported, never silently removed | 1★ |

Depth: 3★ = behavior + edge + error, 2★ = happy path, 1★ = smoke.

COVERAGE: 5/5 paths (100%)

### Exhaustiveness note
The union is: definition-file surface (static, testable), launch surface (one live wave), contamination surface (the property the change exists for), and lifecycle (anchoring + cleanup). Prompt-injection resistance is explicitly NOT claimed and therefore not a row: isolation bounds the damage, it does not prevent the injection.

## DoD

| # | Criterion | Command | Expected | Auto |
|---|-----------|---------|----------|------|
| 1 | Agent-definition test green | `uv run --no-project python3 hooks/tests/test_agent_definitions.py` | exit 0 | yes |
| 2 | Fresh pristine VERIFY after the LAST edit | `make check` | exit 0 | yes |
| 3 | Full suites | `make test-e2e` | exit 0 | yes |
| 4 | Live wave verified: main tree untouched during review | - | `git status` clean before and after, worktrees accounted for | no |
| 5 | Review fleet: security + architecture (agent definitions are harness spec) | - | CRITICAL/MAJOR fixed, re-verified | no |
| 6 | PR to main open, NOT merged | - | `SCORE: <n>/100 (threshold: 90, gate: pr)` | no |
| 7 | Change contract committed | - | six fields, one failure mode | no |
| 8 | Plan updated after every task | - | Progress, Surprises, Decisions | no |

## Progress
- [x] Analysis + second opinion + plan (2026-07-28)
- [x] W1 launch-side (2026-07-28, commit 38f685e: SKILL.md Review Scheduling + protocol Invariants restated per decision 6)
- [x] W2 definitions (2026-07-28, commit ad2ffca: identical 5-bullet confinement block in all 7 `*-reviewer` AGENT.md, no `tools:` key anywhere)
- [x] W3.1 test + W3.2 contract (2026-07-28, commits ad2ffca + 99acd29: `hooks/tests/test_agent_definitions.py` red-green verified against 3 mutated fixtures, contract filed)
- [ ] W3.3 update PR #114 follow-up issue (at close)
- [ ] Review round + fixes (live wave doubles as E2E row 2)
- [ ] PR + SCORE

## Surprises & Discoveries
- (planning) The mechanism both reviewers wanted already exists as `isolation: "worktree"` on the Agent tool; Gemini proposed it from first principles without knowing. The plan shrank from "build isolation" to "pass a parameter and say why".
- (W1-W3) `make check` does NOT run `hooks/tests/*.py`; `make test-e2e` picks the new test up via the glob at `Makefile:31`, so no wiring was needed. Evidence: its pass line appears in `make test-e2e` output.
- (W2) The em-dash lint (`scripts/check_repo.py`, `EM_DASH_SCOPE_SUBSTRINGS`) is scoped to `/skills/` only; `rules/` and `agents/` carry grandfathered em dashes under a "clean on touch" comment. The 8 touched files kept their pre-existing ABOUTME em dashes: strict "clean on touch" would have ballooned the diff beyond this change's scope (see Decisions #8).
- (W2) security-reviewer was the only definition with read-only claims beyond the standard bullet (ABOUTME line 2 and the reasoning-gates sentence "and you stay read-only"); both restated per decision 6, making it the one non-uniform diff of the seven.
- (W2) Reviewer definitions now carry two overlapping citation rules: the new "cite `file:line` against the base SHA" and the pre-existing "Quote exact code with file path and line number". Complementary, not conflicting; dedup deferred (tech-debt candidate).

## Decisions
(append-only)

| # | Decision | Choice | Rationale | Revisit if |
|---|----------|--------|-----------|------------|
| 8 | Em dashes in touched `rules/`/`agents/` files | Left grandfathered ones alone; no new ones introduced | Lint scope excludes those dirs; strict clean-on-touch would balloon an isolation change into a punctuation sweep | The em-dash lint scope widens to `rules/`/`agents/` |
| 9 | Overlapping citation rules in reviewer definitions | Both kept (base-SHA anchor + quote-exact-code) | They compose: one anchors, one evidences; deleting either loses information | A dedup pass merges them into one sentence |

## Outcomes & Retrospective
(fill at close)
