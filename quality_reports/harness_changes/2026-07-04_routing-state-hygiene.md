# ABOUTME: Change contract for routing-advisor state hygiene (sanitized key, atomic write, 7-day GC)
# ABOUTME: Failure mode = state files with raw session ids, torn writes, and unbounded accumulation

# Harness Change Contract: routing-advisor state hygiene

Authored before landing. From the 2026-07-04 skill/hook audit (MINOR m1 + the doom-loop review findings applied to the sibling hook): the audit found 45 stale routing state files and the doom-loop-detector review established the state-file hygiene bar (sanitized filename, atomic replace, stale GC) that routing-advisor predates.

## Component

Hook: `hooks/routing-advisor.py` (state_path sanitization, atomic save via `os.replace`, `sweep_stale` on save). Tests in `hooks/tests/test_routing_advisor.py`.

## Failure mode targeted

Routing state files use the raw session id in the filename (path-traversal-unsafe on hostile input), are written non-atomically (a concurrent hook can read a torn file and reset dedup state, re-nagging), and are never garbage-collected (45 stale files found, growing forever).

## Predicted improvement

State files always land under `~/.claude/tmp` with sanitized names, dedup state survives concurrent edits, and files older than 7 days are swept on write. Verified now by the 8-case test suite (including the hostile-session-id case).

## Invariants preserved

- Advisory-only behavior unchanged: same routes, same once-per-reviewer dedup semantics.
- Same state dir and filename scheme for normal session ids (existing sessions unaffected).
- GC never touches the current session's file and never fails the hook (best-effort).

## Falsification

If a reviewer nudge is lost because GC or the sanitization collides two distinct session ids to the same filename within 7 days, the key scheme is too lossy: widen the sanitized length or hash the id.

## Rollback

`git revert <commit>`. Affects: hooks/routing-advisor.py, hooks/tests/test_routing_advisor.py.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
