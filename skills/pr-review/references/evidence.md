# ABOUTME: Phase 4b mechanics: evidence requirements for Critical/Major findings.
# ABOUTME: Red-green tests run in the isolated clone; unproven claims escalate to second-opinion.

# Evidence Gate (Phase 4b)

Every Critical and Major finding must carry evidence before it reaches consolidation. A claim is not a finding until it is demonstrated. Minor findings are exempt (cost/benefit: they move the score by -3 and never block alone).

## Evidence taxonomy

Pick the FIRST type that applies, top to bottom (same taxonomy as advanced-review; keep the vocabularies aligned):

| Finding class | Required evidence |
|---------------|-------------------|
| Bug / correctness / security-exploitable | **Executable red-green test** (below) |
| Security, not locally executable (e.g. infra, secrets) | CWE id + exact source line + why it is reachable |
| Performance | Big-O derivation or measured numbers from the clone, not adjectives |
| Convention violation | Grep-able reference: the CLAUDE.md/lint rule + a counter-example line already in the repo |
| Architecture / design judgment | Explicit named principle + the concrete cost (what change becomes hard) |

If none applies, the claim is not Critical/Major material: downgrade to Minor or drop.

## Red-green protocol

All writes and runs happen inside `$PR_REVIEW_DIR` (the throwaway clone). The active repo stays read-only.

1. **Write** a test asserting the CORRECT behavior, using the project's own test framework, in a clearly marked file: `<pkg>/prreview_evidence_test.go`, `tests/test_prreview_evidence_*.py`, or equivalent. One file per finding, named after the finding id.
2. **Red**: run it on the PR branch. It MUST fail, and fail for the claimed reason (read the failure output; a compile error or fixture problem proves nothing).
3. **Base check**: run the same test on the merge base (`git stash` the test file across the checkout, or re-copy it). Fails on base too → the issue is **pre-existing** (Phase 4 table applies: note as pre-existing, still blocks merge, does not penalize the author). Passes on base → the PR **introduced** it.
4. **Record**: test command, the failing assertion output (trimmed), and the verdict `demonstrated | pre-existing | unproven` on the finding.
5. **Unproven**: the test passes on the PR branch → the bug does not reproduce. Do NOT silently drop: escalate to Phase 6 second-opinion with the claim, the test, and the passing output. second-opinion confirms with new evidence → keep, with that evidence. Otherwise → drop as unproven, count it in the report header ("Hallucinations caught").

While a claim is escalated, it does not count toward the Phase 5 score; the report notes it as pending only if second-opinion could not run.

## Deliverable

Surviving red-green tests are part of the report: copy each test body into the finding's entry (collapsible block) BEFORE Phase 8 cleanup deletes the clone. The failing test is the repro contract for whoever fixes the PR: red today, green after the fix.

## Budget and skips

- Time-box: one red-green attempt per finding, max ~10 minutes of runner time total per PR. Blown budget → fall back to the non-executable taxonomy row that fits best and say so in the Evidence field.
- Skip the executable path (taxonomy still applies) when: the clone build already failed in Phase 1 (unverified build), the project has no runnable test harness, or the bug needs unavailable external services. Never fabricate a "would fail" test result: an unrun test is not evidence.
