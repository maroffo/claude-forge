# ABOUTME: Change contract: humanizer description rewritten around user intent instead of a pattern list
# ABOUTME: One failure mode: humanizer under-triggers on plain "make it sound less like AI" requests

# Harness Change Contract: humanizer description names user intent and trigger phrases

## Component

Skill `skills/humanizer/SKILL.md`, frontmatter `description` (controls auto-trigger). The body/reference edits in the same patch (fact-preservation rule, register-matched voice, example) are internal and covered by the humanizer eval suite in `evals/`, not by this contract.

## Failure mode targeted

The old description lists detection categories ("inflated symbolism, superficial -ing analyses, vague attributions...") but none of the words users actually type ("sound less like ChatGPT", "less robotic", "humanize", "de-AI", non-English drafts). A router matching request to description has to infer the link, so the skill can be skipped on plain requests. Anticipated from the 2026-09-23 prompt-audit, not from an observed miss.

## Predicted improvement

Skill-routing eval (`scripts/skill-routing-eval.py`, cases + adversarial + holdout): humanizer-expected cases routed correctly stays at or above the pre-change count; no new confusion where a non-humanizer case routes to humanizer. Qualitative: over the next 10 sessions with an explicit "make this sound human/less AI" request, humanizer triggers in all of them.

## Invariants preserved

- Negative routing holds: grammar-only fixes and translation requests do not route to humanizer (evals `06-neg-grammar-only`, `07-neg-translate` keep passing).
- blog-writer, mail-writer, mauro-blogger keep their own routing (they call humanizer internally; the description must not steal their requests).
- Description stays a single-line YAML string under the length limit enforced by `make check`.

## Falsification

Routing eval shows fewer correct humanizer routes than the baseline on main, or any case expecting blog-writer/mail-writer/linkedin-post/none now routes to humanizer. Or a session where the user asks to "humanize" text and the skill does not load.

## Rollback

`git revert` the humanizer commit on `chore/skills-prompt-audit`; or restore the old `description:` line in `skills/humanizer/SKILL.md`.

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| (after 10-20 sessions) | | | |
