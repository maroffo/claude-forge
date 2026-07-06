#!/usr/bin/env python3
# ABOUTME: Tests for codemap-session.py — SessionStart ephemeral map generation + pointer injection
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


def make_go_repo():
    d = tempfile.mkdtemp(prefix="codemap-session-")
    git(d, "init", "-q")
    git(d, "config", "user.email", "t@t")
    git(d, "config", "user.name", "t")
    with open(os.path.join(d, "main.go"), "w") as fh:
        fh.write('package main\n\nfunc routes(r Router) {\n\tr.Get("/ping", pong)\n\tr.Post("/pong", ping)\n}\n')
    git(d, "add", ".")
    git(d, "commit", "-qm", "seed")
    return d


def run_hook(cwd, out_dir):
    payload = json.dumps({"hook_event_name": "SessionStart", "cwd": cwd})
    env = dict(os.environ, CLAUDE_FORGE_CODEMAP_DIR=out_dir)
    proc = subprocess.run(
        [sys.executable, HOOK], input=payload, capture_output=True, text=True, timeout=120, env=env
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.strip()


def main():
    if not shutil.which("sg"):
        sys.exit("FAIL  codemap-session: ast-grep (sg) required on PATH")

    out_dir = tempfile.mkdtemp(prefix="codemap-out-")

    # 1. Go repo with endpoints -> map body injected (not a thin pointer), written out-of-tree, NOT in repo
    repo = make_go_repo()
    out = run_hook(repo, out_dir)
    assert "/ping" in out and "/pong" in out, "hook must inject the map body, not just a pointer"
    assert "orientation map" in out.lower() and "endpoint" in out.lower(), f"headline missing: {out!r}"
    assert not os.path.exists(os.path.join(repo, "CODEMAP.md")), "must NOT write into the repo (ephemeral, out-of-tree)"
    maps = [f for f in os.listdir(out_dir) if f.endswith(".md")]
    assert maps, "map file not written to the out-of-tree dir"
    body = open(os.path.join(out_dir, maps[0])).read()
    assert "/ping" in body and "/pong" in body, "generated map missing endpoints"

    # 2. Regeneration reflects the CURRENT working tree, not HEAD (uncommitted edit visible)
    with open(os.path.join(repo, "extra.go"), "w") as fh:
        fh.write('package main\n\nfunc more(r Router) {\n\tr.Delete("/gone", h)\n}\n')
    # NOT committed
    run_hook(repo, out_dir)
    body = open(os.path.join(out_dir, maps[0])).read()
    assert "/gone" in body, "ephemeral map must reflect uncommitted working-tree edits"

    # 3. Non-git or empty dir -> silent, no map, no crash
    empty = tempfile.mkdtemp(prefix="codemap-empty-")
    out = run_hook(empty, out_dir)
    assert out == "", f"non-repo dir must be silent, got: {out!r}"

    # 4. Repo with no mappable stacks (docs only) -> silent
    docs = tempfile.mkdtemp(prefix="codemap-docs-")
    git(docs, "init", "-q")
    git(docs, "config", "user.email", "t@t")
    git(docs, "config", "user.name", "t")
    with open(os.path.join(docs, "README.md"), "w") as fh:
        fh.write("# docs\n")
    git(docs, "add", "."); git(docs, "commit", "-qm", "seed")
    out = run_hook(docs, out_dir)
    assert out == "", f"no mappable stack must be silent, got: {out!r}"

    # 5. Garbage payload -> exit 0, silent
    proc = subprocess.run([sys.executable, HOOK], input="not json", capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0 and not proc.stdout.strip()

    # 6. slug() never collides across paths that share a sanitized prefix
    import importlib.util
    spec = importlib.util.spec_from_file_location("cs", HOOK)
    cs = importlib.util.module_from_spec(spec); spec.loader.exec_module(cs)
    assert cs.slug("/home/u/foo-bar") != cs.slug("/home/u/foo/bar"), "slug collision: silent overwrite risk"

    # 7. Cache: an unchanged tree does not rescan (map file mtime unchanged on 2nd run)
    cache_dir = tempfile.mkdtemp(prefix="codemap-cache-")
    repo2 = make_go_repo()
    run_hook(repo2, cache_dir)
    mapf = os.path.join(cache_dir, [f for f in os.listdir(cache_dir) if f.endswith(".md")][0])
    assert os.path.isfile(mapf + ".key"), "cache key sidecar not written"
    mtime1 = os.path.getmtime(mapf)
    run_hook(repo2, cache_dir)  # unchanged tree -> cache hit, no rewrite
    assert os.path.getmtime(mapf) == mtime1, "unchanged tree must hit cache, not regenerate"

    print("PASS  codemap-session (7 cases)")


if __name__ == "__main__":
    main()
