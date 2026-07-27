#!/usr/bin/env bash
# ABOUTME: PreToolUse hook denying Edit/Write/NotebookEdit outside the repo-local freeze boundary
# ABOUTME: A debugging aid, not a security gate: fails OPEN on missing jq or an unusable path

set -u

payload=$(cat)

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$HOOK_DIR/_freeze_boundary.sh" ]; then
  # shellcheck source=/dev/null
  . "$HOOK_DIR/_freeze_boundary.sh"
else
  exit 0
fi

warn() { printf 'freeze-guard: %s\n' "$1" >&2; }

# Fail OPEN, unlike main-branch-guard.sh, and deliberately so: that one gates an
# irreversible action, this one is a focus aid. A false DENY here is unrecoverable
# from inside the session (the model cannot even edit the boundary file away),
# while a false ALLOW is visible in the diff and undoable.
if ! command -v jq >/dev/null 2>&1; then
  warn "jq not found, boundary not enforced (brew install jq)"
  exit 0
fi

file_path=$(printf '%s' "$payload" | jq -r '.tool_input.file_path // empty' 2>/dev/null || true)
# A path carrying newlines is not something we can reason about (nor report on one
# line): treat it as unparseable rather than guessing which repo it belongs to.
case "$file_path" in
  *"
"*) file_path="" ;;
esac

# Which repo's boundary applies is decided by the file being edited. When the path
# is unusable we cannot resolve that, so fall back to the session cwd purely to
# learn whether a boundary is active at all, i.e. whether the warning is worth printing.
if [ -n "$file_path" ]; then
  boundary_file=$(freeze_boundary_file "$file_path")
else
  boundary_file=$(freeze_boundary_file "$PWD")
fi

# No boundary file: the hook is inert, zero output.
[ -n "$boundary_file" ] && [ -f "$boundary_file" ] || exit 0

if [ -z "$file_path" ]; then
  warn "boundary active ($boundary_file) but tool_input.file_path is missing or unparseable, allowing this edit"
  exit 0
fi

boundary=$(head -n 1 "$boundary_file" 2>/dev/null | tr -d '\r\n')
if [ -n "$boundary" ]; then
  boundary=$(freeze_physical_path "$boundary")
fi
if [ -z "$boundary" ]; then
  warn "boundary file $boundary_file holds no usable path, allowing this edit (re-run \`/freeze <dir>\` or \`/freeze off\`)"
  exit 0
fi
case "$boundary" in
  */) ;;
  *) boundary="$boundary/" ;;
esac

target=$(freeze_physical_path "$file_path")
if [ -z "$target" ]; then
  warn "cannot resolve a physical path for '$file_path', allowing this edit"
  exit 0
fi

# Prefix match on the boundary with its trailing slash, so a sibling directory
# (/src vs /srcgen) cannot pass as inside. The trailing slash on the target makes
# the boundary directory itself count as inside.
case "$target/" in
  "$boundary"*) exit 0 ;;
esac

jq -cn --arg f "$target" --arg b "${boundary%/}" --arg bf "$boundary_file" \
  '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:("Freeze guard: `" + $f + "` is outside the frozen boundary `" + $b + "` (set in " + $bf + "). Work inside the boundary, or run `/freeze off` to lift it.")}}'
exit 0
