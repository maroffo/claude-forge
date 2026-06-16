# ABOUTME: Change contract for the build-time-chain review-checklist item in reviewer agents
# ABOUTME: Failure mode = a baked-in build value changes at one layer but stays stale elsewhere (learning Pattern 3)

# Harness Change Contract: build-time-chain review-checklist item

Authored before landing. Linked from the commit body. Append-only after merge. Implements Pattern 3 from `quality_reports/learning_corpus/recurrence-report.md`.

## Component

Agent prompts: `agents/architecture-reviewer/AGENT.md` and `agents/dx-reviewer/AGENT.md`, Scope sections. Adds a review question; no frontmatter/description change.

## Failure mode targeted

A value embedded at image-build time or read once at startup is changed at the source, but the stale value persists because the build layer cached it or the substitution chain was not fully cleaned. Recurred across 2 products plus a side-project cousin: Docker Buildx caching `NEXT_PUBLIC_BASE_API` so the old URL stayed baked (wasit), an `EXPO_PUBLIC` var whose removal broke the build because the Terraform to cloudbuild.yaml to Dockerfile chain was only partially cleaned (Wishew), VITE_* build-args meaningless after a framework migration (backbone).

## Predicted improvement

When a build-time env var / build-arg / substitution is touched, the reviewer traces and confirms the entire chain (IaC var to CI build-arg to Dockerfile ARG) is consistent and the build layer is cache-busted. Target: catch the "old URL still baked in after redeploy" class at review (3 corpus occurrences across 2 products). Kept human, not a grep hook: the chain spans repos that are often not in the PR.

## Invariants preserved

- Reviewer agents stay read-only; output format unchanged.
- Addition only (one Scope bullet each); no edits to existing items.
- No change to `description` frontmatter, so routing/auto-trigger is unaffected.
- The check applies only when a build-time var / `ARG` / build substitution is actually touched (not on every PR).

## Falsification

If reviewers cannot enumerate the chain from the diff alone (because it spans repos not in the PR) and the item produces only "cannot verify" non-findings, it is unanswerable as written: either move it to a CI build-arg cache-key assertion or revert. If it never fires because build-time vars are rarely touched, it is harmless but dead; drop on next review of the checklist.

## Rollback

`git revert <commit>`. Affects: `agents/architecture-reviewer/AGENT.md`, `agents/dx-reviewer/AGENT.md`. Remove the added Scope bullet from each.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
