# ABOUTME: Tests for classifier - rule loading, first-match-wins evaluation, state persistence
# ABOUTME: Heaviest test file - covers all classification priority ordering

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
import yaml

from inbox_triage.classifier import (
    classify_all,
    classify_thread,
    load_rules,
    load_state,
    save_state,
)
from inbox_triage.models import GogThread, LabelRule, RuleConfig, SenderRule


def _rules(
    *,
    sender_rules: list[SenderRule] | None = None,
    label_rules: list[LabelRule] | None = None,
    category_rules: dict[str, str] | None = None,
    default_priority: str = "P3",
) -> RuleConfig:
    return RuleConfig(
        account="test@example.com",
        sender_rules=sender_rules or [],
        label_rules=label_rules or [],
        category_rules=category_rules or {},
        default_priority=default_priority,
    )


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


# --- load_rules ---


class TestLoadRules:
    def test_loads_valid_yaml(self, tmp_path: Path):
        data = {
            "account": "max@test.com",
            "sender_rules": [
                {"match": "boss@work.com", "priority": "P1"},
                {"match": "@alerts.com", "priority": "P2"},
            ],
            "label_rules": [
                {"label": "IMPORTANT", "priority": "P1"},
            ],
            "category_rules": {
                "CATEGORY_PROMOTIONS": "P4",
                "CATEGORY_SOCIAL": "P4",
            },
            "default_priority": "P3",
        }
        path = tmp_path / "rules.yaml"
        path.write_text(yaml.dump(data), encoding="utf-8")

        config = load_rules(path)

        assert config.account == "max@test.com"
        assert len(config.sender_rules) == 2
        assert config.sender_rules[0].match == "boss@work.com"
        assert config.sender_rules[0].priority == "P1"
        assert config.sender_rules[1].match == "@alerts.com"
        assert config.sender_rules[1].priority == "P2"
        assert len(config.label_rules) == 1
        assert config.label_rules[0].label == "IMPORTANT"
        assert config.label_rules[0].priority == "P1"
        assert config.category_rules == {"CATEGORY_PROMOTIONS": "P4", "CATEGORY_SOCIAL": "P4"}
        assert config.default_priority == "P3"

    def test_default_priority_uses_default_when_omitted(self, tmp_path: Path):
        data = {
            "account": "a@b.com",
            "sender_rules": [],
            "label_rules": [],
            "category_rules": {},
        }
        path = tmp_path / "rules.yaml"
        path.write_text(yaml.dump(data), encoding="utf-8")

        config = load_rules(path)
        assert config.default_priority == "P3"


# --- classify_thread ---


class TestClassifyThreadSenderExact:
    def test_exact_email_match(self):
        rules = _rules(sender_rules=[SenderRule(match="boss@work.com", priority="P1")])
        thread = _thread(from_="Boss <boss@work.com>")
        result = classify_thread(thread, rules)
        assert result.priority == "P1"
        assert result.matched_rule == "sender:boss@work.com"

    def test_exact_email_match_case_insensitive(self):
        rules = _rules(sender_rules=[SenderRule(match="Boss@Work.COM", priority="P1")])
        thread = _thread(from_="The Boss <boss@work.com>")
        result = classify_thread(thread, rules)
        assert result.priority == "P1"
        assert result.matched_rule == "sender:Boss@Work.COM"


class TestClassifyThreadSenderDomain:
    def test_domain_match(self):
        rules = _rules(sender_rules=[SenderRule(match="@alerts.com", priority="P2")])
        thread = _thread(from_="System <noreply@alerts.com>")
        result = classify_thread(thread, rules)
        assert result.priority == "P2"
        assert result.matched_rule == "sender:@alerts.com"

    def test_domain_match_case_insensitive(self):
        rules = _rules(sender_rules=[SenderRule(match="@Alerts.COM", priority="P2")])
        thread = _thread(from_="System <noreply@alerts.com>")
        result = classify_thread(thread, rules)
        assert result.priority == "P2"
        assert result.matched_rule == "sender:@Alerts.COM"


class TestClassifyThreadLabel:
    def test_label_match(self):
        rules = _rules(label_rules=[LabelRule(label="IMPORTANT", priority="P1")])
        thread = _thread(labels=["INBOX", "IMPORTANT"])
        result = classify_thread(thread, rules)
        assert result.priority == "P1"
        assert result.matched_rule == "label:IMPORTANT"


class TestClassifyThreadCategory:
    def test_category_match(self):
        rules = _rules(category_rules={"CATEGORY_PROMOTIONS": "P4"})
        thread = _thread(labels=["INBOX", "CATEGORY_PROMOTIONS"])
        result = classify_thread(thread, rules)
        assert result.priority == "P4"
        assert result.matched_rule == "category:CATEGORY_PROMOTIONS"


class TestClassifyThreadDefault:
    def test_default_fallback_when_nothing_matches(self):
        rules = _rules(
            sender_rules=[SenderRule(match="other@x.com", priority="P1")],
            label_rules=[LabelRule(label="STARRED", priority="P1")],
            category_rules={"CATEGORY_FORUMS": "P4"},
            default_priority="P3",
        )
        thread = _thread(from_="Unknown <unknown@unknown.com>", labels=["INBOX"])
        result = classify_thread(thread, rules)
        assert result.priority == "P3"
        assert result.matched_rule == "default"


class TestClassifyThreadPriorityOrder:
    """First-match-wins evaluation order: sender exact > sender domain > label > category."""

    def test_sender_exact_beats_domain(self):
        rules = _rules(
            sender_rules=[
                SenderRule(match="boss@work.com", priority="P1"),
                SenderRule(match="@work.com", priority="P3"),
            ]
        )
        thread = _thread(from_="Boss <boss@work.com>")
        result = classify_thread(thread, rules)
        assert result.priority == "P1"
        assert result.matched_rule == "sender:boss@work.com"

    def test_sender_beats_label(self):
        rules = _rules(
            sender_rules=[SenderRule(match="boss@work.com", priority="P1")],
            label_rules=[LabelRule(label="IMPORTANT", priority="P2")],
        )
        thread = _thread(from_="Boss <boss@work.com>", labels=["INBOX", "IMPORTANT"])
        result = classify_thread(thread, rules)
        assert result.priority == "P1"
        assert result.matched_rule == "sender:boss@work.com"

    def test_label_beats_category(self):
        rules = _rules(
            label_rules=[LabelRule(label="IMPORTANT", priority="P1")],
            category_rules={"CATEGORY_PROMOTIONS": "P4"},
        )
        thread = _thread(labels=["INBOX", "IMPORTANT", "CATEGORY_PROMOTIONS"])
        result = classify_thread(thread, rules)
        assert result.priority == "P1"
        assert result.matched_rule == "label:IMPORTANT"


class TestClassifyThreadMatchedRuleFormat:
    def test_sender_exact_format(self):
        rules = _rules(sender_rules=[SenderRule(match="a@b.com", priority="P1")])
        thread = _thread(from_="A <a@b.com>")
        assert classify_thread(thread, rules).matched_rule == "sender:a@b.com"

    def test_sender_domain_format(self):
        rules = _rules(sender_rules=[SenderRule(match="@b.com", priority="P2")])
        thread = _thread(from_="A <a@b.com>")
        assert classify_thread(thread, rules).matched_rule == "sender:@b.com"

    def test_label_format(self):
        rules = _rules(label_rules=[LabelRule(label="STARRED", priority="P1")])
        thread = _thread(labels=["STARRED"])
        assert classify_thread(thread, rules).matched_rule == "label:STARRED"

    def test_category_format(self):
        rules = _rules(category_rules={"CATEGORY_SOCIAL": "P4"})
        thread = _thread(labels=["CATEGORY_SOCIAL"])
        assert classify_thread(thread, rules).matched_rule == "category:CATEGORY_SOCIAL"

    def test_default_format(self):
        rules = _rules()
        thread = _thread()
        assert classify_thread(thread, rules).matched_rule == "default"


# --- classify_all ---


class TestClassifyAll:
    def test_returns_correct_total_count(self):
        rules = _rules(default_priority="P3")
        threads = [_thread(id=f"t{i}") for i in range(5)]
        result = classify_all(threads, rules)
        assert result.total == 5

    def test_date_is_today(self):
        rules = _rules()
        result = classify_all([_thread()], rules)
        assert result.date == date.today().isoformat()

    def test_all_threads_are_classified(self):
        rules = _rules(
            sender_rules=[SenderRule(match="a@b.com", priority="P1")],
            default_priority="P3",
        )
        threads = [
            _thread(id="t1", from_="A <a@b.com>"),
            _thread(id="t2", from_="B <b@c.com>"),
            _thread(id="t3", from_="C <c@d.com>"),
        ]
        result = classify_all(threads, rules)
        assert len(result.classified) == 3
        assert result.classified[0].priority == "P1"
        assert result.classified[0].matched_rule == "sender:a@b.com"
        assert result.classified[1].priority == "P3"
        assert result.classified[1].matched_rule == "default"
        assert result.classified[2].priority == "P3"
        assert result.classified[2].matched_rule == "default"

    def test_empty_list(self):
        rules = _rules()
        result = classify_all([], rules)
        assert result.total == 0
        assert result.classified == []


# --- save_state / load_state ---


class TestStatePersistence:
    def test_round_trip(self, tmp_path: Path):
        rules = _rules(
            sender_rules=[SenderRule(match="a@b.com", priority="P1")],
            label_rules=[LabelRule(label="STARRED", priority="P2")],
            default_priority="P3",
        )
        threads = [
            _thread(id="t1", from_="A <a@b.com>", subject="Urgent"),
            _thread(id="t2", from_="B <b@c.com>", subject="Normal", labels=["INBOX", "STARRED"]),
            _thread(id="t3", from_="C <c@d.com>", subject="Low"),
        ]
        original = classify_all(threads, rules)

        state_path = tmp_path / "state.json"
        save_state(original, state_path)
        loaded = load_state(state_path)

        assert loaded.date == original.date
        assert loaded.total == original.total
        assert len(loaded.classified) == len(original.classified)
        for orig, load in zip(original.classified, loaded.classified):
            assert load.priority == orig.priority
            assert load.matched_rule == orig.matched_rule
            assert load.thread.id == orig.thread.id
            assert load.thread.subject == orig.thread.subject
            assert load.thread.from_ == orig.thread.from_
            assert load.thread.labels == orig.thread.labels

    def test_load_state_raises_for_missing_file(self, tmp_path: Path):
        missing = tmp_path / "does-not-exist.json"
        with pytest.raises(FileNotFoundError, match="State file not found"):
            load_state(missing)
