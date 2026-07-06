#!/usr/bin/env python3
# ABOUTME: SessionStart hook — regenerates an ephemeral, out-of-tree code map for the current repo
# ABOUTME: Fresh against the working tree, cached on tree state; injects the map body. Never writes into the repo.

"""Ephemeral orientation map. Supersedes the committed-artifact design
(codemap-freshness + codemap-regen): a committed generated map is stale the
moment anyone edits without committing, which is the whole duration of a
session. This regenerates against the working tree at SessionStart, stores the
map outside the repo, and injects the map body into context. Fresh by
construction for the session; no VCS churn, no stale-stamp advisory, no
per-Bash regen.

Generation is cached on (HEAD, `git status --porcelain`) so an unchanged tree
reuses the last map instead of re-scanning: deterministic input, so the cache
is not the stamp-trust that sank the committed design. The map body (already
token-capped by the generator) is injected directly rather than pointed at, so
a lazy agent cannot skip reading it. Fail-open: any error exits 0, no output."""

import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys

GENERATOR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "codemap", "generate.py")


def out_dir():
    return os.environ.get("CLAUDE_FORGE_CODEMAP_DIR") or os.path.expanduser("~/.claude-forge/codemaps")


def slug(path):
    """Human-readable prefix plus an abspath hash: two distinct paths can share
    the sanitized prefix (foo-bar vs foo/bar) but never the hash, so one repo's
    map can never silently overwrite another's."""
    ap = os.path.abspath(path)
    prefix = re.sub(r"[^A-Za-z0-9]+", "-", ap).strip("-")[-80:].lstrip("-")
    return f"{prefix}-{hashlib.sha1(ap.encode()).hexdigest()[:8]}"


def load_generator():
    spec = importlib.util.spec_from_file_location("codemap_generate", GENERATOR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def is_git_repo(path):
    try:
        r = subprocess.run(
            ["git", "-C", path, "rev-parse", "--is-inside-work-tree"],
            capture_output=True, text=True, timeout=10,
        )
        return r.returncode == 0 and r.stdout.strip() == "true"
    except OSError:
        return False


def tree_key(repo):
    """Hash of (HEAD, working-tree status). Same tree -> same key -> cache hit."""
    try:
        head = subprocess.run(["git", "-C", repo, "rev-parse", "HEAD"], capture_output=True, text=True, timeout=10)
        status = subprocess.run(["git", "-C", repo, "status", "--porcelain"], capture_output=True, text=True, timeout=15)
    except OSError:
        return None
    if head.returncode != 0 or status.returncode != 0:
        return None
    return hashlib.sha256((head.stdout + "\0" + status.stdout).encode()).hexdigest()[:16]


def counts(md):
    """Section -> count of '- ' bullet lines, for the injected headline."""
    out, section = {}, None
    for line in md.splitlines():
        if line.startswith("## "):
            section = line[3:].split(" (")[0].strip()
            out[section] = 0
        elif section and line.startswith("- "):
            out[section] += 1
    return out


def _atomic_write(path, text):
    tmp = f"{path}.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.replace(tmp, path)  # atomic on POSIX: concurrent sessions never read a half-written map


def main():
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        sys.exit(0)

    repo = payload.get("cwd") or os.getcwd()
    if not os.path.isdir(repo) or not is_git_repo(repo) or not os.path.isfile(GENERATOR):
        sys.exit(0)

    try:
        d = out_dir()
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, slug(repo) + ".md")
        key_path = path + ".key"

        key = tree_key(repo)
        md = None
        if key and os.path.isfile(path) and os.path.isfile(key_path):
            if open(key_path, encoding="utf-8").read().strip() == key:
                md = open(path, encoding="utf-8").read()  # cache hit: unchanged tree, skip the scan

        if md is None:
            g = load_generator()
            if not (g.detect_stacks(repo) & (set(g.STACK_RULES) | {"proto", "next", "workspace"})):
                sys.exit(0)  # nothing worth mapping
            md = g.generate(repo)
            if not counts(md):
                sys.exit(0)
            _atomic_write(path, md)
            if key:
                _atomic_write(key_path, key)
    except Exception:
        sys.exit(0)  # fail-open: a map is a nice-to-have, never hang or break a session

    body_sections = counts(md)
    if not body_sections:
        sys.exit(0)

    headline = ", ".join(f"{n} {name.lower()}" for name, n in body_sections.items() if n)
    # Inject the body, not a pointer: at ~1.2k tokens it is cheap, and a pointer
    # a lazy agent may skip defeats the purpose. Self-labels as a snapshot and
    # delegates live facts to the LSP.
    print(
        f"Repo orientation map ({headline}), generated fresh against the working tree at session "
        f"start. Use it to orient before complex work; for live symbol navigation use the LSP tools, "
        f"not this snapshot (it can drift as you edit).\n\n{md.strip()}"
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
