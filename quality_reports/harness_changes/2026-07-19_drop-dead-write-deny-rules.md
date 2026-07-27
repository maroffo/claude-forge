# ABOUTME: Contract for removing no-op Write() deny rules from permissions
# ABOUTME: Edit(path) rules cover all file-editing tools; Write(path) rules are dead and spam warnings

# Harness Change Contract: drop dead `Write(path)` deny rules (Edit twins already cover them)

## Component

Settings fragment: `hooks/settings.example.json` (this repo) and the live `~/.claude/settings.json` tracked in `workstation_setup` at `claude/.claude/settings.json`. `permissions.deny` block only.

## Failure mode targeted

Claude Code startup emits one warning per `Write(path)` deny rule: "Write(...) is not matched by file permission checks — only Edit(path) rules are." Seven warnings per session (observed 2026-07-19, hikmaAI session). The `Write()` rules are dead: file-permission checks only match `Edit(path)` rules, which already exist for every protected path, so the `Write()` twins add zero protection and pure noise.

## Predicted improvement

The seven permission-rule warnings at session start disappear entirely (0 warnings over the next sessions). No behavior change: every protected path keeps its `Edit(path)` deny rule, which covers Write, Edit, NotebookEdit and all other file-editing tools.

## Invariants preserved

- Every previously protected path (`**/.git/hooks/**`, `~/.ssh/**`, `~/.aws/credentials`, `~/.config/gcloud/**`, `~/.config/gemini-api-key`, `**/id_rsa`, `**/id_ed25519`) retains an `Edit(path)` deny rule.
- No path is removed from protection; only the non-matching `Write()` duplicates go.
- `settings.example.json` and the live settings stay in sync on the deny list (modulo `gemini-api-key`, which is live-only by prior choice).

## Falsification

If a Write tool call to any of the protected paths is ever permitted (not denied) after this change, the assumption "Edit(path) covers Write" is wrong: revert immediately and re-add the `Write()` rules. Checkable by attempting `Write` on e.g. `~/.ssh/test` in a throwaway session and confirming the deny fires.

## Rollback

`git revert <commit>` in claude-forge and workstation_setup. Affects: `hooks/settings.example.json`, `workstation_setup:claude/.claude/settings.json`.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| 2026-07-27 | both settings files inspected 2026-07-27, 8 days after merge | 0 Write( deny rules remain in hooks/settings.example.json or in the live ~/.claude/settings.json, and every protected path kept its Edit twin (6 in the example file, 7 live, the extra being gemini-api-key which the contract declares live-only); no deny-rule startup warning has been reported since; the falsifier (a Write to a protected path being permitted) was never exercised, so the Edit-covers-Write assumption stays untested rather than confirmed | kept |
