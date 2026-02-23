# ABOUTME: Pydantic models for gog Gmail JSON parsing and classification results
# ABOUTME: GogThread, ClassifiedThread, ClassificationResult, RuleConfig

from __future__ import annotations

import re
from collections import defaultdict

from pydantic import BaseModel, ConfigDict, Field

_EMAIL_RE = re.compile(r"<([^>]+)>")


class GogThread(BaseModel):
    """A single thread from `gog gmail search --json` output."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    date: str
    from_: str = Field(alias="from")
    subject: str
    labels: list[str]
    message_count: int = Field(default=1, alias="messageCount")

    @property
    def email(self) -> str:
        """Extract email from 'Name <email>' or bare 'email' format."""
        match = _EMAIL_RE.search(self.from_)
        if match:
            return match.group(1)
        return self.from_.strip()

    @property
    def domain(self) -> str:
        """Extract @domain.com from the email address."""
        addr = self.email
        at = addr.rfind("@")
        if at == -1:
            return ""
        return addr[at:]


class GogSearchResult(BaseModel):
    """Top-level response from `gog gmail search --json`."""

    model_config = ConfigDict(populate_by_name=True)

    threads: list[GogThread] = []
    next_page_token: str | None = Field(default=None, alias="nextPageToken")


class ClassifiedThread(BaseModel):
    """A thread with its classification result."""

    thread: GogThread
    priority: str
    matched_rule: str


class ClassificationResult(BaseModel):
    """Full classification run, saved as state."""

    date: str
    total: int
    classified: list[ClassifiedThread]

    @property
    def by_priority(self) -> dict[str, list[ClassifiedThread]]:
        """Group classified threads by priority."""
        groups: dict[str, list[ClassifiedThread]] = defaultdict(list)
        for item in self.classified:
            groups[item.priority].append(item)
        return dict(groups)


class SenderRule(BaseModel):
    """Match a sender pattern to a priority."""

    match: str
    priority: str


class LabelRule(BaseModel):
    """Match a label to a priority."""

    label: str
    priority: str


class RuleConfig(BaseModel):
    """Classification rules loaded from rules.yaml."""

    account: str
    sender_rules: list[SenderRule]
    label_rules: list[LabelRule]
    category_rules: dict[str, str]
    default_priority: str = "P3"
