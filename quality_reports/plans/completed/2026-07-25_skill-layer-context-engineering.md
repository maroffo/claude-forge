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
- [x] 2026-07-25 — CE#4 (pi): 28/30 on the 30-case set, both misses over-triggering on trivial work
- [x] 2026-07-25 — negatives expanded 4 -> 14, set frozen at 40 cases
- [x] 2026-07-25 — CE#6 (pi): baseline 40/40 on the frozen set
- [x] 2026-07-25 — CE#7 (pi): variance, three identical runs all 40/40. Instrument stable, set saturated
- [x] 2026-07-25 — CE#5 (pi): 8 sections moved to references/ across 5 skills, content conserved, committed
- [ ] F (negative boundaries): **on hold, the data does not justify it** (see Surprises)
- [ ] H (trim tutorial prose): not started
- [ ] `issue-loop-hikma` split: committed nowhere yet, pre-commit gate blocks (no Makefile in claude-hikma-skills)

## Surprises & Discoveries

- **The first eval scored 34/34 and was a broken instrument.** Its prompts had been written by paraphrasing the descriptions themselves, so it measured string matching, not routing. Leakage from author to test. An eval that flatters on the first run deserves suspicion, not celebration.
- **The 28/30 was not noise, it was the case mix.** Three identical runs of the frozen 40-case set all scored 40/40, so the judge is deterministic enough. What changed between the two rounds was the proportion of negatives (4/30 vs 14/40): with more negatives present, the judge became conservative and stopped over-triggering. That is a **batch-judging artifact**: a judge that sees 40 cases at once can infer how many negatives to expect. Real routing sees one prompt at a time and cannot. The instrument therefore over-estimates routing quality, and its absolute number should not be quoted as "the routing is 100%".
- **Consequence for track F:** with the set saturated there is no headroom to improve against, and the only evidence of a real defect (over-triggering on SKIP_SET work) came from the round whose case mix is the least realistic. Rewriting 26 descriptions would mean editing something that shows no measured defect, against an instrument that cannot detect the improvement. Deferred until either a per-case eval (40 separate judge calls, no batch context) or a real-session signal from traces says otherwise.
- **Two of the five skills were symlinks into other repositories** (`advanced-review` -> claude-advanced-review, `issue-loop-hikma` -> claude-hikma-skills). The brief named them by path, so pi edited files outside this repo, on those repos' main branches. Nothing was committed by pi (the sole-committer rule held), but a brief that scopes skills by path can silently cross repository boundaries: check `ls -la skills/` first.

## Outcomes & Retrospective

**Shipped** (same branch, 4 further commits here, plus one commit each in two symlinked repos):

| Track | Result |
|---|---|
| E, routing eval | `scripts/skill-routing-eval.py` with `build` / `run` (per-case) / `score`; 40-case adversarial set + 8-case holdout |
| F, negative boundaries | 3 descriptions, not 26: releasing-software, rails, orchestrator. Per-case accuracy 37.7/40 -> 40/40, stable over 3 runs |
| G, progressive disclosure | 8 sections moved to `references/` across 5 skills; advanced-review 2458 -> 1784, harness-trace 1100 -> 580 |
| H, tutorial-prose trim | **No work found.** The symptoms LEARNING.md recorded (version pinning in descriptions, "what is / why it matters" blocks, per-version enumerations) no longer exist: already fixed in the May `optimize-for-opus-4-8` pass |

Cross-repo: `claude-advanced-review` and `claude-hikma-skills` each got a `feat/progressive-disclosure` branch with one commit, unpushed. The second needed a `Makefile` (check validates skill frontmatter and conventions; test-e2e is a declared no-op) because the pre-commit gate correctly refused to commit into a repo with no checks.

**What this run taught**

1. **An eval that flatters on the first run is broken.** v1 scored 34/34 because its prompts were paraphrases of the descriptions being tested: leakage from author to test. A saturated eval cannot falsify anything.
2. **Batch judging invents competence.** The same 40 cases scored 40/40 in batch and 37.7/40 one case at a time. A judge that sees all cases at once infers how many negatives to expect; real routing never gets that hint. The batch number was not noise, it was a systematically optimistic artifact, and it hid a real defect for two rounds.
3. **The defect was not where the theory said.** The plan predicted sibling confusion (26 descriptions without a "Not for X" boundary). The measurement found zero sibling confusion and three cases of over-triggering on SKIP_SET work: the missing boundary was downward ("not for trivial edits"), not sideways. 3 edits instead of 26, because the data said so.
4. **The rework introduced one of the defects it then found.** The `orchestrator` skill created that morning said "load before step 1 of any task that is not in SKIP_SET" and started volunteering for ordinary edits. The eval caught it the same day.
5. **A holdout that passes before and after proves nothing about generalization.** Ours scored 8/8 both ways: it shows no regression, and that is all. Stated plainly in the contract rather than presented as validation.
6. **Briefs that name paths can cross repository boundaries silently.** Two of five skills were symlinks into other repos; `git status` in the workdir shows nothing. Fixed in the driver's anomaly check.

**Open items**

- Holdout cases that the pre-fix descriptions actually fail would settle whether F generalizes; none found yet.
- Real-session evidence beats the proxy judge: count over-triggering in traces once the change contracts reach their Result rows.
- The remaining always-on cost of the 55 descriptions (2043 words) is unaddressed by design: no measured defect justified touching the other 52.
