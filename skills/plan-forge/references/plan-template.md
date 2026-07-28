# ABOUTME: ExecPlan skeleton emitted by plan-forge; structure is mandatory, prose adapts to the task.
# ABOUTME: Distilled from the hikma-mirsad #576 (asi13-redact-verify) and model-manifest plans (2026-07-12/13).

# ExecPlan template

Path: `quality_reports/plans/active/YYYY-MM-DD_<slug>.md`. Every section below appears in every plan; sections marked (bugfix) or (hot-path) appear when applicable.

```markdown
# ABOUTME: ExecPlan for <one-line what and why>.
# ABOUTME: <one-line mechanism: the fix/feature shape and its key invariant>.

# <Title> (<issue ref or origin>)

**Repo:** <repo>, branch `<branch>` off `<integration-branch>` | **Issue:** <org/repo#N or "in-session analysis"> | **Refs:** <ADRs, prior PRs>
**Origin:** <who asked, when; one line of intent. If second opinion ran: "Analysis + 3-lab second opinion (Claude/Gemini/DeepSeek), unanimous/split on X, YYYY-MM-DD">

## Analysis (verified YYYY-MM-DD on <branch>, do not re-derive)

- Every claim carries file:line evidence from the ACTUAL code, e.g. "extraction glues parts with no separator (gemini.go:109 `sb.WriteString` loop)".
- The root cause / design gap in one falsifiable paragraph.
- Exploitability / impact: when is it safe today, when does it bite.
- Out-of-scope neighbors explicitly named (what looks related but is NOT this task, and why).

### Second-opinion hard requirements folded in   <!-- when step 2 ran -->
1. <requirement> (<which reviewer>, must-fix/consensus): <one line why>.

## Design decisions (locked)

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 1 | <axis> | <choice> | <why; cite reviewer or incident if applicable> |

Append-only after this point. The implementing session does NOT relitigate; execution-time
decisions get NEW rows in ## Decisions below.

## Workstreams & tasklist

### W0 - REPRODUCE (bugfix only, mandatory first)
- [ ] W0.1 Write the failing test FIRST (name the exact scenario + SAFE assertion, bound to the
      DISTINCT failure signal, not a generic status code). It MUST fail on unfixed code; record
      the red output in this plan (`fails_before_fix=true`). It flips green with W1 in the same commit.

### W1..Wn - implementation workstreams
- [ ] Wn.m <task with the invariant it must respect, file paths, and what "done" looks like>

### W(last) - docs + follow-ups
- [ ] docs updated in the same PR (the repo's docs-sync rule); docs-facts/consistency gate green
- [ ] follow-up issues DRAFTED in this plan (orchestrator files them at PR time)

## E2E matrix   <!-- test-heavy tasks -->

| # | Surface | Scenario | Assertion | Depth |
|---|---------|----------|-----------|-------|
| 1 | <shape x adapter/variant> | <action> | <assertion> | 3★ (<the edge and error it also covers>) |
| 2 | <surface> | <action> | <assertion> | 2★ |
| 3 | <surface> | <action> | <assertion> | 1★ (grep / prose-verified in review) |

Depth is MANDATORY on every row: 3★ = behavior + edge + error, 2★ = happy path, 1★ = smoke.
A path the plan knowingly leaves untested is its own row marked `[GAP]`, never an absent row.

COVERAGE: <n>/<m> paths (<p>%)   <!-- MANDATORY, computed over the union below, gaps excluded from n -->

### Exhaustiveness note
The matrix is the union of: <dimensions>. Anything beyond is covered by <property/sweep>; do not
enumerate combinatorially.

### Path trace   <!-- RECOMMENDED, complex verdict only -->
ASCII on purpose, not mermaid: terminal-native and git-diffable, so a reviewer sees the trace move
in the diff. Mermaid stays optional for architecture diagrams. One line per hop, matrix row and
depth at the end of each:

    entry -> parse ............. row 1   3★
          -> store.Write ....... row 4   2★
          -> retry on conflict .. [GAP]
    COVERAGE: 2/3 paths (67%)

## DoD

Executable table, run by `scripts/dod_run.py --plan <this file> --evidence-dir <bundle>` (forge repo).
`Auto: yes` rows MUST carry a runnable Command (executed in repo cwd, pass = exit 0; Expected is the
human-readable meaning of that pass). `Auto: no` rows are human/orchestrator judgment and are never
executed or auto-ticked. Results land in the evidence bundle as `dod-results.json`.

| # | Criterion | Command | Expected | Auto |
|---|-----------|---------|----------|------|
| 1 | (bugfix) REPRODUCE red then green | `<repro test command>` | exit 0 on fixed code (red output pre-fix recorded in W0.1) | yes |
| 2 | Fresh pristine VERIFY after the LAST edit | `<repo verify, e.g. make evidence or make check && make test-e2e>` | exit 0; bundle green when the repo has `make evidence` | yes |
| 3 | (hot-path) bench-compare vs pre-edit baseline | `make bench-compare` | exit 0, or exit!=0 resolved as fix / accept-with-rationale Decision row (never silent) | yes |
| 4 | (test-heavy) Depth column filled, COVERAGE footer computed, gaps counted: <n> | - | matrix complete per template rules | no |
| 5 | Review fleet: <security + architecture + test, or file-routed set> | - | CRITICAL/MAJOR fixed, re-verified | no |
| 6 | PR to <integration-branch> open, NOT merged | - | `SCORE: <n>/100 (threshold: 90, gate: pr, evidence: <bundle-path>)` with fresh computational evidence | no |
| 7 | Follow-up issues filed and linked in the PR body | - | links present | no |
| 8 | This plan updated after every task | - | Progress ticked, Surprises with evidence, Decisions appended | no |

Drop rows whose qualifier does not apply ((bugfix), (hot-path), (test-heavy)); add task-specific
`Auto: yes` rows for every mechanically checkable outcome the plan promises (a curl returning 200,
a grep finding zero stale references, a migration applying cleanly).

## Progress
- [x] Analysis + second opinion + plan (YYYY-MM-DD, planning session)
- [ ] <one row per workstream>
- [ ] Review round + fixes
- [ ] PR + SCORE
- [ ] Close-out (plan -> completed/, retrospective filled)

## Surprises & Discoveries
(fill during execution, with evidence: command output, diff, red test)

## Decisions
(append-only; execution-time decisions land here as new numbered rows)

## Outcomes & Retrospective
(fill at close: shipped, gaps, lessons)
```

## Hard-won rules baked into this shape

- **Analysis carries evidence, not narrative.** "verified, do not re-derive" only means something if a fresh session can click file:line and confirm.
- **REPRODUCE before fix** is what makes a bugfix falsifiable; the red output in the plan is the proof the test binds to the bug. Bind the assertion to the DISTINCT signal (metric label, reason string), never to a status code two gates share.
- **Locked vs execution decisions** split keeps subagents from relitigating design while still recording what they discover.
- **Exhaustiveness note** prevents both thin matrices and combinatorial padding; reviewers check the union argument, not the row count.
- **Depth and COVERAGE are what make the row count mean something.** Without them a smoke row and a full behavioral row look identical on the page, so a thin matrix reads as a thorough one. The ratio is computed from the union, not asserted.
- **Follow-ups drafted in-plan, filed at PR time** keeps issue-creation out of subagent hands (external side effects stay with the orchestrator).
