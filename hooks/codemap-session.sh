#!/usr/bin/env bash
# ABOUTME: Wrapper that invokes the Python codemap-session hook via uv with the payload on stdin
# ABOUTME: See codemap-session.py for the actual logic

exec uv run --no-project python3 "$(dirname "$(readlink -f "$0" 2>/dev/null || echo "$0")")/codemap-session.py"
