#!/usr/bin/env bash
# ABOUTME: Wrapper that invokes the Python review-budget-guard hook via uv with the payload on stdin
# ABOUTME: See review-budget-guard.py for the actual logic

exec uv run --no-project python3 "$(cd "$(dirname "$0")" && pwd)/review-budget-guard.py"
