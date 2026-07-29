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
# one launch and is deliberately confined to the FIRST line of the prompt, so it can
# only ever be something the launcher wrote. Any line would be wrong: briefs quote
# untrusted content verbatim (issue bodies, plan excerpts, file quotes), a quoted
# line starting with the marker would self-exempt the launch, and in the transcript
# an injected exemption is indistinguishable from an authored one. It is not a
# write-enable either: an exempted launch carries no isolation assertion in its
# brief, so the reviewer still self-downgrades to read-only agent-side.

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
# Matched on a normalised key because the Agent tool's resolver is far looser than a
# byte comparison: it folds case AND separators, so `Security-Reviewer`,
# `security_reviewer`, `security reviewer` and `securityreviewer` all start the same
# real reviewer. Dropping the hyphen from the SUFFIX is what closes those three; the
# key then folds to bare alphanumerics so no separator a future spelling invents can
# narrow the match again, which is the one direction this matcher may never move.
# The RAW value stays for the message, which must name what the launcher typed.
# Only `*-reviewer` agent types end in `reviewer`, so folding the separators away
# cannot pull a non-reviewer type into the policy: the whole roster was walked through
# this hook, 7 reviewers plus 4 alias spellings deny, 12 non-reviewers allow.
# LC_ALL=C keeps every class below byte-scoped: under a UTF-8 locale the character
# classes and bracket ranges follow the collation table, so the same spelling could
# decide differently on two machines.
LC_ALL=C
match_key=$(printf '%s' "$subagent_type" | LC_ALL=C tr '[:upper:]' '[:lower:]' | LC_ALL=C tr -cd 'a-z0-9')

# The tool's resolver also folds Unicode compatibility forms, so `dx-reviewer` spelled
# with U+2011 instead of the ASCII hyphen, or entirely in fullwidth latin, starts the
# real reviewer while the normalised key ends in no ASCII `-reviewer`. A byte-level
# normaliser cannot follow that fold, so reviewer-ness is undecidable for any type
# carrying a byte outside printable ASCII, and undecidable belongs in the policy
# branch. Every registered agent type is ASCII, so the conservative reading costs no
# legitimate launch: it only widens the deny set, which is the safe direction. Matched
# on the RAW value with a `case` glob, no binary, so a missing `tr` cannot turn this
# into a deny. The set is printable ASCII plus tab, newline and CR, which the
# normalisation above already strips; NBSP and friends land here instead of in
# `[:space:]`, which under the `LC_ALL=C` pin no longer covers them.
undecidable=""
case "$subagent_type" in
  *[!$'\t\n\r'" "-~]*) undecidable=yes ;;
esac

case "$match_key" in
  *reviewer) ;;
  *) [ -n "$undecidable" ] || exit 0 ;;
esac

# Only "worktree" satisfies the policy, and "remote" deliberately does not: a remote
# launch is off in its own environment, but it carries no isolation assertion in its
# brief either, so the reviewer self-downgrades and the review silently degrades.
# Neither outcome is what the launcher wanted, so both go back to the launcher.
isolation=$(printf '%s' "$payload" | jq -r '.tool_input.isolation // empty')
[ "$isolation" = "worktree" ] && exit 0

# First line only, and line-anchored within it: a mid-sentence mention of the marker
# must not exempt a launch, and neither must untrusted content quoted into the brief
# further down. The first line is cut with parameter expansion and matched with a
# `case` glob, so this path shells out to nothing: `head -1 | grep -E` meant that the
# absence of either binary made an exempt launch DENY, the one direction this hook
# promised never to fail in. `?*` is the old `.+`, at least one character after the
# marker, and a `case` glob is case-sensitive, so `isolation-exempt:` is not the
# marker. The pattern is fixed and its tail is a wildcard, so metacharacters in the
# reason are data.
prompt=$(printf '%s' "$payload" | jq -r '.tool_input.prompt // empty')
first_line=${prompt%%$'\n'*}
case "$first_line" in
  'ISOLATION-EXEMPT: '?*)
    # The reason is attacker-influenced text on its way to a terminal (CWE-117): strip
    # every control byte except tab, so it cannot forge a line attributed to another
    # hook. Carriage return goes too, since it overwrites the printed line just as an
    # escape sequence does. Newline cannot occur here, the line was cut at the first
    # one. A missing `tr` empties the reason and still ALLOWS, so the fail direction
    # holds on this path too.
    reason=$(printf '%s' "${first_line#ISOLATION-EXEMPT: }" | LC_ALL=C tr -d '\000-\010\013-\037\177')
    warn "ISOLATION-EXEMPT honored for $subagent_type: $reason (launch allowed, the reviewer stays read-only agent-side)"
    exit 0
    ;;
esac

jq -cn --arg t "$subagent_type" \
  '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:("Reviewer isolation guard: refusing to launch `" + $t + "` without an isolated worktree. Review agents write mutants and probe files, so an un-isolated launch lands those writes in the real tree: relaunch with isolation: \"worktree\", or make the first line of the prompt '"'"'ISOLATION-EXEMPT: <reason>'"'"' (the reviewer will stay read-only agent-side).")}}'
exit 0
