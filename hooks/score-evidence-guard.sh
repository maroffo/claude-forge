#!/usr/bin/env bash
# ABOUTME: Wrapper that invokes the Python score-evidence-guard hook via uv with the payload on stdin
# ABOUTME: See score-evidence-guard.py for the actual logic

exec uv run --no-project python3 "$(cd "$(dirname "$0")" && pwd)/score-evidence-guard.py"
