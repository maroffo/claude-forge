#!/usr/bin/env python3
# ABOUTME: Stop hook — blocks ending the turn when source files were edited but no test/check ran afterwards
# ABOUTME: One nudge per turn (stop_hook_active guard); scoped to the current turn, main loop only

import json
import os
import re
import sys

SOURCE_EXTS = {
    ".py", ".rb", ".go", ".rs", ".c", ".cpp", ".cc", ".h", ".hpp",
    ".js", ".ts", ".tsx", ".jsx", ".mjs", ".cjs",
    ".kt", ".kts", ".swift", ".java", ".scala", ".dart", ".cs", ".m", ".mm",
    ".sh", ".bash", ".zsh", ".sql", ".ex", ".exs", ".php",
}
# Superset of aboutme-enforcer's exempt list plus scratch locations; keep in sync.
EXEMPT_PATH_SUBSTRINGS = (
    "/.git/", "/node_modules/", "/vendor/", "/dist/", "/build/",
    "/.venv/", "/__pycache__/", "/.next/", "/target/", "/out/",
    "/scratchpad/", "/tmp/", "/temp/",
    "/.claude/projects/", "/memory/",
)

# Commands that count as verification (test, lint, typecheck, build).
# `git commit` counts: the pre-commit-gate hook runs `make check && make test-e2e` on it.
VERIFY_RE = re.compile(
    r"""(\bgit\s+commit\b) | \b(
    make\s+(check|test|lint|build|e2e)\S*
    | pytest | tox
    | python3?\s+(-m\s+(unittest|pytest)\b|\S*/?tests?/\S+)
    | go\s+(test|vet|build)
    | golangci-lint | staticcheck
    | cargo\s+(test|check|clippy|build)
    | (npm|pnpm|yarn|bun)\s+(run\s+)?(test|lint|check|typecheck|build)
    | vitest | jest | tsc | eslint | biome
    | rspec | rubocop | rails\s+test
    | mix\s+test
    | gradlew?\s+\S*(test|check|build|lint)
    | mvn\s+\S*(test|verify)
    | swift\s+(test|build) | xcodebuild
    | dotnet\s+(test|build) | phpunit
    | ruff | mypy | pyright | flake8
    | shellcheck | hadolint | terraform\s+(validate|plan)
    )\b""",
    re.VERBOSE,
)
# Commands that only mention verification tools without running them.
NON_VERIFY_PREFIXES = ("echo ", "grep ", "cat ", "ls ", "find ", "rg ")

MAX_LINE_BYTES = 1_048_576  # skip pathological transcript lines (base64 blobs)
TAIL_BYTES = 10_485_760  # for huge transcripts, scan only the tail (current turn is at the end)


def is_verify_cmd(command):
    cmd = (command or "").lstrip()[:10_000]
    if cmd.startswith(NON_VERIFY_PREFIXES):
        return False
    return bool(VERIFY_RE.search(cmd))


def is_source(path):
    if not path:
        return False
    norm = "/" + path.lstrip("/")
    if any(sub in norm for sub in EXEMPT_PATH_SUBSTRINGS):
        return False
    return os.path.splitext(path)[1].lower() in SOURCE_EXTS


def is_human_message(obj):
    if obj.get("isMeta"):
        return False
    content = (obj.get("message") or {}).get("content")
    if isinstance(content, str):
        return bool(content.strip())
    if isinstance(content, list):
        return any(
            isinstance(c, dict)
            and c.get("type") == "text"
            and (c.get("text") or "").strip()
            for c in content
        )
    return False


def scan(transcript_path):
    """Return (edits, checks, failed_ids). Current turn is idx > last human message.

    edits: [(line_idx, file_path)] of source edits. checks: [(line_idx, tool_use_id)]
    of verification commands. failed_ids: {tool_use_id} whose tool_result carries
    is_error — a failed check is not verification evidence.
    """
    edits, checks = [], []
    failed_ids = set()
    last_human = -1
    with open(transcript_path, encoding="utf-8", errors="ignore") as fh:
        size = os.fstat(fh.fileno()).st_size
        if size > TAIL_BYTES:
            fh.seek(size - TAIL_BYTES)
            fh.readline()  # discard the partial line
        for i, line in enumerate(fh):
            if len(line) > MAX_LINE_BYTES:
                continue
            try:
                obj = json.loads(line)
            except (json.JSONDecodeError, ValueError):
                continue
            if obj.get("isSidechain"):
                continue
            kind = obj.get("type")
            content = (obj.get("message") or {}).get("content") or []
            if kind == "user":
                if is_human_message(obj):
                    last_human = i
                if isinstance(content, list):
                    for c in content:
                        if (
                            isinstance(c, dict)
                            and c.get("type") == "tool_result"
                            and c.get("is_error")
                            and c.get("tool_use_id")
                        ):
                            failed_ids.add(c["tool_use_id"])
                continue
            if kind != "assistant":
                continue
            if not isinstance(content, list):
                continue
            for c in content:
                if not isinstance(c, dict) or c.get("type") != "tool_use":
                    continue
                name = c.get("name", "")
                inp = c.get("input") or {}
                if name in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
                    path = inp.get("file_path") or inp.get("notebook_path") or ""
                    if is_source(path):
                        edits.append((i, path))
                elif name == "Bash" and is_verify_cmd(inp.get("command", "")):
                    checks.append((i, c.get("id")))
    turn_edits = [(i, p) for i, p in edits if i > last_human]
    return turn_edits, checks, failed_ids


def main():
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        sys.exit(0)

    if payload.get("stop_hook_active"):
        sys.exit(0)

    transcript_path = payload.get("transcript_path", "")
    if not transcript_path or not os.path.isfile(transcript_path):
        sys.exit(0)

    try:
        turn_edits, checks, failed_ids = scan(transcript_path)
    except OSError:
        sys.exit(0)

    if not turn_edits:
        sys.exit(0)
    # Evidence: a check issued after BOTH the last source edit and the last failed
    # check — the freshest signal must be green. A check with no tool_use id cannot
    # be correlated to its result: not evidence. A check whose result is missing
    # entirely gets the benefit of the doubt.
    last_edit_idx = turn_edits[-1][0]
    failed_lines = [idx for idx, tool_id in checks if tool_id in failed_ids]
    threshold = max([last_edit_idx] + failed_lines)
    if any(
        idx > threshold and tool_id is not None and tool_id not in failed_ids
        for idx, tool_id in checks
    ):
        sys.exit(0)

    files = []
    for _, p in turn_edits:
        base = "".join(ch for ch in os.path.basename(p)[:80] if ch.isprintable())
        if base not in files:
            files.append(base)
    shown = ", ".join(files[:3]) + (", ..." if len(files) > 3 else "")

    reason = (
        "Verification gate: source files were edited this turn ({}) with no "
        "test/lint/build run afterwards. Run the project's checks (make check, "
        "make test, or the language equivalent) and report the outcome per "
        "rules/verification-protocol.md. If verification genuinely does not "
        "apply (e.g. change is unfinished by design, or covered by a subagent "
        "run), state that explicitly to the user, then stop; you will not be "
        "blocked twice.".format(shown)
    )
    print(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(0)


if __name__ == "__main__":
    main()
