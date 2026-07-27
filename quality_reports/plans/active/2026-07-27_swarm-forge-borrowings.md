# ABOUTME: ExecPlan for the three swarm-forge borrowings, redesigned after a 2-lab second opinion.
# ABOUTME: Orchestrator-side finding dedup, split-persistence review artifacts, crap4go/gremlins as evidence only.

# swarm-forge borrowings (in-session analysis, 2026-07-27)

**Repo:** claude-forge, branch `feat/swarm-forge-borrowings` off `main` | **Issue:** in-session analysis | **Refs:** `github.com/unclebob/swarm-forge` (branches `main`, `six-pack`, `adversaries`), `rules/harness-changes.md`
**Origin:** Max asked whether anything in unclebob/swarm-forge is worth borrowing (2026-07-27). Analysis + 2-lab second opinion (Gemini + DeepSeek; isolated Claude failed 401, expired OAuth in the volume). Both surviving reviewers agreed with all three problem statements and rejected all three originally proposed mechanisms. This plan carries the redesigned mechanisms.

## Analysis (verified 2026-07-27 on main, do not re-derive)

### What was studied and rejected wholesale

swarm-forge is a tmux orchestrator: N agents, each in its own git worktree and tmux window, exchanging work through validated `.handoff` files delivered by a Babashka daemon (`swarmforge/handoff-protocol.md`, 585 lines: priority queues, batch vs task receive modes, audit headers, transaction-like delivery). Rejected in full: we run a single orchestrator with in-process subagents, so this is a second orchestration substrate for no gain. Also rejected: the APS Gherkin pipeline (unclebob's own ecosystem), and note that every published swarm-forge config runs `codex` as the backend, not claude, so its role prompts are tuned for a different model.

### Problem 1: parallel reviewers double-count

Seven read-only reviewer agents declare only a positive `## Scope`. Verified overlaps:

- `agents/architecture-reviewer/AGENT.md:23` (Silent success / fail-open) vs `agents/security-reviewer/AGENT.md:23` (Fail-open enforcement): same defect class, no arbitration.
- `agents/architecture-reviewer/AGENT.md:24` (Build-time / baked-in values) vs `agents/dx-reviewer/AGENT.md:22` (Build-time config chain): near-verbatim.
- `agents/performance-reviewer/AGENT.md:16` (Database: N+1) vs `agents/database-reviewer/AGENT.md:19` (Query patterns: N+1, "defer to performance-reviewer if complex").
- `agents/security-reviewer/AGENT.md:21` (CVEs, "defer deep analysis to dependency-reviewer").
- `agents/test-reviewer/AGENT.md:21` (Assertion quality) vs the `test-design-reviewer` skill (Tautology Theatre).

**Root cause, falsifiable:** the routing table (`skills/orchestrator/SKILL.md:64-74`) maps file patterns to agents, never defect classes to owners, and nothing between step 3 (REVIEW) and step 6 (SCORE) merges findings. So one defect found by two agents is scored twice: `rules/quality-gates.md:63` says "start at 100, subtract Major (-10) and Minor (-3)" over the finding list, and the list has no uniqueness constraint. Two Majors for one defect is -20 for one problem. This is a scoring arithmetic bug, not merely noise.

**Out of scope (looks related, is not):** the two existing inline deferrals at `security-reviewer/AGENT.md:21` and `database-reviewer/AGENT.md:19`. They are depth gradients ("defer *deep analysis*"), not partitions, and stay as they are.

### Problem 2: review findings die with the context

REVIEW findings exist only in session context. `quality_reports/` holds traces, plans, session logs, harness contracts, and no findings corpus. Consequences: after an auto-compact, fix round 3 cannot cite round 1; the fix-round budget (`rules/plan-first-workflow.md`, default 5) is asserted in the final summary and not auditable; `harness-mechanic` has no signal on review quality.

### Problem 3: SCORE has no computational component beyond green/red

`rules/orchestrator-protocol.md:47` requires a SCORE to sit alongside fresh computational evidence, but that evidence is only "test/lint/build ran green after the last edit". Nothing distinguishes complex-and-tested from complex-with-tests-that-assert-nothing, which is exactly what the `test-design-reviewer` skill hunts by reading (Tautology Theatre, `skills/test-design-reviewer/SKILL.md:72`). ~90% of the work is Go.

Tools investigated: `crap4go` (CRAP per function from the standard Go coverage profile, single binary, does not touch sources) adopted; `dry4go` rejected (one commit 2026-05-11, 3 files, 1 test; `golangci-lint` already ships `dupl`); `mutate4go` rejected (embeds a footer manifest **inside every source file it tests**, defaults to differential runs against it, and unclebob needed a dedicated guardrail in his own constitution so agents would not hand-edit it: the design leaks into agent behavior). `go-gremlins/gremlins` chosen for mutation, pre-1.0, leaves sources alone.

### Second-opinion hard requirements folded in

1. **No per-agent negative scope; dedup at the orchestrator instead** (Gemini + DeepSeek, unanimous must-fix): partitioned `## Does Not Own` converts visible duplicates into silent seam-loss, with no mechanism to detect a defect that both agents punt. A miss compounds invisibly through all five fix rounds; a duplicate is caught at SCORE.
2. **Per-round findings must not enter git history** (Gemini + DeepSeek, unanimous must-fix): a finding carries the exploit recipe by construction (the Finding Contract at `rules/quality-gates.md:53` demands evidence such as a reproducing command). Committing it publishes the vulnerable state permanently, without coordinated-disclosure discipline. Artifacts land in the user's project repos, not here.
3. **No fixed CRAP threshold in the rubric** (Gemini + DeepSeek, unanimous must-fix): since coverage=1 zeroes the first term, CRAP ≥ CC always, so any threshold T is silently a cyclomatic-complexity gate at CC > T. A 99%-covered parser with CC=35 scores CRAP 35.001 and would be filed as "missing test coverage", a claim its own evidence contradicts.
4. **Stale artifacts must not become a second amnesia source** (DeepSeek): if round 2 fixes 2 of 3 findings and does not update the artifact, round 3 reads three open findings. Any persisted artifact needs a per-round status column, never a mutable shared list.
5. **A convergence signal nobody checks is worth nothing** (DeepSeek): "no approval.md means it did not converge" only holds if some step reads it. It must be surfaced at PRESENT, not left for a human to notice.
6. **Mutation testing cannot live in the inner loop** (Gemini): it recompiles and reruns the suite per mutant. Advisory target, invoked on suspicion, never in `make check`.

Reviewer error worth recording: DeepSeek asserted `quality_reports/reviews/` is already gitignored by convention. False, `.gitignore:22-26` ignores only `traces/`, `token_baselines/`, `learning_corpus/`; plans are committed. The argument survives, the premise did not.

## Design decisions (locked)

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 1 | Reviewer overlap | Orchestrator-side dedup at the step 3 to 4 boundary. **Zero agent prompt edits.** | Both reviewers, unanimous. Also cheaper: an agent prompt loads once per spawn (7 spawns per review), the orchestrator skill loads once per run |
| 2 | Dedup key | `(file, line, normalized claim)`; on collision keep the highest severity, record every reporting agent, count **once** in SCORE | Fixes the -20-for-one-defect arithmetic at `rules/quality-gates.md:63` |
| 3 | Existing inline deferrals | Left untouched (`security-reviewer/AGENT.md:21`, `database-reviewer/AGENT.md:19`) | Depth gradients, not partitions (DeepSeek) |
| 4 | Per-round findings | `quality_reports/reviews/<slug>/NNN-findings.md`, **gitignored** in the target repo | Reviewers unanimous: exploit detail must not enter history. Supersedes the 2026-07-27 session choice "committati", which was made before this evidence |
| 5 | Convergence record | `approval.md`, **committed**, carrying branch, commit, rounds, severity counts, CWE ids, SCORE, residual risks, and the local findings path. No exploit text, no reproducing commands | Keeps what committing was for (reaches the PR and the human) without publishing the recipe |
| 6 | Findings status | Each `NNN-findings.md` is immutable once written; a later round records `supersedes: NNN` and per-finding status, never edits an earlier file | Requirement 4; mirrors swarm-forge's sequence-numbered, append-only `NNN-recommendations.md` |
| 7 | Convergence surfaced | PRESENT (step 8) prints the artifact path and converged yes/no; new literal line `REVIEW-ARTIFACT: round=<n> path=<path> findings=<c/m/n> converged=<yes/no>` | Requirement 5; free-form phrasing produced 0 extractable events across 6 traced sessions |
| 8 | Go metrics in the rubric | **No new rubric row, no threshold.** crap4go output and surviving gremlins mutants added to the admissible **evidence** forms in the Finding Contract | Requirement 3. The judge already knows CRAP 35 at 99% coverage is fine; a fixed threshold does not |
| 9 | Go metric targets | `make crap`, `make mutation` in the Go template, both outside `check` | Requirement 6 |
| 10 | dry4go / mutate4go | Rejected | `dupl` already in golangci-lint; mutate4go rewrites the sources it tests |
| 11 | swarm-forge substrate | Rejected in full (tmux, worktree-per-role, handoff daemon, priority/batch queues, APS) | Second orchestration substrate, no gain over in-process subagents |

Append-only after this point. The implementing session does NOT relitigate; execution-time decisions get NEW rows in `## Decisions` below.

## Workstreams & tasklist

### W1 - Finding dedup at the orchestrator (supersedes the negative-scope proposal)

- [ ] W1.1 `skills/orchestrator/SKILL.md`, Review Routing section (currently line 64): add a **Finding Consolidation (step 3 to 4)** subsection. Procedure: collect all agent reports; group by `(file, line)`; within a group, merge findings whose claims describe the same defect; keep the highest severity; record `reported_by: <agent>[,<agent>]`; the merged list is what FIX and SCORE consume. Duplicates are expected and harmless: never instruct an agent to skip a concern because another owns it. Invariant to state explicitly: consolidation may lower the finding **count**, never the highest **severity** in a group.
- [ ] W1.2 `rules/orchestrator-protocol.md`, loop step 3: one clause that findings reach FIX consolidated, pointing at the skill. Spine stays a spine; no procedure inlined.
- [ ] W1.3 `rules/quality-gates.md`, "How to Score": state that scoring runs over the **consolidated** list, one defect counted once regardless of how many agents reported it.
- [ ] W1.4 Contract `quality_reports/harness_changes/2026-07-27_finding-dedup.md`. Failure mode: one defect reported by two agents is subtracted twice. Falsification: if a traced session shows a defect that no agent reported because consolidation was read as permission to narrow scope, revert.

### W2 - Review artifacts, split persistence

- [ ] W2.1 `skills/orchestrator/SKILL.md`: **Review Artifacts** section. Per round, write `quality_reports/reviews/<YYYY-MM-DD_slug>/NNN-findings.md` (from `001`): reviewed branch and commit, round number, consolidated findings in Finding Contract shape, per-finding status (`open` / `fixed-in-round-<n>` / `accepted`), `supersedes: NNN` when applicable, and a Verification gaps section. Files are immutable once written. The orchestrator ensures `quality_reports/reviews/` is gitignored in the target repo before the first write (append the line if absent, do not rewrite the file).
- [ ] W2.2 `skills/orchestrator/SKILL.md`: `approval.md`, committed with the change. Fields: branch, commit, rounds run, counts by severity, CWE ids where applicable, final SCORE, residual risks, path of the local findings directory. **Explicit prohibition:** no exploit text, no reproducing command, no vulnerable-code excerpt. Absence of `approval.md` means the loop did not converge.
- [ ] W2.3 `rules/orchestrator-protocol.md`: add `REVIEW-ARTIFACT: round=<n> path=<path> findings=<c/m/n> converged=<yes/no>` to the literal report lines, and reference it from steps 3 and 8.
- [ ] W2.4 `skills/pr-review/SKILL.md`: before reviewing, read `approval.md` and the local findings directory if present; do not re-litigate a finding already recorded accepted, and say when a PR arrives with no approval record.
- [ ] W2.5 Contract `quality_reports/harness_changes/2026-07-27_review-artifacts-split.md`. Failure mode: findings evaporate at auto-compact, so a fix round cannot cite an earlier round and the round budget is unauditable. Falsification: if a session writes an `approval.md` containing an exploit vector or a reproducing command, the redaction boundary failed, revert.

### W3 - Go metrics as evidence

- [ ] W3.1 `skills/project-checks/templates/go.mk`: `crap` and `mutation` targets, both outside the `check` target (which stays exactly `lint vet fmt-check vuln test`). `crap` runs crap4go (`go install github.com/unclebob/crap4go/cmd/crap4go@latest` when absent); `mutation` runs `gremlins unleash` on a path argument, with a comment that it is advisory, slow, and never part of `check`.
- [ ] W3.2 `rules/quality-gates.md`, Finding Contract evidence list: add "a crap4go line (CC, coverage, CRAP) for the touched function" and "a mutant that survives `gremlins` on newly written tests" as admissible evidence forms. **No new severity row, no threshold.** One sentence recording why: CRAP >= CC always, so a CRAP threshold is a complexity gate in disguise.
- [ ] W3.3 `skills/test-design-reviewer/SKILL.md`, Tautology Theatre section (currently line 72): a surviving mutant is admissible evidence for a tautology claim, in place of prose.
- [ ] W3.4 `skills/project-checks/SKILL.md`: document both targets as advisory in the Go row.
- [ ] W3.5 Contract `quality_reports/harness_changes/2026-07-27_go-metrics-as-evidence.md`. Failure mode: coverage and tautology findings rest on reviewer prose with no computational check available. Falsification: if a review cites a CRAP number as the finding itself rather than as evidence for a named defect, the evidence framing failed, revert.

### W4 - docs + follow-ups

- [ ] W4.1 `README.md` / skills table: only if the change surface is visible there (grep first; do not invent doc rows).
- [ ] W4.2 Follow-up issues DRAFTED here, filed by the orchestrator at PR time:
  - Backfill Result rows on the 89 pending harness change contracts (the `checkpoint-reminder` hook has been firing for 19 traced sessions).
  - Evaluate whether `harness-mechanic` should read `quality_reports/reviews/` once a corpus exists (deliberately not wired now: no corpus, and wiring it would be speculative).

## E2E matrix

Prose-harness change: "E2E" means dry-running the loop against a scripted finding set and reading the observable output.

| # | Scenario | Input | Assertion |
|---|----------|-------|-----------|
| 1 | Two agents, same defect | architecture and security both file fail-open at `x.go:42`, Major | One consolidated finding, `reported_by` lists both, SCORE subtracts 10 once |
| 2 | Two agents, same line, different defects | performance files N+1, architecture files god-object, both `y.go:10` | Two findings survive; consolidation groups by line but does not merge distinct claims |
| 3 | Severity collision | one agent Minor, one Major, same defect | Merged finding is Major; consolidation never lowers severity |
| 4 | Round 2 supersedes round 1 | round 1 files 3, round 2 fixes 2 | `002-findings.md` written with `supersedes: 001`, statuses `fixed-in-round-2` x2 + `open` x1; `001-findings.md` byte-identical to before |
| 5 | Redaction boundary | a Critical SQLi with a curl reproducer | reproducer present in the gitignored findings file, absent from `approval.md`, which carries CWE-89 and the count |
| 6 | Non-convergence | 5 fix rounds, still Major open | no `approval.md`; PRESENT prints `converged=no` on the `REVIEW-ARTIFACT` line |
| 7 | Gitignore guard | target repo without a `quality_reports/reviews/` ignore line | line appended once; the rest of `.gitignore` byte-identical |
| 8 | `make check` unchanged | Go template before/after | `check` target byte-identical; `crap` and `mutation` reachable only by explicit invocation |

### Exhaustiveness note

The matrix is the union of three dimensions: consolidation outcomes (merge, no-merge, severity collision), artifact lifecycle (write, supersede, redact, non-convergence, gitignore guard), and the Go template blast radius. Anything beyond is a recombination of these; do not enumerate combinatorially. No row for "three agents report the same defect": rows 1 and 3 already fix the grouping and severity rules, and cardinality is not a distinct behavior.

## DoD

- [ ] Fresh pristine VERIFY after the LAST edit: `make check && make test-e2e`.
- [ ] Review fleet: architecture + dx (prose/harness surface; `rules/` and `skills/` are spec, so security and test have no code to bind to). CRITICAL/MAJOR fixed, re-verified.
- [ ] Three harness change contracts exist, one failure mode each, referenced from their commit bodies (`rules/harness-changes.md`).
- [ ] The 8-row E2E matrix walked and recorded in `## Progress` with observed output.
- [ ] PR to `main` (open, NOT merged), `SCORE: <n>/100 (threshold: 90, gate: pr)` with fresh computational evidence.
- [ ] Follow-up issues filed and linked in the PR body.
- [ ] This plan updated after every task (Progress ticked, Surprises with evidence, Decisions appended).

## Progress

- [x] Analysis + 2-lab second opinion + plan (2026-07-27, planning session)
- [x] W1 finding dedup (3 harness files + contract) (2026-07-27, impl session; W1.1-W1.4 done, `make check` green, DRIFT: aligned)
- [x] W2 review artifacts (3 harness files + contract) (2026-07-27, impl session; W2.1-W2.5 done, `make check` + `make test-e2e` green, DRIFT: aligned; approval.md placed per decision 12)
- [x] W3 Go metrics as evidence (4 files + contract) (2026-07-27, impl session; W3.1-W3.5 done, `check` target byte-identical (od -c vs HEAD), `make check` + `make test-e2e` green, DRIFT: aligned)
- [x] W4 docs + follow-ups drafted (2026-07-27, impl session; README: quality_reports tree line + orchestrator and project-checks skill rows, grep-verified surface; follow-up issues stay drafted in W4.2, filed at PR time)
- [ ] Review round + fixes
- [ ] PR + SCORE
- [ ] Close-out (plan to completed/, retrospective filled)

## Surprises & Discoveries

- The original CRAP threshold rule was arithmetically unsound: CRAP = CC²(1-cov)³ + CC collapses to CRAP = CC at full coverage, so CRAP >= CC always and any threshold T is a CC > T gate. Caught by both reviewers independently, missed by the planning session.
- `mutate4go` writes its manifest as a footer **inside the source file under test**; unclebob's `engineering.prompt` carries a matching "do not hand-edit mutation manifests" guardrail, which is the tell that the design leaked into agent behavior.
- Every published swarm-forge config runs `codex`, not claude.
- DeepSeek asserted `quality_reports/reviews/` was already gitignored by convention. It is not (`.gitignore:22-26`). Reviewer premises need checking even when the conclusion holds.
- (W2, impl session) `approval.md` cannot live inside `quality_reports/reviews/<slug>/`: git does not re-include a file whose parent directory is excluded, so a committed file under the ignored tree would need a force-add on every run. Evidence: gitignore semantics ("It is not possible to re-include a file if a parent directory of that file is excluded", gitignore(5)). Placement moved, see decision 12.
- (W2, impl session) The gitignore guard is prose, not a hook: a session that skips it would commit exploit recipes to a target repo on the first findings write. Recorded in `quality_reports/plans/tech-debt.md`.
- (W3, impl session) crap4go has no tagged release: `@latest` resolves to a master pseudo-version (`v0.0.0-20260521...` at check time), so install-on-demand pins to whatever master is that day. Verified against the Go proxy and GitHub. Also: no project-checks template had an install-on-demand idiom; W3 introduced one (`command -v ... || go install ...` plus a GOTOOLS_BIN PATH prefix scoped to the two new recipes, since GOPATH/bin is not universally on PATH).

## Decisions

(append-only; execution-time decisions land here as new numbered rows, continuing from 11)

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 12 | `approval.md` location | `quality_reports/approvals/<YYYY-MM-DD_slug>.md`, outside the ignored tree, one file per run | git cannot re-include a file whose parent directory is gitignored; a committed record under `quality_reports/reviews/<slug>/` would need force-adds or fragile glob ignores. Also makes decision 5's "path of the local findings directory" field meaningful (committed record points at a genuinely separate local path). E2E rows 5 and 7 read against this path |
| 13 | go.mk parameterization | `PKG` wired only into `mutation` (default `./...`); `crap` takes no argument (crap4go drives `go test -coverprofile` itself); install-on-demand guarded by `command -v`, binaries reached via a GOTOOLS_BIN PATH prefix scoped to the two new recipes | Overloading PKG across both targets would give one variable two meanings; without the PATH prefix, install-on-demand succeeds and the next line fails with command not found. `check`'s execution environment untouched |

## Outcomes & Retrospective

(fill at close)
