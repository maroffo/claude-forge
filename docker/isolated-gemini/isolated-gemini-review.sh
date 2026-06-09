#!/usr/bin/env bash
# ABOUTME: Runs Gemini CLI in an isolated Docker container for unbiased code reviews
# ABOUTME: Custom arm64-native image, API key from file, project source read-only, no user config

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE="gemini-reviewer:latest"
API_KEY_FILE="${HOME}/.config/gemini-api-key"

# --- Usage ---
usage() {
  cat <<EOF
Usage: $(basename "$0") [OPTIONS] <project-path> <prompt>

Run Gemini CLI in an isolated container for unbiased code reviews.
No user config or history is loaded. Uses custom arm64-native image.

Options:
  --model MODEL     Model to use (default: gemini-3.1-pro-preview)
  --output-format   Output format: text, json, stream-json (default: text)
  --api-key-file    Path to API key file (default: ~/.config/gemini-api-key)
  --build           Rebuild the Docker image
  -h, --help        Show this help

Examples:
  $(basename "$0") ~/projects/myapp "Review this codebase for security issues"
  $(basename "$0") --model gemini-2.5-flash ~/projects/myapp "Quick review"
EOF
  exit 0
}

# --- Main ---
MODEL="gemini-3.1-pro-preview"
OUTPUT_FORMAT="text"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --model)
      MODEL="$2"
      shift 2
      ;;
    --output-format)
      OUTPUT_FORMAT="$2"
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

# Run isolated review
docker run --rm \
  -e GEMINI_API_KEY="${API_KEY}" \
  -v "${PROJECT_PATH}:/workspace:ro" \
  "${IMAGE}" \
  -p "${PROMPT}" \
  -m "${MODEL}" \
  --output-format "${OUTPUT_FORMAT}" \
  --sandbox false \
  2>&1 | grep -v "^\[WARN\] Skipping unreadable" | grep -v "^Warning: Could not read"
