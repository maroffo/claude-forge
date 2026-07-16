#!/usr/bin/env bash
# ABOUTME: Polls GitHub for review-worthy PRs and dispatches headless `claude -p` /pr-review runs.
# ABOUTME: Mechanical scope filter + Haiku triage for the fuzzy residue; dedupes via a reviewed-set; single-instance lock.
set -euo pipefail

# ---- config (override via env) ----
REPO="${PR_WATCH_REPO:-Wishew/wishew-monorepo}"
ME="${PR_WATCH_ME:-maroffo}"
# Working copy the reviewer runs in. This script lives in claude-forge, not in the
# reviewed repo, so set PR_WATCH_REPO_DIR (the launchd plist does); the default is a fallback.
REPO_DIR="${PR_WATCH_REPO_DIR:-$HOME/Development/Wishew/wishew-monorepo}"
STATE_DIR="${PR_WATCH_STATE:-$HOME/.local/state/pr-watch}"   # kept OUT of any repo on purpose
WINDOW_MIN="${PR_WATCH_WINDOW_MIN:-1440}"        # look back this many minutes (24h: reviewed-set dedupes, so a failed PR stays retriable)
REVIEW_MODEL="${PR_WATCH_REVIEW_MODEL:-opus}"    # model for the actual review
TRIAGE_MODEL="${PR_WATCH_TRIAGE_MODEL:-haiku}"   # model for the fuzzy "is it architecture?" call
DRY_RUN="${PR_WATCH_DRY_RUN:-0}"                 # 1 = decide + log, do not invoke the reviewer

REVIEWED="$STATE_DIR/reviewed.txt"               # append-only set of handled PR numbers
CONTEXT="$STATE_DIR/context.log"                 # one-liner digest per review, fed back for cross-PR memory
LOG="$STATE_DIR/pr-watch.log"
LOCKDIR="$STATE_DIR/lock.d"

mkdir -p "$STATE_DIR"; : >>"$REVIEWED"; : >>"$CONTEXT"
log(){ echo "$(date -u +%FT%TZ) $*" >>"$LOG"; }

# ---- credentials for the composed sub-steps, so they work headless ----
# /gemini-review reads GEMINI_API_KEY from the env; /second-opinion reads the key
# files directly (gemini + deepseek). $(cat) strips the trailing newline, which is
# what an auth header expects. GEMINI_CLI_TRUST_WORKSPACE avoids the non-interactive
# gemini CLI silently downgrading out of --yolo.
[ -f "$HOME/.config/gemini-api-key" ]   && export GEMINI_API_KEY="$(cat "$HOME/.config/gemini-api-key")"
[ -f "$HOME/.config/deepseek-api-key" ] && export DEEPSEEK_API_KEY="$(cat "$HOME/.config/deepseek-api-key")"
export GEMINI_CLI_TRUST_WORKSPACE=1

# ---- single-instance lock (mkdir is atomic; no flock dependency on macOS) ----
# The lock survives a crash/SIGKILL (the trap never runs), so detect a stale
# lock by the PID recorded inside it and reclaim when that process is gone.
if ! mkdir "$LOCKDIR" 2>/dev/null; then
  stale_pid=$(cat "$LOCKDIR/pid" 2>/dev/null || true)
  if [ -n "$stale_pid" ] && ! kill -0 "$stale_pid" 2>/dev/null; then
    log "stale lock (pid $stale_pid gone), reclaiming"
    rm -rf "$LOCKDIR"
    mkdir "$LOCKDIR" 2>/dev/null || { log "lock race, skipping"; exit 0; }
  else
    log "another run holds the lock, skipping"; exit 0
  fi
fi
echo "$$" > "$LOCKDIR/pid"
trap 'rm -rf "$LOCKDIR" 2>/dev/null || true' EXIT

# ---- list recent PRs (all states: we review even ones already merged/closed without a review) ----
since=$(date -u -v-"${WINDOW_MIN}"M +%FT%TZ 2>/dev/null || date -u -d "${WINDOW_MIN} minutes ago" +%FT%TZ)
prs=$(gh pr list --repo "$REPO" --state all --search "created:>=$since" \
        --json number,title,assignees,files,author --limit 50) || { log "gh pr list failed"; exit 0; }

echo "$prs" | jq -c '.[]' | while read -r pr; do
  num=$(jq -r '.number'  <<<"$pr")
  title=$(jq -r '.title' <<<"$pr")
  grep -qx "$num" "$REVIEWED" && continue          # already handled -> idempotent

  assigned=$(jq -r --arg me "$ME" 'any(.assignees[]?; .login==$me)' <<<"$pr")
  paths=$(jq -r '.files[].path' <<<"$pr")

  # ---- mechanical scope filter (deterministic, no LLM) ----
  bucket=""
  [ "$assigned" = "true" ]                                                    && bucket="assigned-to-me"
  grep -qE '^infra/'                                          <<<"$paths"     && bucket="${bucket:-terraform/infra}"
  grep -qE '^services/.+\.go$|^services/[^/]+/go\.(mod|sum)$' <<<"$paths"     && bucket="${bucket:-golang}"
  grep -qE '(^|/)migrations/|/schema\.prisma$'                <<<"$paths"     && bucket="${bucket:-database}"
  grep -qE '(^|/)nx\.json$|(^|/)turbo\.json$|(^|/)tsconfig\.base' <<<"$paths" && bucket="${bucket:-build-system}"
  grep -qE '^docs/security/|(^|/)(privacy|auth)/'             <<<"$paths"     && bucket="${bucket:-security}"

  decision="skip"; why="$bucket"
  if [ -n "$bucket" ]; then
    decision="review"
  else
    # ---- fuzzy residue only: ask Haiku whether it is an ARCHITECTURAL change ----
    # Cheap pre-filter: must touch non-UI source before spending a token call.
    if grep -qvE '(ui/|/components/|/pages/|\.md$|\.css$|\.snap$|__tests__/)' <<<"$paths" \
       && grep -qE '\.(ts|go|py|rb|kt|swift)$' <<<"$paths"; then
      verdict=$(printf 'PR title: %s\nChanged files:\n%s\n\nIs this primarily a software ARCHITECTURE change (module/boundary/API/data-model/infra structure), as opposed to a UI, copy, or routine feature tweak? Answer with exactly one word: yes or no.' \
                  "$title" "$paths" \
                | claude -p --model "$TRIAGE_MODEL" 2>>"$LOG" | tr '[:upper:]' '[:lower:]' | grep -oE 'yes|no' | head -1 || true)
      if [ "$verdict" = "yes" ]; then decision="review"; why="architecture(haiku)"; fi
    fi
  fi

  if [ "$decision" != "review" ]; then
    log "SKIP   #$num ($title)"; echo "$num" >>"$REVIEWED"; continue
  fi

  log "REVIEW #$num [$why] ($title)"
  if [ "$DRY_RUN" = "1" ]; then echo "$num" >>"$REVIEWED"; continue; fi

  recent_ctx=$(tail -n 20 "$CONTEXT")             # cross-PR memory for the reviewer
  prompt=$(cat <<EOF
Invoke the /pr-review skill on $REPO#$num, then POST the resulting review as a PR comment via gh. Review it whether it is OPEN or already merged/closed.

Environment for the composed sub-steps (all present, use them):
- GEMINI_API_KEY is exported and ~/.config/gemini-api-key exists, so the /pr-review Phase-3 /gemini-review sub-step can run.
- DEEPSEEK_API_KEY is exported and ~/.config/deepseek-api-key exists; with GEMINI_API_KEY this lets /second-opinion spin its isolated Docker panel (claude + gemini + deepseek). GEMINI_CLI_TRUST_WORKSPACE=1 is set for the headless gemini CLI.
- Use /second-opinion ONLY when reviewer verdicts conflict or a Critical is contested (its gating rule), not on every PR.

Rules:
- Verify every claim against source at the PR head/merge SHA; the local checkout may be stale, so read files at the PR ref via gh, not the working tree.
- Score per the repo quality gates and END the posted comment with a line exactly: SCORE: <n>/100 (threshold: 90, gate: pr).

One-line digests of recent related reviews for cross-reference (may be empty):
$recent_ctx

After posting, print ONE final line to stdout in the form: DIGEST #$num <score> <one-sentence outcome>.
EOF
)

  if out=$(cd "$REPO_DIR" && claude -p "$prompt" --model "$REVIEW_MODEL" --dangerously-skip-permissions 2>>"$LOG"); then
    grep -E '^DIGEST ' <<<"$out" >>"$CONTEXT" || true
    echo "$num" >>"$REVIEWED"
    log "DONE   #$num"
  else
    log "FAIL   #$num (reviewer exited non-zero; will retry next poll)"
    # not added to reviewed -> retried next run
  fi
done

log "poll complete"
