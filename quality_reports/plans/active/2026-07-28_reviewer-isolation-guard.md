# ABOUTME: ExecPlan for issue #116: PreToolUse hook denying un-isolated *-reviewer Agent launches
# ABOUTME: Launch-side belt for #115's prose guard; deny with countable ISOLATION-EXEMPT escape, fail-open on env failures

# Reviewer isolation guard: PreToolUse on Agent launches (issue #116)

**Repo:** claude-forge, branch `feat/reviewer-isolation-guard` off `main` | **Issue:** #116, follow-up from #115 and #114 open item 1 | **Refs:** `quality_reports/plans/completed/2026-07-29_reviewer-isolation.md`, `quality_reports/approvals/2026-07-29_reviewer-isolation.md`
**Origin:** #115 shipped `isolation: "worktree"` on review-agent launches plus an agent-side prose guard, and documented the launch parameter as fail-open: nothing in `hooks/` inspects Agent tool calls. This plan adds the preventing point. Second opinion 2026-07-28: Gemini + DeepSeek surviving, isolated Claude FAILED (401 expired OAuth); both survivors endorsed PreToolUse-on-Agent with deny semantics and fail-open on environment failures.

## Analysis (verified 2026-07-28, do not re-derive)

- **The check is deterministic at launch time.** PreToolUse hooks register per tool matcher (`hooks/settings.example.json`, `PreToolUse` array: matchers `Bash`, `Write`, `Edit`, `NotebookEdit`, `MultiEdit` today, no `Agent`) and read a stdin JSON payload with `session_id`, `tool_name`, `tool_input`. For the Agent tool, `tool_input` carries `subagent_type`, `prompt`, and optionally `isolation`. This is unlike the Edit-attribution problem that killed interception in #115's analysis: the launch itself declares reviewer-ness and isolation in one payload.
- **Deny convention exists in-house.** `hooks/freeze-guard.sh` emits `{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"..."}}` and exits 0; `hooks/main-branch-guard.sh` shows the fail-closed variant. Each hook states its fail direction and rationale in a header comment; the repo treats that choice as per-hook and deliberate (freeze-guard fails OPEN with an explicit comparison comment).
- **What #115 left open, verbatim.** `skills/orchestrator/SKILL.md:173`: "The parameter is the whole mechanism, so a launch that omits it fails open. Nothing in `hooks/` inspects it…". `rules/orchestrator-protocol.md:59`: "Prose, not enforcement: nothing checks the parameter…". Both sentences become false the moment this hook lands and MUST be updated in the same change (blast radius, not optional).
- **The agent-side guard stays untouched.** The three-condition write gate (`agents/security-reviewer/AGENT.md:28`, byte-identical in all 7, pinned by `hooks/tests/test_agent_definitions.py` including a 7-file hash) keys on the brief-carried assertion. This plan does NOT touch the 7 AGENT.md files: no PINNED churn, and the guard remains the universal backstop for launch paths the hook cannot see.
- **pr-review must not break.** `skills/pr-review/SKILL.md:81` reviews in a throwaway clone (`$PR_REVIEW_DIR`), deliberately without `isolation` (a worktree of the active repo would be pointless there); `:98` routes the same reviewer agent types. A naive deny breaks the skill. NOTE a pre-existing tension (not caused by this plan): `:118` has reviewers write red-green tests inside `$PR_REVIEW_DIR`, but the #115 agent-side guard already self-downgrades clone-launched reviewers to read-only (in a clone `--git-dir` equals `--git-common-dir`). Out of scope here; filed as follow-up (see below).
- **Workflow bypass is structural.** Workflow-tool scripts spawn subagents via an internal `agent()` primitive with `agentType:`; those launches never pass through the Agent tool, so no PreToolUse matcher sees them. DeepSeek's requirement folded in: this is documented first-class (hook header + SKILL.md), with the agent-side guard named as the layer that still covers it, never handwaved as a footnote.
- **Hook install topology (memory, verified across audits):** `~/.claude/hooks/` entries are per-file symlinks to the forge repo; a NEW hook file requires a post-merge `ln -s` plus a registration block Max applies to `~/.claude/settings.json`. The repo-side source of truth for registration is `hooks/settings.example.json`.

### Second-opinion hard requirements folded in

1. **Deny, not warn** (Gemini + DeepSeek): the targeted failure mode is honest omission by a distracted/unattended orchestrator; an additionalContext warning is invisible on exactly that path. The deny reason must carry the remediation verbatim (Gemini: copy-pasteable relaunch or exemption syntax).
2. **Fail OPEN on environment failures** (both, arguing the freeze-guard precedent): missing jq, unparseable payload, missing `subagent_type` → allow + one stderr warning. The gated action is corrigible (a launch, revertible writes), unlike main-branch-guard's irreversible commit-to-main; a false deny bricks every review until someone notices. Fail closed ONLY on the policy violation itself.
3. **Exemption = prompt marker, not settings allowlist** (Gemini; DeepSeek preferred settings but conceded the payload carries no caller-skill identity, which makes an allowlist structurally impossible). DeepSeek's accident-collision concern is mitigated by anchoring: the marker only counts at line start.
4. **Document that exemption ≠ write-enable** (DeepSeek must-fix): the marker silences the hook only; an exempted launch still self-downgrades to read-only agent-side because the isolation assertion is absent. That is correct for pr-review (clone isolation is orchestrated outside the agent) and MUST be stated where the marker is documented.
5. **Non-git cwd pre-flight** (Gemini): if `git rev-parse --is-inside-work-tree` fails in the session cwd, allow: there is no git state to corrupt and `isolation: "worktree"` could not work anyway.

## Design decisions (locked)

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 1 | Enforcement point | New PreToolUse hook, matcher `Agent`, sh + jq house style (`hooks/reviewer-isolation-guard.sh`) | Only point that sees `subagent_type` + `isolation` together, deterministically, before the launch |
| 2 | Verdict semantics | DENY when `subagent_type` matches `*-reviewer` AND `isolation != "worktree"`, unless exempted; reason carries both remedies verbatim (add the parameter, or add the exemption line) | Failure mode is honest omission; a warning is invisible to an unattended loop (both reviewers) |
| 3 | Fail direction | OPEN on env failures (no jq, bad JSON, missing fields) with stderr warning; closed only on the policy hit. Header comment states this against the freeze-guard/main-branch-guard precedents | Gated action is corrigible; false deny bricks all review (both reviewers) |
| 4 | Exemption mechanism | Line-anchored `ISOLATION-EXEMPT: <reason>` in `tool_input.prompt` (regex `^ISOLATION-EXEMPT: .+` in multiline mode); mid-sentence mentions do NOT count | Payload has no caller identity, so a settings allowlist is impossible; line-anchor kills accidental collisions; greppable → countable, same discipline as #114/#115 |
| 5 | Exemption scope | Marker allows the LAUNCH only; agent-side read-only downgrade still applies and is documented at every place the marker is | DeepSeek must-fix: undocumented, the marker reads as write-enable, which it is not |
| 6 | Scope of reviewer-ness | Suffix match on `subagent_type` ending in `-reviewer` (the 7 agent types; dynamic, no hardcoded list) | Mirrors the dynamic glob of `test_agent_definitions.py`; a future 8th reviewer is covered at birth; `test-design-reviewer` is a skill, not an agent type, and never reaches the Agent tool |
| 7 | Ad-hoc launches | Uniform deny with remediation-bearing reason; NO content heuristics to distinguish orchestrator from user | Heuristics on prompt content are the fragile path #115 already rejected in another form; the cost is one relaunch with a copy-pasteable fix. Revisit if ad-hoc denies become measured friction |
| 8 | Workflow bypass | Documented first-class (hook header + SKILL.md), agent-side guard named as the covering layer; no script parsing | Parsing arbitrary Workflow scripts is over-engineering (Gemini); silence would misrepresent the control (DeepSeek) |
| 9 | `tools:` allowlist | Still not shipped, still pinned by test | Locked in #115 (decision 2); not relitigated |
| 10 | pr-review write-capability tension | Out of scope; follow-up issue filed at close | Pre-existing from #115; fixing it means amending the pinned 7-file block (PINNED churn), a separate contract |

## Workstreams & tasklist

### W1 - The hook
- [ ] W1.1 `hooks/reviewer-isolation-guard.sh` (new): payload on stdin; fail-open ladder (no jq → warn+allow; unparseable → warn+allow; `tool_name != "Agent"` or missing `subagent_type` → allow silently); non-git cwd → allow; suffix match `-reviewer`; `isolation == "worktree"` → allow; line-anchored `ISOLATION-EXEMPT:` in prompt → allow (stderr note naming the reason, so exemptions are loud in the transcript); else deny JSON whose reason contains, verbatim: `relaunch with isolation: "worktree"` and `or add a line 'ISOLATION-EXEMPT: <reason>' to the prompt (the reviewer will stay read-only agent-side)`. Header comment: fail direction + precedent comparison + Workflow-bypass limitation + "countable, not enforced" framing.
- [ ] W1.2 `hooks/settings.example.json`: new `matcher: "Agent"` block registering the hook (timeout 10, matching siblings).

### W2 - Docs made true again
- [ ] W2.1 `skills/orchestrator/SKILL.md:173`: rewrite the fail-open bullet: the omission path is now denied by `reviewer-isolation-guard` on the Agent tool; remaining prose-only paths named explicitly (Workflow `agent()` launches, an edited/unregistered hook); the agent-side guard stays the universal backstop. Document the exemption marker here with decision 5's caveat.
- [ ] W2.2 `rules/orchestrator-protocol.md:59`: update the "Prose, not enforcement: nothing checks the parameter" clause to "hook-enforced on the Agent tool path (`reviewer-isolation-guard`), prose elsewhere (Workflow launches, edited hooks)". One clause, spine stays terse.
- [ ] W2.3 `skills/pr-review/SKILL.md` Phase 3 (~:98): reviewer briefs open with `ISOLATION-EXEMPT: pr-review throwaway clone $PR_REVIEW_DIR` plus one sentence stating the agent-side read-only consequence (decision 5).

### W3 - Test + contract + close
- [ ] W3.1 `hooks/tests/test_reviewer_isolation_guard.py` (new, stdlib, house style: invoke the sh hook as a subprocess with synthetic payloads, like the other hook tests; auto-picked by `Makefile:31` glob): E2E rows 1-6 below.
- [ ] W3.2 Change contract `quality_reports/harness_changes/2026-07-28_reviewer-isolation-guard.md` (six fields, ONE failure mode: un-isolated reviewer launch through the Agent tool).
- [ ] W3.3 Follow-up issue: pr-review reviewers are read-only agent-side post-#115 while `:118` expects red-green writes in the clone (pre-existing tension, decision 10). Label documentation. Close #116 via PR body (`Closes #116`).
- [ ] W3.4 Install note in the PR body: post-merge `ln -s` for the new hook file + registration block for `~/.claude/settings.json` (Max applies; settings.example.json is the source).

## E2E matrix

| # | Surface | Scenario | Assertion | Depth |
|---|---------|----------|-----------|-------|
| 1 | Policy deny | `*-reviewer` launch, no/empty/wrong `isolation`, no marker | deny JSON, reason contains both verbatim remedies | 3★ (missing key, `""`, `"remote"`) |
| 2 | Policy allow | `isolation: "worktree"` present | exit 0, no output | 2★ |
| 3 | Scope | non-reviewer types (`software-engineer`, `Explore`, `general-purpose`) without isolation | allow silently | 2★ |
| 4 | Exemption | line-anchored `ISOLATION-EXEMPT: reason` → allow + stderr note; mid-sentence `…is ISOLATION-EXEMPT because…` → still deny | anchor is load-bearing | 3★ (both directions + marker in middle line of multi-line prompt) |
| 5 | Env failures | jq absent (PATH stripped), malformed JSON, missing `subagent_type` | allow + one stderr warning each (fail-open per decision 3) | 3★ |
| 6 | Non-git cwd | payload fine, cwd outside any repo | allow | 2★ |
| 7 | Live dogfood | register hook locally, launch one real reviewer WITH isolation (silent pass) and one deliberate omission (observed deny in-session), then relaunch per the reason | the deny message is actionable end-to-end | 2★ |

Depth: 3★ = behavior + edge + error, 2★ = happy path, 1★ = smoke.

COVERAGE: 7/7 paths (100%)

### Exhaustiveness note
The union is: the four verdict classes the hook can emit (deny, policy allow, scope allow, exempt allow), the two failure ladders (environment, non-git), and one live launch proving the registration + message loop. Workflow-bypass is deliberately NOT a row: the hook cannot see those launches by construction (decision 8), and pinning a test to its blindness would imply coverage it does not have. Combinatorial padding (every agent type × every isolation value) is forbidden; the suffix rule and the three isolation variants in row 1 cover the input classes.

## DoD

| # | Criterion | Command | Expected | Auto |
|---|-----------|---------|----------|------|
| 1 | Guard test green | `uv run --no-project python3 hooks/tests/test_reviewer_isolation_guard.py` | exit 0 | yes |
| 2 | Fresh pristine VERIFY after the LAST edit | `make check` | exit 0 (shellcheck covers the new sh) | yes |
| 3 | Full suites | `make test-e2e` | exit 0, new test's pass line present | yes |
| 4 | Live dogfood (E2E row 7) | - | deny observed and remediated in-session | no |
| 5 | Review fleet: security + architecture + test (hook is code + test file; routing) | - | CRITICAL/MAJOR fixed, re-verified | no |
| 6 | PR to main open, NOT merged, `Closes #116`, install note (W3.4) | - | `SCORE: <n>/100 (threshold: 90, gate: pr)` | no |
| 7 | Change contract committed | - | six fields, one failure mode | no |
| 8 | Plan updated after every task | - | Progress, Surprises, Decisions | no |

## Progress
- [x] Analysis + second opinion (Claude FAILED 401; Gemini + DeepSeek OK) + plan (2026-07-28)
- [x] W1 hook + registration (2026-07-29): `hooks/reviewer-isolation-guard.sh` (10-step ladder, deny JSON carrying both remedies verbatim), `hooks/settings.example.json` PreToolUse `Agent` block. Evidence: `shellcheck` clean, six hand-driven smoke payloads exercising deny / worktree-allow / anchored-exempt / mid-sentence-deny / non-reviewer / malformed-JSON.
- [x] W2 docs made true again (2026-07-29): `skills/orchestrator/SKILL.md:173` (bullet rewritten, prose-only paths named, exemption documented with the not-a-write-enable caveat), `rules/orchestrator-protocol.md:59` (one clause), `skills/pr-review/SKILL.md` Phase 3 (exemption line + read-only consequence), `README.md` hook-inventory row (decision 12). Evidence: `scripts/check_repo.py check` all PASS; `grep -rn "Nothing in .hooks/\|nothing checks\|Prose, not enforcement"` over `agents/ skills/ rules/ README.md` returns no surviving false claim.
- [ ] W3 test + contract + follow-up + close
- [ ] Review round + fixes
- [ ] PR + SCORE

## Surprises & Discoveries
- (W1) **`make check` does not shellcheck `hooks/*.sh`.** DoD row 2 says "shellcheck covers the new sh"; `Makefile:38` runs it over `install.sh get.sh scripts/pi-exec scripts/score-log.sh` only, so every hook in `hooks/` is unlinted today. The new hook was shellchecked by hand instead (`shellcheck hooks/reviewer-isolation-guard.sh` -> clean, no output). Decision 13 keeps the Makefile untouched and files the gap as tech debt.
- (W1) **The plan contradicts itself on missing `subagent_type`:** W1.1 says "allow silently", E2E row 5 groups it with the environment failures that must warn. Resolved as decision 11 (silent), because `subagent_type` is optional on the Agent tool: a warning there fires on ordinary general-purpose launches.
- (planning) pr-review Phase 4b (`skills/pr-review/SKILL.md:118`) expects reviewers to WRITE red-green tests in `$PR_REVIEW_DIR`, but the #115 agent-side gate already self-downgrades clone-launched reviewers to read-only (`--git-dir` == `--git-common-dir` in a clone). Pre-existing tension, discovered while scoping the exemption; decision 10 defers it to a follow-up issue.

## Decisions
(append-only)

| # | Decision | Choice | Rationale | Revisit if |
|---|----------|--------|-----------|------------|
| 11 | Missing `subagent_type` on an `Agent` payload | Allow **silently** (W1.1 wording), NOT allow+warn (E2E row 5 wording). The plan contradicts itself on this one input class; silence wins | `subagent_type` is optional on the Agent tool and defaults to `general-purpose`, so its absence is an ordinary non-reviewer launch, not an environment failure. Warning there would print on every general-purpose launch, which is stderr noise, not a fail-open signal. Row 5 keeps its warning assertions for jq-missing and malformed JSON | A launch path is observed where an `Agent` payload legitimately loses a `subagent_type` it did carry |
| 12 | `README.md` hook inventory | Add a `reviewer-isolation-guard.sh` row in W2 (extra file vs the plan's file list) | `README.md:105-120` enumerates every hook with its trigger and fail direction. A shipped hook absent from it is exactly the "doc references old behavior" staleness the quality gates score as Minor. Same "docs made true again" class as W2.1/W2.2, not scope expansion | - |
| 13 | shellcheck coverage of the new hook | Run `shellcheck hooks/reviewer-isolation-guard.sh` by hand; do NOT widen `Makefile` `lint-shell` | DoD row 2 assumes `make check` shellchecks the new file; it does not (`lint-shell` covers `install.sh get.sh scripts/pi-exec scripts/score-log.sh` only). Widening it to `hooks/*.sh` would pull ~20 pre-existing scripts into this PR's gate: unrelated diff, unbounded outcome. Filed as tech debt at close | The hooks suite grows a second unlinted shell hook, i.e. the gap starts costing real defects |

## Outcomes & Retrospective
(fill at close)
