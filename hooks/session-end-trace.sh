#!/usr/bin/env bash
# ABOUTME: Wrapper that invokes session-end-trace.py via uv with payload on stdin
# ABOUTME: See session-end-trace.py for logic

exec uv run --no-project python3 "$(dirname "$0")/session-end-trace.py"
