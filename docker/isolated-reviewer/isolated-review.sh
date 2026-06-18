#!/usr/bin/env bash
# ABOUTME: Runs Claude Code in an isolated Docker container for unbiased code reviews
# ABOUTME: Mounts only OAuth credentials (read-only) and project source (read-only), no user config

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="claude-reviewer:latest"
CREDENTIALS_VOLUME="claude-reviewer-auth"

# Optional wall-clock guard: prefix docker run with timeout/gtimeout if available,
# else run unguarded. Prevents a non-responsive reviewer from hanging forever when
# invoked from a terminal (the orchestrated /second-opinion flow is already bounded
# by the harness Bash-tool timeout). Override the limit with REVIEW_TIMEOUT.
TIMEOUT_CMD="$(command -v timeout || command -v gtimeout || true)"
REVIEW_TIMEOUT="${REVIEW_TIMEOUT:-300}"

# --- Usage ---
usage() {
  cat <<EOF
Usage: $(basename "$0") [OPTIONS] <project-path> <prompt>

Run Claude Code in an isolated container for unbiased code reviews.
No user config, memories, or rules are loaded.

Options:
  --model MODEL     Model to use (default: sonnet)
  --output-format   Output format: text, json, stream-json (default: text)
  --login           Run interactive login to refresh credentials
  --build           Rebuild the Docker image
  -h, --help        Show this help

Examples:
  $(basename "$0") ~/projects/myapp "Review this codebase for security issues"
  $(basename "$0") --model opus ~/projects/myapp "Is the error handling consistent?"
  $(basename "$0") --login
EOF
  exit 0
}

# --- Login flow ---
do_login() {
  echo "Starting interactive login in container..."
  echo "A URL will appear. Open it in your browser to authenticate."
  echo ""

  # Login writes to the volume; extract credentials after
  docker run -it --rm \
    -v "${CREDENTIALS_VOLUME}:/home/node/.claude" \
    --entrypoint bash \
    "${IMAGE_NAME}" \
    -c "claude login"

  echo ""
  echo "Login complete. Credentials saved to volume '${CREDENTIALS_VOLUME}'."
}

# --- Build image ---
do_build() {
  echo "Building ${IMAGE_NAME}..."
  docker build -t "${IMAGE_NAME}" "${SCRIPT_DIR}"
  echo "Build complete."
}

# --- Check credentials exist in volume ---
check_credentials() {
  if ! docker run --rm \
    -v "${CREDENTIALS_VOLUME}:/home/node/.claude" \
    --entrypoint bash \
    "${IMAGE_NAME}" \
    -c "grep -q claudeAiOauth /home/node/.claude/.credentials.json" 2>/dev/null; then
    echo "ERROR: No valid credentials found. Run '$(basename "$0") --login' first." >&2
    exit 1
  fi
}

# --- Main ---
MODEL="opus"
OUTPUT_FORMAT="text"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --login)
      do_login
      exit 0
      ;;
    --build)
      do_build
      exit 0
      ;;
    --model)
      MODEL="$2"
      shift 2
      ;;
    --output-format)
      OUTPUT_FORMAT="$2"
      shift 2
      ;;
    -h|--help)
      usage
      ;;
    *)
      break
      ;;
  esac
done

if [[ $# -lt 2 ]]; then
  echo "ERROR: Missing required arguments." >&2
  echo "Usage: $(basename "$0") <project-path> <prompt>" >&2
  exit 1
fi

PROJECT_PATH="$(cd "$1" && pwd)"
PROMPT="$2"

# Check image exists
if ! docker image inspect "${IMAGE_NAME}" &>/dev/null; then
  echo "Image '${IMAGE_NAME}' not found. Building..."
  do_build
fi

# Verify credentials exist in volume
check_credentials

# Run isolated review (credentials stay in volume, never touch host filesystem)
${TIMEOUT_CMD:+${TIMEOUT_CMD} ${REVIEW_TIMEOUT}} docker run --rm \
  -v "${CREDENTIALS_VOLUME}:/home/node/.claude:ro" \
  -v "${PROJECT_PATH}:/workspace:ro" \
  "${IMAGE_NAME}" \
  --print \
  --model "${MODEL}" \
  --output-format "${OUTPUT_FORMAT}" \
  "${PROMPT}" || {
  rc=$?
  if [[ $rc -eq 124 ]]; then
    echo "ERROR: Claude reviewer timed out after ${REVIEW_TIMEOUT}s (override with REVIEW_TIMEOUT=<seconds>)." >&2
  fi
  exit $rc
}
