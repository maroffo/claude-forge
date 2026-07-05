#!/usr/bin/env bash
# ABOUTME: Wrapper that invokes checkpoint-reminder.py via uv with payload on stdin
# ABOUTME: See checkpoint-reminder.py for logic

exec uv run --no-project python3 "$(dirname "$0")/checkpoint-reminder.py"
