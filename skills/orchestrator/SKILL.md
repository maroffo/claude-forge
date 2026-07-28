---
name: orchestrator
description: "Full contractor-mode loop: sub-protocols (LOCALIZE, BENCH-BASELINE, REPRODUCE, DRIFT), review routing by file pattern, blast radius, UAT, parallelism and effort caps, escalation, just-do-it, goal-backed runs. Load it to RUN that loop, once you have an approved plan and are entering step 1, or when a step needs its detail. It is a protocol, not a way to do the work: it never replaces the language, review or planning skill the task itself calls for, and a task small enough to just edit (SKIP_SET) needs none of it. The always-on spine lives in rules/orchestrator-protocol.md. Not for trace capture (harness-trace) or harness optimization (harness-mechanic)."
---

# ABOUTME: Detail of the autonomous development loop, loaded on demand at step 1 (spine stays in rules/orchestrator-protocol.md)
# ABOUTME: Sub-protocols, review routing, blast radius, UAT, parallelism, effort, escalation, goal-backed runs

# Orchestrator (contractor mode): full protocol

The spine (loop steps, SKIP_SET, literal report lines, invariants) is always in context from `rules/orchestrator-protocol.md`. This file carries everything else. Read the section you need; you do not need to read all of it.

**Plan checkpoints** (`<!-- checkpoint:verify -->`, `<!-- checkpoint:decide -->`, see plan-first-workflow) halt the loop mid-IMPLEMENT: pause the current subtask, present state, resume only after human approval.

At plan approval (between step 0 and step 1), if the task has a deterministic done-criterion, propose a `/goal` line for Max to set: see Goal-Backed Runs below.

## Research + Complexity (Step 0)

research-analyst searches docs/solutions/, LEARNING.md, MEMORY.md, vault, then external. Returns: comparison table, recommendation, ecosystem solutions (avoid hand-rolling), 1-2 common pitfalls. MUST end with complexity verdict:

| Level | Criteria | Effect |
|-------|----------|--------|
| simple | Known tech, <3 files, prior art exists | Standard flow |
| moderate | Some unknowns, 3-5 files | Standard flow |
| complex | Unfamiliar tech, >5 files, multiple approaches, no prior art, cross-cutting | Extended flow: write `quality_reports/research/YYYY-MM-DD_desc.md` + `/second-opinion` on approach + activate annotation cycle (see plan-first-workflow) |

## Implementation (Step 1)

Split into independent workstreams. Each software-engineer receives: **scope** (files), **plan** (subtask + criteria), **context** (lang/framework). Single-scope: implement directly. See parallelism rules below.

**Declared exclusions (page faults).** Any brief that scopes context (engineer or reviewer) also declares what was deliberately cut and how to recover it: `excluded: <files/areas>; read on demand from <path>`. An implicit omission reads as "does not exist" and the agent concludes from absence; a declared one is a recoverable page fault. One line, listing only deliberate cuts, never an inventory of everything untouched.

### Executor selection

Default executor is the native software-engineer subagent. Cost-sensitive scoped implementation or mechanical-analysis subtasks MAY instead route to `scripts/pi-exec` (the pi coding agent driving gemini flash, Google-billed), invoked via Bash, to conserve Anthropic credits.

Preferred invocation in DELEGATED prompts (fresh implementing sessions): the `software-engineer-pi` agent from the registry, a thin haiku driver that runs the wrapper and relays results; it is not a skill and must not be searched for as one. It cannot edit files or implement natively, so "executor unavailable" surfaces as a loud report, never as a silent fallback. Direct Bash invocation of the wrapper remains valid for the orchestrator in-session. If pi fails a subtask twice, re-implementation goes to the native software-engineer and the fallback is DECLARED in the summary (it is the change contract's falsification signal, never silent).

Constraints on a pi-executed subtask (non-negotiable, since pi runs outside Claude Code's hook loop; the spine states them too):
- The orchestrator is the sole committer: pi never commits. Hooks that fire on Claude Code tool events (verify-before-stop, aboutme-enforcer) cannot see pi processes; pre-commit-gate still gates every commit because the orchestrator makes them all.
- DRIFT (1c) is mandatory and its skip conditions are void: every pi-executed subtask gets a fresh-context drift check, even a single trivial one.
- Review and spec roles are never routed to pi: cross-model review of Gemini-written code is the point (native Fable/Opus stays adversarial). Rewriting rules, agents or skills is a spec role.
- The ORCHESTRATOR reports each pi-executed subtask on the literal `EXECUTOR:` line. The wrapper's own stdout `EXECUTOR:` line (model/brief/workdir) is a local log, not the trace signal.

### Sub-protocols

| Sub-step | When it runs | How | Trace data | Skip when |
|----------|--------------|-----|------------|-----------|
| **LOCALIZE** (1a) | Before any edits | Engineer outputs `files_to_edit`. Orchestrator checks files exist and align with plan. WARN on extras. STOP on missing planned files UNLESS engineer provides `scope_reduction_rationale` (e.g., "File `X` turned out not to need editing because ..."). | `{files_planned, files_proposed, precision, recall, mismatches, scope_reduction_rationale?}` | Plan lists exact files; single-file task |
| **BENCH-BASELINE** (1a, hot-path) | With LOCALIZE, before any edits | If the task touches a repo's hot-path packages (mirsad `internal/{lsh,pii,decode,control,adapter,proxy,cache}` today), run that repo's `make bench-baseline` on the clean pre-edit tree → `.bench/baseline.txt`. Machine must be quiet (see VERIFY). | `{baseline_captured, bench_pkgs, baseline_path}` | No `bench-baseline` target; task touches no hot-path package |
| **REPRODUCE** (1b) | Bug-fix only, after LOCALIZE | Script that FAILS on current code and PASSES after the fix. Target files from LOCALIZE. | `{script, fails_before_fix, passes_after_fix}` (passes_after_fix null until VERIFY) | Not a bug-fix; purely visual bug; plan says infeasible |
| **DRIFT** (1c) | After each subtask (including parallel ones, using `git diff -- <files_for_subtask>` to avoid races) | Fresh-context agent receives: subtask description + scoped diff. One question: "Did we build exactly this, no more, no less?" Verdict: aligned / minor drift (WARN, proceed) / significant drift (STOP). | `{subtask_id, verdict, deviations}` | Single subtask; trivial (<10 LOC) |

Report each executed sub-step on the literal line from the spine. Free-form phrasing is invisible in telemetry.

## VERIFY (Step 2)

Run tests, lint, build. Max 2 retries on flake; on the 3rd failure, STOP and escalate (same flow as Step 7 escalation).

If REPRODUCE ran (step 1b), also confirm `reproduction_confirmed = true`: the script that previously FAILED must now PASS. If not, the fix didn't address the reported bug; return to FIX.

If a `.bench/baseline.txt` exists for the task (BENCH-BASELINE ran), also run `make bench-compare`. Exit ≠ 0 ⇒ a **Major** finding, never an auto-fail: either fix the regression, or add an explicit accept-with-rationale row to the plan's Decisions table ("expected cost of feature X: +N% on Y"). Never a silent accept. The A/B is only valid on a **quiet** machine: competing benchmark or build processes invalidate the same-session comparison (observed live).

## Review Routing (Step 3)

Open every round with the literal `REVIEW-ROUND: n=<n> budget=<b> scope=full`, where `n` is `total_fix_rounds` (REVIEW->FIX plus UAT->FIX cycles, the same number the plan's Budget bounds) and `<b>` is that budget. Without it the round is invisible to telemetry and to `review-budget-guard`, which then has nothing to count.

| Pattern | Agents |
|---------|--------|
| `*.go`, `*.rb`, `*.py`, `*.ts`, `*.kt`, `*.swift` | architecture + security |
| Hot paths, queries, caching | + performance |
| `*_test.*`, `*_spec.*` | + test + test-design-reviewer |
| `go.mod`, `Gemfile`, `package.json`, `pyproject.toml` | dependency |
| `migrations/`, `schema.rb`, `*.sql` | database |
| `docs/`, `README*`, `ADR/`, `*.md` | dx |
| No match | architecture + security (minimum) |

Findings come back in the Finding Contract shape (`rules/quality-gates.md`): severity, location, claim, fix, evidence.

### Finding Consolidation (step 3 → 4)

Reviewers overlap by design: the routing table above maps file patterns to agents, never defect classes to owners. Consolidate the reports before FIX runs:

0. **Join.** Reviewers run in background (see Review Scheduling), so consolidation is the barrier: collect every launched agent before proceeding. Mechanically: write the launched roster to `quality_reports/reviews/<slug>/000-roster.md` at launch; wait for each completion notification; for any agent that signals idle WITHOUT a report, request it with `SendMessage({to: <agent name>})`, because a backgrounded reviewer does NOT reliably self-deliver (observed 2026-07-28: of three, one delivered only on request and two never did, and had to be relaunched synchronously). Count `agents=` from reports actually in hand, read off the roster file, never from memory. **Not FIX**, FIX is skippable when no Critical/Major lands, and that is exactly the path where a missing reviewer reads as "clean". Record the launched roster in the round's findings file and print `agents=<returned>/<launched>` on the `REVIEW-ARTIFACT:` line; `review-budget-guard` blocks a SCORE while they disagree. A stopped-at-cap agent counts as returned only once its truncation finding exists (see Review Scheduling).
0b. **Snapshot check.** Findings are anchored to the SHA each reviewer read. Before consolidating, confirm the working tree still matches it (`git rev-parse HEAD` plus a clean-tree check for the reviewed paths). A mismatch means the tree moved under a running reviewer: say so loudly and either re-anchor the affected findings or re-run that reviewer. Silently consolidating line-anchored findings against a moved tree produces fixes at the wrong lines.
1. Collect every agent report.
2. Group findings by `(file, line)`.
3. Within a group, merge the findings whose claims describe the same defect; the dedup key is `(file, line, normalized claim)`.
4. On merge, keep the **highest** severity of the group and record `reported_by: <agent>[,<agent>]`, listing every agent that reported it.
5. The consolidated list is what FIX (step 4) and SCORE (step 6) consume.

**Duplicates are expected and harmless.** Never instruct an agent to skip a concern because another agent owns it: a duplicate is caught here, a concern that every agent assumes someone else owns is caught nowhere. The two existing inline deferrals (security-reviewer defers deep CVE analysis to dependency-reviewer, database-reviewer defers complex N+1 to performance-reviewer) are depth gradients, not partitions, and stay as they are.

**Invariant:** consolidation may lower the finding *count*, never the highest *severity* in a group. Grouping by line is not merging by line: an N+1 and a god-object both filed at `y.go:10` are distinct claims, so both survive as separate findings.

## Review Artifacts

Findings that live only in session context die at the next auto-compact: fix round 3 cannot cite round 1, and the fix-round budget ends up asserted in the final summary instead of auditable. Persist them, split in two, because a finding carries the exploit recipe by construction (the Finding Contract demands evidence such as a reproducing command). The recipe stays local; only a redacted record is committed.

### Per-round findings (local, gitignored)

Each REVIEW round writes one file: `quality_reports/reviews/<YYYY-MM-DD_slug>/NNN-findings.md`, numbered from `001` in round order. The slug is the plan file's own slug (`quality_reports/plans/active/YYYY-MM-DD_<slug>.md`); with no plan on disk, derive it from the branch name; either way reuse it verbatim for `approval.md`, so the two paths always pair. Contents:

| Field | Content |
|-------|---------|
| Reviewed branch and commit | Branch name plus the exact commit SHA the round reviewed |
| Round | Round number, matching `NNN` |
| Findings | The **consolidated** list (see Finding Consolidation) in Finding Contract shape: severity, location, claim, fix, evidence |
| Status | Per finding, one of `open` / `fixed-in-round-<n>` / `accepted` |
| `supersedes: NNN` | Present when this round restates findings first recorded in an earlier file |
| Reviewer roster | Every agent launched this round, with per-agent status `completed` / `truncated`; the source `agents=` is counted from |
| Leftover worktrees | Every review worktree still on disk at consolidation: path, owning agent, disposition (`removed after consolidation` / `kept: <why>`). Absent means none survived auto-clean, not that nobody looked |
| Verification gaps | What this round could not check, and why |

**Immutable once written.** A later round never edits an earlier file: it writes the next `NNN`, carries `supersedes: NNN`, and restates fresh per-finding statuses for everything it inherits. A mutable shared list would be a second amnesia source: if round 2 fixed 2 of 3 findings and did not update the file, round 3 reads three open findings and re-fixes two.

**Gitignore guard, before the FIRST write.** These artifacts land in the user's project repos, not in claude-forge. Check the target repo's `.gitignore` for a `quality_reports/reviews/` entry; append the line if absent, never rewrite the existing file. Exploit detail must not enter git history: committing it publishes the vulnerable state permanently, with no coordinated-disclosure discipline.

### approval.md (committed)

Written at convergence and committed with the change, at `quality_reports/approvals/<YYYY-MM-DD_slug>.md` (outside the ignored tree, so the record reaches the PR and the human reviewer):

| Field | Content |
|-------|---------|
| Branch, commit | What was approved |
| Rounds run | Count, matching the highest `NNN` written |
| Counts by severity | Critical / Major / Minor, over the consolidated list |
| CWE ids | Where applicable, id only |
| Final SCORE | In the canonical `SCORE:` form |
| Residual risks | What was accepted and why, in one line each |
| Findings path | Path of the local, gitignored findings directory |

**Prohibited in `approval.md`:** no exploit text, no reproducing command, no vulnerable-code excerpt. The findings files carry the recipe locally; `approval.md` carries only the redacted record. A CWE id and a count are the level of detail it may reach.

**Absence of `approval.md` means the loop did not converge.** That is a signal only if something reads it, so PRESENT (step 8) surfaces it on the literal `REVIEW-ARTIFACT:` line with `converged=no` (on that line, `findings=<c/m/n>` carries the Critical/Major/Minor counts, in that order, over the consolidated list). It is never left for a human to notice.

## Blast Radius (Step 5b, conditional)

After RE-VERIFY, before SCORE. Detects entropy: docs, tests, imports still referencing pre-change behavior.

### Trigger (ANY of)

- Changed files add/remove/rename **exported symbols**. Detect with `ast-grep` or a **fully-qualified** regex (e.g., `\bMyModule\.MyFunc\b`). **Never naked grep** on common names like `get`, `init`, `render`: they explode to hundreds of false matches.
- More than 3 files changed
- Schema/migration changes, CLI flag definitions, REST/gRPC endpoint handlers

### How

1. **CLI pre-filter:** `ast-grep` or qualified regex for changed symbols; collect importers, docs, tests referencing them.
2. **Fresh-context agent** receives only snippets of related files (not full files). Flags stale references, old-behavior assertions, comments describing removed logic, broken imports.
3. **Report:** MAJOR (functional contradiction) or MINOR (stale comment/doc). CRITICAL contradictions re-enter FIX (step 4) before SCORE. Close with the literal `BLAST-RADIUS:` line from the spine (ast-grep usage is NOT a signal; only that line is).

### Skip when

Docs-only; pure refactors with no API change; pre-filter found 0 related files. When a trigger held but a skip condition applies, say so on the same literal line.

## UAT: Goal-Backward Verification (Step 9)

UAT is **Outcome Verification with a human walkthrough**. The schema (observable truths → evidence → pass/fail) lives in `verification-protocol.md`; don't redefine it here.

Build the table from the goal (3-7 observable truths). Fill `Evidence` via CLI/output for every truth that can be verified mechanically. Use `AskUserQuestion` **only** for truths that need human judgment (visual, subjective, UX). On failure: feed into fix loop (step 4), re-verify, re-score, re-UAT failed items only. UAT→FIX rounds count against the plan's fix-round budget.

**Skip when:** in SKIP_SET.

## Review Scheduling

Review agents cannot conflict with the tree the loop is building, so they never need to block it. That is a property of how they are launched (isolated, below), not a promise about what they do: reviewers write by design. Measured over 420 reviewer launches (78 sessions): per-agent latency is not the problem (median 2.0 min, p90 6.1), but a single pathological run consumed 20% of all blocking time in the dataset, and the worst sessions ran 8-15 review rounds against a budget of 5.

- **Launch backgrounded** (`run_in_background: true`) with an explicit `name`, and say which reviewers are running and what you are doing meanwhile. A silent multi-minute block leaves interruption as the user's only control, which is how four of the six longest recorded "runs" ended.
- **Launch isolated** (`isolation: "worktree"`, on every review-agent launch, alongside `run_in_background: true`). The agent gets a temporary worktree copy of the repo and its file writes land there. The cost is roughly 200-500ms of setup plus a checkout's worth of disk per agent, and it is paid because reviewers write: the PR #114 round found its Critical through mutation testing (11 mutants written to the hook source, suite run against each) and executable probes. A mutation run that dies before restoring leaves surviving mutants on disk; in a copy that is a worktree you throw away, in the main tree it is corrupted source that the next build and the next reviewer both consume.
- **What is isolated is the working tree, not the repository.** A worktree shares the `.git` database with the main repo (objects, refs, branches, stash, config, hooks; only `HEAD`, `refs/bisect` and `refs/worktree/*` are per-worktree), so a reviewer reaching for git plumbing can still move state the main tree reads. The reviewer definitions carry the rule that follows from this: never mutate shared git state, and undo a mutant by rewriting file content, not with `stash` or `checkout <ref>`.
- **The parameter is the whole mechanism, so a launch that omits it fails open.** Nothing in `hooks/` inspects it, and an agent launched without it is a write-encouraged reviewer standing in the real tree, which is worse on that path than the old "never edit files" prose it replaced. The definitions fail closed on their side (compare `git rev-parse --git-dir` against `--git-common-dir`, downgrade to strictly read-only when they match), but that is a second belt: every path that routes these agents, `pr-review` and ad-hoc `Agent` calls included, either carries the parameter or accepts the exposure knowingly.
- **Name the base SHA in the brief** and require `file:line` citations against it. The worktree is a copy, so a finding that does not say what it was anchored to cannot be checked against the main tree; the consolidation snapshot check (step 0b) keys on exactly that SHA, and an anchor that no longer exists there is a stale finding, not a defect.
- **Clean up after consolidation, never before.** An unchanged worktree auto-cleans. One the reviewer changed does not, and what it changed is the evidence behind its findings, so remove it only once its report is consolidated, with `git worktree remove --force <path>` (plain `remove` refuses a dirty tree, which is exactly the case that survives auto-clean). Every worktree still on disk at consolidation goes in the round's findings file as a **Leftover worktrees** row, never silently deleted.
- **This is isolation, not permission.** A reviewer can still write anything inside its own copy, and a prompt-injected reviewer is still prompt-injected. The copy bounds where the damage lands; it does not prevent it. No `tools:` allowlist backs this up, deliberately: with `Bash` allowed the allowlist is theatre, and without it the empirical review above becomes impossible (rejected 2026-07-28, two independent reviewers; pinned by `hooks/tests/test_agent_definitions.py`).
- **Do non-conflicting work while they run**: change contracts, plan updates, commit-message prep. Never edit a file that is under review, that moves the tree beneath a running reviewer (see Consolidation step 0b).
- **Cap: 15 minutes per reviewer**, enforced harness-side (`TaskStop` on the backgrounded task), because the `Agent` tool has no timeout parameter and a synchronous launch therefore cannot be capped at all. **Never state the cap in the reviewer's prompt**: an agent told its deadline returns shallow findings fast, which is worse than truncation because it is indistinguishable from diligence.
- **Poll, do not hope.** Between the non-conflicting work items, check outstanding reviewers (`TaskList`, or a `Monitor` with an until-condition). At the 15-minute mark for an agent, `TaskStop` it. An unattended orchestrator has no clock event: without an explicit poll the cap is a number in a document, not a limit.
- **No commits while a reviewer is outstanding.** `git commit` runs the pre-commit gate, which runs the test suites and moves HEAD, tripping the snapshot check for every running reviewer at once. Preparing a commit message is safe; committing is not.
- **A stopped agent is `truncated`, never clean.** Record its per-agent status in the findings file and file a **Major** finding, "review incomplete: covered X, uncovered Y", so it flows through the normal FIX/escalation path. `converged=yes` requires every routed agent `completed`. Major, not Critical: an infra timeout should cost a fix round, not zero the score.

## Parallelism

| Agent class | Default | Max | Scheduling | Condition for max |
|-------------|---------|-----|------------|-------------------|
| Main-tree read-only (research-analyst, review agents, explorers) | 5 | 7 | background | Always |
| Write (software-engineer) | 3 | 5 | synchronous | File scopes disjoint AND no shared integration surfaces |

**Shared integration surfaces** (even a 1-line change needs a sequential wave): routing tables, barrel exports / `index.*`, DI container config, dependency manifests (`go.mod`, `package.json`), migrations directory, shared test fixtures.

If the plan requires edits to a shared surface, run the parallel batch first, then a **sequential INTEGRATE wave** for the shared files.

**Pilot before a large run:** any fan-out over ~10 similar items (parallel agents, workflow stages, batch migrations) runs 1-2 items first; inspect the result, fix prompt or approach, then launch the rest. A full-fleet launch on an unproven prompt burns tokens at fleet scale.

## Effort assignment

Effort is the cost lever, not model downgrade (Opus 4.8 recalibrated effort: `high` thinks less, `xhigh` substantially more; re-baseline, don't port 4.7 tuning). Each agent pins `effort:` in its frontmatter per role:

| Role | effort | Why |
|------|--------|-----|
| Orchestrator / main coding session | `xhigh` (settings `effortLevel`) | Anthropic agentic/coding default |
| software-engineer | inherit (omitted) | writes code at session effort |
| Review agents, research-analyst, tech-writer | `medium` | bounded analysis that gates the loop |
| harness-mechanic | `high` | cross-trace synthesis |
| project-analyzer | `low` + `model: haiku` | mechanical extraction |

Override per task with `/effort`. Do not pass `effort: inherit` (invalid; omit instead).

## Escalation (Step 7)

`total_fix_rounds` counts every REVIEW→FIX cycle AND every UAT→FIX cycle. When it reaches the plan's fix-round budget (default 5) without meeting the score threshold, STOP and escalate.

Present to the human:
- Current score and threshold
- Top 3 unresolved findings (Critical/Major)
- Round-by-round score delta
- Hypothesis on why progress stalled
- Options: lower threshold, accept remaining risk, re-plan, abandon

## Just-do-it mode

Skip final approval and auto-commit when ALL of: SCORE ≥ 80, no Critical findings, BLAST-RADIUS clean. **Bypasses UAT** (no human walkthrough possible in this mode). Stops at a local commit on the feature branch: does not push, does not open a PR.

## Goal-Backed Runs (optional)

`/goal` (CLI ≥ 2.1.139) wraps a session-scoped prompt-based Stop hook: an evaluator (small fast model, no tool access) re-checks a completion condition after every turn and sends Claude back to work until it holds. It complements `score-evidence-guard`: the hook rejects SCORE claims lacking fresh evidence; `/goal` rejects stopping before the gate is met.

- `/goal` is user-typed; Claude cannot set it. At plan approval, when the task has a deterministic done-criterion, propose the exact line for Max to set, phrased against the canonical `SCORE:` format so the evaluator finds it verbatim in the transcript, e.g.:
  `/goal the transcript reports a line matching SCORE: <n>/100 (threshold: 80, gate: commit) with n >= 80, after make check && make test-e2e pass on the final code, or stop after 5 fix rounds`
- The turn-cap clause mirrors the plan's fix-round budget. Reaching it triggers the escalation flow, never a silent stop.
- The condition must be transcript-evaluable: the evaluator runs no commands, so it can only judge what the session surfaced. The `SCORE:` line format is exactly what it keys on.
- Skip for SKIP_SET and for tasks whose done-criterion needs human judgment (visual, UX): those stay with UAT (step 9).

## Trace Capture

Use the `harness-trace` skill (schema, JSONL format, capture logic). Trace is skipped for SKIP_SET. Trace files are local-only (gitignored).
