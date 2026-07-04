# ABOUTME: Change contract for the AGENT.md schema lint in make check (frontmatter parses, name=dir, description)
# ABOUTME: Failure mode = agent definitions had zero mechanical validation; an unparseable AGENT.md is an unspawnable agent

# Harness Change Contract: agent schema lint

Authored before landing. Follow-up to `2026-07-04_agent-frontmatter-first.md`: that fix pinned the block-order class; this closes the wider gap that agents had no schema validation at all, while skills have had one for months.

## Component

Lint: `scripts/check_repo.py` new `check_agent_schema` (frontmatter must parse at the top, `name` must match the directory, `description` present and 20-2500 chars), wired into `make check` (runs on every commit via the pre-commit gate).

## Failure mode targeted

Agent definitions were mechanically unvalidated: a malformed AGENT.md ships silently and the agent just never appears in the registry, with no error anywhere. harness-mechanic was broken this way for an unknown number of weeks; nothing but a human asking "does it actually work?" surfaced it.

## Predicted improvement

The class cannot ship again: any AGENT.md that would not register fails `make check` at commit time. Red-green verified (synthetic broken agent fails, current 12 agents pass).

## Invariants preserved

- Unlike SKILL.md, no ABOUTME-only fallback is allowed for agents (they have no registry fallback either).
- All 12 existing agents pass unchanged.
- Runs in check mode only: docs-only commits still skip test-e2e, but never skip this.

## Falsification

If the lint fails on a legitimately structured agent the registry DOES accept (schema mismatch between lint and runtime), relax the lint to match observed runtime behavior, never the reverse.

## Rollback

`git revert <commit>` or delete `check_agent_schema` and its report line.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
