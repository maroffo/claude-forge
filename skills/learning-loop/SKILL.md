---
name: learning-loop
description: "Mine LEARNING.md retrospectives across all repos for recurring failure-modes, then propose harness changes (hooks, rules, skills, checklist items) with falsifiable change-contracts. Also runs the doc-gardening pass over the governance docs (stale rules, dead cross-references, skill-table drift). Use when user says learning loop, mine learnings, recurring failures, what should I fix in my process, cross-repo retrospective, doc gardening, stale docs, or run learning-loop. Runs on human schedule, never autonomously. Not for single-project retrospectives (use learning-docs) or trace/token analysis (use harness-mechanic)."
compatibility: "Requires uv. Optional: Obsidian CLI to archive the report to the vault."
---

# ABOUTME: Cross-repo learning loop, turns scattered LEARNING.md into ranked harness changes
# ABOUTME: Deterministic ingest (script) + recurrence detection (agent) + change-contract output

# Learning Loop

Turns the LEARNING.md retrospectives scattered across every repo into process improvements. The value is not the count of lessons, it is the **recurrence**: a failure shape that appears in one repo is an anecdote, the same shape across repos is a signal worth a mechanical fix.

Two halves, by design:

1. **Ingest (deterministic, no LLM).** `scripts/learning_corpus.py` discovers all LEARNING.md, dedupes working copies, splits each into atomic learnings, emits a JSONL corpus. Reproducible and free.
2. **Recurrence (agent pass).** An agent clusters the corpus by failure shape, keeps only patterns spanning two or more distinct repos, ranks them, and proposes one harness action per pattern with a six-field change-contract.

This pairs with, but is distinct from, related tools. `learning-docs` writes a single project's LEARNING.md (the input to this loop). `harness-mechanic` reads execution traces and token baselines (mechanical signals: cost, tool-call shape); this loop reads the human retrospectives (what actually went wrong and why). `knowledge-sync` promotes vault patterns to skills; this loop promotes cross-repo failure-modes to harness changes.

## When to run

On a human schedule (monthly, or after a milestone closes across several repos), never autonomously. The corpus is cheap to rebuild; the agent pass costs tokens, so do not loop it.

## Cadence guard

| Signal | Criteria | Action |
|--------|----------|--------|
| weak | failure shape in 1 repo | watch-list, do not propose |
| strong | shape in 2+ distinct repos | propose a harness action |
| cross-product | shape across 2+ products (HikmaAI / Wishew / a side-project) | highest priority |
| applied | already covered by a hook or rule | skip |

## Process

### Step 1: Build the corpus (deterministic)

```bash
cd <claude-forge>
make learning-corpus            # writes quality_reports/learning_corpus/corpus.jsonl
# or, to scan a different root or see coverage:
uv run scripts/learning_corpus.py --root ~/Development --stats
```

The output lives under `quality_reports/learning_corpus/`, which is gitignored: it contains private war stories from work repos and must not be committed.

### Step 2: Recurrence detection (agent)

Spawn one analysis agent over the corpus. Give it, verbatim, the rules that keep counting honest:

- **Logical repo grouping.** The `repo` field is a path; collapse same-repo variants (e.g. a backbone present at two paths is one repo) before counting. Group products: all `hikmaAI/*` is one product, all `Wishew/*` is one product, each `private/*` is its own side-project. Cross-product recurrence is the strongest signal.
- **Threshold.** Keep only clusters with two or more distinct logical repos. List singletons separately as a watch-list.
- **Rank** by (recurrence count) times (cross-product breadth) times (preventability by a mechanical change).
- **Cluster by failure shape, not surface topic.** "Everything reports success but nothing verifies it" is a shape; "a Redis bug" is a topic.

For each ranked pattern the agent outputs: a name, the failure shape in one sentence, the member learnings as evidence (repo, date, title), a breadth verdict, exactly one proposed harness action (new hook / new or edited rule / skill update / review-checklist item, concrete), and a six-field change-contract (see `rules/harness-changes.md` and the template at `quality_reports/harness_changes/TEMPLATE.md`).

Write the report to `quality_reports/learning_corpus/recurrence-report.md`. Demand skepticism: better five real patterns than fifteen forced ones.

### Step 3: Triage with the human

Present the executive summary and the ranked patterns. For each one the human accepts:

1. Copy the agent's change-contract to `quality_reports/harness_changes/YYYY-MM-DD_<slug>.md`.
2. Implement the single action (one hook, one rule edit, one skill update, or one checklist line).
3. Land the contract with the change, per `rules/harness-changes.md`.

Prefer the cheapest fully-mechanical win first (zero-judgment, near-zero false-positive hooks) over the highest-value-but-fuzzy one. A noisy hook trains the human to ignore it.

### Step 4 (optional): Archive

Archive the report to the vault for trend tracking across runs, so the repeat-pattern rate (how many of last run's patterns recurred) becomes visible over time.

## Doc-gardening pass

The rot this loop fights in process shows up in the governance docs themselves: rules pointing at renamed files, CLAUDE.md tables routing to skills that no longer exist, SKILL.md claims contradicted by newer change contracts. OpenAI's harness-engineering team runs a recurring "doc-gardening" agent for exactly this. Run it on the same human cadence, or after a batch of harness changes lands.

1. **Deterministic scan.** `make doc-garden` (wraps `scripts/doc_gardening.py`): reports dead backticked repo paths across CLAUDE.md.example, README, rules/, agents/, skills/*/SKILL.md, plus skill-table drift. Exit 1 on findings. UNLISTED-SKILL lines are advisory input for step 2, not defects (the CLAUDE.md table is a curated map, not an index).
2. **Agent pass (judgment).** Give one agent the scan output plus the most recent change contracts (last 5, `ls -t quality_reports/harness_changes/`) and ask, per governance doc: does any claim contradict what the code, hooks, or a newer contract now says? Output fix-up proposals, one line each: file, stale claim, what changed, proposed edit.
3. **Triage.** Trivial fixes (dead path, renamed file) apply directly. Anything touching a trigger surface (SKILL.md description, rules/) gets its own change contract per `rules/harness-changes.md`.

Anti-goals for this pass: no prose rewrites, no reorganization, staleness only.

## Output contract

- `corpus.jsonl`: one atomic learning per line, fields `{repo, source, section, date, title, body, body_lines}`.
- `recurrence-report.md`: executive summary, ranked patterns with evidence and change-contracts, singleton watch-list, data caveats.
- Zero to N change-contracts under `quality_reports/harness_changes/`, one per accepted pattern.

## Anti-goals

- Do not run autonomously or on every session: it is a periodic review, not a hook.
- Do not propose more than one failure mode per change-contract: ambiguous falsification kills the loop.
- Do not commit the corpus or the report: they hold private incident detail.
- Do not treat trace metrics as input here: that is `harness-mechanic`'s job, and the highest-value signals (a green test that lies) are invisible to traces.
