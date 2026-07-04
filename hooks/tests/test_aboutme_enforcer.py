#!/usr/bin/env python3
# ABOUTME: Tests for aboutme-enforcer.py — Write deny, Edit advisory, exemptions
# ABOUTME: Run with: uv run --no-project python3 hooks/tests/test_aboutme_enforcer.py

import json
import os
import subprocess
import sys

HOOK = os.path.join(os.path.dirname(__file__), "..", "aboutme-enforcer.py")


def run_hook(event, tool, **tool_input):
    payload = json.dumps({
        "hook_event_name": event, "tool_name": tool, "tool_input": tool_input,
    })
    proc = subprocess.run(
        [sys.executable, HOOK], input=payload, capture_output=True, text=True, timeout=30
    )
    assert proc.returncode == 0, proc.stderr
    out = proc.stdout.strip()
    return json.loads(out) if out else None


def is_deny(result):
    return bool(result) and result.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"


PY_OK = "# ABOUTME: does a thing\n# ABOUTME: in a way\nimport os\nprint(os.name)\n"
PY_BAD = "import os\nimport sys\nprint(os.name, sys.platform)\n"


def main():
    # Write of a non-trivial .py without ABOUTME: deny
    assert is_deny(run_hook("PreToolUse", "Write", file_path="/repo/app/x.py", content=PY_BAD)), "missing-aboutme"
    # With ABOUTME: pass
    assert run_hook("PreToolUse", "Write", file_path="/repo/app/x.py", content=PY_OK) is None, "with-aboutme"
    # Shebang before ABOUTME still passes
    assert run_hook("PreToolUse", "Write", file_path="/repo/x.sh",
                    content="#!/bin/bash\n" + PY_OK) is None, "shebang"
    # Trivial content (<3 non-empty lines): pass
    assert run_hook("PreToolUse", "Write", file_path="/repo/t.py", content="x = 1\n") is None, "trivial"
    # Exempt path: pass
    assert run_hook("PreToolUse", "Write", file_path="/repo/node_modules/a.js", content=PY_BAD) is None, "exempt-path"
    # Uncommentable format (.json): pass
    assert run_hook("PreToolUse", "Write", file_path="/repo/a.json", content='{"a": 1, "b": 2, "c": 3}') is None, "json"
    # Markdown with YAML frontmatter (content doc): pass
    fm_doc = "---\ntitle: x\n---\n\nbody line\nbody line 2\n"
    assert run_hook("PreToolUse", "Write", file_path="/repo/blog/post.md", content=fm_doc) is None, "frontmatter-doc"
    # SKILL.md with frontmatter but no ABOUTME: deny (explicitly required)
    assert is_deny(run_hook("PreToolUse", "Write", file_path="/repo/skills/x/SKILL.md", content=fm_doc)), "skillmd-requires-aboutme"
    # PostToolUse Edit that removes an ABOUTME line: advisory warning
    out = run_hook("PostToolUse", "Edit", file_path="/repo/app/x.py",
                   old_string="# ABOUTME: does a thing", new_string="# does a thing")
    assert out and "ABOUTME" in out["hookSpecificOutput"]["additionalContext"], "edit-advisory"
    # Edit that keeps ABOUTME: silent
    assert run_hook("PostToolUse", "Edit", file_path="/repo/app/x.py",
                    old_string="# ABOUTME: does a thing", new_string="# ABOUTME: does another thing") is None, "edit-ok"
    # Malformed stdin tolerated
    proc = subprocess.run([sys.executable, HOOK], input="not json", capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0 and not proc.stdout.strip()

    print("PASS  aboutme-enforcer (11 cases)")


if __name__ == "__main__":
    main()
