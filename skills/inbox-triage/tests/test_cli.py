# ABOUTME: Tests for CLI - classify and archive subcommands
# ABOUTME: Covers stdin parsing, state persistence, archive dry-run and execution

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from inbox_triage.cli import _parse_args, main
from inbox_triage.models import ClassificationResult, ClassifiedThread, GogThread


def _gog_json(threads: list[dict]) -> str:
    """Build a gog search result JSON string."""
    return json.dumps({"threads": threads})


def _thread_dict(
    *,
    id: str = "t1",
    from_: str = "Alice <alice@example.com>",
    subject: str = "Hello",
    labels: list[str] | None = None,
) -> dict:
    return {
        "id": id,
        "date": "2026-02-23",
        "from": from_,
        "subject": subject,
        "labels": labels if labels is not None else ["INBOX", "UNREAD"],
        "messageCount": 1,
    }


def _state_with_threads(tmp_path: Path) -> Path:
    """Create a state file with P3 and P4 threads."""
    threads = [
        ClassifiedThread(
            thread=GogThread(
                id="t1",
                date="2026-02-23",
                subject="Normal email",
                labels=["INBOX"],
                **{"from": "alice@example.com"},
            ),
            priority="P3",
            matched_rule="default",
        ),
        ClassifiedThread(
            thread=GogThread(
                id="t2",
                date="2026-02-23",
                subject="Promo",
                labels=["INBOX", "CATEGORY_PROMOTIONS"],
                **{"from": "shop@store.com"},
            ),
            priority="P4",
            matched_rule="category:CATEGORY_PROMOTIONS",
        ),
    ]
    result = ClassificationResult(date="2026-02-23", total=2, classified=threads)
    state_path = tmp_path / "state.json"
    state_path.write_text(json.dumps(result.model_dump(mode="json"), indent=2))
    return state_path


class TestParseArgs:
    def test_classify_defaults(self):
        args = _parse_args(["classify"])
        assert args.command == "classify"
        assert args.state is None

    def test_classify_with_rules(self, tmp_path):
        rules_path = tmp_path / "rules.yaml"
        rules_path.touch()
        args = _parse_args(["classify", "--rules", str(rules_path)])
        assert args.rules == rules_path

    def test_archive_priorities(self):
        args = _parse_args(["archive", "p3", "p4"])
        assert args.command == "archive"
        assert args.priorities == ["p3", "p4"]
        assert args.yes is False

    def test_archive_with_yes(self):
        args = _parse_args(["archive", "p4", "--yes"])
        assert args.yes is True

    def test_no_command_fails(self):
        with pytest.raises(SystemExit):
            _parse_args([])


class TestClassifyCommand:
    def test_classify_reads_stdin_and_saves_state(self, tmp_path):
        rules_path = tmp_path / "rules.yaml"
        rules_path.write_text(
            "account: test@example.com\n"
            "sender_rules: []\n"
            "label_rules: []\n"
            "category_rules:\n"
            "  CATEGORY_PROMOTIONS: P4\n"
            "default_priority: P3\n"
        )
        state_path = tmp_path / "state.json"
        stdin_data = _gog_json(
            [
                _thread_dict(id="t1", labels=["INBOX", "CATEGORY_PROMOTIONS"]),
                _thread_dict(id="t2"),
            ]
        )

        with patch("sys.stdin") as mock_stdin:
            mock_stdin.read.return_value = stdin_data
            main(["classify", "--rules", str(rules_path), "--state", str(state_path)])

        assert state_path.exists()
        state = json.loads(state_path.read_text())
        assert state["total"] == 2
        assert len(state["classified"]) == 2

    def test_classify_empty_stdin_exits(self, capsys):
        with patch("sys.stdin") as mock_stdin, pytest.raises(SystemExit):
            mock_stdin.read.return_value = ""
            main(["classify"])


class TestArchiveCommand:
    def test_archive_dry_run(self, tmp_path, capsys):
        state_path = _state_with_threads(tmp_path)
        main(["archive", "p4", "--state", str(state_path)])
        captured = capsys.readouterr()
        assert "gog gmail thread modify t2" in captured.out
        assert "Dry run" in captured.out

    def test_archive_no_threads(self, tmp_path, capsys):
        state_path = _state_with_threads(tmp_path)
        main(["archive", "p1", "--state", str(state_path)])
        captured = capsys.readouterr()
        assert "No threads to archive" in captured.out

    def test_archive_uppercase_conversion(self, tmp_path, capsys):
        state_path = _state_with_threads(tmp_path)
        main(["archive", "p3", "--state", str(state_path)])
        captured = capsys.readouterr()
        assert "gog gmail thread modify t1" in captured.out

    def test_archive_missing_state(self, tmp_path):
        missing = tmp_path / "nope.json"
        with pytest.raises(FileNotFoundError):
            main(["archive", "p4", "--state", str(missing)])
