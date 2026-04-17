#!/usr/bin/env bash
# ABOUTME: PreToolUse hook — enforces `make check` + `make test-e2e` before `git commit`
# ABOUTME: Deny decision if target is missing or command fails; points to /project-checks

set -u

# Read the Bash tool input JSON from stdin
payload=$(cat)
cmd=$(printf '%s' "$payload" | jq -r '.tool_input.command // empty')

# Only act on `git commit` (bare, or with args/flags). Exclude `git commit-tree`.
# Match: start-of-command OR preceded by shell separator, then `git`+space+`commit`, then space/end.
if ! printf '%s' "$cmd" | grep -qE '(^|[;&|[:space:]])git[[:space:]]+commit([[:space:]]|$)'; then
  exit 0
fi

deny() {
  local reason="$1"
  jq -cn --arg r "$reason" '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: $r
    }
  }'
  exit 0
}

# Require a Makefile in the current repo
if [ ! -f Makefile ] && [ ! -f makefile ] && [ ! -f GNUmakefile ]; then
  deny "Pre-commit gate: no Makefile in $(pwd). Run /project-checks to scaffold \`make check\` and \`make test-e2e\`, or add the targets yourself."
fi

# Ensure targets exist (dry-run check)
if ! make -n check >/dev/null 2>&1; then
  deny "Pre-commit gate: no \`make check\` target. Run /project-checks to scaffold it."
fi
if ! make -n test-e2e >/dev/null 2>&1; then
  deny "Pre-commit gate: no \`make test-e2e\` target. Add one or run /project-checks."
fi

# Run the gates
if ! make check; then
  deny "Pre-commit gate: \`make check\` failed. Fix lint/vet/test issues, then retry the commit."
fi
if ! make test-e2e; then
  deny "Pre-commit gate: \`make test-e2e\` failed. Fix failing end-to-end tests, then retry the commit."
fi

# All green — allow commit (silent success)
exit 0
