# ABOUTME: Shared pytest fixtures for autoresearch-prompt tests
# ABOUTME: Provides sample eval examples, prompt content, and mock clients

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from autoresearch_prompt.models import EvalExample


@pytest.fixture
def sample_extract_example() -> EvalExample:
    return EvalExample.model_validate(
        {
            "from": "Test Author <test@example.com>",
            "subject": "AI Firewall patterns",
            "content": "An AI Firewall is a reverse proxy for AI traffic...",
            "expected_action": "extract",
            "expected_category": "AI Agents and Tools",
            "expected_content": "AI Gateway pattern for production AI security",
        }
    )


@pytest.fixture
def sample_skip_example() -> EvalExample:
    return EvalExample.model_validate(
        {
            "from": "Newsletter <news@example.com>",
            "subject": "Weekly job listings",
            "content": "Here are 68 hottest jobs this week...",
            "expected_action": "skip",
        }
    )


@pytest.fixture
def sample_prompt_md(tmp_path: Path) -> Path:
    prompt = tmp_path / "prompt.md"
    prompt.write_text(
        "## System\n\nYou are a newsletter classifier.\n\n"
        "## User\n\nFrom: {{from}}\nSubject: {{subject}}\n\n{{content}}\n",
        encoding="utf-8",
    )
    return prompt


@pytest.fixture
def mock_anthropic_client() -> MagicMock:
    client = MagicMock()
    response = MagicMock()
    text = (
        '{"action": "extract", "category": "AI Agents and Tools",'
        ' "content": "test insight", "reason": "relevant"}'
    )
    response.content = [MagicMock(text=text)]
    response.usage.input_tokens = 100
    response.usage.output_tokens = 50
    client.messages.create.return_value = response
    return client
