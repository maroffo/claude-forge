# ABOUTME: Solution note for the git -C commit-gate bypass (trigger regex missed the -C form)
# ABOUTME: Category infrastructure; from the 2026-07-04 skill/hook audit

# Problem

All four PreToolUse commit gates (pre-commit-gate, main-branch-guard, commit-intent-guard, gitignore-anchor-lint) matched commands with `(^|[;&|\s])git\s+commit(\s|$)`. `git -C /path commit ...` never matched, so cross-repo commits ran with zero gating. The smoking gun: the shared `_commit_target.sh` helper parsed `git -C` for repo resolution, but that branch was dead code since the gates never fired for that form.

# Solution

Widen the trigger to allow an optional `-C <path>` between `git` and `commit`:

- shell: `(^|[;&|[:space:]])git[[:space:]]+(-C[[:space:]]+[^[:space:]]+[[:space:]]+)?commit([[:space:]]|$)`
- python: `(^|[;&|\s])git\s+(-C\s+\S+\s+)?commit(\s|$)`

Plus a 16-case regression suite (`hooks/tests/test_commit_gates.py`) pinning both positive and negative cases (`git log --grep commit` and `git commit-tree` must stay ignored).

# Why It Works

The gates self-filter on the raw command string (the settings-level `if:` field is not a supported matcher), so the regex IS the gate's front door. Quoted `-C` paths containing spaces are accepted as a documented miss. Related lesson: if a helper handles a case its callers can never produce, verify the case actually reaches the helper.
