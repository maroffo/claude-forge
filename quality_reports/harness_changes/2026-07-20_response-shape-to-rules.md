# ABOUTME: Superseding contract: Response Shape moves from CLAUDE.md into the symlinked rules/
# ABOUTME: Targets silent drift between the tracked template and the private live copy

# Harness Change Contract: move Response Shape from CLAUDE.md to rules/

Supersedes `2026-07-20_response-shape.md` (same day, same session). That contract's failure mode (uncalibrated answer length) and its falsification conditions still hold and carry over unchanged to `rules/response-shape.md`; this contract targets only the location.

## Component

New rule `rules/response-shape.md`. The identical block is removed from `CLAUDE.md.example` and from the live `~/.claude/CLAUDE.md`; the `# Workflow` rules index in both gains a `response shape (answer length)` entry.

## Failure mode targeted

User-agnostic instructions placed in `CLAUDE.md` must be written twice, because `install.sh:255` copies the template and `install.sh:289-290` personalizes the copy with `sed`. The copy is deliberate (a symlink would put the user's name, email and work domain inside a public repo), but it means the two files can diverge in silence: an edit to one is invisible to the other, and only the template is under version control. Observed at authoring time on 2026-07-20: the same 9-line block had to be applied by hand to both files, and rollback required a manual deletion on top of `git revert`.

## Predicted improvement

Editing this instruction becomes a single tracked write instead of two, and rollback becomes `git revert` alone with no manual step. Checkable at the next edit of the Response Shape text: exactly one file changes, and `~/.claude/CLAUDE.md` shows no diff.

## Invariants preserved

- The rule text stays semantically identical to the version in `2026-07-20_response-shape.md`; this is a move, not a rewrite. The only additions are the ABOUTME header, an explicit pointer to the Decision Framework's home in CLAUDE.md, and the plan-mode precedence line (which restates `## Plan Mode`, it does not change it).
- `~/.claude/rules -> forge/rules` stays a symlink and the rule loads into context, verified empirically: the five pre-existing files in `rules/` are present in the session system prompt.
- `CLAUDE.md` stays a copy, never a symlink: no personal data enters the tracked repo.
- Discoverability does not silently degrade: the `# Workflow` rules index in CLAUDE.md names the new rule.

## Falsification

- `rules/response-shape.md` does not appear in the system prompt of a fresh session (the symlink auto-load assumption was wrong): revert to the CLAUDE.md placement.
- Answer-length calibration regresses relative to the CLAUDE.md placement, i.e. either falsification condition of `2026-07-20_response-shape.md` fires and the plausible cause is that a rules file carries less weight than CLAUDE.md itself.

## Rollback

`git revert <commit>` in claude-forge, then re-add the `# Response Shape` block to `~/.claude/CLAUDE.md` by hand (untracked). Affects: `rules/response-shape.md`, `CLAUDE.md.example`, `~/.claude/CLAUDE.md`.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| 2026-07-27 | verified live in this session, 7 days after merge | the primary falsifier is refuted directly: rules/response-shape.md (148 words) appears in this session's system prompt sourced from the repo path through the ~/.claude/rules symlink, and the block exists in exactly one tracked file with no copy left in CLAUDE.md.example, so editing it is now a single write; one declared invariant has since eroded, the "# Workflow rules index names the new rule" discoverability clause was removed when 2026-07-25_claude-md-dedup.md rewrote that paragraph, which is harmless because every file in rules/ loads unconditionally | kept |

Verdict: **kept** / **reverted** / **modified** (link to follow-up contract). If reverted, write one line on why the prediction missed.
