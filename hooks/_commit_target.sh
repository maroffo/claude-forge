#!/usr/bin/env bash
# ABOUTME: Shared helper, resolves the git repo a `git commit` command actually targets
# ABOUTME: Sourced by the commit-gate hooks so they inspect the right repo on cross-repo commits

# resolve_commit_dir <command-string>
#
# Commit-gate hooks run in the session cwd, which may differ from the repo the
# command targets (e.g. `cd /other/repo && git commit`, or `git -C /other/repo commit`).
# This echoes the directory the commit runs in, or nothing if the command gives no hint
# (callers then keep the current cwd, i.e. the prior behavior, so resolution failure is
# never a regression).
#
# Precedence: an explicit `git -C <path>` wins (that is where git operates), otherwise
# the first `cd <path>` in the command. Handles bare, single-, and double-quoted paths.
resolve_commit_dir() {
  local cmd="$1" path=""

  # 1) git -C <path>
  path=$(printf '%s' "$cmd" \
    | grep -oE "git[[:space:]]+-C[[:space:]]+(\"[^\"]+\"|'[^']+'|[^[:space:]]+)" \
    | head -1 \
    | sed -E "s/^git[[:space:]]+-C[[:space:]]+//; s/^[\"']//; s/[\"']$//")

  # 2) else the first `cd <path>` (start of command or after a shell separator)
  if [ -z "$path" ]; then
    path=$(printf '%s' "$cmd" \
      | grep -oE "(^|[;&|[:space:]])cd[[:space:]]+(\"[^\"]+\"|'[^']+'|[^[:space:]&|;]+)" \
      | head -1 \
      | sed -E "s/.*cd[[:space:]]+//; s/^[\"']//; s/[\"']$//")
  fi

  printf '%s' "$path"
}

# cd_to_commit_target <command-string>
# Convenience: resolve and cd if the target is a real directory. Silent no-op otherwise.
cd_to_commit_target() {
  local tgt
  tgt=$(resolve_commit_dir "$1")
  if [ -n "$tgt" ] && [ -d "$tgt" ]; then
    cd "$tgt" 2>/dev/null || true
  fi
}
