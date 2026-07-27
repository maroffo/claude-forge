# ABOUTME: Change contract: stop commit-intent-guard false positives on "placeholder" as domain vocabulary
# ABOUTME: Tightens the comment pattern to stub-intent forms only; wrapped-comment continuations pass

# Harness Change Contract: commit-intent-guard "placeholder" domain-vocabulary false positive

## Component

Hook: `hooks/commit-intent-guard.py`, `COMMENT_PATTERNS` entry `(r"^placeholder\b", "placeholder")`,
plus regression cases in `hooks/tests/test_commit_gates.py`.

## Failure mode targeted

The pattern flags ANY added comment line whose body starts with the word "placeholder",
including mid-sentence continuations of wrapped comments. Observed 2026-07-11 (hikma-mirsad,
PR #568 merge commit): upstream comment in `internal/pii/detector.go` wrapped as
"...its label wins the ⏎ placeholder and its presence marks the region for replacement..."
— "placeholder" here is redaction domain vocabulary (`[ENTITY_TYPE]` placeholder), not a stub.
The commit was blocked and the already-reviewed upstream comment had to be reworded
("redaction token") to land the merge. In redaction/templating codebases this vocabulary is
routine, so the false positive will recur, and each recurrence pressures toward the exact
behaviors the hook exists to prevent (rewording reviewed code, or bypass temptation).

One change = one failure mode: the OTHER footgun found the same day (PreToolUse evaluates
the index before the `git add` in a compound `add && commit` executes) is NOT addressed
here; it needs its own contract.

## Predicted improvement

False-positive denies on descriptive/mid-sentence "placeholder" comment lines drop from
1 observed (2026-07-11) to 0 over the next 20 sessions, while every stub-intent form in
the new regression tests (`# placeholder`, `# placeholder: ...`, `# placeholder for ...`,
`# placeholder implementation`) keeps denying.

## Invariants preserved

- TODO / FIXME / XXX comment patterns unchanged.
- Statement-level stubs (`raise NotImplementedError`, stub `pass`) unchanged.
- Bare `# placeholder`, `# placeholder:`/`.`/`-`, and `# placeholder <for|until|impl*|code|logic|value|here|only>` still deny (encoded as regression tests).
- Case sensitivity unchanged (lowercase-only, matching the pre-existing behavior).
- No bypass path added; deny mechanism untouched.

## Falsification

If within the next 20 sessions a genuine unfinished-work comment beginning with
"placeholder" lands in a commit because the tightened pattern no longer matches it
(checkable post-hoc: grep merged commits for added `^\s*(#|//)\s*placeholder\b` lines and
judge intent), the tightening under-catches: extend the stub-word alternation or revert.

## Rollback

`git revert <this commit>`. Affects: `hooks/commit-intent-guard.py`,
`hooks/tests/test_commit_gates.py`, this contract file.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| 2026-07-27 | 16 days and roughly 60 commits since 2026-07-11 | the tightened stub-intent alternation is live and no further false-positive deny on a descriptive placeholder comment was recorded, down from the 1 observed on 2026-07-11, while the guard did produce two false positives of other shapes in the window (heredoc-parsed commit message, doom-loop on batch edits) so the class is alive but not on this pattern | kept |
