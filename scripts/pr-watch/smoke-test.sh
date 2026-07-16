#!/usr/bin/env bash
# ABOUTME: Smoke test that the headless /pr-review path actually invokes the skill and the API keys.
# ABOUTME: Runs a no-post review of a given PR and asserts the SUBSTEPS line; re-run after a claude/gh/gemini upgrade.
set -euo pipefail

PR="${1:?usage: smoke-test.sh <pr-number> [owner/repo]}"
REPO="${2:-${PR_WATCH_REPO:-Wishew/wishew-monorepo}}"

# Same env the bot exports, so the composed sub-steps can run.
[ -f "$HOME/.config/gemini-api-key" ]   && export GEMINI_API_KEY="$(cat "$HOME/.config/gemini-api-key")"
[ -f "$HOME/.config/deepseek-api-key" ] && export DEEPSEEK_API_KEY="$(cat "$HOME/.config/deepseek-api-key")"
export GEMINI_CLI_TRUST_WORKSPACE=1

prompt="Invoke the /pr-review skill on $REPO#$PR. CONTROLLED TEST: do NOT post any PR comment; print the review to stdout instead. Use /gemini-review as the /pr-review flow prescribes, and /second-opinion only if a finding is contested. End with exactly one line: SUBSTEPS: pr-review-skill=<yes|no> gemini-review=<yes|no> second-opinion=<yes|no|na>."

echo "smoke-testing headless /pr-review on $REPO#$PR (no comment will be posted)..."
out=$(claude -p "$prompt" --model "${PR_WATCH_REVIEW_MODEL:-opus}" --dangerously-skip-permissions)

line=$(grep -oE 'SUBSTEPS: .*' <<<"$out" | tail -1)
grep -E 'SCORE:' <<<"$out" | tail -1 || true
echo "${line:-SUBSTEPS: (line not found)}"

grep -q 'pr-review-skill=yes' <<<"$line" \
  && { echo "PASS: /pr-review skill invoked"; exit 0; } \
  || { echo "FAIL: /pr-review skill was not invoked (review ran from memory, or the prompt drifted)"; exit 1; }
