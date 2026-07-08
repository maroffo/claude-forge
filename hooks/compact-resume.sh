#!/usr/bin/env bash
# ABOUTME: Wrapper that invokes compact-resume.py via uv with payload on stdin
# ABOUTME: See compact-resume.py for logic

exec uv run --no-project python3 "$(dirname "$0")/compact-resume.py"
