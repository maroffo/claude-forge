# ABOUTME: ExecPlan for the five gstack borrowings: freeze hook, plan-matrix depth, scope modes, score history, drift check.
# ABOUTME: All five redesigned after a 2-lab second opinion; hooks fail open, boundary is repo-local, drift check is unthrottled and silent-when-clean.

# gstack borrowings (in-session analysis, 2026-07-27)

**Repo:** claude-forge, branch `feat/gstack-borrowings` off `main` | **Issue:** in-session analysis | **Refs:** `github.com/garrytan/gstack`, `rules/harness-changes.md`, precedent plan `quality_reports/plans/completed/2026-07-27_swarm-forge-borrowings.md`
**Origin:** Max asked whether gstack (from x.com/beamnxw article) has ideas worth borrowing (2026-07-27), then selected 5 of 6 candidates via AskUserQuestion (scrape→skillify deferred: coupled to gstack's Playwright daemon + bun). Analysis + 2-lab second opinion (Gemini + DeepSeek; isolated Claude failed 401, expired OAuth in the volume, same failure as swarm-forge day). Reviewers overturned two of my design choices (fail mode, boundary location), split on one (Selective Expansion, resolved per DeepSeek), and extended two (drift check content-drift, matrix fold-in).

## Analysis (verified 2026-07-27 on main, do not re-derive)

### gstack mechanics studied (source read via gh api, 2026-07-27)

- **freeze**: skill-frontmatter-registered PreToolUse hooks on Edit/Write run `freeze/bin/check-freeze.sh`; boundary = ONE absolute path in `~/.gstack/freeze-dir.txt`; no file = allow-all; prefix match after `cd … && pwd -P`; fails OPEN on parse failure; documented NOT a security boundary (Bash bypasses it). Known bug worth not repeating: the skill writes the state file via `$GSTACK_STATE_ROOT` while the hook reads `${CLAUDE_PLUGIN_DATA:-$HOME/.gstack}`: two path sources that only accidentally agree.
- **plan-eng-review diagrams**: prompt-only, no validator; devices = priority line ("Never skip … the test diagram"), anti-skip rule naming the excuse, Completion Summary with fillable slot ("diagram produced, ___ gaps"). Artifact = ASCII test-coverage diagram: per-test depth stars (3=behavior+edge+error, 2=happy path, 1=smoke), [GAP] markers, computed `COVERAGE: n/m paths (p%)` line. ASCII over mermaid deliberately (terminal-native, git-diffable).
- **plan-ceo-review scope modes**: EXPANSION / SELECTIVE EXPANSION / HOLD SCOPE / REDUCTION chosen via AskUserQuestion with context defaults (greenfield→expansion, enhancement→selective, bugfix/refactor→hold, >15 files→suggest reduction). Invariant: no silent scope change in any mode, every add/cut individually opted in. Carries a premise NOT imported here: "COMPLETENESS IS CHEAP … boil the ocean".
- **health**: weighted 0-10 composite, missing tool = skip + weight redistribution, one JSONL line per run to a per-project history file, trend = tail-10 + delta. Their own caveat: the model does the arithmetic and the append; no script.
- **auto-update/drift**: SessionStart script, `set +e` exit 0 always, 1h throttle timestamp written regardless of outcome, background fork, mkdir-as-lock, `GIT_TERMINAL_PROMPT=0`. The auto-update itself is REJECTED for forge (unattended hourly `git pull` + re-setup of the harness is a supply-chain surface, and forge is the source repo Max develops). Only the defensive patterns are kept, for a read-only check.
- **scrape→skillify**: REJECTED for now: hard-depends on gstack's `$B` browse daemon (Playwright/CDP sidecar) and bun. Transferable patterns (stage→test→approve→atomic-rename, bounded conversation walk-back, pure-parser/impure-driver split) recorded as a deferred idea for a future skill-forge "codify" mode.

### forge gaps these close (file:line, verified)

- Orchestrator invariant "software-engineer … scoped to its assigned files" (`rules/orchestrator-protocol.md`, Invariants) has no deterministic enforcement; `quality_reports/plans/tech-debt.md:7` already asks for a PreToolUse write-gate in the same family.
- Fail-mode precedent divergence: `hooks/main-branch-guard.sh:10-13` fails CLOSED when jq is missing. Second opinion (unanimous): that is a precondition failure on a commit gate; a debugging aid must fail OPEN on data-element parse failure or it bricks the session (false-DENY is non-obvious and unrecoverable in-session; false-ALLOW is obvious and undoable).
- No diagram/depth mandate anywhere: `grep -ri diagram\|mermaid` over `skills/plan-forge/`, `skills/orchestrator/SKILL.md`, `rules/plan-first-workflow.md` = 0 hits. The E2E matrix (`skills/plan-forge/references/plan-template.md:50-55`) records scenario × assertion but not test DEPTH: a smoke test and a full behavioral test are indistinguishable rows.
- Hold Scope is hardcoded: `skills/refine-requirements/SKILL.md:26` ("capture as deferred idea, redirect") and `:34` ("clarify HOW … not WHETHER to add more"). No sanctioned path to deliberately opt into scope exploration.
- `/score` has no history: `skills/score/SKILL.md` reports a point-in-time number; SCORE events land in harness-trace JSONL per-session but no cross-session trend view exists.
- Install drift: two documented incidents (stale `agents/` copies missed by two audits; new hook files needing post-merge `ln -s`). `install.sh:211-233` guards symlinks at install time only; nothing checks at runtime. Max's `~/.claude/hooks/` also contains NON-forge hooks (`notify.sh`, `herdr-agent-state.sh`) that must never be flagged.

### Second-opinion hard requirements folded in

1. **Freeze fails open on unparseable data, inert when no boundary file** (Gemini + DeepSeek, unanimous must-fix): DENY-on-unparseable bricks the session (user cannot even re-freeze; recovery requires an external terminal). Fail-closed remains only for gates guarding irreversible actions (main-branch-guard class), not debugging aids.
2. **Boundary is repo-local, never global** (unanimous must-fix): a global `~/.claude/freeze-boundary` freezes every concurrent session in every repo. Boundary file lives at the git root of the frozen repo.
3. **One source of truth for the boundary path** (DeepSeek): gstack's write-path/read-path mismatch is the exact bug class; skill and hook must share one constant, covered by the existing `hooks/tests/test_hook_constants_sync.py` pattern.
4. **Per-agent scoping stays out of v1, honestly** (DeepSeek; Gemini's env-var counterproposal rejected): Agent-tool subagents share the CLI process env; there is no per-subagent export point, so an env-var scheme is prose pretending to be enforcement.
5. **Never batch scope expansions** (DeepSeek): each proposed addition is its own AskUserQuestion; bundling into one "Selective Expansion accepted" is the erosion vector.
6. **Score history gitignored for the honest reason** (DeepSeek): fields carry no exploits, but branch names + low scores are a metadata leak corroborating gitignored findings. Document that the file is a denormalized view of harness-trace SCORE events.
7. **Drift check must catch stale COPIES, not just symlinks** (DeepSeek): the original incident class was a regular file with old content, which a dangling/missing check passes. Compare content (shasum) for regular files matching forge names.
8. **No throttle on the drift check; silent when clean** (Gemini, supersedes my 1/day): the check is <10ms read-only; the value is catching drift on the FIRST session after a merge. Zero output when clean removes the noise-budget concern; a throttle only adds a clock-skew failure mode (DeepSeek).

Reviewer claim rejected, with reason: mkdir-lock on concurrent `/freeze` writes (DeepSeek "borrow"): single-user racing themselves on a one-line file write; overengineering per `rules/quality-gates.md` Major rubric ("error handling for unreachable scenarios"). Gemini's "drop Selective Expansion entirely" rejected: the deliberate, opt-in expansion mode is precisely the borrow Max selected; requirement 5 contains the erosion vector.

## Design decisions (locked)

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 1 | Freeze fail mode | No boundary file → hook inert (allow). File present + tool path unparseable → ALLOW + one-line warning to stderr. File present + path parses + outside boundary → deny | Requirement 1, unanimous. Not a security boundary; say so in the skill like gstack does |
| 2 | Boundary location | `<git-root>/.freeze-boundary`, single absolute dir path inside the repo, gitignored; hook resolves the git root of the file being edited (reuse `_commit_target.sh` idiom) | Requirement 2, unanimous. Cross-repo sessions untouched |
| 3 | Freeze surface | ONE skill `/freeze` (`/freeze <dir>`, `/freeze status`, `/freeze off`); one hook `hooks/freeze-guard.sh` on PreToolUse Edit\|Write\|NotebookEdit; registered in settings.example.json like every forge hook, NOT via skill frontmatter | Fewer harness surfaces than gstack's 4 skills; forge convention is settings.json registration |
| 4 | Boundary path constant | Defined once in `hooks/_freeze_boundary.sh`, sourced by hook; skill quotes the same constant; `test_hook_constants_sync.py` extended to cover it | Requirement 3; gstack's bug not repeated |
| 5 | Per-agent enforcement | Out of v1, stated in the skill ("session-wide; does not scope parallel subagents") | Requirement 4 |
| 6 | Depth in plans | E2E matrix gains a `Depth` column (3★ behavior+edge+error / 2★ happy path / 1★ smoke) and a computed `COVERAGE: n/m paths (p%)` footer; both MANDATORY where the matrix is (test-heavy tasks). Full ASCII path-trace diagram RECOMMENDED for complex-verdict plans only. Mermaid stays optional for architecture | DeepSeek fold-in: kills matrix↔diagram sync drift; Gemini: mandatory-for-all is ceremony. Stars and ratio are the additive content |
| 7 | Diagram validator | None in v1; DoD slot ("Depth column filled, COVERAGE footer present, N gaps") + human plan approval are the pressure. Presence-check hook recorded in tech-debt with the falsification below | Both reviewers call slot-only weak; contract falsification makes the decay measurable before we build a hook |
| 8 | Scope modes | refine-requirements step 0: bugfix/refactor → Hold Scope silently, NO question; feature → AskUserQuestion Hold (default) / Selective Expansion / Reduction; greenfield → same + Expansion. Unsure → Hold. Every expansion is its own AskUserQuestion (never batched); declined expansions become deferred ideas as today. "Boil the ocean" premise NOT imported | Requirement 5; split resolved per DeepSeek; defaults table kept (misclassification escape = Hold) |
| 9 | Score history | `scripts/score-log.sh` does the append (model never does arithmetic-append); file `quality_reports/score-history.jsonl` in the TARGET repo, gitignored, guard appends the ignore line exactly once (reuse the reviews/ guard idiom); `/score` renders tail-10 trend + delta vs previous | Requirement 6; gstack's model-arithmetic caveat fixed |
| 10 | Drift check scope | `hooks/forge-drift-check.sh` on SessionStart startup\|resume, no throttle, `set +e` exit 0 always, SILENT when clean, ≤3 lines when not. Checks, only for entries resolving into a forge checkout: (a) dangling symlinks; (b) repo hooks/agents/rules files with no ~/.claude entry, only for categories already managed by ≥1 forge symlink; (c) forge-named hook .sh present but unregistered in settings.json; (d) regular-file entries matching forge names with differing shasum (stale copy) | Requirements 7, 8. Non-forge hooks ignored by construction (realpath test). settings matcher-format drift = documented known gap |
| 11 | Drift check omissions | `~/.claude/.forge-omit` (one name per line) suppresses intentionally-absent components on secondary machines | DeepSeek false-positive attack (partial installs) |
| 12 | Auto-update | Never. Drift check is read-only, no network, no git | Supply-chain surface; forge is the source repo |
| 13 | skillify | Deferred, not planned. One tech-debt line pointing at the transferable patterns | Coupled to $B daemon + bun; Max deferred it at scope selection |

Append-only after this point. The implementing session does NOT relitigate; execution-time decisions get NEW rows in ## Decisions below.

## Workstreams & tasklist

Writer concurrency: W1, W3, W4, W5 have disjoint file scopes and may run in parallel (max 3 at once per budget); W2 touches plan-forge only. W6 last.

### W1 - freeze guard (hook + skill + contract)
- [ ] W1.1 `hooks/_freeze_boundary.sh`: single constant `FREEZE_BOUNDARY_BASENAME=".freeze-boundary"` + helper resolving it from a file path's git root. ABOUTME header.
- [ ] W1.2 `hooks/freeze-guard.sh`: PreToolUse on Edit|Write|NotebookEdit. Reads `tool_input.file_path` via jq; jq missing → allow + warning (decision 1: this hook is an aid, not a gate); no boundary file at the target's git root → allow; path unparseable → allow + one-line stderr warning; parsed path (physical, `pwd -P` idiom from gstack) outside boundary → deny JSON with the boundary path and the `/freeze off` remedy in the message.
- [ ] W1.3 `skills/freeze/SKILL.md`: `/freeze <dir>` writes the boundary file (absolute physical path, trailing slash) at the CURRENT repo's git root and ensures `.freeze-boundary` is gitignored there (guard idiom); `/freeze status` prints it; `/freeze off` removes it. States plainly: not a security boundary (Bash bypasses it), session-wide, does not scope parallel subagents (decision 5).
- [ ] W1.4 `hooks/tests/test_freeze_guard.py`: matrix rows 1-6 below; extend `test_hook_constants_sync.py` for the shared constant.
- [ ] W1.5 settings.example.json: three matcher entries (Edit, Write, NotebookEdit) with timeout 10.
- [ ] W1.6 Contract `quality_reports/harness_changes/2026-07-27_freeze-guard.md`. Failure mode: edits landing outside the intended work area during focused debugging (orchestrator scope invariant unenforced). Falsification: a session where freeze is active and a legitimate in-boundary edit is denied (false block), or the hook measurably fails open more than it protects (boundary set but >0 out-of-boundary edits pass in a traced session).

### W2 - plan depth (template + contract)
- [ ] W2.1 `skills/plan-forge/references/plan-template.md`: E2E matrix gains `Depth` column + `COVERAGE: n/m paths (p%)` footer with the star legend inline; new RECOMMENDED (complex verdict only) ASCII path-trace subsection with a 4-line example; DoD line "- [ ] (test-heavy) Depth column filled, COVERAGE footer computed, gaps counted: <n>".
- [ ] W2.2 `skills/plan-forge/SKILL.md` step 3 non-negotiables: one line adding the Depth/COVERAGE mandate next to the existing exhaustiveness note.
- [ ] W2.3 Contract. Failure mode: E2E matrices where smoke tests are indistinguishable from behavioral tests, hiding thin coverage behind row count. Falsification: ≥2 of the next 10 test-heavy plans ship with the Depth column empty or COVERAGE absent (the prompt-only device decayed → build the presence-check hook from tech-debt).

### W3 - scope modes (skill + rule + contract)
- [ ] W3.1 `skills/refine-requirements/SKILL.md`: mode step per decision 8, with the never-batch rule verbatim ("each proposed addition is its own AskUserQuestion; never bundle"), unsure→Hold escape, declined→deferred idea unchanged. Description frontmatter UNTOUCHED (trigger surface stable).
- [ ] W3.2 `rules/plan-first-workflow.md` Requirements Refinement: one line replacing the implicit always-Hold with "scope mode chosen explicitly (Hold default; expansions only ever individually opted in); see refine-requirements".
- [ ] W3.3 Contract. Failure mode: no sanctioned path to deliberately explore scope at refinement time (the office-hours reframe value lost to hardcoded Hold). Falsification: a refinement session where the model proposes expansions unprompted in Hold mode, or batches multiple expansions into one question (erosion the reviewers predicted → revert to hardcoded Hold).

### W4 - score history (script + skill + contract)
- [ ] W4.1 `scripts/score-log.sh`: args `--score --gate --check --e2e --major --minor`; appends one JSONL line `{ts,branch,score,gate,check,e2e,major,minor}` to `quality_reports/score-history.jsonl` (creating dir), ensures the gitignore line exactly once (reviews/ guard idiom); prints the tail-10 trend table + delta vs previous on `--trend`.
- [ ] W4.2 `skills/score/SKILL.md`: after reporting, call the script to append and render trend; comment in both places: "denormalized view of harness-trace SCORE events; change one, change the other".
- [ ] W4.3 Contract (optional tier, ship anyway). Failure mode: no cross-session quality trend; regressions between sessions invisible. Falsification: history file corrupt/diverging from trace SCORE events, or trend never consulted in 20 sessions.

### W5 - drift check (hook + contract)
- [ ] W5.1 `hooks/forge-drift-check.sh` per decisions 10-11. Forge-origin test: entry resolves (readlink/realpath) into the repo containing this hook's own physical location. Categories: hooks/*.sh, agents/*, rules/*.md (skills/ only when `~/.claude/skills` itself is forge-managed). Output lines prefixed `[forge-drift]` with the exact `ln -s` or registration remedy.
- [ ] W5.2 `hooks/tests/test_forge_drift_check.py`: matrix rows 10-16.
- [ ] W5.3 settings.example.json: SessionStart startup|resume entry.
- [ ] W5.4 Contract. Failure mode: post-merge stale copies / missing symlinks / unregistered hooks surviving undetected across sessions (2 documented incidents). Falsification: a third stale-install incident on a machine where the check runs, or recurring false positives that train Max to ignore `[forge-drift]` lines.
- [ ] W5.5 Bootstrap note in README hooks section: the check cannot detect its own missing installation; the post-merge step for THIS PR is manual (`ln -s` + settings.json), listed in the PR body.

### W6 - docs + follow-ups
- [ ] W6.1 README: rows for /freeze skill, freeze-guard + forge-drift-check hooks, score-history file in the quality_reports tree.
- [ ] W6.2 tech-debt.md: (a) plan Depth/COVERAGE presence-check hook (from decision 7); (b) skillify transferable patterns for a future skill-forge "codify" mode (from decision 13); (c) settings.json matcher-format drift not covered by the drift check (known gap).
- [ ] W6.3 Delete the stale duplicate `quality_reports/plans/active/2026-07-27_swarm-forge-borrowings.md` (untracked pre-execution snapshot; `completed/` copy is authoritative, verified by diff 2026-07-27).
- [ ] W6.4 Follow-up issues DRAFTED here (orchestrator files at PR time): none anticipated; add if execution surfaces them.

## E2E matrix

| # | Surface | Scenario | Assertion | Depth |
|---|---------|----------|-----------|-------|
| 1 | freeze-guard | boundary set, Edit inside boundary | allow (`{}` / no deny JSON) | 3★ (also trailing-slash and exact-dir edge) |
| 2 | freeze-guard | boundary set, Write outside boundary | deny JSON names boundary + `/freeze off` remedy | 3★ (also NotebookEdit path) |
| 3 | freeze-guard | no boundary file anywhere | allow, zero output | 2★ |
| 4 | freeze-guard | boundary file present, `tool_input.file_path` missing/garbled | ALLOW + one-line stderr warning (decision 1) | 3★ (garbled JSON, empty path, newline in path) |
| 5 | freeze-guard | edit in a DIFFERENT repo than the frozen one | allow (boundary is repo-local, decision 2) | 3★ |
| 6 | freeze-guard | jq absent | allow + warning, NOT deny (differs from main-branch-guard by design) | 2★ |
| 7 | /freeze skill | `/freeze <dir>` then `/freeze off` | boundary file created at git root with physical path, gitignore line appended once, then removed | 2★ |
| 8 | score-log | two sequential runs | two valid JSONL lines, trend shows delta, gitignore line present exactly once (idempotent) | 3★ (second guard run no-op) |
| 9 | score-log | history absent | `--trend` reports "no history yet", exit 0 | 2★ |
| 10 | drift-check | dangling symlink in ~/.claude/hooks | one `[forge-drift]` line with remedy | 2★ |
| 11 | drift-check | new repo hook file, no ~/.claude symlink, category forge-managed | flagged with exact `ln -s` remedy | 3★ (and NOT flagged when category has zero forge symlinks) |
| 12 | drift-check | forge hook symlinked but absent from settings.json | flagged | 2★ |
| 13 | drift-check | non-forge hook (notify.sh analog) present + registered | silent (realpath does not resolve into forge) | 3★ |
| 14 | drift-check | regular file named like a forge hook, content differs from repo | flagged as stale copy (shasum mismatch, requirement 7) | 3★ (identical content → silent) |
| 15 | drift-check | name listed in `.forge-omit` | silent | 2★ |
| 16 | drift-check | everything clean | zero output, exit 0 | 3★ (the noise budget IS the feature) |
| 17 | refine-requirements | bugfix task | no mode question asked, Hold applied | 2★ (prose-verified in review, not scripted) |
| 18 | plan-template | rendered template | Depth column + COVERAGE footer present in E2E section, DoD slot present | 1★ (grep) |

COVERAGE: 18/18 planned paths (100% of the union below).

### Exhaustiveness note
The matrix is the union of: freeze-guard decision states (boundary × parse × repo × jq) × the two mutating tools sharing one code path, score-log lifecycle (append/trend/bootstrap/idempotence), drift-check finding classes (a-d of decision 10) × origin (forge/non-forge/omitted) × clean case, plus one prose row per prompt-surface change. Hook rows are pytest cases in `hooks/tests/` per house convention; rows 17-18 are review-verified, not scripted: do not enumerate prompt behavior combinatorially.

## Budget

| Limit | Value |
|-------|-------|
| Fix rounds | 5 (default) |
| Concurrent write agents | 3 (W1/W3/W4/W5 disjoint; never >3) |
| Sub-agents total | 10 (5 SE + review fleet + fixes); more = re-plan |
| Minimum evidence to finalize | `make check` + `make test-e2e` green after last edit |

## DoD
- [ ] Fresh pristine VERIFY after the LAST edit: `make check && make test-e2e` in claude-forge.
- [ ] All five contracts committed alongside their changes, referenced in commit bodies (`rules/harness-changes.md`).
- [ ] Depth column filled, COVERAGE footer computed, gaps counted: 0 (this plan's own matrix, dogfooding W2).
- [ ] Review fleet: security + architecture + test reviewers on the diff; findings consolidated per orchestrator Finding Consolidation; CRITICAL/MAJOR fixed, re-verified.
- [ ] PR to `main` (open, NOT merged), `SCORE: <n>/100 (threshold: 90, gate: pr)` with fresh computational evidence.
- [ ] PR body lists the manual post-merge steps: `ln -s` for freeze-guard.sh, _freeze_boundary.sh, forge-drift-check.sh; settings.json registration for both hooks (drift check cannot see itself until installed).
- [ ] This plan updated after every task (Progress ticked, Surprises with evidence, Decisions appended).

## Progress
- [x] Analysis + scope selection + 2-lab second opinion + plan (2026-07-27, planning session)
- [x] W1 freeze guard (2026-07-27, wave 1; DRIFT aligned; matrix rows 1-6 green in make test-e2e)
- [ ] W2 plan depth
- [x] W3 scope modes (2026-07-27, wave 1; DRIFT aligned; frontmatter description byte-identical)
- [x] W4 score history (2026-07-27, wave 1; DRIFT aligned; matrix rows 8-9 green in make test-e2e)
- [ ] W5 drift check
- [ ] W6 docs + cleanup
- [ ] E2E matrix walked, observed output per row
- [ ] Review round + fixes
- [ ] PR + SCORE
- [ ] Close-out (plan → completed/, retrospective filled)

## Surprises & Discoveries
(fill during execution, with evidence: command output, diff, red test)

- **W1 sibling-prefix trap caught by its own tests**: a boundary written without a trailing slash matched a sibling directory (`/src` vs `/srcgen`). Fixed by comparing `"$target/"` against a boundary normalized to a trailing slash; the same slash makes the boundary dir itself count as inside. Pinned as a regression case in matrix row 1 (`hooks/tests/test_freeze_guard.py`).
- **`lint-shell` does not shellcheck `hooks/`** (only install.sh, get.sh, scripts/pi-exec, now scripts/score-log.sh). Both new hooks were shellchecked by hand during W1: clean. Existing convention, left as is.
- **The plan's "W1/W3/W4/W5 disjoint" missed a shared surface**: W1.5 and W5.3 both edit `hooks/settings.example.json`. Resolved by decision 15 (W5 moved to wave 2), no conflict occurred.

## Decisions
(append-only; execution-time decisions land here as new numbered rows, continuing from 13)

| # | Decision | Choice | Rationale | Revisit if |
|---|----------|--------|-----------|------------|
| 14 | Subagents do not commit or stage; orchestrator commits each workstream sequentially after its wave (contract together with its change, explicit paths) | Serialize all commits in the orchestrator | The worktree's git index is shared: parallel agents committing concurrently would sweep each other's staged files into the wrong commit. Also honors the orchestrator sole-committer invariant | Worktree-per-agent isolation becomes available for SE agents |
| 15 | Wave order: W1+W3+W4 parallel, then W2+W5, W6 last inline | W5 moved out of wave 1 | W1.5 and W5.3 both edit hooks/settings.example.json (shared integration surface per orchestrator parallelism rules); the plan's "W1/W3/W4/W5 disjoint" missed this overlap | - |
| 16 | (W1) Newline-bearing `tool_input.file_path` treated as unparseable: allow + warning, never resolved | Fail-open branch of matrix row 4 | Legal POSIX path, but it breaks the one-line warning contract and any repo inference is guesswork | - |
| 17 | (W1) Boundary file contents normalized through `freeze_physical_path` before comparison | Symlink-resolved on read, not just on write | A boundary spelled through a symlink would false-deny every edit inside it: exactly the unrecoverable failure the contract's falsification #1 names. Regression case in row 1 | - |
| 18 | (W1) Gitignore line for the boundary is anchored (`/.freeze-boundary`) | Anchored, not bare | The file only ever lives at the repo root; `gitignore-anchor-lint.py` warns on bare names | - |
| 19 | (W1) Empty or whitespace-only boundary file = unusable data: allow + warning | Same class as a missing path | Otherwise it would deny every edit in the repo (the false-block failure) | - |
| 20 | (W1) Tests invoke bash by absolute path in the jq-absent case | Shrunken PATH constrains the hook, not the test harness | Row 6 must starve the hook's lookups without breaking subprocess launch | - |

## Outcomes & Retrospective
(fill at close: shipped, gaps, lessons)
