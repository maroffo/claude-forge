#!/usr/bin/env python3
# ABOUTME: SessionStart hook — regenerates an ephemeral, out-of-tree code map for the current repo
# ABOUTME: Fresh against the working tree every session; injects a compact pointer. Never writes into the repo.

"""Ephemeral orientation map. Supersedes the committed-artifact design
(codemap-freshness + codemap-regen): a committed generated map is stale the
moment anyone edits without committing, which is the whole duration of a
session. This regenerates against the working tree at SessionStart, stores the
map outside the repo, and injects a compact pointer. Fresh by construction for
the session; no VCS churn, no stale-stamp advisory, no per-Bash regen.
Fail-open: any error exits 0 with no output."""

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
    return re.sub(r"[^A-Za-z0-9]+", "-", os.path.abspath(path)).strip("-")


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


def counts(md):
    """Section -> count of '- ' bullet lines, for the injected pointer."""
    out, section = {}, None
    for line in md.splitlines():
        if line.startswith("## "):
            section = line[3:].split(" (")[0].strip()
            out[section] = 0
        elif section and line.startswith("- "):
            out[section] += 1
    return out


def main():
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        sys.exit(0)

    repo = payload.get("cwd") or os.getcwd()
    if not os.path.isdir(repo) or not is_git_repo(repo) or not os.path.isfile(GENERATOR):
        sys.exit(0)

    try:
        g = load_generator()
        if not (g.detect_stacks(repo) & (set(g.STACK_RULES) | {"proto", "next", "workspace"})):
            sys.exit(0)  # nothing worth mapping
        md = g.generate(repo)
    except Exception:
        sys.exit(0)

    body_sections = counts(md)
    if not body_sections:
        sys.exit(0)

    try:
        d = out_dir()
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, slug(repo) + ".md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(md)
    except OSError:
        sys.exit(0)

    headline = ", ".join(f"{n} {name.lower()}" for name, n in body_sections.items() if n)
    print(
        f"Code map (fresh, generated against the working tree) for this repo: {headline}. "
        f"Read {path} to orient before complex work; it lists endpoints, routes, and structure. "
        f"For live symbol navigation use the LSP tools, not this snapshot."
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
