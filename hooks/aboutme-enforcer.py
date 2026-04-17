#!/usr/bin/env python3
# ABOUTME: Enforces 2-line ABOUTME header on new source files (Write=block, Edit=advisory)
# ABOUTME: Exempts lock files, vendored/generated paths, and uncommentable formats

import sys
import os
import json

EXEMPT_PATH_SUBSTRINGS = (
    "/.git/", "/node_modules/", "/vendor/", "/dist/", "/build/",
    "/.venv/", "/__pycache__/", "/.next/", "/target/", "/out/",
    "/migrations/", "/testdata/", "/fixtures/",
    "/.ruff_cache/", "/.pytest_cache/", "/.mypy_cache/", "/.cache/",
    "/coverage/", "/.terraform/",
    # Memory files use YAML frontmatter as their header convention, not ABOUTME
    "/.claude/projects/", "/memory/",
)
EXEMPT_BASENAMES = {
    "package-lock.json", "Cargo.lock", "Gemfile.lock", "uv.lock",
    "poetry.lock", "composer.lock", "yarn.lock", "pnpm-lock.yaml",
    "bun.lockb", "go.sum", "pdm.lock", ".gitignore", ".gitattributes",
    ".DS_Store",
}
EXEMPT_EXTS = {
    ".json", ".lock", ".sum", ".pid", ".log", ".xml", ".plist",
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".pdf",
    ".zip", ".tar", ".gz", ".tgz", ".bz2", ".7z",
    ".ico", ".woff", ".woff2", ".ttf", ".eot",
    ".html", ".css", ".scss",
    ".sql",
}

HASH_EXTS = {
    ".md", ".sh", ".bash", ".zsh", ".py", ".rb", ".yaml", ".yml",
    ".toml", ".conf", ".ini", ".cfg", ".tf", ".tfvars", ".r", ".R",
    ".pl", ".pm", ".mk",
}
SLASH_EXTS = {
    ".js", ".ts", ".tsx", ".jsx", ".mjs", ".cjs",
    ".go", ".swift", ".kt", ".kts", ".rs",
    ".c", ".cpp", ".cc", ".h", ".hpp", ".hh",
    ".java", ".scala", ".groovy", ".dart", ".cs", ".m", ".mm",
    ".proto", ".fbs",
}
HASH_BASENAMES = {
    "Makefile", "Dockerfile", "Rakefile", "Gemfile",
    "Brewfile", "Procfile", "Vagrantfile", "Jenkinsfile",
}


def comment_prefix(path):
    base = os.path.basename(path)
    if base in HASH_BASENAMES:
        return "#"
    ext = os.path.splitext(base)[1].lower()
    if ext in HASH_EXTS:
        return "#"
    if ext in SLASH_EXTS:
        return "//"
    return None


def is_exempt(path):
    norm = "/" + path.lstrip("/")
    if any(sub in norm for sub in EXEMPT_PATH_SUBSTRINGS):
        return True
    base = os.path.basename(path)
    if base in EXEMPT_BASENAMES:
        return True
    ext = os.path.splitext(base)[1].lower()
    if ext in EXEMPT_EXTS:
        return True
    return False


def has_aboutme(text, prefix):
    if not prefix:
        return False
    lines = text.splitlines()
    if lines and lines[0].startswith("#!"):
        lines = lines[1:]
    if lines and lines[0].strip() == "---":
        for i, l in enumerate(lines[1:], 1):
            if l.strip() == "---":
                lines = lines[i + 1:]
                break
    head = [l for l in lines[:10] if l.strip()][:2]
    if len(head) < 2:
        return False
    marker = prefix + " ABOUTME:"
    return all(l.startswith(marker) for l in head)


def content_is_trivial(text):
    return len([l for l in text.splitlines() if l.strip()]) < 3


def main():
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        sys.exit(0)

    tool = payload.get("tool_name", "")
    event = payload.get("hook_event_name", "")
    tool_input = payload.get("tool_input", {}) or {}
    path = tool_input.get("file_path", "")

    if not path or is_exempt(path):
        sys.exit(0)

    prefix = comment_prefix(path)
    if prefix is None:
        sys.exit(0)

    if event == "PreToolUse" and tool == "Write":
        content = tool_input.get("content", "") or ""
        if content_is_trivial(content):
            sys.exit(0)
        if not has_aboutme(content, prefix):
            reason = (
                "ABOUTME header missing. Non-trivial source files must start "
                "with 2 lines: `" + prefix + " ABOUTME: <summary 1>` and `"
                + prefix + " ABOUTME: <summary 2>`. Place them after any "
                "shebang or YAML frontmatter."
            )
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason
                }
            }))
        sys.exit(0)

    if event == "PostToolUse" and tool == "Edit":
        old = tool_input.get("old_string", "") or ""
        new = tool_input.get("new_string", "") or ""
        marker = prefix + " ABOUTME:"
        if marker in old and marker not in new:
            msg = (
                "Warning: this edit removed the ABOUTME header from " + path
                + ". Restore 2 `" + prefix + " ABOUTME:` lines at the top."
            )
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": msg
                }
            }))
        sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
