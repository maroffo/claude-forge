# ABOUTME: Change contract for cutting the duplicated blocks out of CLAUDE.md (skill catalog, hook inventory, second-opinion trigger)
# ABOUTME: Source: "The new rules of context engineering for Claude 5 generation models" (claude.com blog), rules 3 and 4

# Harness Change Contract: CLAUDE.md carries only what nothing else carries

## Component

`~/.claude/CLAUDE.md` and its repo copy `CLAUDE.md.example` (both edited, and their pre-existing drift resolved in passing), plus `skills/second-opinion/SKILL.md` (receives the auto-trigger rules that were living in CLAUDE.md) and `skills/skill-forge/SKILL.md` (its checklist item for registering a new skill in the deleted table becomes "nothing to add").

Removed from CLAUDE.md: the 40-row skill catalog table, the `# Enforcement Layer (hooks)` inventory of 11 hooks, the `# Second Opinion (auto-trigger)` block, and the redundant half of `# Knowledge Capture`. The Workflow paragraph now says skills and agents are found through their own descriptions.

## Failure mode targeted

CLAUDE.md restates what the harness already injects: a mechanical inventory (2026-07-25, `scratchpad/dedup-inventory.md`) measured **691 of its 944 words (73.2%) as duplicated** by skill frontmatter descriptions, by hook messages that fire at the moment they apply, or by the rules files themselves. Every session paid for that inventory before the first user token, and a catalog that must be maintained by hand drifts: the installed copy and `CLAUDE.md.example` had already diverged (`mauro-blogger` in one, `issue-loop-wishew` in the other).

## Predicted improvement

CLAUDE.md drops from 944 to under 500 words (measured: 475, -50%), with no instruction lost: each removed block is reachable from a skill description, a hook message, or a rules file. Total always-on context (CLAUDE.md + rules/) drops from 5059 to about 3000 words. Over the next 10 sessions, skill selection stays as good as before: no session picks a wrong skill, or fails to find one, because the catalog is gone.

## Invariants preserved

- No instruction is deleted outright. Each one either stays in CLAUDE.md or moves to the surface that owns it (`second-opinion`'s auto-trigger rules moved into that skill's description AND body).
- The auto-trigger conditions for second-opinion stay visible without loading the skill: they are in its `description`, which the harness injects.
- The installed `~/.claude/CLAUDE.md` and the repo `CLAUDE.md.example` stay byte-identical (verified with `diff`).
- Interaction, Code Philosophy, Decision Framework, Git, Code Search, Writing and Python policy are untouched: they exist nowhere else.

## Falsification

If over the next 10 sessions a skill that used to be listed in the catalog is not invoked when it should have been (observed: the session hand-rolls work that `plan-forge`, `source-control`, `verify-frontend` or a language skill covers), the catalog was doing real routing work: restore it, in a compressed form.

Second falsifier: if `/second-opinion` stops firing on its own on complex tasks and 🔴 decisions (0 auto-invocations over 10 qualifying sessions, against the pre-change rate), the move into the skill description lost the trigger: put the block back in CLAUDE.md.

## Rollback

`cp scratchpad/CLAUDE.md.bak ~/.claude/CLAUDE.md` for the installed copy, plus `git revert <commit>` for `CLAUDE.md.example` and `skills/second-opinion/SKILL.md`.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| 2026-07-27 | word counts verified 2026-07-27; 2 traced sessions since merge against a 10-session behavioural window | the size prediction landed exactly: CLAUDE.md.example is 475 words as predicted (from 944) and total always-on context is 3134 words (475 plus 2659 across 6 rules) against a predicted about 3055, the small excess being rules added since; this session's own system prompt confirms the deduped content, no skill catalog, no hook inventory, no second-opinion block; both behavioural falsifiers need 10 sessions and only 2 have been traced, with no observed case of a formerly-catalogued skill failing to be invoked | kept |
