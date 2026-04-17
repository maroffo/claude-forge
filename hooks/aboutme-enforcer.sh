#!/usr/bin/env bash
# ABOUTME: Wrapper that invokes the Python ABOUTME enforcer via uv with the payload on stdin
# ABOUTME: See aboutme-enforcer.py for the actual logic

exec uv run --no-project python3 "$(dirname "$0")/aboutme-enforcer.py"
