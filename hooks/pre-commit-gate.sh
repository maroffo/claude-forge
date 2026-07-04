#!/usr/bin/env bash
# ABOUTME: PreToolUse hook — enforces `make check` + `make test-e2e` before `git commit`
# ABOUTME: Deny decision if target is missing or command fails; points to /project-checks

set -u

# Read the Bash tool input JSON from stdin
payload=$(cat)

# Safety gate: if jq is missing we cannot inspect the command; fail closed.
if ! command -v jq >/dev/null 2>&1; then
  printf '%s' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"pre-commit-gate: jq not found, cannot inspect the command. Install jq (brew install jq) and retry."}}'
  exit 0
fi
cmd=$(printf '%s' "$payload" | jq -r '.tool_input.command // empty')

# Only act on `git commit` (bare, or with args/flags). Exclude `git commit-tree`.
# Match: start-of-command OR preceded by shell separator, then `git`+space+`commit`, then space/end.
# Also matches `git -C <path> commit` (unquoted/space-free path).
if ! printf '%s' "$cmd" | grep -qE '(^|[;&|[:space:]])git[[:space:]]+(-C[[:space:]]+[^[:space:]]+[[:space:]]+)?commit([[:space:]]|$)'; then
  exit 0
fi

# Run the gate against the repo the commit actually targets (cd/-C), not the
# session cwd, so a cross-repo commit is gated by the right repo's Makefile.
HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$HOOK_DIR/_commit_target.sh" ]; then
  # shellcheck source=/dev/null
  . "$HOOK_DIR/_commit_target.sh"
  cd_to_commit_target "$cmd"
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

# Source-gate the expensive suite: when the staged diff is docs/assets only,
# `make check` still runs but `make test-e2e` is skipped. Commits that stage at
# commit time (-a/--all/--include, or explicit pathspecs we can't see) run everything.
run_e2e=1
if ! printf '%s' "$cmd" | grep -qE '(^|[[:space:]])(-[a-zA-Z]*a[a-zA-Z]*|--all|--include)([[:space:]]|$)'; then
  staged=$(git diff --cached --name-only)
  if [ -n "$staged" ]; then
    run_e2e=0
    while IFS= read -r f; do
      case "$f" in
        *.md|*.txt|*.rst|*.adoc|*.png|*.jpg|*.jpeg|*.gif|*.svg|*.webp) ;;
        *) run_e2e=1; break ;;
      esac
    done <<STAGED_EOF
$staged
STAGED_EOF
  fi
fi

# Run the gates
if ! make check; then
  deny "Pre-commit gate: \`make check\` failed. Fix lint/vet/test issues, then retry the commit."
fi
if [ "$run_e2e" = "1" ]; then
  if ! make test-e2e; then
    deny "Pre-commit gate: \`make test-e2e\` failed. Fix failing end-to-end tests, then retry the commit."
  fi
else
  echo "pre-commit-gate: docs-only staged diff, skipping make test-e2e" >&2
fi

# All green — allow commit (silent success)
exit 0
