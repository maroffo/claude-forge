# ABOUTME: Shared test fixtures for inbox-triage tests
# ABOUTME: Common GogThread and RuleConfig builders

from __future__ import annotations

import pytest

from inbox_triage.models import GogThread, RuleConfig


@pytest.fixture
def sample_thread() -> GogThread:
    return GogThread(
        id="thread_001",
        date="2026-02-23",
        subject="Test email",
        labels=["INBOX", "UNREAD"],
        **{"from": "Test User <test@example.com>"},
    )


@pytest.fixture
def sample_rules() -> RuleConfig:
    return RuleConfig(
        account="test@example.com",
        sender_rules=[],
        label_rules=[],
        category_rules={},
        default_priority="P3",
    )
