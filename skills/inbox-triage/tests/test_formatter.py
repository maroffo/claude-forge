# ABOUTME: Tests for formatter.py - markdown output and archive command generation
# ABOUTME: Covers sender display, summary format, P4 grouping, archive commands

from __future__ import annotations

from inbox_triage.formatter import (
    DEFAULT_ACCOUNT,
    _sender_display,
    format_archive_commands,
    format_summary,
)
from inbox_triage.models import ClassificationResult, ClassifiedThread, GogThread


def _thread(
    *,
    id: str = "t1",
    from_: str = "Alice <alice@example.com>",
    subject: str = "Hello",
    labels: list[str] | None = None,
) -> GogThread:
    return GogThread(
        id=id,
        date="2026-02-23",
        subject=subject,
        labels=labels if labels is not None else ["INBOX"],
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


# --- _sender_display ---


class TestSenderDisplay:
    def test_name_and_email(self):
        assert _sender_display("Alice Smith <alice@example.com>") == "Alice Smith"

    def test_quoted_name(self):
        assert _sender_display('"Bob Jones" <bob@example.com>') == "Bob Jones"

    def test_bare_email(self):
        assert _sender_display("noreply@example.com") == "noreply@example.com"

    def test_email_in_angle_brackets_no_name(self):
        # Edge case: " <email>" with no name portion should return email
        assert _sender_display("<noreply@example.com>") == "<noreply@example.com>"

    def test_whitespace_trimmed(self):
        assert _sender_display("  Alice <alice@example.com>  ") == "Alice"

    def test_name_with_dots(self):
        assert _sender_display("Dr. Alice Smith <alice@example.com>") == "Dr. Alice Smith"


# --- format_summary ---


class TestFormatSummary:
    def test_header_and_total(self):
        result = ClassificationResult(date="2026-02-23", total=5, classified=[])
        md = format_summary(result)
        assert "## Inbox Triage - 2026-02-23" in md
        assert "**Total:** 5 threads" in md

    def test_p1_section(self):
        result = ClassificationResult(
            date="2026-02-23",
            total=1,
            classified=[
                _classified(priority="P1", from_="Boss <boss@work.com>", subject="URGENT"),
            ],
        )
        md = format_summary(result)
        assert "### P1 - Urgent (1)" in md
        assert "- [ ] **Boss** - URGENT" in md

    def test_p2_section(self):
        result = ClassificationResult(
            date="2026-02-23",
            total=1,
            classified=[
                _classified(priority="P2", from_="Team <team@work.com>", subject="Review needed")
            ],
        )
        md = format_summary(result)
        assert "### P2 - Important (1)" in md
        assert "- [ ] **Team** - Review needed" in md

    def test_p3_checkbox_format(self):
        result = ClassificationResult(
            date="2026-02-23",
            total=2,
            classified=[
                _classified(priority="P3", from_="Alice <a@b.com>", subject="Meeting notes"),
                _classified(
                    priority="P3", id="t2", from_="Bob <b@b.com>", subject="Quick question"
                ),
            ],
        )
        md = format_summary(result)
        assert "### P3 - Normal (2)" in md
        assert "- [ ] **Alice** - Meeting notes" in md
        assert "- [ ] **Bob** - Quick question" in md

    def test_p4_compact_grouped(self):
        result = ClassificationResult(
            date="2026-02-23",
            total=5,
            classified=[
                _classified(priority="P4", id="t1", matched_rule="category:CATEGORY_PROMOTIONS"),
                _classified(priority="P4", id="t2", matched_rule="category:CATEGORY_PROMOTIONS"),
                _classified(priority="P4", id="t3", matched_rule="category:CATEGORY_PROMOTIONS"),
                _classified(priority="P4", id="t4", matched_rule="sender:@aliexpress.com"),
                _classified(priority="P4", id="t5", matched_rule="sender:@aliexpress.com"),
            ],
        )
        md = format_summary(result)
        assert "### P4 - Low Priority (5)" in md
        assert "- category:CATEGORY_PROMOTIONS: 3" in md
        assert "- sender:@aliexpress.com: 2" in md
        # P4 should NOT have checkbox lines
        assert "- [ ]" not in md

    def test_empty_priorities_omitted(self):
        result = ClassificationResult(
            date="2026-02-23",
            total=1,
            classified=[_classified(priority="P1")],
        )
        md = format_summary(result)
        assert "P2" not in md
        assert "P3" not in md
        assert "P4" not in md

    def test_archive_commands_in_footer(self):
        result = ClassificationResult(
            date="2026-02-23",
            total=3,
            classified=[
                _classified(priority="P3", id="t1"),
                _classified(priority="P4", id="t2", matched_rule="label:promo"),
                _classified(priority="P4", id="t3", matched_rule="label:promo"),
            ],
        )
        md = format_summary(result)
        assert "### Actions" in md
        assert "Archive P3" in md
        assert "(1 threads)" in md
        assert "Archive P4" in md
        assert "(2 threads)" in md
        assert "-- inbox-triage archive p3 --yes" in md
        assert "-- inbox-triage archive p4 --yes" in md

    def test_no_actions_when_no_p3_p4(self):
        result = ClassificationResult(
            date="2026-02-23",
            total=1,
            classified=[_classified(priority="P1")],
        )
        md = format_summary(result)
        assert "### Actions" not in md

    def test_full_output_ordering(self):
        """Sections appear in P1, P2, P3, P4 order."""
        result = ClassificationResult(
            date="2026-02-23",
            total=4,
            classified=[
                _classified(priority="P3", id="t1"),
                _classified(priority="P1", id="t2"),
                _classified(priority="P4", id="t3", matched_rule="label:x"),
                _classified(priority="P2", id="t4"),
            ],
        )
        md = format_summary(result)
        p1_pos = md.index("### P1")
        p2_pos = md.index("### P2")
        p3_pos = md.index("### P3")
        p4_pos = md.index("### P4")
        assert p1_pos < p2_pos < p3_pos < p4_pos

    def test_bare_email_sender_in_output(self):
        result = ClassificationResult(
            date="2026-02-23",
            total=1,
            classified=[
                _classified(priority="P2", from_="noreply@shop.com", subject="Your order")
            ],
        )
        md = format_summary(result)
        assert "- [ ] **noreply@shop.com** - Your order" in md


# --- format_archive_commands ---


class TestFormatArchiveCommands:
    def test_single_priority(self):
        result = ClassificationResult(
            date="2026-02-23",
            total=2,
            classified=[
                _classified(priority="P4", id="abc123", matched_rule="label:x"),
                _classified(priority="P4", id="def456", matched_rule="label:y"),
            ],
        )
        cmds = format_archive_commands(result, ["P4"])
        assert len(cmds) == 2
        assert cmds[0][0] == "abc123"
        assert "gog gmail thread modify abc123" in cmds[0][1]
        assert f"--account={DEFAULT_ACCOUNT}" in cmds[0][1]
        assert "--remove=INBOX,UNREAD" in cmds[0][1]
        assert cmds[1][0] == "def456"

    def test_multiple_priorities(self):
        result = ClassificationResult(
            date="2026-02-23",
            total=3,
            classified=[
                _classified(priority="P3", id="t1"),
                _classified(priority="P4", id="t2", matched_rule="label:x"),
                _classified(priority="P4", id="t3", matched_rule="label:y"),
            ],
        )
        cmds = format_archive_commands(result, ["P3", "P4"])
        assert len(cmds) == 3
        thread_ids = [tid for tid, _ in cmds]
        assert thread_ids == ["t1", "t2", "t3"]

    def test_empty_priority(self):
        result = ClassificationResult(date="2026-02-23", total=0, classified=[])
        cmds = format_archive_commands(result, ["P4"])
        assert cmds == []

    def test_ignores_other_priorities(self):
        result = ClassificationResult(
            date="2026-02-23",
            total=2,
            classified=[
                _classified(priority="P1", id="t1"),
                _classified(priority="P4", id="t2", matched_rule="label:x"),
            ],
        )
        cmds = format_archive_commands(result, ["P4"])
        assert len(cmds) == 1
        assert cmds[0][0] == "t2"
