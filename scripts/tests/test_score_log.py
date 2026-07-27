#!/usr/bin/env python3
# ABOUTME: Subprocess tests for scripts/score-log.sh (E2E matrix rows 8-9): append, trend, gitignore guard.
# ABOUTME: Run with: uv run --no-project python3 scripts/tests/test_score_log.py

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

SCORE_LOG = Path(__file__).resolve().parent.parent / "score-log.sh"
HISTORY_REL = "quality_reports/score-history.jsonl"


class ScoreLogTest(unittest.TestCase):
    """Every case runs against a throwaway `git init` repo, never against a real
    checkout: the script writes to the git root of its current directory."""

    def _run(self, args, cwd):
        return subprocess.run(
            [str(SCORE_LOG), *args], cwd=str(cwd), capture_output=True, text=True, timeout=60
        )

    def _append(self, cwd, score, gate="pr", major=0, minor=0):
        r = self._run(
            ["--score", str(score), "--gate", gate, "--check", "pass",
             "--e2e", "pass", "--major", str(major), "--minor", str(minor)],
            cwd,
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        return r

    def _rows(self, repo):
        text = (repo / HISTORY_REL).read_text(encoding="utf-8")
        self.assertTrue(text.endswith("\n"), "every JSONL row must be newline-terminated")
        return [json.loads(line) for line in text.splitlines()]

    # Row 8 (3*): two sequential appends.

    def test_two_appends_produce_two_valid_rows(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d).resolve()
            subprocess.run(["git", "init", "-b", "feat/demo", str(repo)],
                           capture_output=True, check=True)
            self._append(repo, 88, gate="commit", major=1, minor=2)
            self._append(repo, 92, gate="pr", major=0, minor=1)

            rows = self._rows(repo)
            self.assertEqual(len(rows), 2, rows)
            self.assertEqual([r["score"] for r in rows], [88, 92])
            self.assertEqual([r["gate"] for r in rows], ["commit", "pr"])
            self.assertEqual([r["major"] for r in rows], [1, 0])
            self.assertEqual([r["minor"] for r in rows], [2, 1])
            for row in rows:
                # Types matter: score/major/minor are JSON numbers, not strings, or the
                # trend arithmetic silently degrades to "score field unreadable".
                self.assertIsInstance(row["score"], int)
                self.assertIsInstance(row["major"], int)
                self.assertIsInstance(row["minor"], int)
                self.assertEqual(row["branch"], "feat/demo")
                self.assertEqual(row["check"], "pass")
                self.assertEqual(row["e2e"], "pass")
                self.assertRegex(row["ts"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

    def test_trend_shows_table_and_delta(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d).resolve()
            subprocess.run(["git", "init", "-b", "feat/demo", str(repo)],
                           capture_output=True, check=True)
            self._append(repo, 88, gate="commit")
            self._append(repo, 92)

            r = self._run(["--trend"], repo)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("delta vs previous: +4 (88 -> 92)", r.stdout)
            self.assertIn("2 entries, showing last 2", r.stdout)
            header = [ln for ln in r.stdout.splitlines() if ln.startswith("ts ")]
            self.assertEqual(len(header), 1, r.stdout)
            for column in ("branch", "score", "gate"):
                self.assertIn(column, header[0])
            self.assertIn("feat/demo", r.stdout)

    def test_trend_delta_is_negative_on_regression(self):
        # The whole point of the history is catching a drop between sessions.
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d).resolve()
            subprocess.run(["git", "init", "-b", "feat/demo", str(repo)],
                           capture_output=True, check=True)
            self._append(repo, 95, gate="excellence")
            self._append(repo, 71, gate="commit")
            r = self._run(["--trend"], repo)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("delta vs previous: -24 (95 -> 71)", r.stdout)

    def test_trend_keeps_only_the_last_ten(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d).resolve()
            subprocess.run(["git", "init", "-b", "feat/demo", str(repo)],
                           capture_output=True, check=True)
            for score in range(80, 92):  # 12 entries
                self._append(repo, score)
            r = self._run(["--trend"], repo)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("12 entries, showing last 10", r.stdout)
            self.assertNotIn(" 80 ", r.stdout)  # the two oldest rows are off the tail
            self.assertEqual(len(self._rows(repo)), 12, "trend must not truncate the file")

    def test_gitignore_guard_is_idempotent(self):
        # Second run must be a no-op on .gitignore: byte-identical before and after.
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d).resolve()
            subprocess.run(["git", "init", "-b", "feat/demo", str(repo)],
                           capture_output=True, check=True)
            self._append(repo, 88)
            after_first = (repo / ".gitignore").read_bytes()
            self._append(repo, 92)
            after_second = (repo / ".gitignore").read_bytes()

            self.assertEqual(after_first, after_second, "guard rewrote .gitignore on re-run")
            lines = after_second.decode("utf-8").splitlines()
            self.assertEqual(lines.count(HISTORY_REL), 1, lines)

    def test_gitignore_guard_appends_without_rewriting(self):
        # Edge: a pre-existing .gitignore with no trailing newline. The guard appends,
        # so the last existing line must survive intact rather than absorbing ours.
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d).resolve()
            subprocess.run(["git", "init", "-b", "feat/demo", str(repo)],
                           capture_output=True, check=True)
            (repo / ".gitignore").write_text("node_modules/\n*.log", encoding="utf-8")
            self._append(repo, 88)

            lines = (repo / ".gitignore").read_text(encoding="utf-8").splitlines()
            self.assertEqual(lines[0], "node_modules/")
            self.assertEqual(lines[1], "*.log")
            self.assertEqual(lines.count(HISTORY_REL), 1, lines)

    def test_history_lands_at_git_root_from_a_subdirectory(self):
        # /score is invoked wherever the work is; the history belongs to the repo root.
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d).resolve()
            subprocess.run(["git", "init", "-b", "feat/demo", str(repo)],
                           capture_output=True, check=True)
            sub = repo / "pkg" / "deep"
            sub.mkdir(parents=True)
            self._append(sub, 88)

            self.assertTrue((repo / HISTORY_REL).is_file())
            self.assertFalse((sub / HISTORY_REL).exists())

    def test_corrupt_line_is_skipped_and_reported(self):
        # Falsification condition of the contract is "history file corrupt": the trend
        # must survive it and say so, not crash and not silently drop it.
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d).resolve()
            subprocess.run(["git", "init", "-b", "feat/demo", str(repo)],
                           capture_output=True, check=True)
            self._append(repo, 88)
            with (repo / HISTORY_REL).open("a", encoding="utf-8") as fh:
                fh.write("{not json\n")

            r = self._run(["--trend"], repo)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("skipped 1 unparseable line(s)", r.stdout)
            self.assertIn("1 entries", r.stdout)

    # Row 8 error arm: bad input never reaches the history file.

    def test_invalid_arguments_are_rejected(self):
        cases = [
            (["--score", "101", "--gate", "pr", "--check", "pass",
              "--e2e", "pass", "--major", "0", "--minor", "0"], "--score"),
            (["--score", "ninety", "--gate", "pr", "--check", "pass",
              "--e2e", "pass", "--major", "0", "--minor", "0"], "--score"),
            (["--score", "90", "--gate", "shipit", "--check", "pass",
              "--e2e", "pass", "--major", "0", "--minor", "0"], "--gate"),
            (["--score", "90", "--gate", "pr", "--check", "maybe",
              "--e2e", "pass", "--major", "0", "--minor", "0"], "--check"),
            (["--score", "90", "--gate", "pr", "--check", "pass",
              "--e2e", "maybe", "--major", "0", "--minor", "0"], "--e2e"),
            (["--score", "90", "--gate", "pr", "--check", "pass",
              "--e2e", "pass", "--major", "-1", "--minor", "0"], "--major"),
            (["--score", "90", "--gate", "pr"], "requires"),
            (["--score"], "requires a value"),
            (["--bogus"], "unknown argument"),
        ]
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d).resolve()
            subprocess.run(["git", "init", "-b", "feat/demo", str(repo)],
                           capture_output=True, check=True)
            for args, expected in cases:
                with self.subTest(args=args):
                    r = self._run(args, repo)
                    self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
                    self.assertIn(expected, r.stderr)
            self.assertFalse((repo / HISTORY_REL).exists(), "a rejected run must write nothing")

    def test_outside_a_git_repo_is_an_error(self):
        with tempfile.TemporaryDirectory() as d:
            # A bare temp dir under a non-repo parent: git finds no work tree here.
            r = self._run(["--trend"], Path(d).resolve())
            self.assertEqual(r.returncode, 2, r.stdout)
            self.assertIn("not inside a git repository", r.stderr)

    # Row 9 (2*): bootstrap, no history yet.

    def test_trend_without_history_says_so_and_exits_zero(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d).resolve()
            subprocess.run(["git", "init", "-b", "feat/demo", str(repo)],
                           capture_output=True, check=True)
            r = self._run(["--trend"], repo)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("no history yet", r.stdout)
            # A read-only query creates nothing, not even the directory.
            self.assertFalse((repo / "quality_reports").exists())
            self.assertFalse((repo / ".gitignore").exists())


if __name__ == "__main__":
    unittest.main()
