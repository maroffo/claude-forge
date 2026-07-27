# ABOUTME: Change contract — new verify-frontend skill for end-to-end UI verification
# ABOUTME: Targets UI changes passing the quality gate with green tests but no runtime check

# Harness Change Contract: verify-frontend skill (new)

## Component

Skill (new): `skills/verify-frontend/SKILL.md`. Plus one pointer line in `rules/verification-protocol.md` (After Every Code Change section).

## Failure mode targeted

UI changes pass VERIFY (step 2) and the quality gate with green tests/lint/build only: no dev server, no browser, no console check, no visual confirmation. Tests can encode the same wrong assumption as the code (verification-protocol already states this for backend; the UI runtime surface had no equivalent). Anticipated failure, imported from the ClaudeDevs loops article (2026-07-07) pattern `verify-frontend-change`.

## Predicted improvement

Over the next 10 sessions touching rendered UI: at least 1 defect (console error, broken interaction, visual regression) caught by the browser protocol that tests missed. Qualitative fallback: every UI-change report includes the quantitative verification block (console delta, screenshots) instead of "tests pass".

## Invariants preserved

- verification-protocol test/lint/build still runs; the skill adds, never replaces.
- No auto-fix of pre-existing console errors (noted, not silently fixed — NO unrelated changes rule).
- Skill triggers only on frontend/UI work; backend-only sessions see zero overhead.
- No browser-dialog-triggering interactions (session-blocking).

## Falsification

If over 10 UI sessions the protocol produces zero findings beyond what tests caught AND adds noticeable latency/token cost per session, the skill is overhead — revert. Also revert if it misfires on backend-only tasks more than twice (trigger surface too broad).

## Rollback

`git revert <commit>`. Affects: `skills/verify-frontend/SKILL.md` (delete), `rules/verification-protocol.md` (one line).

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| 2026-07-27 | 20 traced sessions (13 with more than 3 events), 2026-06-08 to 2026-07-27 | insufficient data: no session touched rendered UI (the traced work is markdown, Python and shell in claude-forge), so the browser protocol neither caught a defect nor misfired on backend-only work; re-check after 10 sessions in a frontend repo | kept |
