# ABOUTME: Change contract: pr-review Claim discipline (real, reachable, impact-sized, evidence-bounded findings)
# ABOUTME: Targets overclaimed severities set by reviewer votes and claims worded past their evidence

# Harness Change Contract: pr-review findings must be real, reachable and sized to impact

## Component

`skills/pr-review/SKILL.md` (new Finding Rules, Claim discipline; Phase 3 brief; Phase 5 re-check; Phase 6 asks second-opinion for evidence, not a classification), `skills/pr-review/prompts/gemini-segment.md` (trigger and severity rules), `scripts/pr-watch/pr-watch.sh` (one prompt line pointing at the rules). The digest-window change has its own contract (2026-11-16_pr-watch-digest-context.md).

## Failure mode targeted

Severities set by agreement instead of impact, and claims worded past their evidence. Example, #8372 review M1: the reviewer wrote "I leaned Minor" (it needs a GCS integrity fault first) and kept Major because "the architecture reviewer and isolated Gemini both called it Major". 35/50 of the last 50 digests contain "lowered from", i.e. a subagent overclaim the main reviewer had to correct. Max reported the reviews as inaccurate (2026-11-16).

## Predicted improvement

Over the next 20 pr-watch reviews: every Critical/Major names its trigger; zero severities justified by reviewer count; "lowered from" digests fall from 35/50 to at most 8/20.

## Invariants preserved

- Evidence gate (Phase 4b) unchanged: Critical/Major still need red-green or taxonomy evidence.
- Pre-existing issues still reported and still block (green-pipeline rule).
- Scoring rubric and gates unchanged apart from the Test requests override (separate contract).

## Falsification

Revert if a defect ships in a PR the bot reviewed after this change and the pre-change rules would have reported it (a finding dropped as "no trigger" or sized down that turns out real), or if Max flags two reviews in a row as missing real issues.

## Rollback

`git revert <commit>`. Affects: skills/pr-review/SKILL.md, skills/pr-review/prompts/gemini-segment.md, scripts/pr-watch/pr-watch.sh.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
