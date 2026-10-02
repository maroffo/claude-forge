#!/usr/bin/env python3
# ABOUTME: Tests for scripts/check_repo.py file collection: what the static checks scan in a checkout.
# ABOUTME: Run with: uv run --no-project python3 scripts/tests/test_check_repo.py

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

CHECK_REPO = Path(__file__).resolve().parent.parent / "check_repo.py"
_spec = importlib.util.spec_from_file_location("check_repo", CHECK_REPO)
check_repo = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check_repo)

SKILL = "---\nname: {name}\ndescription: x\n---\n# ABOUTME: a\n# ABOUTME: b\n"


class CollectMdTest(unittest.TestCase):
    """Every case runs against a throwaway `git init` repo: ~/.claude/skills points at
    the forge checkout, so other tools drop machine-local files into it and the
    checks must only see what belongs to the repo."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)

    def tearDown(self):
        self._tmp.cleanup()

    def _write(self, rel, text="x\n"):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        return p

    def _collected(self):
        return {p.relative_to(self.root).as_posix() for p in check_repo.collect_md(self.root)}

    def test_tracked_files_are_scanned(self):
        self._write("skills/kept/SKILL.md", SKILL.format(name="kept"))
        self._write("README.md")
        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        self.assertEqual(self._collected(), {"skills/kept/SKILL.md", "README.md"})

    def test_extra_files_are_scanned_whatever_their_suffix(self):
        self._write("CLAUDE.md.example")
        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        self.assertEqual(self._collected(), {"CLAUDE.md.example"})

    def test_untracked_files_not_yet_added_are_scanned(self):
        # A skill being written is checked before `git add`, not only at commit time.
        self._write("skills/draft/SKILL.md", SKILL.format(name="draft"))
        self.assertIn("skills/draft/SKILL.md", self._collected())

    def test_gitignored_machine_local_files_are_not_scanned(self):
        self._write(".gitignore", "/skills/synced/\n")
        self._write("skills/synced/abc/docx/SKILL.md", "no frontmatter, no ABOUTME — at all\n")
        self.assertNotIn("skills/synced/abc/docx/SKILL.md", self._collected())

    def test_tracked_file_deleted_from_disk_is_skipped(self):
        p = self._write("rules/gone.md")
        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        p.unlink()
        self.assertEqual(self._collected(), set())

    def test_files_outside_scope_are_not_scanned(self):
        self._write("docs/notes.md")
        self._write("skills/kept/notes.txt")
        self.assertEqual(self._collected(), set())


if __name__ == "__main__":
    unittest.main()
