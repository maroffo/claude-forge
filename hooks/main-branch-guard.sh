#!/usr/bin/env bash
# ABOUTME: PreToolUse hook blocking git commits directly on main/master
# ABOUTME: Makes the "NEVER work on main/master" rule model-proof

set -u

payload=$(cat)
cmd=$(printf '%s' "$payload" | jq -r '.tool_input.command // empty')

# Only intercept real `git commit` (not commit-tree, not log --grep=commit)
if ! printf '%s' "$cmd" | grep -qE '(^|[;&|[:space:]])git[[:space:]]+commit([[:space:]]|$)'; then
  exit 0
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
