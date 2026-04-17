#!/usr/bin/env bash
# ABOUTME: Wrapper that invokes commit-intent-guard.py via uv with payload on stdin
# ABOUTME: See commit-intent-guard.py for logic

exec uv run --no-project python3 "$(dirname "$0")/commit-intent-guard.py"
