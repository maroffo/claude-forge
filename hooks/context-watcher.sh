#!/usr/bin/env bash
# ABOUTME: Wrapper that invokes context-watcher.py via uv with payload on stdin
# ABOUTME: See context-watcher.py for logic

exec uv run --no-project python3 "$(dirname "$0")/context-watcher.py"
