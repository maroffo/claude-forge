#!/usr/bin/env python3
# ABOUTME: PostToolUse hook that nudges Claude to invoke review agents matching the files touched
# ABOUTME: Dedup per-session via state file; emits additionalContext once per new reviewer required

import json
import os
import sys
import fnmatch
from pathlib import Path

STATE_DIR = Path.home() / ".claude" / "tmp"

# Routing rules: (patterns, agents). First match wins per pattern group.
ROUTES = [
    (["go.mod", "go.sum", "Gemfile", "Gemfile.lock", "package.json", "package-lock.json",
      "pnpm-lock.yaml", "yarn.lock", "pyproject.toml", "uv.lock", "Cargo.toml", "Cargo.lock",
      "requirements.txt"],
     ["dependency-reviewer"]),
    (["migrations/**", "db/migrate/**", "schema.rb", "*.sql"],
     ["database-reviewer"]),
    (["*_test.go", "*_test.py", "*_spec.rb", "*.test.ts", "*.test.tsx", "*.test.js",
      "**/tests/**", "**/spec/**", "**/__tests__/**"],
     ["test-reviewer", "test-design-reviewer"]),
    (["*.go", "*.py", "*.rb", "*.ts", "*.tsx", "*.js", "*.jsx", "*.kt", "*.kts",
      "*.swift", "*.rs", "*.java", "*.scala"],
     ["architecture-reviewer", "security-reviewer"]),
    (["**/*.md", "README*", "CHANGELOG*", "docs/**"],
     ["dx-reviewer"]),
]

REVIEWER_NAMES = {
    "dependency-reviewer", "database-reviewer", "test-reviewer", "test-design-reviewer",
    "architecture-reviewer", "security-reviewer", "performance-reviewer", "dx-reviewer",
}


def matches(path, patterns):
    base = os.path.basename(path)
    for pat in patterns:
        if "**" in pat:
            prefix = pat.split("**")[0].rstrip("/")
            if prefix and prefix in path:
                return True
        elif fnmatch.fnmatch(base, pat) or fnmatch.fnmatch(path, pat):
            return True
    return False


def reviewers_for(paths):
    required = set()
    for path in paths:
        for patterns, agents in ROUTES:
            if matches(path, patterns):
                required.update(agents)
    return required


def state_path(session_id):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    return STATE_DIR / f"routing-{session_id}.json"


def load_state(session_id):
    p = state_path(session_id)
    if p.exists():
        try:
            return json.loads(p.read_text())
        except json.JSONDecodeError:
            pass
    return {"files_touched": [], "reviewers_advised": []}


def save_state(session_id, state):
    state_path(session_id).write_text(json.dumps(state))


def advise(msg):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": msg
        }
    }))


def main():
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        sys.exit(0)

    session_id = payload.get("session_id") or "unknown"
    tool = payload.get("tool_name", "")
    ti = payload.get("tool_input", {}) or {}

    state = load_state(session_id)
    touched = set(state.get("files_touched", []))
    advised = set(state.get("reviewers_advised", []))

    if tool in ("Write", "Edit", "MultiEdit"):
        path = ti.get("file_path", "")
        if path:
            touched.add(path)
    elif tool == "Agent":
        subtype = ti.get("subagent_type", "")
        if subtype in REVIEWER_NAMES:
            advised.add(subtype)
            state["files_touched"] = sorted(touched)
            state["reviewers_advised"] = sorted(advised)
            save_state(session_id, state)
            sys.exit(0)
    else:
        sys.exit(0)

    required = reviewers_for(touched)
    missing = required - advised

    # Persist touched even if nothing to advise (state grows monotonically)
    state["files_touched"] = sorted(touched)
    state["reviewers_advised"] = sorted(advised)
    save_state(session_id, state)

    if missing:
        # Mark as advised so we don't re-nag next time
        state["reviewers_advised"] = sorted(advised | missing)
        save_state(session_id, state)
        matched_files = [p for p in sorted(touched) if any(
            matches(p, patterns) for patterns, agents in ROUTES
            if set(agents) & missing
        )]
        sample = ", ".join(matched_files[:3]) + (" ..." if len(matched_files) > 3 else "")
        reviewers = ", ".join(sorted(missing))
        advise(
            f"Routing advisor: files touched match reviewer routes ({sample}). "
            f"Before VERIFY/SCORE, invoke: {reviewers}. "
            f"(This reminder fires once per reviewer per session.)"
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
