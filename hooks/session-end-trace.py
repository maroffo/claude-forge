#!/usr/bin/env python3
# ABOUTME: SessionEnd hook that auto-extracts trace JSONL via harness-trace skill
# ABOUTME: No-op outside claude-forge cwd. Fail-silent, never blocks session termination.

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

CLAUDE_FORGE = Path.home() / "Development" / "private" / "claude-forge"
TRACE_DIR_REL = "quality_reports/traces"
SKILL_DIR_REL = "skills/harness-trace"


def _read_payload() -> dict:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def _is_claude_forge(cwd: str | None) -> bool:
    if not cwd:
        return False
    try:
        return Path(cwd).resolve() == CLAUDE_FORGE.resolve()
    except OSError:
        return False


def main() -> int:
    payload = _read_payload()
    cwd = payload.get("cwd")
    transcript = payload.get("transcript_path")
    session_id = payload.get("session_id") or ""

    if not _is_claude_forge(cwd):
        return 0
    if not transcript or not Path(transcript).is_file():
        return 0

    skill_dir = CLAUDE_FORGE / SKILL_DIR_REL
    output_dir = CLAUDE_FORGE / TRACE_DIR_REL
    output_dir.mkdir(parents=True, exist_ok=True)

    slug = session_id[:12] if session_id else Path(transcript).stem[:12]

    cmd = [
        "uv", "run", "--project", str(skill_dir), "--",
        "harness-trace", "extract",
        transcript,
        "--slug", slug,
        "--output", str(output_dir),
    ]

    try:
        subprocess.run(
            cmd,
            cwd=str(skill_dir),
            timeout=8,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
    except (subprocess.TimeoutExpired, OSError):
        pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
