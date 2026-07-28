#!/usr/bin/env bash
# ABOUTME: Appends one JSONL row per /score run to the target repo's quality_reports/score-history.jsonl
# ABOUTME: --trend renders the tail-10 table plus the delta vs the previous entry; the model never appends by hand

# The history file is a denormalized view of harness-trace SCORE events; change one,
# change the other (the mirrored note lives in skills/score/SKILL.md).
#
# Two properties this script exists to hold:
#   1. The append is done here, never by the model. A model computing a timestamp and
#      hand-writing an arithmetic delta into a log is the caveat gstack's `health` skill
#      carries; a script makes the row mechanical (plan decision 9).
#   2. The file is gitignored in the target repo. The fields carry no exploits, but a
#      branch name next to a low score is a metadata leak that corroborates gitignored
#      review findings, so it stays local (plan requirement 6).

set -euo pipefail

HISTORY_REL="quality_reports/score-history.jsonl"

usage() {
  cat <<'EOF'
usage: score-log.sh --score <n> --threshold <n> --gate <commit|pr|excellence> \
                    --check <pass|fail> --e2e <pass|fail> --major <n> --minor <n> \
                    [--evidence <bundle-path>]
       score-log.sh --trend

  --evidence is optional and additive: the evidence-bundle path from the SCORE
  literal's evidence field, when the repo produced one (make evidence).

  Append mode (all seven required flags) writes ONE JSONL line to
  <git-root>/quality_reports/score-history.jsonl, creating the directory and
  ensuring the target repo's .gitignore carries the history path exactly once.

  --threshold and --gate are the pair the canonical SCORE line prints
  (`SCORE: <n>/100 (threshold: <t>, gate: commit|pr|excellence)`): the INTENDED
  action and the number it is judged against, not the highest bar cleared.

  --trend prints the last 10 entries plus the delta vs the previous one.
  No history yet: --trend says so and exits 0.

Exit codes: 2 = bad arguments or not inside a git repository.
EOF
}

die() {
  local code="$1"
  shift
  printf 'score-log: %s\n' "$*" >&2
  exit "$code"
}

# Leading zeros are rejected rather than accepted and normalised: bash reads `08` as
# octal, so a value that slipped through here would blow up in the arithmetic
# comparison or in printf %d, after the file had already been touched.
is_uint() {
  [[ "$1" =~ ^(0|[1-9][0-9]*)$ ]]
}

# Appends the history path to the target repo's .gitignore if it is not already an
# exact line. Append-only and idempotent: the .gitignore belongs to the target repo,
# so it is never rewritten or reordered.
#
# Single writer assumed: /score is interactive and one run appends one row. Racing
# copies can each see no ignore line and each append one, leaving duplicates. They
# are harmless (git ignores the path either way) and stable: the next run's
# `grep -qxF` matches the first duplicate and appends nothing, so the count never
# grows again, but nothing removes the extra lines either.
ensure_gitignored() {
  local gi="$1/.gitignore"
  if [[ -f "$gi" ]] && grep -qxF "$HISTORY_REL" "$gi"; then
    return 0
  fi
  local prefix=""
  if [[ -s "$gi" ]]; then
    # Command substitution strips trailing newlines, so a non-empty result means the
    # file does not end in one and the append would otherwise glue onto the last line.
    if [[ -n "$(tail -c 1 "$gi")" ]]; then
      prefix=$'\n\n'
    else
      prefix=$'\n'
    fi
  fi
  printf '%s# /score history (local: branch names next to low scores corroborate gitignored findings)\n%s\n' \
    "$prefix" "$HISTORY_REL" >> "$gi"
}

render_trend() {
  uv run --no-project python3 - "$1" <<'PY'
import json
import sys

path = sys.argv[1]
rows, unparseable = [], 0
with open(path, encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            unparseable += 1

# Loud, and before the empty-history exit: a history whose every line is corrupt
# reads exactly like a fresh one, and "corrupt history" is the falsification
# condition of this change.
if unparseable:
    print("warning: skipped %d unparseable line(s) in %s" % (unparseable, path))

if not rows:
    print("no history yet (%s)" % path)
    sys.exit(0)

tail = rows[-10:]
cols = ("ts", "branch", "score", "threshold", "gate")
widths = [max(len(c), *(len(str(r.get(c, "?"))) for r in tail)) for c in cols]

print("score history: %s (%d entries, showing last %d)" % (path, len(rows), len(tail)))
print("  ".join(c.ljust(w) for c, w in zip(cols, widths)).rstrip())
for r in tail:
    print("  ".join(str(r.get(c, "?")).ljust(w) for c, w in zip(cols, widths)).rstrip())

if len(rows) < 2:
    print("delta vs previous: n/a (first entry)")
else:
    prev, cur = rows[-2].get("score"), rows[-1].get("score")
    if isinstance(prev, int) and isinstance(cur, int):
        delta = cur - prev
        print("delta vs previous: %+d (%d -> %d)" % (delta, prev, cur))
    else:
        print("delta vs previous: n/a (score field unreadable)")
PY
}

mode="append"
score=""
threshold=""
gate=""
check=""
e2e=""
major=""
minor=""
evidence=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --trend)
      mode="trend"
      shift
      ;;
    --score|--threshold|--gate|--check|--e2e|--major|--minor|--evidence)
      [[ $# -ge 2 ]] || die 2 "$1 requires a value"
      case "$1" in
        --score) score="$2" ;;
        --threshold) threshold="$2" ;;
        --gate) gate="$2" ;;
        --check) check="$2" ;;
        --e2e) e2e="$2" ;;
        --major) major="$2" ;;
        --minor) minor="$2" ;;
        --evidence) evidence="$2" ;;
      esac
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die 2 "unknown argument: $1"
      ;;
  esac
done

# The history belongs to the repo being scored, which is the current directory's repo,
# not necessarily claude-forge: /score runs wherever the work is.
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || die 2 "not inside a git repository"
repo_root="$(git rev-parse --show-toplevel)"
history="$repo_root/$HISTORY_REL"

if [[ "$mode" == "trend" ]]; then
  if [[ ! -f "$history" ]]; then
    printf 'no history yet (%s)\n' "$history"
    exit 0
  fi
  render_trend "$history"
  exit 0
fi

[[ -n "$score" && -n "$threshold" && -n "$gate" && -n "$check" && -n "$e2e" && -n "$major" && -n "$minor" ]] ||
  die 2 "append mode requires --score --threshold --gate --check --e2e --major --minor"
is_uint "$score" && [[ "$score" -le 100 ]] || die 2 "--score must be an integer 0-100: $score"
is_uint "$threshold" && [[ "$threshold" -le 100 ]] ||
  die 2 "--threshold must be an integer 0-100: $threshold"
case "$gate" in
  commit|pr|excellence) ;;
  *) die 2 "--gate must be commit, pr or excellence: $gate" ;;
esac
case "$check" in
  pass|fail) ;;
  *) die 2 "--check must be pass or fail: $check" ;;
esac
case "$e2e" in
  pass|fail) ;;
  *) die 2 "--e2e must be pass or fail: $e2e" ;;
esac
is_uint "$major" || die 2 "--major must be a non-negative integer: $major"
is_uint "$minor" || die 2 "--minor must be a non-negative integer: $minor"

mkdir -p "$(dirname "$history")"
ensure_gitignored "$repo_root"

ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
branch="$(git branch --show-current)"
[[ -n "$branch" ]] || branch="detached"
# Ref names may legally contain a double quote; control chars are stripped so a crafted
# branch name cannot forge extra JSONL rows.
branch="$(printf '%s' "$branch" | tr -d '[:cntrl:]' | sed 's/\\/\\\\/g; s/"/\\"/g')"

# --evidence is optional and additive (stage A of the evidence-path rollout):
# rows without it stay valid, consumers must not require the field. The value
# must respect the SCORE literal's char class ([^,)\n]+): a path the hook and
# extractor would truncate must not land verbatim in history, so it is rejected
# here rather than silently recorded as something the guard never validated.
if [[ "$evidence" == *,* || "$evidence" == *\)* ]]; then
  die 2 "--evidence must not contain ',' or ')': the SCORE literal cannot carry it: $evidence"
fi
# Escaped like the branch name: paths are attacker-adjacent input.
if [[ -n "$evidence" ]]; then
  evidence="$(printf '%s' "$evidence" | tr -d '[:cntrl:]' | sed 's/\\/\\\\/g; s/"/\\"/g')"
  printf '{"ts":"%s","branch":"%s","score":%d,"threshold":%d,"gate":"%s","check":"%s","e2e":"%s","major":%d,"minor":%d,"evidence":"%s"}\n' \
    "$ts" "$branch" "$score" "$threshold" "$gate" "$check" "$e2e" "$major" "$minor" "$evidence" >> "$history"
else
  printf '{"ts":"%s","branch":"%s","score":%d,"threshold":%d,"gate":"%s","check":"%s","e2e":"%s","major":%d,"minor":%d}\n' \
    "$ts" "$branch" "$score" "$threshold" "$gate" "$check" "$e2e" "$major" "$minor" >> "$history"
fi

printf 'appended: %s\n' "$history"
