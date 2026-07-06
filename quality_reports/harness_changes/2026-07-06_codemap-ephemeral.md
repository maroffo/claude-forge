# ABOUTME: Change contract for the ephemeral codemap-session hook (supersedes the committed-artifact design)
# ABOUTME: Map regenerated against the working tree each SessionStart, stored out-of-tree, pointer injected

# Harness Change Contract: codemap-session — ephemeral, working-tree-fresh orientation map

Supersedes `2026-07-05_codemap-toolkit.md` (reverted). Same goal (token-cheap orientation for
agents), different delivery: the committed + commit-stamped + regen-on-Bash design manufactured
the exact silent-staleness anti-goal the harness exists to prevent.

## Component

- Hook: `hooks/codemap-session.py` + `.sh` (SessionStart). Replaces the removed
  `codemap-freshness.*` and `codemap-regen.*`.
- Reused unchanged: `codemap/generate.py`, `codemap/rules/*.yml` (extraction validated in the
  superseded contract; only lifecycle changed).
- Settings fragment: `hooks/settings.example.json` (SessionStart startup|resume).

## Failure mode targeted

The superseded design committed a generated `CODEMAP.md` into each repo, stamped with the
generating commit, regenerated post-commit. Three failures, confirmed by three independent
isolated reviewers (Claude/Gemini/DeepSeek, unanimous) on 2026-07-05:
1. A committed generated map is stale the instant anyone edits without committing, i.e. for the
   whole duration of an active session, exactly when the map is read.
2. The regen (PostToolUse) and freshness-advisory (SessionStart) hooks fought into a steady
   state: map always one commit behind, working tree always dirty, advisory crying wolf every
   session.
3. The regen hook spawned a uv/python process on every Bash call in every session to early-exit
   on non-commits: latency tax for a commit-only benefit.

## Predicted improvement

The map an agent reads is fresh against the current working tree, not a past commit. Zero VCS
churn (nothing committed), zero per-Bash process spawns, both prior hooks deleted. Over the next
10 sessions in repos with mappable stacks: the injected pointer appears at SessionStart, the
out-of-tree map matches the working tree (spot-check: an uncommitted endpoint edit is reflected),
and no CODEMAP.md ever appears inside a repo.

## Invariants preserved

- Fail-open: any error exits 0, no output.
- Never writes into the repo; map lives under `~/.claude-forge/codemaps/<slug>.md`
  (override `CLAUDE_FORGE_CODEMAP_DIR`).
- Deterministic generator, no LLM, no network (unchanged).
- Silent for non-git dirs and repos with no mappable stack (zero cost, zero noise).
- The map body (token-capped by the generator) is injected directly, not pointed at, so a lazy
  agent cannot skip it. Self-labelled as a snapshot; live facts delegated to the LSP.
- Generation is cached on `(HEAD, git status --porcelain)`: an unchanged tree reuses the last map
  instead of re-scanning. Deterministic input, so the cache is not the stamp-trust that sank v1.
- The out-of-tree filename carries an 8-char hash of the repo abspath, so two paths that share a
  sanitized prefix (`foo-bar` vs `foo/bar`) never collide onto one file. Writes are atomic
  (temp + `os.replace`), so concurrent sessions never read a half-written map.

## Falsification

If SessionStart generation regularly exceeds the 20s timeout on real repos (blocking session
start), or the injected pointer proves useless (agents ignore it / never read the map, per trace
inspection over 10 sessions), revert to no map and lean on Serena + on-demand ast-grep alone.
Also revert if generation ever mutates a repo (writes inside the working tree).

## Rollback

`git revert <commit>`; remove the `codemap-session.*` symlinks and the SessionStart entry from
`~/.claude/settings.json`; `rm -rf ~/.claude-forge/codemaps`. Affects: hooks/codemap-session.*,
hooks/tests/test_codemap_session.py, hooks/settings.example.json.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
