# ABOUTME: Living plan for applying the Claude 5 context-engineering rules to the skill layer (descriptions + bodies)
# ABOUTME: Phase 2 of 2026-07-25_context-engineering-claude5.md; adds a routing eval as the falsification instrument

# Context engineering, phase 2: the skill layer

**Branch:** `feat/context-engineering-claude5`
**Started:** 2026-07-25
**Predecessor:** `2026-07-25_context-engineering-claude5.md` (CLAUDE.md + rules/, shipped in 5 commits)

## Problem (measured, 2026-07-25)

| Surface | Words | Paid |
|---|---|---|
| 55 skill descriptions | **2043 (~2.8k tokens)** | every session, they are the injected listing |
| 55 skill bodies | 38063 | only when a skill loads |

The descriptions alone now cost two thirds of what the entire rest of the always-on context costs after phase 1 (3055 words).

But length is the wrong lever here. The blog's rule 2 says a description is an **interface**: it must be unambiguous, not short. Current state:

- **26 of 55 have no negative boundary** (no "Not for X, use Y"), including clusters that collide: advanced-review / gemini-review / score, learning-docs / learning-loop, refine-requirements / plan-forge.
- 8 of 55 state no trigger at all.
- LEARNING.md already recorded the downstream symptom: review agents are under-invoked, `general-purpose` used as fallback 17 times across 89 transcripts.

## Decisions

| # | Decision | Choice | Rationale | Revisit if |
|---|---|---|---|---|
| 1 | Scope | All four tracks: routing eval, negative boundaries, references split, tutorial-prose trim | Max, 2026-07-25 | — |
| 2 | Order | Eval first, then bodies (pi, mechanical) in parallel with descriptions (native, judgment) | Without a measurement, a change contract on descriptions has no checkable falsification | — |
| 3 | Judge for the eval | pi / gemini-flash over the live description listing | Routing in a real session is done by Opus, but running 30 real sessions is impractical. A fixed proxy judge measures description ambiguity; the A/B delta is the signal, not the absolute number | The proxy disagrees with observed real-session routing |
| 4 | First case set discarded | `cases.jsonl` scored 34/34 and was retired as saturated | The prompts reused the literal trigger words from the descriptions, so it measured string matching. A saturated eval cannot falsify anything | — |
| 5 | Live case set | `cases-adversarial.jsonl`: paraphrases avoiding trigger words, overlapping domains, distractors, 4 negatives | Adversarial cases are what the Graph Engineering note (§VII-C) prescribes for evaluation | — |

## Budget

| Limit | This run |
|-------|----------|
| Fix rounds | 5, then escalate |
| Concurrent write agents | 2 (pi on bodies, me on descriptions: disjoint files) |
| Sub-agents for the whole run | 4 pi subtasks |
| Minimum evidence to finalize | `make check` and `make test-e2e` green, plus a before/after routing-eval score on the same case set and judge |

## Work

### E. Routing eval (instrument, not a change)
- [x] `scripts/skill-routing-eval.py`: `build` emits the judge prompt from the LIVE descriptions, `score` compares answers against a case file
- [x] `cases.jsonl` (v1, retired: saturated at 34/34)
- [x] `cases-adversarial.jsonl` (30 cases, live)
- [ ] Baseline measured on the adversarial set
- Observable outcome: `uv run python3 scripts/skill-routing-eval.py score --answers <f> --cases <f>` prints accuracy plus per-cluster breakdown and the confusion list

### F. Negative boundaries on the 26 descriptions (native, judgment)
- [ ] Add "Not for X (use Y)" to the descriptions that lack it, starting from the colliding clusters the baseline actually gets wrong
- [ ] Re-run the eval with the same judge and case set; keep only if accuracy improves
- Observable outcome: routing accuracy after > accuracy before, on the same instrument

### G. Progressive disclosure of large bodies (pi, mechanical)
- [ ] 5 skills, 8 sections moved into `references/`: advanced-review (troubleshooting, sonarqube, repo-mode), second-opinion (setup), harness-trace (schema, troubleshooting), test-design-reviewer (scoring), issue-loop-hikma (common-issues)
- Observable outcome: each SKILL.md shrinks, the sum of body plus new references stays within a few words of the original (nothing lost), `make check` green

### H. Trim tutorial prose (native, judgment)
- [ ] Cut explanations of things the model already knows (SOLID, N+1, injection, per-version feature lists), a failure LEARNING.md line 169 already recorded for the 4.7 era
- Observable outcome: word count down, routing eval unchanged (bodies do not affect routing), no instruction lost

## Progress

- [x] 2026-07-25 — measured the two surfaces, found the 26 missing boundaries
- [x] 2026-07-25 — eval instrument written; v1 case set retired as saturated, adversarial set written
- [ ] CE#4-routing-adversarial (pi): baseline on the adversarial set
- [ ] CE#5-skill-references (pi): the 8 section moves

## Surprises & Discoveries

- The first eval scored a perfect 34/34, which looked like good news and was actually a broken instrument: the prompts had been written by paraphrasing the descriptions themselves. Leakage from author to test. Worth remembering the next time an eval looks flattering on the first run.

## Outcomes & Retrospective

_(filled at close)_
