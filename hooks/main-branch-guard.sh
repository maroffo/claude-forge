#!/usr/bin/env bash
# ABOUTME: PreToolUse hook blocking git commits directly on main/master
# ABOUTME: Makes the "NEVER work on main/master" rule model-proof

set -u

payload=$(cat)

# Safety gate: if jq is missing we cannot inspect the command; fail closed.
if ! command -v jq >/dev/null 2>&1; then
  printf '%s' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"main-branch-guard: jq not found, cannot inspect the command. Install jq (brew install jq) and retry."}}'
  exit 0
fi
cmd=$(printf '%s' "$payload" | jq -r '.tool_input.command // empty')

# Only intercept real `git commit` (not commit-tree, not log --grep=commit).
# Also matches `git -C <path> commit` (unquoted/space-free path; quoted paths
# with spaces are rare enough to accept the miss).
if ! printf '%s' "$cmd" | grep -qE '(^|[;&|[:space:]])git[[:space:]]+(-C[[:space:]]+[^[:space:]]+[[:space:]]+)?commit([[:space:]]|$)'; then
  exit 0
fi

# Evaluate the repo the commit actually targets (cd/-C), not the session cwd,
# so a cross-repo commit on a feature branch is not blocked because cwd sits on main.
HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$HOOK_DIR/_commit_target.sh" ]; then
  # shellcheck source=/dev/null
  . "$HOOK_DIR/_commit_target.sh"
  cd_to_commit_target "$cmd"
fi

branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
case "$branch" in
  main|master)
    jq -cn --arg b "$branch" \
      '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:("Main-branch guard: refusing to commit directly on `" + $b + "`. Create a feature branch first: `git checkout -b feat/<slug>`. If this is genuinely intentional, ask the user to confirm.")}}'
    exit 0
    ;;
esac

exit 0
