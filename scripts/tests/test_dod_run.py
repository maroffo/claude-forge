#!/usr/bin/env python3
# ABOUTME: Subprocess tests for scripts/dod_run.py: table parsing, auto/manual split, exit codes, results file
# ABOUTME: Run with: uv run --no-project python3 scripts/tests/test_dod_run.py

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

DOD_RUN = Path(__file__).resolve().parent.parent / "dod_run.py"

HEADER = "| # | Criterion | Command | Expected | Auto |\n|---|---|---|---|---|\n"


def plan_with(rows):
    return "# Plan\n\n## DoD\n\ntext before the table\n\n" + HEADER + rows + "\n## Next section\n"


class DodRunTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.evidence = self.root / "evidence"
        self.evidence.mkdir()
        self.addCleanup(self.tmp.cleanup)

    ALLOW = ("--allow", "true", "--allow", "false", "--allow", "test ", "--allow", "sleep ")

    def _run(self, plan_text, extra=(), allow=None):
        plan = self.root / "plan.md"
        plan.write_text(plan_text, encoding="utf-8")
        allow_flags = self.ALLOW if allow is None else allow
        return subprocess.run(
            [sys.executable, str(DOD_RUN), "--plan", str(plan),
             "--evidence-dir", str(self.evidence), "--repo", str(self.root),
             *allow_flags, *extra],
            capture_output=True, text=True, timeout=120,
        )

    def _results(self):
        return json.loads((self.evidence / "dod-results.json").read_text(encoding="utf-8"))

    def test_all_auto_pass_exits_zero_and_writes_results(self):
        r = self._run(plan_with(
            "| 1 | true passes | `true` | exit 0 | yes |\n"
            "| 2 | manual row | — | human judgment | no |\n"
        ))
        self.assertEqual(r.returncode, 0, r.stderr)
        out = self._results()
        self.assertTrue(out["overall_pass"])
        self.assertEqual(out["auto_rows"], 1)
        self.assertEqual(out["manual_rows"], 1)
        self.assertTrue(out["rows"][0]["passed"])
        self.assertIsNone(out["rows"][1]["passed"], "manual rows are never executed")
        self.assertEqual(out["rows"][1]["command"], "")

    def test_failing_auto_row_exits_one_but_still_writes_results(self):
        r = self._run(plan_with(
            "| 1 | passes | `true` | exit 0 | yes |\n"
            "| 2 | fails | `false` | exit 0 | yes |\n"
        ))
        self.assertEqual(r.returncode, 1)
        out = self._results()
        self.assertFalse(out["overall_pass"])
        self.assertTrue(out["rows"][0]["passed"])
        self.assertFalse(out["rows"][1]["passed"])
        self.assertEqual(out["rows"][1]["exit_code"], 1)

    def test_auto_row_without_command_is_a_failure_not_a_pass(self):
        r = self._run(plan_with("| 1 | claims to be auto | — | something | yes |\n"))
        self.assertEqual(r.returncode, 1)
        out = self._results()
        self.assertFalse(out["overall_pass"])
        self.assertFalse(out["rows"][0]["passed"])

    def test_command_runs_in_repo_cwd(self):
        (self.root / "marker.txt").write_text("x", encoding="utf-8")
        r = self._run(plan_with("| 1 | sees repo files | `test -f marker.txt` | exit 0 | yes |\n"))
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_missing_dod_section_exits_two_without_results(self):
        r = self._run("# Plan\n\nno dod here\n")
        self.assertEqual(r.returncode, 2)
        self.assertIn("no '## DoD' section", r.stderr)
        self.assertFalse((self.evidence / "dod-results.json").exists())

    def test_wrong_header_exits_two(self):
        r = self._run("## DoD\n\n| A | B |\n|---|---|\n| 1 | 2 |\n")
        self.assertEqual(r.returncode, 2)
        self.assertIn("header", r.stderr)

    def test_non_allowlisted_command_fails_without_executing(self):
        marker = self.root / "should-not-exist.txt"
        r = self._run(
            plan_with(f"| 1 | injected | `touch {marker}` | exit 0 | yes |\n"),
            allow=(),
        )
        self.assertEqual(r.returncode, 1)
        self.assertFalse(marker.exists(), "non-allowlisted command must never execute")
        out = self._results()
        self.assertFalse(out["rows"][0]["passed"])
        self.assertIn("allowlist", out["rows"][0]["output_tail"])

    def test_allow_flag_extends_the_allowlist(self):
        r = self._run(plan_with("| 1 | ok | `true` | exit 0 | yes |\n"), allow=("--allow", "true"))
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_escaped_pipe_in_command_cell(self):
        r = self._run(
            plan_with("| 1 | piped | `true \\| sort` | exit 0 | yes |\n"),
            allow=("--allow", "true"),
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        out = self._results()
        self.assertEqual(out["rows"][0]["command"], "true | sort")

    def test_missing_evidence_dir_exits_two(self):
        plan = self.root / "plan.md"
        plan.write_text(plan_with("| 1 | x | `true` | exit 0 | yes |\n"), encoding="utf-8")
        r = subprocess.run(
            [sys.executable, str(DOD_RUN), "--plan", str(plan),
             "--evidence-dir", str(self.root / "absent"), "--repo", str(self.root)],
            capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(r.returncode, 2)

    def test_timeout_reds_the_row(self):
        r = self._run(
            plan_with("| 1 | hangs | `sleep 5` | exit 0 | yes |\n"), extra=("--timeout", "1"),
        )
        self.assertEqual(r.returncode, 1)
        out = self._results()
        self.assertFalse(out["rows"][0]["passed"])
        self.assertIn("timeout", out["rows"][0]["output_tail"])

    def test_table_stops_at_next_section(self):
        r = self._run(plan_with("| 1 | ok | `true` | exit 0 | yes |\n")
                      + "\n| stray | table | not | dod | rows |\n")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(len(self._results()["rows"]), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
