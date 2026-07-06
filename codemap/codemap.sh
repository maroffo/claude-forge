#!/usr/bin/env bash
# ABOUTME: `codemap` CLI — prints a fresh code-orientation map for a repo to stdout (no file, no cache)
# ABOUTME: On-demand tool an agent runs via Bash, or a human runs in the terminal. See codemap/generate.py.

# Resolve the generator relative to this script, following the install symlink.
here="$(cd "$(dirname "$(readlink -f "$0" 2>/dev/null || echo "$0")")" && pwd)"
repo="${1:-$PWD}"

exec uv run --no-project python3 "$here/generate.py" --repo "$repo" --print
