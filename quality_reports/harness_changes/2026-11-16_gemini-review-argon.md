# ABOUTME: Change contract: gemini-review mandates gemini-4-argon and pr-review pins its segments to that model
# ABOUTME: Targets segment reviews running on an older or substituted model

# Harness Change Contract: Gemini segments run on gemini-4-argon

## Component

`skills/gemini-review/SKILL.md` (model `gemini-3.1-pro-preview` to `gemini-4-argon`, three occurrences), `skills/pr-review/SKILL.md` Phase 3 (segments use the gemini-review model, never a substitute).

## Failure mode targeted

Segments run on whatever model the bot picks: the #8372 review header names `gemini-3.8-flash` although gemini-review mandates `gemini-3.1-pro-preview`, and pr-review Phase 3 did not name a model. Max chose Argon for the segments too (2026-11-16). `models/gemini-4-argon` is listed for the key in use, and both the host CLI and the `gemini-reviewer` image answered a probe on it the same day.

## Predicted improvement

Every one of the next 20 pr-watch review headers names `gemini-4-argon` for the segments. Joint effect on refuted-Gemini digests is tracked in the trust contract (2026-11-16_gemini-cli-trust-true.md).

## Invariants preserved

- gemini-review still forbids model substitution and fallback.
- Segment size and prompt unchanged by this contract.

## Falsification

Revert to `gemini-3.1-pro-preview` if Argon segments time out or hit quota on more than 3 of the next 20 reviews, or if review wall time grows more than 50% with no drop in refuted-Gemini digests.

## Rollback

`git revert <commit>`. Affects: skills/gemini-review/SKILL.md, skills/pr-review/SKILL.md (Phase 3 sentence).

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
