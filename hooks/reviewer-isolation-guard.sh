#!/usr/bin/env bash
# ABOUTME: PreToolUse hook denying *-reviewer Agent launches that omit isolation: "worktree"
# ABOUTME: Fails OPEN on environment failures, closed only on the policy violation itself

set -u

# Fail direction, deliberately split. Every environment failure (no jq, unparseable
# payload, missing fields, a cwd outside any repo) ALLOWS, at most with one stderr
# line; only the policy violation itself denies. Same reasoning as freeze-guard.sh,
# which also fails open because it is a focus aid, and the opposite of
# main-branch-guard.sh, which fails closed because it gates an irreversible commit.
# Here the gated action is corrigible: a launch, and writes that show up in the diff
# and can be reverted. A false DENY, by contrast, bricks every review in every
# session until someone notices.
#
# What this hook cannot see: Workflow-tool scripts spawn subagents through an
# internal agent() primitive that never goes through the Agent tool, so no
# PreToolUse matcher observes those launches. That is not a gap to patch here
# (parsing arbitrary Workflow scripts is the fragile path); the agent-side
# three-condition write gate in the reviewer definitions is the layer that still
# covers them, and it stays the universal backstop.
#
# The ISOLATION-EXEMPT marker is countable, not enforced. It silences THIS hook for
# one launch and is deliberately line-anchored and greppable, so exemptions can be
# counted in transcripts. It is not a write-enable: an exempted launch carries no
# isolation assertion in its brief, so the reviewer still self-downgrades to
# read-only agent-side.

payload=$(cat)

warn() { printf 'reviewer-isolation-guard: %s\n' "$1" >&2; }

if ! command -v jq >/dev/null 2>&1; then
  warn "jq not found, reviewer isolation not enforced (brew install jq)"
  exit 0
fi

# One extraction doubles as the JSON validity check: jq exits non-zero on a parse
# error, and the ladder below needs tool_name first anyway.
tool_name=$(printf '%s' "$payload" | jq -r '.tool_name // empty' 2>/dev/null) || {
  warn "payload is not valid JSON, reviewer isolation not enforced for this launch"
  exit 0
}
[ "$tool_name" = "Agent" ] || exit 0

# subagent_type is optional on the Agent tool and defaults to general-purpose, so
# its absence is an ordinary non-reviewer launch, not an environment failure:
# allow silently, or the warning fires on every general-purpose launch.
subagent_type=$(printf '%s' "$payload" | jq -r '.tool_input.subagent_type // empty')
[ -n "$subagent_type" ] || exit 0

# Outside a work tree there is no git state to corrupt, and isolation: "worktree"
# could not be honored anyway.
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0

# Suffix match, never a hardcoded list: a future eighth reviewer is covered at birth.
case "$subagent_type" in
  *-reviewer) ;;
  *) exit 0 ;;
esac

isolation=$(printf '%s' "$payload" | jq -r '.tool_input.isolation // empty')
[ "$isolation" = "worktree" ] && exit 0

# Line-anchored on purpose: a mid-sentence mention of the marker must not exempt a
# launch, while a marker on any line of a multi-line prompt must. The trailing
# newline makes the prompt's last line visible to grep; the pattern is fixed, so
# regex metacharacters in the prompt cannot alter the match.
prompt=$(printf '%s' "$payload" | jq -r '.tool_input.prompt // empty')
exempt_line=$(printf '%s\n' "$prompt" | grep -m1 -E '^ISOLATION-EXEMPT: .+' || true)
if [ -n "$exempt_line" ]; then
  warn "ISOLATION-EXEMPT honored for $subagent_type: ${exempt_line#ISOLATION-EXEMPT: } (launch allowed, the reviewer stays read-only agent-side)"
  exit 0
fi

jq -cn --arg t "$subagent_type" \
  '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:("Reviewer isolation guard: refusing to launch `" + $t + "` without an isolated worktree. Review agents write mutants and probe files, so an un-isolated launch lands those writes in the real tree: relaunch with isolation: \"worktree\", or add a line '"'"'ISOLATION-EXEMPT: <reason>'"'"' to the prompt (the reviewer will stay read-only agent-side).")}}'
exit 0
