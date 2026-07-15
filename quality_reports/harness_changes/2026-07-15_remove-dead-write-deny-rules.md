# ABOUTME: Contract for removing dead Write(path) deny rules from global settings.json
# ABOUTME: Write() file rules are no longer consulted by the permission checker; Edit() covers all file-editing tools

# Harness Change Contract: remove 7 dead `Write(path)` deny rules from `~/.claude/settings.json`

## Component

Settings fragment: `~/.claude/settings.json`, `permissions.deny` array.

## Failure mode targeted

Claude Code CLI (observed 2026-07-15 at startup) warns per rule: "Permission deny rule Write(...) is not matched by file permission checks — only Edit(path) rules are." The checker unified file-operation permissions under `Edit(path)` rules, which cover Edit, Write, and NotebookEdit; the 7 `Write(...)` entries are dead config producing 7 warning lines every session start (noise that trains the eye to ignore startup warnings).

## Predicted improvement

Startup warnings about deny rules drop from 7 to 0 on the next `claude` launch. No other behavior change.

## Invariants preserved

- Every protected path keeps its `Edit(...)` twin: `**/.git/hooks/**`, `~/.ssh/**`, `~/.aws/credentials`, `~/.config/gcloud/**`, `~/.config/gemini-api-key`, `**/id_rsa`, `**/id_ed25519`. Effective deny surface is unchanged (Edit rules already covered the Write tool).
- Attempting to Write to any of those paths must still be denied.
- JSON stays valid (verified with `json.load` after the edit).

## Falsification

If, on a current CLI version, a Write tool call to a protected path (e.g. `~/.ssh/test`) is ALLOWED after this change, the assumption "Edit rules cover all file-editing tools" is wrong for this version: revert immediately.

## Rollback

Re-add the 7 removed lines to `permissions.deny` in `~/.claude/settings.json`: `Write(**/.git/hooks/**)`, `Write(~/.ssh/**)`, `Write(~/.aws/credentials)`, `Write(~/.config/gcloud/**)`, `Write(~/.config/gemini-api-key)`, `Write(**/id_rsa)`, `Write(**/id_ed25519)`.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
