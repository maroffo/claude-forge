#!/usr/bin/env bash
# ABOUTME: Wrapper that invokes commit-intent-guard.py via uv with payload on stdin
# ABOUTME: Resolves the commit's target repo (cd/-C) and cd's there so the .py inspects the right repo

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
payload=$(cat)
cmd=$(printf '%s' "$payload" | jq -r '.tool_input.command // empty')
if [ -f "$HOOK_DIR/_commit_target.sh" ]; then
  # shellcheck source=/dev/null
  . "$HOOK_DIR/_commit_target.sh"
  cd_to_commit_target "$cmd"
fi
printf '%s' "$payload" | uv run --no-project python3 "$HOOK_DIR/commit-intent-guard.py"
