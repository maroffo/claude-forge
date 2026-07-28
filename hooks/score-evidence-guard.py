#!/usr/bin/env python3
# ABOUTME: Stop hook — blocks ending a turn that reports SCORE without fresh computational evidence
# ABOUTME: Two-confirmation gate (Bringles import): a verify command must run after the last source edit

import datetime
import json
import os
import re
import sys

# Keep in sync with verify-before-stop.py (source detection + verify commands).
SOURCE_EXTS = {
    ".py", ".rb", ".go", ".rs", ".c", ".cpp", ".cc", ".h", ".hpp",
    ".js", ".ts", ".tsx", ".jsx", ".mjs", ".cjs",
    ".kt", ".kts", ".swift", ".java", ".scala", ".dart", ".cs", ".m", ".mm",
    ".sh", ".bash", ".zsh", ".sql", ".ex", ".exs", ".php",
}
EXEMPT_PATH_SUBSTRINGS = (
    "/.git/", "/node_modules/", "/vendor/", "/dist/", "/build/",
    "/.venv/", "/__pycache__/", "/.next/", "/target/", "/out/",
    "/scratchpad/", "/tmp/", "/temp/",
    "/.claude/projects/", "/memory/",
)
VERIFY_RE = re.compile(
    r"""(\bgit\s+commit\b) | \b(
    make\s+(check|test|lint|build|e2e|evidence)\S*
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
NON_VERIFY_PREFIXES = ("echo ", "grep ", "cat ", "ls ", "find ", "rg ")

# The literal step-6 reporting form from rules/orchestrator-protocol.md.
# The evidence group is optional (stage A of the evidence-path rollout): a bare
# `SCORE: n/100 (...)` keeps matching. The group is anchored INSIDE the literal's
# parentheses: prose after the closing paren that happens to say "evidence:" is
# never treated as a claim (it would otherwise cause spurious blocks).
SCORE_RE = re.compile(
    r"^SCORE:\s*\d{1,3}/100\b"
    r"(?:\s*\([^)\n]*?\bevidence:\s*(?P<evidence>[^,)\n]+)[^)\n]*\))?",
    re.MULTILINE,
)

# Subagent types allowed to edit files per orchestrator-protocol Invariants.
WRITE_AGENT_TYPES = {"software-engineer"}

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


def parse_event_ts(obj):
    """Epoch seconds of a transcript event's ISO timestamp, or None."""
    ts = obj.get("timestamp")
    if not isinstance(ts, str):
        return None
    try:
        return datetime.datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def scan(transcript_path):
    """Return (score_lines, edit_lines, verifies, failed_ids, last_human).

    score_lines: [(line_idx, evidence_path_or_None)] of assistant text blocks
        containing a SCORE report (evidence from the last SCORE in the block).
    edit_lines: [(line_idx, epoch_ts_or_None)] of source-file edits, including
        write-class subagent launches (their file edits happen on sidechains,
        invisible here).
    verifies: [(line_idx, tool_use_id)] of verification commands (main loop only).
    failed_ids: {tool_use_id} whose tool_result carries is_error.
    """
    score_lines, edit_lines, verifies = [], [], []
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
            except (json.JSONDecodeError, ValueError, RecursionError):
                continue
            if obj.get("isSidechain"):
                continue
            kind = obj.get("type")
            content = (obj.get("message") or {}).get("content")
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
            if kind != "assistant" or not isinstance(content, list):
                continue
            for c in content:
                if not isinstance(c, dict):
                    continue
                if c.get("type") == "text":
                    matches = list(SCORE_RE.finditer(c.get("text") or ""))
                    if matches:
                        evidence = (matches[-1].group("evidence") or "").strip() or None
                        score_lines.append((i, evidence))
                    continue
                if c.get("type") != "tool_use":
                    continue
                name = c.get("name", "")
                inp = c.get("input") or {}
                if name in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
                    path = inp.get("file_path") or inp.get("notebook_path") or ""
                    if is_source(path):
                        edit_lines.append((i, parse_event_ts(obj)))
                elif name in ("Task", "Agent") and inp.get("subagent_type") in WRITE_AGENT_TYPES:
                    # Write-class subagents edit files on sidechains we cannot see;
                    # their launch invalidates any earlier evidence. Read-only agents
                    # (reviewers) do not: REVIEW legitimately runs after VERIFY.
                    edit_lines.append((i, parse_event_ts(obj)))
                elif name == "Bash" and is_verify_cmd(inp.get("command", "")):
                    verifies.append((i, c.get("id")))
    return score_lines, edit_lines, verifies, failed_ids, last_human


def evidence_block_reason(path, cwd, last_edit_ts):
    """Why a claimed evidence path is provably invalid, or None (valid / fail-open).

    Stat-only checks; unexpected errors return None (fail-open): an infra error
    must never wedge a session, only a present-but-false claim blocks.
    """
    # A malformed claim value (NUL, control chars) is a false claim, not an
    # infra error: it must block, not slip through the fail-open net below.
    if any(ord(ch) < 32 for ch in path):
        return "contains control characters (malformed claim)"
    try:
        root = os.path.realpath(cwd)
        bundle = os.path.realpath(path if os.path.isabs(path) else os.path.join(root, path))
        if bundle != root and not bundle.startswith(root + os.sep):
            return "resolves outside the project directory"
        if not os.path.isdir(bundle):
            return "does not exist (or is not a directory)"
        meta = os.path.join(bundle, "metadata.json")
        if not os.path.isfile(meta):
            return "has no metadata.json manifest"
        try:
            st = os.stat(meta)
        except OSError:
            return None
        if st.st_size == 0:
            return "has an empty metadata.json (not a real bundle manifest)"
        if last_edit_ts is not None and st.st_mtime < last_edit_ts:
            return "predates the last source edit (stale bundle: regenerate it)"
        return None
    except Exception:
        return None


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
        score_lines, edit_lines, verifies, failed_ids, last_human = scan(transcript_path)
    except Exception:
        sys.exit(0)  # fail-open: a broken transcript must never break a session

    # Only act when THIS turn reported a score.
    turn_scores = [(idx, ev) for idx, ev in score_lines if idx > last_human]
    if not turn_scores:
        sys.exit(0)

    # When a SCORE claims an evidence bundle, the claim must be provably true:
    # in-repo, existing, with a metadata.json no older than the last source edit.
    # A false evidence claim is worse than none, so it blocks even if a verify
    # ran. EVERY claimed path in the turn is validated: a false claim followed
    # by a bare re-report must not slip into telemetry unchallenged.
    edit_ts = [ts for _idx, ts in edit_lines if ts is not None]
    for _idx, claimed in turn_scores:
        if not claimed:
            continue
        problem = evidence_block_reason(
            claimed, payload.get("cwd") or os.getcwd(), max(edit_ts) if edit_ts else None
        )
        if problem:
            reason = (
                f"This turn's SCORE cites evidence bundle '{claimed}', which "
                f"{problem}. An evidence claim must point at a real, fresh bundle "
                "(run `make evidence` after the last edit and cite its directory), "
                "or drop the evidence field and rely on the standard verify gate."
            )
            print(json.dumps({"decision": "block", "reason": reason}))
            sys.exit(0)

    # Evidence: a successful verify command issued after BOTH the last source edit
    # and the last failed verify — the freshest computational signal must be green.
    # A verify with no tool_use id cannot be correlated to its result: not evidence.
    # A verify with no result at all gets the benefit of the doubt.
    last_edit = edit_lines[-1][0] if edit_lines else -1
    failed_lines = [idx for idx, tool_id in verifies if tool_id in failed_ids]
    threshold = max([last_edit] + failed_lines)
    for idx, tool_id in verifies:
        if idx > threshold and tool_id is not None and tool_id not in failed_ids:
            sys.exit(0)

    reason = (
        "Two-confirmation gate: this turn reports a SCORE, but no successful "
        "test/lint/build command ran after the last source edit. A score is a "
        "judge verdict; it is only valid alongside fresh computational evidence "
        "(rules/orchestrator-protocol.md step 6). Run the project's checks "
        "(make check, make test-e2e, or the language equivalent) and re-report. "
        "If verification ran inside a subagent and is not visible here, state "
        "that explicitly to the user, then stop; you will not be blocked twice."
    )
    print(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(0)


if __name__ == "__main__":
    main()
