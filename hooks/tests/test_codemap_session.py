#!/usr/bin/env python3
# ABOUTME: Tests for codemap-session.py — SessionStart nudge advertising the `codemap` command
# ABOUTME: Run with: uv run --no-project python3 hooks/tests/test_codemap_session.py (needs sg + uv)

import json
import os
import shutil
import subprocess
import sys
import tempfile

HOOK = os.path.join(os.path.dirname(__file__), "..", "codemap-session.py")


def git(repo, *args):
    subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True, text=True)


def make_repo(files):
    d = tempfile.mkdtemp(prefix="codemap-session-")
    git(d, "init", "-q")
    git(d, "config", "user.email", "t@t")
    git(d, "config", "user.name", "t")
    for name, content in files.items():
        full = os.path.join(d, name)
        os.makedirs(os.path.dirname(full), exist_ok=True) if os.path.dirname(name) else None
        with open(full, "w") as fh:
            fh.write(content)
    git(d, "add", "."); git(d, "commit", "-qm", "seed")
    return d


def run_hook(cwd):
    payload = json.dumps({"hook_event_name": "SessionStart", "cwd": cwd})
    proc = subprocess.run([sys.executable, HOOK], input=payload, capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.strip()


def main():
    if not shutil.which("sg"):
        sys.exit("FAIL  codemap-session: ast-grep (sg) required on PATH")

    # 1. Go repo -> nudge names `codemap`, is imperative, mentions the stack; writes NO file
    go = make_repo({"main.go": 'package main\n\nfunc r(x Router){ x.Get("/p", h) }\n'})
    out = run_hook(go)
    assert "codemap" in out, f"nudge must name the codemap command: {out!r}"
    assert "Go" in out, f"nudge should carry the free structural summary: {out!r}"
    assert "/p" not in out, "nudge must NOT contain generated endpoints (that needs a scan)"
    assert not os.path.exists(os.path.join(go, "CODEMAP.md")), "nudge hook must not write any file"

    # 2. pnpm monorepo -> nudge reports the free workspace count
    mono = make_repo({
        "pnpm-workspace.yaml": "packages:\n  - services/*\n",
        "services/api/package.json": '{"name":"@x/api"}\n',
        "services/api/index.ts": "import {Hono} from 'hono'\nconst a=new Hono()\na.get('/h',c=>c.json({}))\n",
        "package.json": '{"name":"root","dependencies":{"hono":"1"}}\n',
    })
    out = run_hook(mono)
    assert "codemap" in out and "1 pnpm workspace" in out, f"monorepo nudge missing workspace count: {out!r}"

    # 3. Docs-only repo -> silent (no mappable stack)
    docs = make_repo({"README.md": "# docs\n"})
    assert run_hook(docs) == "", "docs-only repo must be silent"

    # 4. Non-git dir -> silent
    empty = tempfile.mkdtemp(prefix="codemap-nogit-")
    assert run_hook(empty) == "", "non-git dir must be silent"

    # 5. Garbage payload -> exit 0, silent
    proc = subprocess.run([sys.executable, HOOK], input="not json", capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0 and not proc.stdout.strip()

    print("PASS  codemap-session (5 cases)")


if __name__ == "__main__":
    main()
