#!/usr/bin/env bash
# ABOUTME: Wrapper that invokes the Python .gitignore anchor lint via uv with the payload on stdin
# ABOUTME: See gitignore-anchor-lint.py for the actual logic

exec uv run --no-project python3 "$(dirname "$0")/gitignore-anchor-lint.py"
