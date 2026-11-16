---
name: pr-review
description: "PR-level review that composes gemini-review, the orchestrator review fleet, and (when contested) second-opinion, reading each commit's intent before judging. Use when user says review PR, review pull request, analyze PR, pr review, or /pr-review. Not for pre-commit review (use gemini-review)."
compatibility: "Requires gh CLI, Gemini CLI (GEMINI_API_KEY), and project CLAUDE.md for conventions."
---

# ABOUTME: Commit-aware PR review that reads each commit's intent before judging code.
# ABOUTME: Composes the existing review tiers and reclassifies findings by commit narrative, never re-implementing them.

# PR Review - Commit-by-Commit

## Review Tiers - pick the right one

pr-review is the PR-level tier. It COMPOSES the tiers below; it never re-implements them.

| Tier | What it is | Use when |
|------|-----------|----------|
| `gemini-review` | Fast pre-commit review of the working diff | Before committing local changes |
| Orchestrator Step 3 agents | In-loop review during implementation | While building, routed by file pattern |
| `advanced-review` | Deep isolated multi-LLM review with hard evidence | High-stakes, thorough audit |
| `pr-review` (this) | PR-level orchestration over a submitted PR | Reviewing a PR, commit by commit |

pr-review's unique value is **commit-narrative awareness**: reading each commit's intent to tell a deliberate deferral from a bug, then reclassifying findings. Everything else it delegates to the tiers above.

## Trigger

Activate when user says: "review PR", "review pull request", "analyze PR", "pr review", or `/pr-review`.

## Arguments

```
/pr-review <number|url>           Review a specific PR
/pr-review <number> --quick       Skip the gated second-opinion (faster, less thorough)
/pr-review <number> --no-gemini   Skip Gemini batches (offline mode)
```

## Why Commit-by-Commit

A monolithic diff loses context. Each commit carries intent via its message:
- A "fix(security):" commit means the author knew about the vuln.
- A "deferred to phase N" note means incomplete code is intentional.
- A fix commit after a feature commit means the issue was caught and addressed.

This lets the review reduce false positives (intent vs oversight), reveal the development narrative (feature to review to fix cycles), spot incomplete fixes, and catch regressions where a later commit breaks an earlier one.

## Finding Rules

These two rules bind every reviewer (delegated agents, Gemini segments, second-opinion) and the final report. Phase 3 pastes them into every agent brief, `prompts/gemini-segment.md` carries their Gemini form, and Phase 6 passes Claim discipline to second-opinion.

### Claim discipline

A finding is a claim about this PR's code at the reviewed head. It reaches the report only when it is:

1. **Real.** The cited line was read at the reviewed head (`git show <sha>:<file>` or the clone), not recalled, inferred from the diff summary, or taken from another reviewer's paraphrase.
2. **Reachable.** It names the trigger: the input, state or sequence that produces the wrong outcome, and how the deployed system gets there. "Could", "might" or "in theory" without a trigger is not a finding. When reaching it needs another fault first (a storage integrity failure, an operator misusing a tool, a compromised dependency), say so and size the severity for that.
3. **Sized to impact, not to votes.** Severity = impact × likelihood on the real deployment. Reviewer agreement is not evidence: "two reviewers called it Major" never sets a severity. When your own reading says lower, report the lower severity and state why; keep the higher one only with the evidence that overrides your reading.
4. **Worded within its evidence.** "Breaks", "data loss", "unsafe", "bypass", "race" only when demonstrated; otherwise state exactly what fails and when. The same holds for positive claims: "verified", "green", "reproduced" only for what you ran in this review, and say what you did not run.
5. **Not padding.** No finding for code that is correct but could be more defensive, hypothetical future misuse, style already consistent with the file, or a trade-off the PR documents. A speculative concern either gets evidence or stays out of the report.

### Test requests

A PR review hunts defects, not coverage. Tests that pin guard clauses, wiring or implementation details cost maintenance and add no safety, and the test code a review supplies gets pasted into the codebase verbatim. For PR reviews this section overrides two parts of `rules/quality-gates.md`: the "Missing test coverage for new code" Major, and "a mutant that survives gremlins" as a form of evidence (it is evidence for no finding here).

- **An uncovered line is not a finding.** Neither is a surviving mutant. Do not run mutation probes to hunt unpinned clauses, and do not ask for one test per guard, nil check, early return, error wrap, log line, constant or wiring call.
- **Ask for a test only when all three hold:** the untested behavior has a concrete regression a likely future change would cause; that regression costs something real (money, user data, auth or permissions, erasure and compliance, a prod outage); and nothing else catches it (types, an existing integration or e2e test, a CI lane that runs on PRs). It is then a Minor: one sentence naming the scenario to cover, no code.
- **Major only for an unpinned fix:** the PR fixes a bug and ships no test that fails without the fix. The one probe this rule allows, and needs as evidence: in the clone, revert only the fix hunk and run the PR's touched test files; all green means the fix is unpinned (`references/evidence.md`, taxonomy).
- **No test code in the report except Phase 4b evidence.** The only test a review may carry is the red-green test that demonstrates a Critical/Major bug (`references/evidence.md`, Deliverable). Never supply killing-test suites, mutant tables or "K1/K2/K3" blocks.

## Execution Flow

### Phase 0: Gather PR metadata

```bash
gh pr view <N> --json title,body,state,baseRefName,headRefName,additions,deletions,changedFiles,commits,labels,author
gh pr diff <N> --name-only
gh pr diff <N> > /tmp/pr<N>-diff.patch                                    # full diff for delegated reviewers
gh pr view <N> --json commits --jq '.commits[] | "\(.oid) \(.messageHeadline)"'  # chronological commits
```

**Scope assessment:**
- < 300 lines, < 5 files: simple, standard review.
- 300-1000 lines, 5-15 files: moderate, commit-by-commit adds value.
- \> 1000 lines or > 15 files: large, commit-by-commit essential + flag scope concern.
- \> 5000 lines or > 50 files: excessive, recommend reject-and-split.

### Phase 0b: Prior review record

Read what the implementing loop already recorded before judging anything (see the `orchestrator` skill, Review Artifacts):

- **Committed:** `quality_reports/approvals/<YYYY-MM-DD_slug>.md` on the PR branch. Redacted by design: branch, commit, rounds run, severity counts, CWE ids, final SCORE, residual risks, and the path of the local findings directory.
- **Local, if present:** that findings directory, `quality_reports/reviews/<slug>/NNN-findings.md`. It is gitignored, so it exists only when the PR was built on this machine; its absence says nothing about the PR.

How it changes the review:

| Record says | Do |
|-------------|-----|
| Finding `accepted` | Do not re-litigate. Cite the record and the stated rationale, unless new evidence contradicts it |
| Finding `fixed-in-round-<n>` | Verify against the diff, do not re-derive from scratch |
| Finding still `open` | Treat as a live finding of the recorded severity |
| No approval record at all | State it explicitly in the Phase 7 report: the loop did not converge, or never ran. Never read silence as a clean bill |

### Phase 1: Isolated build verification

Never check out the PR on the active repo: review always happens in a throwaway clone so uncommitted work is never contaminated. Clone, checkout the PR, run the project gate (`make check` or the CLAUDE.md equivalent), and export `$PR_REVIEW_DIR` for every later phase. Full mechanics, partial-clone budget, and base-branch comparison: `references/isolated-clone.md`.

### Phase 2: Commit narrative analysis

Read each commit oldest-first. For each, extract intent (message subject + body), scope (`--stat`), type (conventional prefix), and whether it responds to a prior review ("address findings", "fix Gemini review").

Build a commit graph tracking `introduced_in[finding]`, `fixed_in[finding]`, and `still_open[finding]`. Signals to watch:
- **fix after feat**: author caught something (verify the fix is complete).
- **"deferred to" / "phase N" / "TODO"**: intentional incompleteness (note, don't penalize as a bug).
- **duplicate commit messages**: rebase or amend residue (process smell).
- **"address review findings"**: cross-reference the review it responds to.
- **nolint / shellcheck disable**: conscious suppression (verify justification).

### Phase 3: Delegate specialized review

Route reviewers by file pattern using the **Review Routing table in the `orchestrator` skill (Step 3)**. Do not duplicate that table here; apply it as written. In parallel, run `/gemini-review` on the diff segmented by package (target < 3000 lines per segment) using `prompts/gemini-segment.md`, on the model `/gemini-review` mandates (`gemini-4-argon`), never a substitute.

Each delegated reviewer receives a **domain slice**, not the full diff: only the hunks of files its routing pattern matched, within a soft budget of ~20k token per brief (drop whole out-of-domain files first; if still over, keep the hunks and cut surrounding context). The brief declares the cut per the page-fault rule in the `orchestrator` skill (Step 1): `excluded: <files>; read on demand from /tmp/pr<N>-diff.patch or $PR_REVIEW_DIR`. Simple PRs (< 300 lines) pass whole, slicing overhead is not worth it there. Every reviewer also gets the project CLAUDE.md conventions and `$PR_REVIEW_DIR` as the working directory, with instructions to read real source (never hallucinate) and classify each finding as Critical/Major/Minor with exact `file:line`. The review already runs in a throwaway clone, so these launches deliberately omit `isolation: "worktree"`; each brief therefore opens with the line `ISOLATION-EXEMPT: pr-review throwaway clone $PR_REVIEW_DIR`, verbatim and as the FIRST line of the prompt, which is the only place `reviewer-isolation-guard` reads it (a marker further down is quoted content, not an authored exemption, and does not exempt). That satisfies the launch guard only: the brief carries no isolation assertion, so the reviewer stays read-only agent-side.

Every brief also carries the two Finding Rules sections (Claim discipline, Test requests) verbatim. The test reviewer's brief adds one line, since its agent definition encourages mutation runs: `PR review scope: no mutation runs and no killing-test suites; report test gaps only as the Test requests rule allows.`

Gemini hallucination patterns to filter (cross-validate every Gemini Critical against source): language-feature availability by version, database-engine limits misattributed across engines, standard-library APIs that do not exist.

### Phase 4: Commit-context reclassification (unique value)

Cross-reference Phase 3 findings against the Phase 2 narrative. For each finding: which commit introduced it, was there a fix commit, is the fix complete, was it intentional?

| Commit context | Effect on severity |
|----------------|-------------------|
| Bug with no fix attempt | Keep severity |
| Fix attempted but incomplete | Keep severity, note partial fix |
| Intentional deferral with TODO | Downgrade 1 level if tracked, keep if untracked |
| Intentional design choice with justification | Downgrade 1 level, note rationale |
| Pre-existing on base branch (not introduced by PR) | Note as pre-existing, still must fix (green-pipeline rule) |
| Conscious suppression with valid reason | Downgrade to Minor |
| Conscious suppression without justification | Keep severity |

### Phase 4b: Evidence gate

No Critical or Major finding reaches consolidation as a bare claim. Bug-class claims require an **executable red-green test** written and run inside `$PR_REVIEW_DIR` (fails on the PR branch = demonstrated; fails on the merge base too = pre-existing). Non-executable finding classes use the evidence taxonomy instead (CWE + line, Big-O derivation, grep-able convention, named principle). A test that does NOT fail means the claim is unproven: escalate it to Phase 6, never report it as-is. Full protocol, taxonomy, budget, and skip conditions: `references/evidence.md`.

### Phase 5: Consolidation and scoring

Deduplicate: when several reviewers find the same issue, keep one entry with cross-references, e.g. `[Security/Architecture]`. Order the report by severity (Critical first), then by component within each band.

Score per `rules/quality-gates.md` (Critical = auto-fail, Major -10, Minor -3; commit >= 80, PR merge >= 90, excellence >= 95). Do not restate the rubric here. Only evidence-backed Critical/Major findings count toward the score; claims escalated as unproven (Phase 4b) are excluded until second-opinion resolves them. Test gaps are scored per the Test requests rule, not as the rubric's "Missing test coverage" Major. Before scoring, re-read every surviving finding against Claim discipline and drop or resize the ones that fail it.

### Phase 6: Second opinion (gated)

Invoke `/second-opinion` **only when** reviewer verdicts conflict, a Critical finding is contested, or a Critical/Major claim came back **unproven** from the Phase 4b evidence gate (its red-green test did not fail). Otherwise skip it: it spins up an isolated container and is not free. When invoked, pass the disputed finding(s), the conflicting verdicts (for unproven claims: the test and its passing output) and the Claim discipline section, and ask for evidence on the trigger and the impact, not for a classification. Its answer moves a severity only when it brings new evidence (a line, a trigger, a failing case); a bare verdict is a vote and changes nothing. For unproven claims, keep only if second-opinion supplies new evidence; otherwise drop and count under "Hallucinations caught".

### Phase 7: Present report

Use the report structure in `references/output-format.md`: header (branch, scope, score, reviewers, hallucinations caught), commit narrative, Critical/Major/Minor sections, a reclassifications table, dependencies, process observations, and a recommendation (APPROVE / FIX BEFORE MERGE / REJECT AND SPLIT).

### Phase 8: Cleanup

Always remove the temp clone after the report, whatever the outcome, and even on interruption (build failure, agent timeout, user abort). Evidence tests live only in the clone: make sure surviving repro tests were copied into the report (Phase 4b deliverable) before deleting.

```bash
rm -rf "$PR_REVIEW_DIR"; unset PR_REVIEW_DIR
```

Stale `pr-review-*` directories under `$TMPDIR` are safe to delete at any time.

## Quality Notes

- **Never relay raw agent output**: synthesize, deduplicate, verify.
- **Every Critical must be source-verified**: read the actual `file:line` before reporting.
- **Every Critical/Major must carry evidence** (Phase 4b): a claim without a failing test or a taxonomy-backed proof is not a finding.
- **Commit context changes severity**: a conscious deferral is not a bug.
- **Pre-existing issues**: still block (green pipeline is everyone's responsibility) but don't penalize the author's score.
- **Large PRs (> 50 files)**: always recommend reject-and-split, even if quality is high.

See `references/isolated-clone.md` for clone mechanics and the full troubleshooting table.
