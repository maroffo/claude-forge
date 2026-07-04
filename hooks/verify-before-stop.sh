#!/usr/bin/env bash
# ABOUTME: Wrapper that invokes the Python verify-before-stop hook via uv with the payload on stdin
# ABOUTME: See verify-before-stop.py for the actual logic

exec uv run --no-project python3 "$(cd "$(dirname "$0")" && pwd)/verify-before-stop.py"
