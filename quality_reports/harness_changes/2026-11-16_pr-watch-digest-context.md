# ABOUTME: Change contract: pr-watch feeds 5 bounded, single-per-run digests and forbids borrowing from them
# ABOUTME: Targets reviews anchoring severities on precedents from unrelated PRs

# Harness Change Contract: cross-PR digests stop steering severities

## Component

`scripts/pr-watch/pr-watch.sh`: the reviewer prompt gets `tail -n 5` of `context.log` instead of 20 lines, labelled as never a source of severity, precedent or finding; each run appends only its final `DIGEST` line, cut to 300 characters; the prompt asks for an outcome of at most 200 characters.

## Failure mode targeted

Each review received about 20 KB of digests from unrelated PRs (last 20 lines measured 2026-11-16), with duplicates because every echoed `DIGEST` line was appended (#8346 six times in those 20 lines). Reviews then cite other PRs' decisions as precedent for severity ("per D40", "on the #8328 precedent").

## Predicted improvement

The injected block shrinks from about 20 KB to at most 1.5 KB (5 lines of at most 300 characters). Over the next 20 reviews, zero severities justified by another PR's digest.

## Invariants preserved

- The DIGEST line format the menu-bar GUI parses (`^DIGEST #(\d+)\s+(\S+)\s+(.*)$`) is unchanged.
- A run that fails still appends nothing and stays retriable.
- `reviewed.txt` dedupe is untouched.

## Falsification

Revert if Max flags a review that missed a cross-PR conflict (two open PRs touching the same contract) that the longer digest window would have surfaced.

## Rollback

`git revert <commit>`. Affects: scripts/pr-watch/pr-watch.sh.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
