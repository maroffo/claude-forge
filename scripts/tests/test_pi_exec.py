#!/usr/bin/env python3
# ABOUTME: Offline subprocess tests for scripts/pi-exec (E2E matrix rows 1-6).
# ABOUTME: Stdlib unittest, no network: dry-run happy path, arg validation, key gate, flag pass-through.

import os
import shlex
import subprocess
import tempfile
import unittest
from pathlib import Path

PI_EXEC = Path(__file__).resolve().parent.parent / "pi-exec"


class PiExecTest(unittest.TestCase):
    """Every case is fully offline: dry-run prints without executing pi, and the
    validation failures (exit 2 / exit 3) return before any pi invocation."""

    def _run(self, args, cwd, scrub_key=False, empty_key=False):
        env = os.environ.copy()
        # Deterministic key so the exit-3 gate passes for the dry-run cases,
        # regardless of whether the host env carries a real GEMINI_API_KEY.
        env.setdefault("GEMINI_API_KEY", "test-key-offline")
        if scrub_key:
            env.pop("GEMINI_API_KEY", None)
        if empty_key:
            env["GEMINI_API_KEY"] = ""
        return subprocess.run(
            [str(PI_EXEC), *args],
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
        )

    def _cmd_tokens(self, stdout):
        """Tokens of the dry-run command line (first line), parsed back through the
        same shell quoting pi-exec emits via printf %q, so token boundaries survive."""
        return shlex.split(stdout.splitlines()[0])

    def test_dry_run_happy_path(self):
        # Row 1: exit 0; printed command carries -p as a standalone token, the default
        # model, and the brief canonicalized to an absolute @<path>.
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "ok.md").write_text("brief\n")
            r = self._run(["--brief", "ok.md", "--workdir", ".", "--dry-run"], cwd=d)
            self.assertEqual(r.returncode, 0, r.stderr)
            tokens = self._cmd_tokens(r.stdout)
            self.assertIn("-p", tokens)
            self.assertIn("google/gemini-3.6-flash", tokens)
            self.assertTrue(
                any(t.startswith("@") and t.endswith("/ok.md") for t in tokens),
                tokens,
            )
            # The EXECUTOR trace marker must never appear in dry-run output.
            self.assertNotIn("EXECUTOR:", r.stdout)

    def test_missing_brief(self):
        # Row 2: exit 2; stderr names the missing brief path.
        with tempfile.TemporaryDirectory() as d:
            r = self._run(["--brief", "absent.md", "--workdir", ".", "--dry-run"], cwd=d)
            self.assertEqual(r.returncode, 2, r.stderr)
            self.assertIn("absent.md", r.stderr)

    def test_missing_api_key(self):
        # Row 3: exit 3 with the key scrubbed. --dry-run keeps this offline because the
        # exit-3 gate fires before the dry-run branch, so a gate regression stays offline.
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "ok.md").write_text("brief\n")
            r = self._run(["--brief", "ok.md", "--workdir", ".", "--dry-run"], cwd=d, scrub_key=True)
            self.assertEqual(r.returncode, 3, r.stderr)
            self.assertIn("GEMINI_API_KEY", r.stderr)
            self.assertNotIn("EXECUTOR:", r.stdout)

    def test_empty_api_key(self):
        # Row 3b: GEMINI_API_KEY present but empty -> exit 3, same gate as unset.
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "ok.md").write_text("brief\n")
            r = self._run(["--brief", "ok.md", "--workdir", ".", "--dry-run"], cwd=d, empty_key=True)
            self.assertEqual(r.returncode, 3, r.stderr)
            self.assertIn("GEMINI_API_KEY", r.stderr)

    def test_model_override(self):
        # Row 4: the --model override replaces the default in the printed command.
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "ok.md").write_text("brief\n")
            r = self._run(
                ["--brief", "ok.md", "--workdir", ".", "--model", "google/gemini-3.6-pro", "--dry-run"],
                cwd=d,
            )
            self.assertEqual(r.returncode, 0, r.stderr)
            tokens = self._cmd_tokens(r.stdout)
            self.assertIn("google/gemini-3.6-pro", tokens)
            # Override replaces, never appends: the default model must be absent.
            self.assertNotIn("google/gemini-3.6-flash", tokens)

    def test_thinking_override(self):
        # Row 5: the --thinking override lands in the printed command.
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "ok.md").write_text("brief\n")
            r = self._run(
                ["--brief", "ok.md", "--workdir", ".", "--thinking", "high", "--dry-run"],
                cwd=d,
            )
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("--thinking high", r.stdout)

    def test_bad_workdir(self):
        # Row 6: workdir is not a directory -> exit 2, and stderr names the bad workdir.
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "ok.md").write_text("brief\n")
            r = self._run(
                ["--brief", "ok.md", "--workdir", "/nonexistent/nope", "--dry-run"],
                cwd=d,
            )
            self.assertEqual(r.returncode, 2, r.stderr)
            self.assertIn("/nonexistent/nope", r.stderr)


if __name__ == "__main__":
    unittest.main()
