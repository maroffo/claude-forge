# ABOUTME: Plan to optimize the claude-forge harness for Claude Opus 4.8
# ABOUTME: Effort assignment, version alignment, scaffolding audit, trace-driven deferral

# Plan: Optimize claude-forge for Opus 4.8

Date: 2026-05-30. Scope chosen by Max: ALL FOUR angles, FULL surface, plan-first.

## What actually changes in 4.8 (research, sourced)

- Effort levels recalibrated, NOT portable from 4.7: `high` thinks less, `xhigh` substantially more. CC default = `high`. Anthropic recommends `xhigh` for coding/agentic. Official subagent mapping: `low` = simple subagents, `medium` = balanced agentic.
- Config surface CONFIRMED: agent frontmatter + skill frontmatter both support `model:` and `effort:` (low/medium/high/xhigh/max); settings.json supports `model` + `effortLevel`. `[1m]` is display-only, not configurable. Aliases (`opus`) and `inherit` valid.
- Aggressive context trimming STILL endorsed on 1M window (attention budget / context rot unchanged). Window = headroom, not license to stop trimming. Min cacheable prompt now 1024 tokens.
- 4.7 tool-skipping + comment-verbosity fixed at model level; 4x better self-checking. Some "remember to call tool" / "be terse" / "double-check yourself" scaffolding now redundant.
- No breaking API changes 4.7 to 4.8. Prompts/evals port as-is.

Sources: whats-new-claude-4-8, migration-guide, effort, adaptive-thinking, effective-context-engineering (all docs.anthropic / platform.claude.com).

## Honest constraint: trace-driven angle is weak

Only 3 trace JSONL (2026-05-20, gitignored, ~13KB) + 2 baselines. Not enough for data-driven optimization. We act on documented 4.8 deltas + static review, NOT on measured failure patterns. Real trace-driven pass = run `/harness-mechanic` later, after accumulating 4.8-era traces. Documented as deferred, not done.

## Workstreams

### A. Effort assignment to subagents (highest-value, genuinely 4.8-specific)
Add `effort:` to agent frontmatter per official role mapping:
- Read-only reviewers (architecture, security, performance, database, dependency, dx, test) -> `effort: medium` (analysis that gates quality; not `low` because findings drive fix loops).
- research-analyst, tech-writer -> `effort: medium`.
- harness-mechanic -> `effort: high` (cross-trace synthesis).
- software-engineer -> `inherit` (explicit; inherits orchestrator effort, writes code).
- project-analyzer -> keep `model: haiku`, add `effort: low`.
Files: 12x agents/*/AGENT.md (frontmatter only).
Also: document the effort policy as a column/section in rules/orchestrator-protocol.md (Parallelism table area).

### B. Session defaults (decision D1 below)
- hooks/settings.example.json: add `effortLevel` key with documented value.
- README + install.sh: document the default + that `xhigh` is the recommended manual bump for heavy coding sessions (`/effort xhigh`).

### C. Version-pin alignment
- README.md:12 "Tuned for Claude Opus 4.7" -> 4.8, add one clause re effort-aware subagents.
- skills/autoresearch-prompt: pricing map + DEFAULT_MODEL pin sonnet-4-5/haiku-4-5. Update to current IDs + pricing (decision D2). Touches evaluator.py + SKILL.md + 2 test files -> TDD (red-green), software-engineer.
- advanced-review / second-opinion `--model opus`: LEAVE AS-IS. Alias auto-resolves to latest opus (4.8). Pinning would be worse. Note only.
- harness-trace tests (opus-4-6/4-7): test fixtures, low priority. Optional: add a 4-8 parse case. Skipping unless D2 work touches them.
- gemini-review `gemini-3.1-pro-preview`: NOT a Claude model. Out of scope.

### D. Scaffolding audit (conservative, no rewrites)
Identify + trim ONLY clearly-redundant prose in always-on files (CLAUDE.md.example, rules/): tool-forcing reminders, anti-verbosity lines, "double-check yourself" self-review prose that 4.8 absorbs. Each candidate proposed individually; trim only if removal is obviously safe. NO behavioral change to gates, routing, decision framework. Trimming stays aligned with "keep aggressive trimming" guidance.

### E. README architecture note
Reflect effort policy in the architecture section (one paragraph).

## Harness-change contracts (Max's own rule)
A, B, C(autoresearch), D touch hooks/rules/agents/skills -> each gets a six-field contract in quality_reports/harness_changes/ committed alongside. One failure mode per contract. Estimate: 3-4 contracts (A effort-policy, B effort-default, C model-pins, D scaffolding-trim).

## Execution order (orchestrator)
1. A (mechanical frontmatter) + C-README + E in one parallel-safe wave.
2. B (settings + docs).
3. C-autoresearch (TDD code change, isolated, software-engineer).
4. D (delicate, last, individually reviewed).
5. VERIFY: `make check` + skill tests for autoresearch. REVIEW: dx + architecture on rules/agents diffs. Contracts written. SCORE.
Branch: feat/optimize-opus-4-8 (NOT main).

## Decisions (resolved 2026-05-30)
| # | Decision | Choice | Rationale | Revisit if |
|---|----------|--------|-----------|------------|
| D1 | settings.example.json effortLevel | `xhigh` | Max: Anthropic coding/agentic rec; this harness is a coding harness | cost/latency on trivial sessions becomes a problem |
| D2 | autoresearch-prompt model pins | config-driven (no pins) | Max: eliminate future drift | adds too much config surface |
| D3 | WS-D scaffolding audit | include now, conservative | Max: trim only obviously-safe redundancy, one at a time | a trim changes behavior |

## Unresolved questions
- Exact current pricing for autoresearch config defaults (verify at implementation; mark source).
