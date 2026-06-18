#!/usr/bin/env bash
# ABOUTME: Runs pi (DeepSeek) in an isolated Docker container for unbiased second opinions
# ABOUTME: Custom arm64-native image, API key from file, project source read-only, no user config

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE="deepseek-reviewer:latest"
API_KEY_FILE="${HOME}/.config/deepseek-api-key"

# Optional wall-clock guard: prefix docker run with timeout/gtimeout if available,
# else run unguarded. Prevents a non-responsive reviewer from hanging forever when
# invoked from a terminal (the orchestrated /second-opinion flow is already bounded
# by the harness Bash-tool timeout). Override the limit with REVIEW_TIMEOUT.
# Default is higher than the other reviewers: deepseek-reasoner (R1) can spend
# several minutes in its reasoning phase before emitting the answer.
TIMEOUT_CMD="$(command -v timeout || command -v gtimeout || true)"
REVIEW_TIMEOUT="${REVIEW_TIMEOUT:-600}"

# --- Usage ---
usage() {
  cat <<EOF
Usage: $(basename "$0") [OPTIONS] <project-path> <prompt>

Run pi (DeepSeek) in an isolated container for unbiased second opinions.
No user config or history is loaded. Uses custom arm64-native image.

Options:
  --model MODEL     Model to use (default: deepseek-reasoner)
  --api-key-file    Path to API key file (default: ~/.config/deepseek-api-key)
  --build           Rebuild the Docker image
  -h, --help        Show this help

Examples:
  $(basename "$0") ~/projects/myapp "Review this architecture decision"
  $(basename "$0") --model deepseek-chat ~/projects/myapp "Quick take"
EOF
  exit 0
}

# --- Main ---
MODEL="deepseek-reasoner"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --model)
      MODEL="$2"
      shift 2
      ;;
    --api-key-file)
      API_KEY_FILE="$2"
      shift 2
      ;;
    --build)
      echo "Building ${IMAGE}..."
      docker build -t "${IMAGE}" "${SCRIPT_DIR}"
      exit 0
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

# Read API key
if [[ ! -f "${API_KEY_FILE}" ]]; then
  echo "ERROR: API key file not found at ${API_KEY_FILE}" >&2
  echo "Create it with: echo 'YOUR_KEY' > ${API_KEY_FILE} && chmod 600 ${API_KEY_FILE}" >&2
  exit 1
fi

API_KEY="$(cat "${API_KEY_FILE}")"
if [[ -z "${API_KEY}" ]]; then
  echo "ERROR: API key file is empty." >&2
  exit 1
fi

# Check image exists
if ! docker image inspect "${IMAGE}" &>/dev/null; then
  echo "Image '${IMAGE}' not found. Building..."
  docker build -t "${IMAGE}" "${SCRIPT_DIR}"
fi

# Run isolated second opinion.
# -t read: read-only tool access (parity with other reviewers, no edit/write/bash).
# --no-session: ephemeral, leaves no session state behind.
${TIMEOUT_CMD:+${TIMEOUT_CMD} ${REVIEW_TIMEOUT}} docker run --rm \
  -e DEEPSEEK_API_KEY="${API_KEY}" \
  -v "${PROJECT_PATH}:/workspace:ro" \
  "${IMAGE}" \
  --provider deepseek \
  --model "${MODEL}" \
  -p \
  -t read \
  --no-session \
  "${PROMPT}" || {
  rc=$?
  if [[ $rc -eq 124 ]]; then
    echo "ERROR: DeepSeek reviewer timed out after ${REVIEW_TIMEOUT}s (override with REVIEW_TIMEOUT=<seconds>)." >&2
  fi
  exit $rc
}
