#!/usr/bin/env bash
# ABOUTME: Wrapper that invokes retrospective-nudge.py via uv with payload on stdin
# ABOUTME: See retrospective-nudge.py for logic

exec uv run --no-project python3 "$(dirname "$0")/retrospective-nudge.py"
