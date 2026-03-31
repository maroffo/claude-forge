# ABOUTME: Shared pytest fixtures for harness-trace tests
# ABOUTME: Provides sample session JSONL data and trace entries

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest


@pytest.fixture()
def sample_session_jsonl(tmp_path: Path) -> Path:
    """Create a sample session JSONL file with orchestrator step indicators."""
    messages = [
        {
            "type": "user",
            "timestamp": 1711900000000,
            "message": {"content": "Implement a health check endpoint"},
        },
        {
            "type": "assistant",
            "timestamp": 1711900060000,
            "message": {
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "## Requirements Refinement\n\n"
                            "I found 2 ambiguities and asked 2 clarifying questions."
                        ),
                    }
                ]
            },
        },
        {
            "type": "assistant",
            "timestamp": 1711900120000,
            "message": {
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "## Research\n\n"
                            "Complexity: moderate\n"
                            "Consulted 3 sources."
                        ),
                    }
                ]
            },
        },
        {
            "type": "assistant",
            "timestamp": 1711900180000,
            "message": {
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "## Implementation Report\n\n"
                            "Launched software-engineer agent.\n"
                            "4 files changed."
                        ),
                    }
                ]
            },
        },
        {
            "type": "assistant",
            "timestamp": 1711900240000,
            "message": {
                "content": [
                    {
                        "type": "text",
                        "text": "Tests pass. Lint clean. Build ok.",
                    }
                ]
            },
        },
        {
            "type": "assistant",
            "timestamp": 1711900300000,
            "message": {
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "## Architecture Review\n\n"
                            "CRITICAL: 0\n"
                            "MAJOR: 1\n"
                            "MINOR: 2\n"
                            "Recommendation: FIX BEFORE MERGE"
                        ),
                    }
                ]
            },
        },
        {
            "type": "assistant",
            "timestamp": 1711900360000,
            "message": {
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Fixed major findings. Findings addressed: 1.\n"
                            "Deviation R1: null check missing in handler."
                        ),
                    }
                ]
            },
        },
        {
            "type": "assistant",
            "timestamp": 1711900420000,
            "message": {
                "content": [
                    {
                        "type": "text",
                        "text": "Quality score: 87. Threshold: 80. Gate: commit.",
                    }
                ]
            },
        },
        {
            "type": "assistant",
            "timestamp": 1711900480000,
            "message": {
                "content": [
                    {
                        "type": "text",
                        "text": "UAT: goal-backward verification passed.",
                    }
                ]
            },
        },
    ]

    session_file = tmp_path / "test-session.jsonl"
    with session_file.open("w") as f:
        for msg in messages:
            f.write(json.dumps(msg) + "\n")

    return session_file


@pytest.fixture()
def sample_trace_entry() -> dict:
    """A sample trace entry as a dict."""
    return {
        "v": 1,
        "session": "test-session",
        "ts": datetime(2026, 3, 31, 10, 0, 0, tzinfo=UTC).isoformat(),
        "step": "SCORE",
        "data": {"score": 87, "threshold": 80, "gate": "commit"},
    }
