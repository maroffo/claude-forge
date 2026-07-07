# ABOUTME: Change contract — pilot-before-large-run rule in orchestrator parallelism section
# ABOUTME: Targets full fan-out launched on an unproven prompt, wasting tokens at fleet scale

# Harness Change Contract: Pilot before a large run

## Component

Rule: `rules/orchestrator-protocol.md`, Parallelism section, one paragraph.

## Failure mode targeted

A large fan-out (parallel agents, workflow stages, batch migrations over >10 similar items) launches all at once on a prompt or approach that turns out flawed: every agent repeats the same mistake and the whole fleet's tokens are wasted before anyone inspects a result. Anticipated failure, imported from the ClaudeDevs loops article ("Pilot before a large run: dynamic workflows can spawn hundreds of agents").

## Predicted improvement

Qualitative, sample = next 5 sessions with a >10-item fan-out: each shows a 1-2 item pilot in the trace before the full launch. Token effect: a flawed prompt costs 1-2 agents' worth of tokens, not N.

## Invariants preserved

- Parallelism caps unchanged (read-only 5/7, write 3/5).
- Small fan-outs (≤10 items) unaffected: no added latency for normal work.
- INTEGRATE-wave sequencing for shared surfaces unchanged.

## Falsification

If over 5 large-fan-out sessions the pilot never changes the prompt or approach (pilot always identical to final run), the rule adds a round-trip with no benefit: revert. If agents start piloting trivial 3-item batches (over-application), tighten the threshold wording or revert.

## Rollback

`git revert <commit>`. Affects: `rules/orchestrator-protocol.md` (one paragraph).

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
