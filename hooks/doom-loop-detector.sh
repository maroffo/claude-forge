#!/usr/bin/env bash
# ABOUTME: Wrapper that invokes the Python doom-loop detector via uv with the payload on stdin
# ABOUTME: See doom-loop-detector.py for the actual logic

exec uv run --no-project python3 "$(cd "$(dirname "$0")" && pwd)/doom-loop-detector.py"
