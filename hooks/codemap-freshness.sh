#!/usr/bin/env bash
# ABOUTME: Wrapper that invokes the Python codemap-freshness hook via uv with the payload on stdin
# ABOUTME: See codemap-freshness.py for the actual logic

exec uv run --no-project python3 "$(dirname "$(readlink -f "$0" 2>/dev/null || echo "$0")")/codemap-freshness.py"
