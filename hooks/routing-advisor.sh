#!/usr/bin/env bash
# ABOUTME: Wrapper that invokes routing-advisor.py via uv with payload on stdin
# ABOUTME: See routing-advisor.py for logic

exec uv run --no-project python3 "$(dirname "$0")/routing-advisor.py"
