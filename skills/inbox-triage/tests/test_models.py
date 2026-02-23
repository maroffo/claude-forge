# ABOUTME: Tests for Pydantic models - parsing, properties, aliases
# ABOUTME: GogThread (email/domain/label extraction), GogSearchResult, ClassificationResult

from __future__ import annotations

from inbox_triage.models import (
    ClassificationResult,
    ClassifiedThread,
    GogSearchResult,
    GogThread,
)


def _thread(
    *,
    id: str = "t1",
    from_: str = "Alice <alice@example.com>",
    subject: str = "Hello",
    labels: list[str] | None = None,
    message_count: int = 1,
) -> GogThread:
    return GogThread(
        id=id,
        date="2026-02-23",
        subject=subject,
        labels=labels if labels is not None else ["INBOX"],
        message_count=message_count,
        **{"from": from_},
    )


def _classified(
    *,
    priority: str = "P3",
    matched_rule: str = "default",
    id: str = "t1",
    from_: str = "Alice <alice@example.com>",
    subject: str = "Hello",
    labels: list[str] | None = None,
) -> ClassifiedThread:
    return ClassifiedThread(
        thread=_thread(id=id, from_=from_, subject=subject, labels=labels),
        priority=priority,
        matched_rule=matched_rule,
    )


# --- GogThread parsing ---


class TestGogThreadParsing:
    def test_parse_from_dict_with_from_key(self):
        """The JSON alias 'from' works for parsing."""
        data = {
            "id": "abc",
            "date": "2026-02-23",
            "from": "Bob <bob@test.com>",
            "subject": "Test",
            "labels": ["INBOX"],
        }
        thread = GogThread.model_validate(data)
        assert thread.from_ == "Bob <bob@test.com>"
        assert thread.id == "abc"

    def test_parse_from_dict_with_from_underscore_key(self):
        """populate_by_name=True allows using the field name 'from_'."""
        data = {
            "id": "abc",
            "date": "2026-02-23",
            "from_": "Bob <bob@test.com>",
            "subject": "Test",
            "labels": ["INBOX"],
        }
        thread = GogThread.model_validate(data)
        assert thread.from_ == "Bob <bob@test.com>"

    def test_default_message_count(self):
        thread = _thread()
        assert thread.message_count == 1

    def test_explicit_message_count(self):
        data = {
            "id": "t1",
            "date": "2026-02-23",
            "from": "Alice <a@b.com>",
            "subject": "Hi",
            "labels": ["INBOX"],
            "messageCount": 5,
        }
        thread = GogThread.model_validate(data)
        assert thread.message_count == 5


# --- GogThread.email property ---


class TestGogThreadEmail:
    def test_email_from_name_angle_bracket_format(self):
        thread = _thread(from_="Alice Smith <alice@example.com>")
        assert thread.email == "alice@example.com"

    def test_email_bare_address(self):
        thread = _thread(from_="noreply@example.com")
        assert thread.email == "noreply@example.com"

    def test_email_bare_address_with_whitespace(self):
        thread = _thread(from_="  noreply@example.com  ")
        assert thread.email == "noreply@example.com"

    def test_email_quoted_name(self):
        thread = _thread(from_='"Bob Jones" <bob@test.com>')
        assert thread.email == "bob@test.com"


# --- GogThread.domain property ---


class TestGogThreadDomain:
    def test_domain_from_angle_bracket_format(self):
        thread = _thread(from_="Alice <alice@example.com>")
        assert thread.domain == "@example.com"

    def test_domain_from_bare_email(self):
        thread = _thread(from_="noreply@shop.io")
        assert thread.domain == "@shop.io"

    def test_domain_no_at_sign(self):
        thread = _thread(from_="not-an-email")
        assert thread.domain == ""


# --- GogThread.labels as list[str] ---


class TestGogThreadLabels:
    def test_labels_parsed_from_dict(self):
        data = {
            "id": "t1",
            "date": "2026-02-23",
            "from": "Alice <a@b.com>",
            "subject": "Hi",
            "labels": ["INBOX", "UNREAD", "IMPORTANT"],
        }
        thread = GogThread.model_validate(data)
        assert thread.labels == ["INBOX", "UNREAD", "IMPORTANT"]

    def test_single_label_list(self):
        thread = _thread(labels=["INBOX"])
        assert thread.labels == ["INBOX"]

    def test_empty_labels_list(self):
        thread = _thread(labels=[])
        assert thread.labels == []

    def test_default_labels(self):
        thread = _thread()
        assert thread.labels == ["INBOX"]


# --- GogSearchResult ---


class TestGogSearchResult:
    def test_default_empty_threads(self):
        result = GogSearchResult()
        assert result.threads == []
        assert result.next_page_token is None

    def test_parse_with_threads_and_token(self):
        data = {
            "threads": [
                {
                    "id": "t1",
                    "date": "2026-02-23",
                    "from": "Alice <a@b.com>",
                    "subject": "Hi",
                    "labels": ["INBOX"],
                },
                {
                    "id": "t2",
                    "date": "2026-02-23",
                    "from": "Bob <b@c.com>",
                    "subject": "Hey",
                    "labels": ["INBOX", "UNREAD"],
                },
            ],
            "nextPageToken": "abc123",
        }
        result = GogSearchResult.model_validate(data)
        assert len(result.threads) == 2
        assert result.threads[0].id == "t1"
        assert result.threads[1].from_ == "Bob <b@c.com>"
        assert result.next_page_token == "abc123"


# --- ClassificationResult.by_priority ---


class TestClassificationResultByPriority:
    def test_groups_by_priority(self):
        result = ClassificationResult(
            date="2026-02-23",
            total=4,
            classified=[
                _classified(priority="P1", id="t1"),
                _classified(priority="P3", id="t2"),
                _classified(priority="P1", id="t3"),
                _classified(priority="P4", id="t4", matched_rule="label:promo"),
            ],
        )
        groups = result.by_priority
        assert set(groups.keys()) == {"P1", "P3", "P4"}
        assert len(groups["P1"]) == 2
        assert len(groups["P3"]) == 1
        assert len(groups["P4"]) == 1
        assert groups["P1"][0].thread.id == "t1"
        assert groups["P1"][1].thread.id == "t3"

    def test_empty_classified(self):
        result = ClassificationResult(date="2026-02-23", total=0, classified=[])
        assert result.by_priority == {}

    def test_single_priority(self):
        result = ClassificationResult(
            date="2026-02-23",
            total=2,
            classified=[
                _classified(priority="P2", id="t1"),
                _classified(priority="P2", id="t2"),
            ],
        )
        groups = result.by_priority
        assert list(groups.keys()) == ["P2"]
        assert len(groups["P2"]) == 2
