#!/usr/bin/env python3
# ABOUTME: Offline subprocess tests for scripts/pi-exec (E2E matrix rows 1-6).
# ABOUTME: Stdlib unittest, no network: dry-run happy path, arg validation, key gate, flag pass-through.

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

PI_EXEC = Path(__file__).resolve().parent.parent / "pi-exec"


class PiExecTest(unittest.TestCase):
    """Every case is fully offline: dry-run prints without executing pi, and the
    validation failures (exit 2 / exit 3) return before any pi invocation."""

    def _run(self, args, cwd, scrub_key=False):
        env = os.environ.copy()
        # Deterministic key so the exit-3 gate passes for the dry-run cases,
        # regardless of whether the host env carries a real GEMINI_API_KEY.
        env.setdefault("GEMINI_API_KEY", "test-key-offline")
        if scrub_key:
            env.pop("GEMINI_API_KEY", None)
        return subprocess.run(
            [str(PI_EXEC), *args],
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
        )

    def test_dry_run_happy_path(self):
        # Row 1: exit 0; printed command carries -p, the default model, and @ok.md.
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "ok.md").write_text("brief\n")
            r = self._run(["--brief", "ok.md", "--workdir", ".", "--dry-run"], cwd=d)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("-p", r.stdout)
            self.assertIn("google/gemini-3.6-flash", r.stdout)
            self.assertIn("@ok.md", r.stdout)
            # The EXECUTOR trace marker must never appear in dry-run output.
            self.assertNotIn("EXECUTOR:", r.stdout)

    def test_missing_brief(self):
        # Row 2: exit 2; stderr names the missing brief path.
        with tempfile.TemporaryDirectory() as d:
            r = self._run(["--brief", "absent.md", "--workdir", ".", "--dry-run"], cwd=d)
            self.assertEqual(r.returncode, 2, r.stderr)
            self.assertIn("absent.md", r.stderr)

    def test_missing_api_key(self):
        # Row 3: exit 3 with the key scrubbed, no --dry-run needed, before any pi call.
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "ok.md").write_text("brief\n")
            r = self._run(["--brief", "ok.md", "--workdir", "."], cwd=d, scrub_key=True)
            self.assertEqual(r.returncode, 3, r.stderr)
            self.assertIn("GEMINI_API_KEY", r.stderr)
            self.assertNotIn("EXECUTOR:", r.stdout)

    def test_model_override(self):
        # Row 4: the --model override lands in the printed command.
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "ok.md").write_text("brief\n")
            r = self._run(
                ["--brief", "ok.md", "--workdir", ".", "--model", "google/gemini-3.6-pro", "--dry-run"],
                cwd=d,
            )
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("google/gemini-3.6-pro", r.stdout)

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
        # Row 6: workdir is not a directory -> exit 2.
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "ok.md").write_text("brief\n")
            r = self._run(
                ["--brief", "ok.md", "--workdir", "/nonexistent/nope", "--dry-run"],
                cwd=d,
            )
            self.assertEqual(r.returncode, 2, r.stderr)


if __name__ == "__main__":
    unittest.main()
