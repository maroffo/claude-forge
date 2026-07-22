# ABOUTME: ExecPlan for scripts/pi-exec: route implementation/analysis subtasks to pi + gemini-3.6-flash to save Anthropic credits.
# ABOUTME: Bash wrapper + orchestrator executor-selection rule + change contract; orchestrator stays sole committer, review stays native.

# pi-flash executor (in-session analysis)

**Repo:** claude-forge, branch `feat/pi-flash-executor` off `main` | **Issue:** in-session analysis 2026-07-22 | **Refs:** rules/harness-changes.md, quality_reports/harness_changes/TEMPLATE.md
**Origin:** Max, 2026-07-22: Anthropic models slow this week, weekly credits nearly exhausted with backlog open. Offload implementation and mechanical-analysis subtasks to the pi coding agent + gemini-3.6-flash (Google-billed), keep spec writing + adversarial review on Fable/Opus. Second opinion SKIPPED (explicit): mechanical plumbing with one obvious shape, design adversarially discussed and approved in-session (fork vs branch, hook coverage, commit ownership); complexity verdict: simple (known tech, 6 files, live smoke test already proves the chain).

## Analysis (verified 2026-07-22 on main, do not re-derive)

- pi 0.73.1 at `/opt/homebrew/bin/pi`; headless mode `-p`, brief via `@file`, `--model` accepts `provider/id` and passes UNKNOWN ids through with a warning. Live smoke test on this machine (2026-07-22): `pi --no-session --no-tools -p --model google/gemini-3.6-flash "Reply with exactly: OK"` printed the warning `Model "gemini-3.6-flash" not found for provider "google". Using custom model id.` and then `OK`.
- `GEMINI_API_KEY` present in env; pi's default provider is already `google` (pi --help). Cost lands on Google, not on Claude credits.
- pi's offline model registry tops out at gemini-3.1 previews (`pi --offline --list-models gemini`); custom-ID pass-through works but pi lacks context-window metadata for the model. Follow-up drafted (W4.3b): `pi update` once the registry knows 3.6.
- Insertion point for the rule edit: `rules/orchestrator-protocol.md` section "## Implementation (Step 1)" (line 53); the sub-protocol table already defines literal report lines for LOCALIZE/REPRODUCE/DRIFT (lines 59-75), so a literal `EXECUTOR:` line makes pi-executed subtasks countable by harness-trace.
- Enforcement gap (the design constraint): hooks live in Claude Code's event loop; a pi process spawned via Bash bypasses verify-before-stop and aboutme-enforcer entirely. pre-commit-gate and commit-intent-guard still fire IF commits are made by the orchestrator. Hence Decisions 3 and 4: orchestrator sole committer, DRIFT mandatory on pi output.
- Verify surface: `make check` = check_repo.py + lint-shell + lint-dockerfile (Makefile:24-27), but lint-shell shellchecks ONLY `install.sh get.sh` (Makefile:36-41), and `make test-e2e` iterates ONLY `hooks/tests/test_*.py codemap/tests/test_*.py` (Makefile:30-34). Both need one-line extensions or the new wrapper ships unlinted and untested.
- Script conventions: `#!/usr/bin/env bash`, 2-line ABOUTME header, strict-mode `set` flags (scripts/metrics-weekly.sh:1-6).
- Out-of-scope neighbors: issue-loop-wishew integration (only after the pilot, follow-up W4.3a); migrating review/spec roles to pi (never: cross-model review diversity is the point, Decision 5); a role-prompt library for pi briefs (follow-up W4.3c).

## Design decisions (locked)

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 1 | Mechanism | Bash wrapper `scripts/pi-exec` on a branch of claude-forge, NOT a fork | ~/.claude symlinks make a fork non-live; two harnesses drift |
| 2 | Default model | `google/gemini-3.6-flash` via custom-ID pass-through; `--model` flag to override | Verified live 2026-07-22; registry refresh is a follow-up, not a blocker |
| 3 | Commit ownership | pi NEVER commits; orchestrator is sole committer | Keeps pre-commit-gate + commit-intent-guard in the path (hooks cannot see pi processes) |
| 4 | DRIFT on pi output | Mandatory, never skipped, even for single subtasks | Compensates verify-before-stop + aboutme-enforcer not covering pi output |
| 5 | Review/spec roles | Stay native (Fable/Opus), never routed to pi | Cross-model review of Gemini-written code removes correlated blind spots |
| 6 | pi invocation hygiene | `-p`; context-file discovery ON (CLAUDE.md/AGENTS.md of the target repo); extensions/skills/prompt-templates/themes OFF; sessions saved (pi default dir), session path echoed at end | Repo context helps implementation; user-installed pi extensions are nondeterministic; JSONL sessions enable post-mortem |
| 7 | Thinking default | `low`; `--thinking` flag to override per subtask | flash-class + cost goal; escalate per subtask, not globally |
| 8 | Observability | Wrapper prints a literal `EXECUTOR: pi-exec model=<id> brief=<file> workdir=<dir>` line; rule documents the format | harness-trace counts pi-executed subtasks; contract falsification needs the denominator |
| 9 | Offline testability | `--dry-run` prints the pi command without executing | Real API calls stay out of make test-e2e (network, cost); TDD stays deterministic |

Append-only after this point. The implementing session does NOT relitigate; execution-time decisions get NEW rows in ## Decisions below.

## Workstreams & tasklist

(not a bugfix: W0 REPRODUCE not applicable)

### W1 - change contract (first, per rules/harness-changes.md)
- [ ] W1.1 Write `quality_reports/harness_changes/2026-07-22_pi-flash-executor.md` following TEMPLATE.md. Component: `scripts/pi-exec` + `rules/orchestrator-protocol.md` + `Makefile`. Failure mode targeted: weekly Anthropic credit exhaustion mid-week with backlog open (observed 2026-07-22, this session). Predicted improvement: Anthropic token spend per implemented issue drops 40-60% on tasks whose implementation subtasks route through pi-exec, measured via harness-trace + EXECUTOR lines over the first 5 tasks. Invariants preserved: SCORE thresholds unchanged; review agents native and read-only; orchestrator sole committer; no --no-verify paths added. Falsification: over the first 5 pi-executed subtasks, mean fix rounds > 2x the traced baseline, OR 2+ subtasks require full native re-implementation; then revert. Rollback: stop invoking scripts/pi-exec; `git revert <commit>`.

### W2 - wrapper, TDD
- [ ] W2.1 RED: `scripts/tests/test_pi_exec.py` (stdlib unittest, subprocess-based, offline, run via `uv run`): dry-run happy path builds the expected pi command; missing brief file exits 2; missing GEMINI_API_KEY (scrubbed env) exits 3 before any pi invocation; `--model`/`--thinking` overrides land in the command; workdir not a directory exits 2. Confirm the suite FAILS with pi-exec absent; record the red output in this plan.
- [ ] W2.2 GREEN: `scripts/pi-exec` (bash, 2-line ABOUTME, `set -euo pipefail`). Args: `--brief <file> --workdir <dir> [--model <id>] [--thinking <level>] [--dry-run]`. Builds `pi -p --model <id> --thinking <level> --no-extensions --no-skills --no-prompt-templates --no-themes @<brief>` executed with cwd=workdir; prints the `EXECUTOR:` line (Decision 8) before running; after completion echoes the newest pi session file path. Suite green.
- [ ] W2.3 Makefile wiring: lint-shell file list gains `scripts/pi-exec`; test-e2e loop gains `scripts/tests/test_*.py`. `make check && make test-e2e` pristine.

### W3 - rule edit
- [ ] W3.1 `rules/orchestrator-protocol.md`: new "### Executor selection" subsection under "## Implementation (Step 1)". Content: default executor is the native software-engineer subagent; cost-sensitive scoped implementation or mechanical-analysis subtasks MAY route to `scripts/pi-exec` (pi coding agent, gemini flash, Google-billed); constraints stated normatively from Decisions 3-5 (orchestrator sole committer, DRIFT mandatory and its skip-condition voided for pi-executed subtasks, review/spec roles never routed to pi); literal report line format `EXECUTOR: pi-exec model=<id> subtask=<id>`. Keep the edit to one tight subsection; no other section touched.

### W4 - docs + follow-ups
- [ ] W4.1 README: add pi-exec to the scripts/components inventory IF such an inventory exists (check first; do not invent a section).
- [ ] W4.2 Live smoke (manual, Google-billed cents, requires GEMINI_API_KEY in env): toy brief in a throwaway git dir, real pi run edits a file, EXECUTOR line + session path printed, exit 0. Record output in Surprises.
- [ ] W4.3 Follow-up issues DRAFTED here (orchestrator files them at PR time): (a) pilot pi-exec on 1 real scoped subtask, then append the Result row to the change contract; (b) run `pi update` once the registry includes gemini-3.6-flash and drop the custom-ID warning from the smoke expectations; (c) evaluate a role-prompt library for pi briefs (`agents/pi/*.md`) after the pilot.

## E2E matrix

| # | Case | Invocation | Assertion |
|---|------|------------|-----------|
| 1 | dry-run happy path | `--brief ok.md --workdir <tmp> --dry-run` | exit 0; printed command contains `-p`, `google/gemini-3.6-flash`, `@ok.md` |
| 2 | missing brief | `--brief absent.md --workdir <tmp> --dry-run` | exit 2; stderr names the missing path |
| 3 | no API key | env without GEMINI_API_KEY | exit 3 BEFORE any pi invocation |
| 4 | model override | `--model google/gemini-3.6-pro --dry-run` | printed command carries the override |
| 5 | thinking override | `--thinking high --dry-run` | printed command carries `--thinking high` |
| 6 | bad workdir | `--workdir /nonexistent --dry-run` | exit 2 |
| 7 | live smoke (manual, W4.2) | real run, toy brief | target file edited; EXECUTOR line + session path printed; exit 0 |

### Exhaustiveness note
The matrix is the union of: argument validation (2, 3, 6) x flag pass-through (4, 5) x one happy path per mode (1 dry, 7 live). Flags are independent pass-throughs; do not enumerate combinations.

## DoD
- [ ] Fresh pristine VERIFY after the LAST edit: `make check && make test-e2e`.
- [ ] Review fleet: architecture + security (shell script, no file-routing match: minimum set) + dx (rules/*.md) + test (new test file). CRITICAL/MAJOR fixed, re-verified.
- [ ] PR to main (open, NOT merged), `SCORE: <n>/100 (threshold: 90, gate: pr)` with fresh computational evidence.
- [ ] Follow-up issues filed and linked in the PR body.
- [ ] This plan updated after every task (Progress ticked, Surprises with evidence, Decisions appended).

(BENCH-BASELINE: skipped, repo has no bench targets and no hot path)

## Progress
- [x] Analysis + plan (2026-07-22, planning session; second opinion skipped: mechanical plumbing, design approved in-session)
- [x] W1 contract (2026-07-22, authored first, commits with the change)
- [x] W2 wrapper TDD + Makefile wiring (2026-07-22, RED then GREEN; DRIFT verdict minor_drift, accepted as Decision 11)
- [x] W3 rule edit (2026-07-22, DRIFT verdict aligned)
- [x] W4 docs + live smoke + follow-ups drafted (2026-07-22, README inventory + stale line fixed, smoke EXIT=0)
- [ ] Review round + fixes
- [ ] PR + SCORE
- [ ] Close-out (plan moved to completed/, retrospective filled)

## Surprises & Discoveries

- W2.1 RED recorded: suite run with pi-exec absent fails 6/6 with `FileNotFoundError: ... scripts/pi-exec`, `Ran 6 tests ... FAILED (errors=6)`, exit 1. GREEN after W2.2: `Ran 6 tests ... OK`.
- shellcheck was NOT installed on this host: `make check` printed `SKIP shellcheck`, so lint-shell never exercised the new wrapper and "shellcheck-clean" was prose, not evidence. Installed via brew (Decision 10); fresh `make check` now reports `PASS shellcheck` with scripts/pi-exec in the list.
- README line 111 went stale from our own Makefile change (it enumerated `make test-e2e` coverage as hooks/tests only); caught during W4.1, fixed in the same PR (blast-radius item resolved at source).
- W4.2 live smoke (real Gemini call, Google-billed): `EXECUTOR: pi-exec model=google/gemini-3.6-flash brief=.../brief.md workdir=.../pi-smoke`, pi created hello.txt with the exact requested content, session JSONL path echoed (`~/.pi/agent/sessions/...2026-07-22T14-34-19...jsonl`), EXIT=0. The custom-ID warning (`Model "gemini-3.6-flash" not found for provider "google". Using custom model id.`) still prints, as expected until follow-up (b) runs `pi update`.

## Decisions
(append-only; execution-time decisions land here as new numbered rows)

| # | Decision | Choice | Rationale | Revisit if |
|---|----------|--------|-----------|------------|
| 10 | shellcheck availability | Installed via brew on this host during execution | lint-shell SKIPped silently, making the wrapper's lint status unverifiable; the gate must actually run | host provisioning moves to a managed setup |
| 11 | W2 minor drift | Accepted: `--help`/usage block and extra `workdir:` line in dry-run output | DRIFT flagged both as unrequested; kept as operability aids, no behavioral change, tests unaffected | either interferes with trace parsing or tests |

## Outcomes & Retrospective
(fill at close: shipped, gaps, lessons)
