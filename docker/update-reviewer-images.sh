#!/usr/bin/env bash
# ABOUTME: Daily auto-update check for isolated reviewer Docker images
# ABOUTME: Compares installed vs latest npm versions, rebuilds if newer. Runs in background.

set -euo pipefail

STAMP_FILE="${HOME}/.cache/claude-forge-reviewer-update"
LOCK_FILE="${STAMP_FILE}.lock"
LOG_FILE="${HOME}/.cache/claude-forge-reviewer-update.log"
FORGE_DIR="${HOME}/Development/private/claude-forge"
UPDATE_INTERVAL=86400  # 24 hours in seconds

# --- Guard: skip if already checked today ---
if [[ -f "$STAMP_FILE" ]]; then
  last_check=$(cat "$STAMP_FILE" 2>/dev/null || echo 0)
  now=$(date +%s)
  if (( now - last_check < UPDATE_INTERVAL )); then
    return 0 2>/dev/null || exit 0
  fi
fi

# --- Guard: skip if another instance is running ---
if [[ -f "$LOCK_FILE" ]]; then
  lock_age=$(( $(date +%s) - $(stat -f %m "$LOCK_FILE" 2>/dev/null || echo 0) ))
  if (( lock_age < 600 )); then
    return 0 2>/dev/null || exit 0
  fi
  rm -f "$LOCK_FILE"  # stale lock
fi

mkdir -p "$(dirname "$STAMP_FILE")"
echo $$ > "$LOCK_FILE"
trap 'rm -f "$LOCK_FILE"' EXIT

{
  echo "=== $(date) ==="

  # --- Check Docker is running ---
  if ! docker info &>/dev/null; then
    echo "Docker not running, skipping update check"
    date +%s > "$STAMP_FILE"
    exit 0
  fi

  updated=false

  # --- Claude Code ---
  if docker image ls --format '{{.Repository}}' claude-reviewer | grep -q claude-reviewer; then
    installed=$(docker run --rm --entrypoint claude claude-reviewer:latest --version 2>/dev/null | awk '{print $1}' || echo "unknown")
    latest=$(npm view @anthropic-ai/claude-code version 2>/dev/null || echo "unknown")
    echo "Claude Code: installed=$installed latest=$latest"

    if [[ "$latest" != "unknown" && "$installed" != "$latest" ]]; then
      echo "Rebuilding claude-reviewer with v${latest}..."
      docker build \
        --build-arg CLAUDE_CODE_VERSION="$latest" \
        -t claude-reviewer:latest \
        "${FORGE_DIR}/docker/isolated-reviewer" && updated=true
    fi
  else
    echo "claude-reviewer:latest not found, skipping"
  fi

  # --- Gemini CLI ---
  if docker image ls --format '{{.Repository}}' gemini-reviewer | grep -q gemini-reviewer; then
    installed=$(docker run --rm gemini-reviewer:latest --version 2>/dev/null || echo "unknown")
    latest=$(npm view @google/gemini-cli version 2>/dev/null || echo "unknown")
    echo "Gemini CLI: installed=$installed latest=$latest"

    if [[ "$latest" != "unknown" && "$installed" != "$latest" ]]; then
      echo "Rebuilding gemini-reviewer with v${latest}..."
      docker build \
        --build-arg GEMINI_CLI_VERSION="$latest" \
        -t gemini-reviewer:latest \
        "${FORGE_DIR}/docker/isolated-gemini" && updated=true
    fi
  else
    echo "gemini-reviewer:latest not found, skipping"
  fi

  if $updated; then
    echo "Images updated."
  else
    echo "All images up to date."
  fi

  date +%s > "$STAMP_FILE"
  echo "Done."
} >> "$LOG_FILE" 2>&1
