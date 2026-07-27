#!/usr/bin/env bash
# ABOUTME: Shared helper, locates the repo-local freeze boundary file for a given path
# ABOUTME: Single source of truth for the boundary basename, sourced by freeze-guard.sh and quoted by skills/freeze

# The boundary is repo-local: one file at the git root of the frozen repo, holding
# one absolute physical directory path. The basename lives here and nowhere else;
# skills/freeze/SKILL.md quotes it and hooks/tests/test_hook_constants_sync.py
# asserts the two agree (gstack ships the opposite: the skill writes through one
# path source and the hook reads through another, and they only accidentally match).
FREEZE_BOUNDARY_BASENAME=".freeze-boundary"

# freeze_existing_dir <path>
#
# Deepest existing ancestor directory of <path>, or nothing. A Write targets a file
# that does not exist yet, so the path itself is usually not something we can `cd` into.
freeze_existing_dir() {
  local dir="$1" parent
  [ -n "$dir" ] || return 0
  while [ ! -d "$dir" ]; do
    parent=$(dirname "$dir")
    [ "$parent" = "$dir" ] && return 0
    dir="$parent"
  done
  printf '%s' "$dir"
}

# freeze_physical_path <path>
#
# Absolute, symlink-resolved form of <path> (the `cd … && pwd -P` idiom), or nothing
# when no ancestor of it exists. The trailing components that do not exist yet are
# appended verbatim, so a not-yet-created file still compares against the boundary.
freeze_physical_path() {
  local target="$1" dir rest
  [ -n "$target" ] || return 0
  case "$target" in
    /*) ;;
    *) target="$PWD/$target" ;;
  esac
  dir=$(freeze_existing_dir "$target")
  [ -n "$dir" ] || return 0
  rest=${target#"$dir"}
  rest=${rest#/}
  dir=$(cd "$dir" 2>/dev/null && pwd -P) || return 0
  [ -n "$dir" ] || return 0
  if [ -n "$rest" ]; then
    printf '%s/%s' "${dir%/}" "$rest"
  else
    printf '%s' "$dir"
  fi
}

# freeze_boundary_file <path>
#
# Path of the boundary file for the repo containing <path>, or nothing when <path>
# is not inside a git repo. Resolving the git root of the EDITED path (not of the
# session cwd) is what keeps a freeze in one repo from freezing another.
freeze_boundary_file() {
  local dir root
  dir=$(freeze_existing_dir "$1")
  [ -n "$dir" ] || return 0
  root=$(cd "$dir" 2>/dev/null && git rev-parse --show-toplevel 2>/dev/null) || return 0
  [ -n "$root" ] || return 0
  root=$(cd "$root" 2>/dev/null && pwd -P) || return 0
  printf '%s/%s' "${root%/}" "$FREEZE_BOUNDARY_BASENAME"
}
