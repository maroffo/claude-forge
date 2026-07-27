---
name: plan-forge
description: "Turn a GitHub issue or an in-session analysis into a locked ExecPlan on disk plus a ready-to-paste implementation prompt and /goal line for a fresh session using opus subagents in a separate worktree. Use when user says plan-forge, issue to plan, prepara il piano, piano di implementazione, fai il piano per la issue N, forge a plan. Runs deep code analysis, /second-opinion on the approach, writes quality_reports/plans/active/ with decisions table, tasklist, exhaustive E2E matrix, DoD. Not for implementing (the emitted prompt drives that), not for trivial SKIP_SET fixes, not for ADRs (use adr)."
compatibility: "Needs gh CLI (issue mode); step 2 relies on the second-opinion skill (Docker isolated reviewers)"
---

# ABOUTME: Issue or in-session analysis to locked ExecPlan + implementation prompt + /goal line
# ABOUTME: Deep code analysis, 3-lab second opinion, plan on disk, delegation prompt for opus subagents in a worktree

# Plan Forge

Codifies the delivery-prep playbook proven on hikma-mirsad#576 (verify-after-rewrite) and the model-manifest task: the planning session (main loop, typically Fable) does analysis and planning; implementation is delegated to a FRESH session driving opus-4.8 software-engineer subagents in a separate worktree, held to the plan by a /goal line.

## Quality Notes

- Every mechanic claimed by the issue or discussion gets verified in the actual code (file:line) before it enters the plan. Never plan from memory or from the issue text alone.
- The plan is the source of truth for a session that has NO chat context. Self-containment test: could a fresh session execute from the plan file alone?
- Locked decisions are locked: the implementing session must not relitigate them.

## Step 0: Resolve the input

- Issue mode: `gh issue view <N> --repo <org/repo> --json title,body,comments`. Read refs it cites (ADRs, prior PRs).
- Analysis mode: the problem was already dissected in this session; consolidate that.
- If neither gives a crisp problem statement, ask at most 1-2 clarifying questions (AskUserQuestion), then proceed.

## Step 1: Deep analysis (code-level, evidence-first)

1. Read the actual code paths involved. Cite `file:line` for every mechanic (detection surface, write path, config default, ...). Grep, do not assume.
2. State the root cause or design gap in one paragraph a reviewer could falsify.
3. Enumerate candidate approaches INCLUDING rejected ones with the reason (rejections are load-bearing for the second opinion and the plan).
4. Note blast radius: which packages, which tests, hot-path or not (check the repo's perf-gate rule; mirsad: `internal/{lsh,pii,decode,control,adapter,proxy,cache}`).

## Step 2: Second opinion (mandatory for non-trivial work)

Invoke the `second-opinion` skill with: problem context + verbatim code excerpts + your recommendation + rejected alternatives + 3-5 explicit questions (hidden flaws? failure paths not closed? false-positive/false-block scenarios? operational semantics like metrics/reasons?).

Fold every hard requirement the reviewers surface back into the locked decisions, citing which reviewer (e.g. "full-chain verify, Claude isolated, must-fix"). Skip the second opinion only when the task is mechanical plumbing with one obvious shape; say so explicitly.

## Step 3: Write the ExecPlan to disk

Path: `quality_reports/plans/active/YYYY-MM-DD_<slug>.md` in the target repo (worktree-safe path if the session is isolated). Follow `references/plan-template.md` exactly. Non-negotiables:

- Analysis section marked "verified, do not re-derive", with file:line evidence.
- Locked design-decisions table (append-only afterwards).
- W0 = REPRODUCE-first for any bugfix: a failing test recorded RED before one line of fix code.
- E2E matrix WITH an exhaustiveness note (the union rationale; forbid combinatorial padding).
- Wherever that matrix exists, its `Depth` column (3★ behavior+edge+error / 2★ happy path / 1★ smoke) and its computed `COVERAGE: n/m paths (p%)` footer are mandatory, not optional decoration.
- DoD includes: fresh pristine VERIFY after last edit; BENCH-BASELINE/bench-compare when hot-path; review fleet (minimum security + architecture + test, or the repo's file-routing); PR to the integration branch NOT merged; `SCORE: <n>/100 (threshold: 90, gate: pr)`; plan updated after every task.
- Empty living-plan sections: Progress, Surprises & Discoveries, Decisions, Outcomes & Retrospective.

Mirror to vault if Obsidian is up (`obsidian create name="Plans/YYYY-MM-DD - <desc>" ... silent`); repo copy stays authoritative.

## Step 4: Emit the implementation prompt + /goal line

Fill `references/impl-prompt-template.md` from the plan (repo, branch, plan path, hot-path yes/no, verify commands, reproduce clause). Present BOTH blocks to the user: the prompt to paste into a fresh session, and the `/goal` line they type immediately after (only the user can set /goal).

The prompt must carry, verbatim from the template: worktree from updated origin/<integration-branch>; plan copied + committed FIRST; bench-baseline pre-edit on a quiet machine when hot-path; REPRODUCE red before fix code; subagents = software-engineer, model opus-4.8; shared-worktree git guards; review fleet + fix + re-verify + canonical SCORE; follow-up issues filed; PR opened, never merged by the agent.

## Common Issues

| Issue | Solution |
|-------|----------|
| Issue text is vague or aspirational | Step 0 questions; if still fuzzy, stop and say what is missing |
| A second-opinion reviewer fails (401/timeout) | Degrade per that skill: synthesize from survivors, report status line |
| Plan file name collides | Append `-2` to the slug; never overwrite another task's plan |
| Target repo lacks make check/e2e equivalents | Name the repo's actual verify commands in prompt AND goal line |
| Hot-path unclear | Grep the repo's perf/bench rule; when in doubt, include BENCH-BASELINE (cheap) |

## References

- `references/plan-template.md`: the ExecPlan skeleton (structure is mandatory, prose adapts)
- `references/impl-prompt-template.md`: the implementation prompt + /goal templates with placeholders
- Rules this operationalizes: `plan-first-workflow` (plan shape, living plans), the `orchestrator` skill (SCORE format, BENCH-BASELINE, review routing), `verification-protocol` (REPRODUCE, outcome verification)
