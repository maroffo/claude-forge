# ABOUTME: Extracts structured traces from raw Claude Code session JSONL files
# ABOUTME: Tool-use blocks as primary signal (high precision); text regex as fallback

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from harness_trace.models import SCHEMA_VERSION, TraceEntry

# ---- Text-based step patterns (fallback when tool signal is absent) ---------

# Each row: (regex, step_name). Tried in order against assistant message text.
# Loose prose heuristics only: the literal report lines (LOCALIZE/REPRODUCE/
# DRIFT/BLAST-RADIUS) are handled separately via LITERAL_REPORT_STEPS below,
# where detection and extraction share one compiled pattern.
STEP_PATTERNS: list[tuple[str, str]] = [
    (r"requirements?\s+refinement|refin(?:e|ing)\s+requirements?", "REFINE"),
    (r"complexity.*?:\s*(simple|moderate|complex)", "RESEARCH"),
    (r"implementation\s+report|implementing\s+(?:step|phase)", "IMPLEMENT"),
    (r"(?:tests?|lint|build)\s+(?:pass|fail|clean|ok|broken)", "VERIFY"),
    (r"(?:architecture|security|performance|test|dependency|database|dx)\s+review", "REVIEW"),
    (r"fix(?:ing|ed)?\s+(?:critical|major)\s+findings?|findings?\s+addressed", "FIX"),
    (r"score:\s*(\d+)|quality.*?score.*?(\d+)", "SCORE"),
    (r"round\s+(\d+)\s+of\s+(\d+)|loop(?:ing)?\s+back", "LOOP"),
    (r"uat|goal-backward\s+verification|user\s+acceptance", "UAT"),
]

# Same-line separator required and digits bounded: cross-newline slack let
# "### MAJOR\n1. foo" read as "MAJOR: 1", and unbounded digit runs overflow
# int() (Python's 4300-digit str-to-int limit) on crafted input.
FINDINGS_PATTERN = re.compile(
    r"(CRITICAL|MAJOR|MINOR)[ \t]*[:\-][ \t]*(\d{1,6})\b", re.IGNORECASE
)
SCORE_PATTERN = re.compile(r"score\s*[:\-=]?\s*(\d{1,6})\b", re.IGNORECASE)
FILES_CHANGED_PATTERN = re.compile(r"(\d{1,6})\s+files?\s+changed", re.IGNORECASE)
AGENT_PATTERN = re.compile(
    r"(software-engineer|research-analyst|security-reviewer|performance-reviewer|"
    r"architecture-reviewer|test-reviewer|dependency-reviewer|database-reviewer|"
    r"dx-reviewer|tech-writer|project-analyzer)",
    re.IGNORECASE,
)
COMPLEXITY_PATTERN = re.compile(
    r"complexity\s*[:\-]?\s*(simple|moderate|complex)", re.IGNORECASE
)

# Literal sub-step report lines (orchestrator-protocol steps 1a/1b/1c/5b).
# The normative format lives in rules/orchestrator-protocol.md; these compiled
# patterns are the single source for BOTH detection and extraction (see
# LITERAL_REPORT_STEPS), so a detected line always yields data. Digits bounded
# like FINDINGS_PATTERN; floats capped; free-text captures bounded too (a
# crafted multi-KB token must not become a multi-KB trace field).
LOCALIZE_REPORT_PATTERN = re.compile(
    r"\bLOCALIZE:\s*planned=(\d{1,6})\s+proposed=(\d{1,6})"
    r"(?:\s+precision=(\d\.?\d{0,4}))?(?:\s+recall=(\d\.?\d{0,4}))?"
    r"(?:\s+mismatches=(\S{1,2000}))?",
    re.IGNORECASE,
)
MISMATCHES_LIST_CAP = 50
REPRODUCE_REPORT_PATTERN = re.compile(
    r"\bREPRODUCE:\s*script=(\S{1,256})\s+fails_before_fix=(true|false)", re.IGNORECASE
)
DRIFT_REPORT_PATTERN = re.compile(
    r"\bDRIFT:\s*subtask=(\S{1,64})\s+verdict=(aligned|minor_drift|significant_drift)",
    re.IGNORECASE,
)
EXECUTOR_REPORT_PATTERN = re.compile(
    r"\bEXECUTOR:\s*(\S{1,64})\s+model=(\S{1,128})\s+subtask=(\S{1,64})",
    re.IGNORECASE,
)

# ---- Tool-use signals (primary, high-precision) -----------------------------

# Bash command substrings that indicate a verification run.
VERIFY_BASH_PATTERNS = [
    "pytest",
    "make check",
    "make test",
    "go test",
    "npm test",
    "npm run test",
    "yarn test",
    "pnpm test",
    "cargo test",
    "rspec",
    "rake test",
    "mix test",
    "uv run -- pytest",
    "uv run pytest",
]

# Verify commands that gate lint/static checks rather than tests.
# No build command patterns exist yet, so VerifyData.build_ok is a dead axis
# (always None) until one is added under its own contract.
LINT_BASH_PATTERNS = ["make check"]

# Output markers that mean failure even when the command exited 0
# (e.g. `pytest || true` chains). "0 failed" must NOT match, nor must
# fixed-error summaries like ruff's "Found 3 errors (3 fixed, 0 remaining)".
# `[^\S\n]*` (not `\s*`) after the newline: a whitespace class that can eat
# newlines backtracks quadratically on blank-line-heavy output.
VERIFY_FAIL_PATTERN = re.compile(
    r"[1-9]\d*\s+failed\b|\bFAILED\b|(?:^|\n)[^\S\n]*FAIL\b"
)

# Only the tail of huge tool outputs is scanned: test-runner verdicts print
# last, and an unbounded scan is a DoS surface on crafted multi-MB outputs.
VERIFY_SCAN_TAIL = 100_000
REVIEW_SCAN_HEAD = 200_000

# BLAST_RADIUS is keyed on the literal step-5b report line, never on ast-grep
# tool usage: the always-use-sg code-search rule saturates that signal (15
# events in one session from ordinary searches, 0 in sessions where step 5b
# actually triggered). Detection matches the whole line; severities and
# files_checked are then scanned within it, so field order does not matter.
BLAST_REPORT_LINE_PATTERN = re.compile(
    r"\bBLAST-RADIUS:\s*(?:clean|skipped|MAJOR=\d{1,6}|MINOR=\d{1,6})[^\n]*",
    re.IGNORECASE,
)
BLAST_SKIP_REASON_PATTERN = re.compile(
    r"\bBLAST-RADIUS:\s*skipped\s*(?:\(([^)\n]{0,200})\))?", re.IGNORECASE
)
BLAST_SEVERITY_PATTERN = re.compile(r"(MAJOR|MINOR)=(\d{1,6})", re.IGNORECASE)
BLAST_FILES_CHECKED_PATTERN = re.compile(r"\(files_checked=(\d{1,6})\)", re.IGNORECASE)

# Bash command substrings indicating a git commit (signals end of FIX/IMPLEMENT round).
COMMIT_BASH_PATTERNS = ["git commit", "git push"]

# Flags that skip the pre-commit-gate hook; a commit carrying one is NOT
# verification evidence (and they are forbidden by the harness anyway).
COMMIT_VERIFY_BYPASS = ("--no-verify", "--no-hooks", "--no-pre-commit-hook")

# Positive markers that a `git commit` actually landed: the commit summary line
# (`[branch abc1234] msg`) or the diffstat (`N files changed`). Resolved
# positively rather than from is_error, because both a pre-commit-gate deny and
# a plain "nothing to commit" surface as errors.
COMMIT_SUCCESS_PATTERN = re.compile(r"\b\d+ files? changed\b|\[\S+ [0-9a-f]{7,}\]")


def _extract_timestamp(msg: dict[str, Any]) -> datetime:
    ts = msg.get("timestamp")
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(ts / 1000, tz=UTC)
    if isinstance(ts, str):
        try:
            return datetime.fromisoformat(ts)
        except ValueError:
            pass
    return datetime.now(tz=UTC)


def _get_message_text(msg: dict[str, Any]) -> str:
    content = msg.get("message", {}).get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
            elif isinstance(block, str):
                parts.append(block)
        return "\n".join(parts)
    return ""


def _iter_tool_uses(msg: dict[str, Any]):
    """Yield (block_id, name, input_dict) for every tool_use block in an assistant message."""
    content = msg.get("message", {}).get("content")
    if not isinstance(content, list):
        return
    for block in content:
        if isinstance(block, dict) and block.get("type") == "tool_use":
            yield block.get("id", ""), block.get("name", ""), block.get("input", {}) or {}


def _iter_tool_results(msg: dict[str, Any]):
    """Yield (tool_use_id, is_error, text) for every tool_result block in a user message."""
    content = msg.get("message", {}).get("content")
    if not isinstance(content, list):
        return
    for block in content:
        if not (isinstance(block, dict) and block.get("type") == "tool_result"):
            continue
        tool_use_id = block.get("tool_use_id", "")
        if not tool_use_id:
            continue
        raw = block.get("content")
        if isinstance(raw, list):
            text = "\n".join(
                b.get("text", "") for b in raw
                if isinstance(b, dict) and b.get("type") == "text"
            )
        else:
            text = raw if isinstance(raw, str) else ""
        yield tool_use_id, bool(block.get("is_error", False)), text


def _verify_target_fields(cmd: str) -> list[str]:
    """Which VerifyData axes a verify command speaks to (lint vs tests)."""
    cmd_lower = cmd.lower()
    fields = []
    if any(p in cmd_lower for p in LINT_BASH_PATTERNS):
        fields.append("lint_clean")
    test_patterns = [p for p in VERIFY_BASH_PATTERNS if p not in LINT_BASH_PATTERNS]
    if any(p in cmd_lower for p in test_patterns):
        fields.append("tests_pass")
    return fields


def _apply_commit_verify_result(entry: TraceEntry, is_error: bool, tail: str) -> None:
    """Resolve a git-commit VERIFY from its tool_result, fail-closed.

    The pre-commit-gate runs `make check` (lint) on every commit and
    `make test-e2e` (tests) UNLESS the staged diff is docs-only, in which case
    e2e is skipped. The skip marker is not surfaced in the commit's tool_result
    (verified empirically), so from a landed commit we can only prove lint:

    - On any error/deny (`is_error`, the "Pre-commit gate:" reason prefix, or a
      failure marker), fail closed: set the named axis False, never True.
    - On success, set only `lint_clean=True`. `tests_pass` stays None (unknown),
      because we cannot tell a docs-only commit (e2e skipped) from a code one.

    So `tests_pass` is never asserted True from a commit; that would fabricate a
    pass the commit does not evidence.
    """
    low = tail.lower()
    if is_error or "pre-commit gate:" in low or VERIFY_FAIL_PATTERN.search(tail):
        if "make check" in low:
            entry.data["lint_clean"] = False
        if "test-e2e" in low:
            entry.data["tests_pass"] = False
        # A non-gate failure (e.g. "nothing to commit") names no axis: stays None.
        return
    if COMMIT_SUCCESS_PATTERN.search(tail):
        entry.data["lint_clean"] = True


def _apply_verify_result(entry: TraceEntry, cmd: str, is_error: bool, text: str) -> None:
    """Resolve a pending VERIFY entry's outcome from its tool_result."""
    tail = text[-VERIFY_SCAN_TAIL:]
    if "git commit" in cmd.lower():
        _apply_commit_verify_result(entry, is_error, tail)
        return
    success = not is_error and not VERIFY_FAIL_PATTERN.search(tail)
    fields = _verify_target_fields(cmd)
    if success:
        for field in fields:
            entry.data[field] = True
    elif len(fields) == 1:
        entry.data[fields[0]] = False
    # A failing compound command (e.g. `make check && make test`) can't attribute
    # the failure to one axis; all its axes stay None (unknown).


# Markdown heading (or bold line) opening a severity section in a reviewer report,
# e.g. "### MAJOR (internal contradictions)" or "**CRITICAL**".
REVIEW_SECTION_PATTERN = re.compile(
    r"^(?:#{1,6}\s*|\*\*)(CRITICAL|MAJOR|MINOR)\b", re.MULTILINE
)
REVIEW_BULLET_PATTERN = re.compile(r"^(?:[-*]|\d+\.)\s+", re.MULTILINE)


def _parse_review_sections(text: str) -> dict[str, int]:
    """Count findings from '### SEVERITY' sections: one bullet = one finding."""
    # Fenced code blocks may quote bullets verbatim; they are not findings.
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    matches = list(REVIEW_SECTION_PATTERN.finditer(text))
    findings: dict[str, int] = {}
    for i, m in enumerate(matches):
        sev = m.group(1).upper()
        section_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[m.end():section_end]
        # Cut at the next non-severity heading so trailing sections don't bleed in.
        next_heading = re.search(r"^#{1,6}\s", body, re.MULTILINE)
        if next_heading:
            body = body[:next_heading.start()]
        findings[sev] = findings.get(sev, 0) + len(REVIEW_BULLET_PATTERN.findall(body))
    return findings


def _apply_review_result(entry: TraceEntry, text: str) -> None:
    """Fill a pending REVIEW entry's findings from the reviewer's returned report.

    Two formats are recognized: section-style reports ("### MAJOR" followed by
    one bullet per finding) and explicit counts ("MAJOR: 1"). Section format
    wins when present: real reports mix headings with prose that the count
    pattern could misread. Anything else leaves findings empty rather than
    fabricating counts.
    """
    text = text[:REVIEW_SCAN_HEAD]
    findings = _parse_review_sections(text)
    if not findings:
        for sm in FINDINGS_PATTERN.finditer(text):
            sev = sm.group(1).upper()
            findings[sev] = findings.get(sev, 0) + int(sm.group(2))
    if findings:
        entry.data["findings"] = findings


def _bash_command(tool_input: dict[str, Any]) -> str:
    return str(tool_input.get("command", ""))


def _matches_any(cmd: str, patterns: list[str]) -> bool:
    cmd_lower = cmd.lower()
    return any(p in cmd_lower for p in patterns)


def _extract_text_step_data(step: str, text: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    if step == "RESEARCH":
        m = COMPLEXITY_PATTERN.search(text)
        if m:
            data["complexity"] = m.group(1).lower()
    elif step == "IMPLEMENT":
        agents = list({a.lower() for a in AGENT_PATTERN.findall(text)})
        if agents:
            data["agents"] = agents
        m = FILES_CHANGED_PATTERN.search(text)
        if m:
            data["files_changed"] = int(m.group(1))
    elif step == "VERIFY":
        tl = text.lower()
        data["tests_pass"] = bool(
            re.search(r"tests?\s+pass", tl) and not re.search(r"tests?\s+fail", tl)
        )
        data["lint_clean"] = bool(
            re.search(r"lint\s+(?:clean|pass|ok)", tl)
            and not re.search(r"lint\s+(?:fail|error)", tl)
        )
        data["build_ok"] = bool(
            re.search(r"build\s+(?:ok|pass|success)", tl)
            and not re.search(r"build\s+(?:fail|broken|error)", tl)
        )
    elif step == "REVIEW":
        agents = list({a.lower() for a in AGENT_PATTERN.findall(text)})
        if agents:
            data["agents"] = agents
        findings: dict[str, int] = {}
        for sm in FINDINGS_PATTERN.finditer(text):
            sev = sm.group(1).upper()
            findings[sev] = findings.get(sev, 0) + int(sm.group(2))
        if findings:
            data["findings"] = findings
    elif step == "LOCALIZE":
        m = LOCALIZE_REPORT_PATTERN.search(text)
        if m:
            data["planned_count"] = int(m.group(1))
            data["proposed_count"] = int(m.group(2))
            if m.group(3):
                data["precision"] = float(m.group(3))
            if m.group(4):
                data["recall"] = float(m.group(4))
            raw_mismatches = m.group(5)
            if raw_mismatches:
                data["mismatches"] = (
                    []
                    if raw_mismatches.lower() == "none"
                    else raw_mismatches.split(",")[:MISMATCHES_LIST_CAP]
                )
    elif step == "REPRODUCE":
        m = REPRODUCE_REPORT_PATTERN.search(text)
        if m:
            data["script"] = m.group(1)
            data["fails_before_fix"] = m.group(2).lower() == "true"
    elif step == "DRIFT_CHECK":
        m = DRIFT_REPORT_PATTERN.search(text)
        if m:
            data["subtask_id"] = m.group(1)
            data["verdict"] = m.group(2).lower()
    elif step == "EXECUTOR":
        m = EXECUTOR_REPORT_PATTERN.search(text)
        if m:
            data["executor"] = m.group(1)
            data["model"] = m.group(2)
            data["subtask_id"] = m.group(3)
    elif step == "BLAST_RADIUS":
        line_m = BLAST_REPORT_LINE_PATTERN.search(text)
        if line_m:
            line = line_m.group(0)
            skip_m = BLAST_SKIP_REASON_PATTERN.search(line)
            if skip_m:
                data["triggered"] = False
                data["trigger_reason"] = (skip_m.group(1) or "skipped").strip()
            else:
                # `clean` reports have no severity tokens: contradictions stays {}.
                # trigger_reason is left default; the report line does not say
                # WHY step 5b triggered, and a constant filler carries no signal.
                data["triggered"] = True
                data["contradictions"] = {
                    sev.upper(): int(count)
                    for sev, count in BLAST_SEVERITY_PATTERN.findall(line)
                }
                files_m = BLAST_FILES_CHECKED_PATTERN.search(line)
                if files_m:
                    data["files_scanned"] = int(files_m.group(1))
    elif step == "SCORE":
        m = SCORE_PATTERN.search(text)
        if m:
            data["score"] = int(m.group(1))
    elif step == "LOOP":
        m = re.search(r"round\s+(\d+)\s+of\s+(\d+)", text, re.IGNORECASE)
        if m:
            data["round"] = int(m.group(1))
            data["total_rounds"] = int(m.group(2))
    elif step == "UAT":
        data["performed"] = True
    return data


def _new_entry(session_slug: str, ts: datetime, step: str, data: dict[str, Any]) -> TraceEntry:
    return TraceEntry(
        v=SCHEMA_VERSION,
        session=session_slug,
        ts=ts,
        step=step,  # type: ignore[arg-type]
        data=data,
    )


def _process_tool_use(
    block_id: str,
    name: str,
    tool_input: dict[str, Any],
    ts: datetime,
    session_slug: str,
    counters: dict[str, int],
    entries: list[TraceEntry],
    tool_signaled_steps: set[str],
    pending_verify: dict[str, tuple[TraceEntry, str]],
    pending_review: dict[str, TraceEntry],
) -> None:
    """Emit trace entries derived from a single tool_use block."""

    counters["tool_calls"] += 1

    if name == "Agent":
        subagent = (tool_input.get("subagent_type") or "").lower()
        # Always emit a ROUTE event for any Agent call.
        entries.append(_new_entry(
            session_slug, ts, "ROUTE",
            {
                "router": "orchestrator",
                "target": subagent or "unknown",
                "alternatives_considered": [],
                "decision_basis": "explicit subagent_type",
            },
        ))
        # If the agent is a reviewer, also emit a REVIEW entry; findings are
        # filled from the reviewer's tool_result when it arrives.
        if subagent.endswith("-reviewer"):
            entry = _new_entry(
                session_slug, ts, "REVIEW",
                {"agents": [subagent], "findings": {}},
            )
            entries.append(entry)
            if block_id:
                pending_review[block_id] = entry
            tool_signaled_steps.add("REVIEW")
        elif subagent == "software-engineer":
            counters["engineer_calls"] += 1
            tool_signaled_steps.add("IMPLEMENT")
        return

    if name in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        counters["edits"] += 1
        tool_signaled_steps.add("IMPLEMENT")
        return

    if name == "Bash":
        counters["bash_calls"] += 1
        cmd = _bash_command(tool_input)
        cmd_lower = cmd.lower()
        # `git commit` is checked before the generic verify patterns: a commit
        # message like `-m "add pytest fixtures"` would otherwise match "pytest"
        # and take the wrong branch (undercounting the commit).
        if "git commit" in cmd_lower:
            counters["commits"] += 1
            # The pre-commit-gate PreToolUse hook runs `make check` +
            # `make test-e2e` before the commit executes, so a successful commit
            # is verification evidence. The bypass flags are forbidden by the
            # harness and do not actually skip this hook (it is not a git hook);
            # we still decline to emit VERIFY for them, conservatively.
            if not any(b in cmd_lower for b in COMMIT_VERIFY_BYPASS):
                counters["verify_runs"] += 1
                entry = _new_entry(
                    session_slug, ts, "VERIFY",
                    {"tests_pass": None, "lint_clean": None, "build_ok": None},
                )
                entries.append(entry)
                if block_id:
                    pending_verify[block_id] = (entry, cmd)
                tool_signaled_steps.add("VERIFY")
        elif _matches_any(cmd, VERIFY_BASH_PATTERNS):
            counters["verify_runs"] += 1
            entry = _new_entry(
                session_slug, ts, "VERIFY",
                # Tri-state: outcome resolved later from the paired tool_result;
                # None means unknown (result missing or axis not addressed).
                {"tests_pass": None, "lint_clean": None, "build_ok": None},
            )
            entries.append(entry)
            if block_id:
                pending_verify[block_id] = (entry, cmd)
            tool_signaled_steps.add("VERIFY")
        elif _matches_any(cmd, COMMIT_BASH_PATTERNS):
            # `git push` and other commit-family commands: counted, no VERIFY.
            counters["commits"] += 1
        return

    if name == "WebFetch":
        counters["web_fetches"] += 1
        url = str(tool_input.get("url", ""))
        if "arxiv" in url.lower() or "docs" in url.lower():
            entries.append(_new_entry(
                session_slug, ts, "RESEARCH",
                {"sources_consulted": 1},
            ))
            tool_signaled_steps.add("RESEARCH")
        return

    if name == "AskUserQuestion":
        counters["hitl_gates"] += 1
        return


ACTIVE_GAP_CEILING_S = 300  # 5 minutes; longer inter-message gaps treated as idle.


def _compute_active_min(message_timestamps: list[datetime]) -> int:
    """Sum inter-message gaps clamped at ACTIVE_GAP_CEILING_S, return minutes.

    Distinguishes active work time from session calendar span. A session that
    sits idle for 3 days between two interactions only contributes the 5-minute
    ceiling for the gap, not 3 days.
    """
    if len(message_timestamps) < 2:
        return 0
    total_s = 0.0
    for prev, curr in zip(message_timestamps, message_timestamps[1:]):
        gap = (curr - prev).total_seconds()
        if gap <= 0:
            continue
        total_s += min(gap, ACTIVE_GAP_CEILING_S)
    return int(total_s // 60)


def _compute_summary(
    counters: dict[str, int],
    ts_start: datetime | None,
    ts_end: datetime | None,
    message_timestamps: list[datetime],
) -> dict[str, Any]:
    """Build SUMMARY.data with computed metrics (paper §5.2.1).

    `duration_min` is calendar span (last_ts - first_ts). For sessions kept open
    across days, this can be misleadingly large. `active_min` inside
    `trajectory_efficiency` is the bounded-gap working time and is the right
    metric for cross-session cost comparison.
    """
    if ts_start and ts_end and ts_end > ts_start:
        duration_min = int((ts_end - ts_start).total_seconds() // 60)
    else:
        duration_min = 0

    active_min = _compute_active_min(message_timestamps)

    return {
        "duration_min": duration_min,
        "files_changed": counters["edits"],
        "metrics": {
            "trajectory_efficiency": {
                "tool_calls": counters["tool_calls"],
                "edits": counters["edits"],
                "executions": counters["bash_calls"],
                "active_min": active_min,
            },
            "verification_strength": {
                "oracles_count": counters["verify_runs"],
            },
            "safety_compliance": {
                "hitl_gates_hit": counters["hitl_gates"],
            },
            "replayability": {
                "full_trace_captured": True,
            },
        },
    }


def extract_traces(session_path: Path, session_slug: str | None = None) -> list[TraceEntry]:
    """Extract structured traces from a raw session JSONL file.

    Tool-use blocks are the primary signal (high precision). Text regex is
    used as fallback only for steps that the tool stream did not surface
    (e.g. SCORE numeric reports, REFINE/UAT pure-text gates).

    Args:
        session_path: Path to the session JSONL file.
        session_slug: Optional session identifier. Defaults to filename stem.

    Returns:
        List of TraceEntry objects in chronological order, ending with SUMMARY.
    """
    if session_slug is None:
        session_slug = session_path.stem

    entries: list[TraceEntry] = []
    counters = {
        "tool_calls": 0,
        "edits": 0,
        "bash_calls": 0,
        "verify_runs": 0,
        "hitl_gates": 0,
        "web_fetches": 0,
        "engineer_calls": 0,
        "commits": 0,
    }
    tool_signaled_steps: set[str] = set()
    # tool_use_id -> (VERIFY entry, bash command); outcome filled by the paired tool_result.
    pending_verify: dict[str, tuple[TraceEntry, str]] = {}
    # tool_use_id -> REVIEW entry; findings filled from the reviewer's tool_result.
    pending_review: dict[str, TraceEntry] = {}
    seen_text_step_keys: set[str] = set()
    ts_start: datetime | None = None
    ts_end: datetime | None = None
    message_timestamps: list[datetime] = []

    # First pass: walk JSONL, collect tool-use signals + record text candidates per message.
    text_candidates: list[tuple[datetime, str]] = []

    with session_path.open() as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if msg.get("type") == "user":
                # Resolve pending verify outcomes from tool_result blocks.
                for tool_use_id, is_error, result_text in _iter_tool_results(msg):
                    pending = pending_verify.pop(tool_use_id, None)
                    if pending is not None:
                        v_entry, v_cmd = pending
                        _apply_verify_result(v_entry, v_cmd, is_error, result_text)
                    r_entry = pending_review.pop(tool_use_id, None)
                    if r_entry is not None and not is_error:
                        _apply_review_result(r_entry, result_text)
                continue
            if msg.get("type") != "assistant":
                continue

            ts = _extract_timestamp(msg)
            if ts_start is None:
                ts_start = ts
            ts_end = ts
            message_timestamps.append(ts)

            for block_id, name, tool_input in _iter_tool_uses(msg):
                _process_tool_use(
                    block_id, name, tool_input, ts, session_slug,
                    counters, entries, tool_signaled_steps,
                    pending_verify, pending_review,
                )

            text = _get_message_text(msg)
            if text:
                text_candidates.append((ts, text))

    # Second pass: text fallback for steps the tool stream did not cover.
    # Two classes of pattern:
    #   1. Literal report lines (LITERAL_REPORT_STEPS): exact mandated formats,
    #      checked independently per message because the protocol co-locates
    #      them in one turn (LOCALIZE + REPRODUCE, BLAST-RADIUS + SCORE).
    #   2. Prose heuristics (STEP_PATTERNS): loose regexes, first-match-wins
    #      per message. This avoids the v1 problem where prose like "tests
    #      pass" in a casual chat would create false steps.
    text_only_eligible = {
        "REFINE", "RESEARCH", "IMPLEMENT", "VERIFY", "REVIEW",
        "FIX", "SCORE", "LOOP", "UAT",
    }
    literal_report_steps: list[tuple[str, re.Pattern[str]]] = [
        ("LOCALIZE", LOCALIZE_REPORT_PATTERN),
        ("REPRODUCE", REPRODUCE_REPORT_PATTERN),
        ("DRIFT_CHECK", DRIFT_REPORT_PATTERN),
        ("BLAST_RADIUS", BLAST_REPORT_LINE_PATTERN),
        ("EXECUTOR", EXECUTOR_REPORT_PATTERN),
    ]

    for ts, text in text_candidates:
        # Fenced code blocks may quote report lines or step-like prose verbatim
        # (same forgery vector as review bullets, see _parse_review_sections):
        # strip them before any step matching.
        text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        for step_name, report_pattern in literal_report_steps:
            if report_pattern.search(text):
                entries.append(_new_entry(
                    session_slug, ts, step_name,
                    _extract_text_step_data(step_name, text),
                ))
        for pattern, step_name in STEP_PATTERNS:
            if step_name not in text_only_eligible:
                continue
            # Skip if the tool stream already covered this step (avoid double counting
            # ambiguous prose like "tests pass" when a real pytest ran).
            if step_name in tool_signaled_steps and step_name in {"REVIEW", "VERIFY"}:
                continue
            if not re.search(pattern, text, re.IGNORECASE):
                continue
            count = sum(1 for e in entries if e.step == step_name)
            step_key = f"{step_name}_{count}"
            if step_key in seen_text_step_keys:
                continue
            seen_text_step_keys.add(step_key)
            data = _extract_text_step_data(step_name, text)
            entries.append(_new_entry(session_slug, ts, step_name, data))
            break  # one step per message

    # Sort chronologically; tool-use entries and text-fallback entries interleave by ts.
    entries.sort(key=lambda e: e.ts)

    # Append a synthetic SUMMARY entry with computed metrics, but only when the
    # session actually did something. A pure chat with no tool calls and no text
    # signals gets no SUMMARY (a SUMMARY of zeros is misleading). Edit-only
    # sessions DO get a SUMMARY: edits are real work even without other steps.
    if ts_end is not None and (entries or counters["tool_calls"] > 0):
        entries.append(_new_entry(
            session_slug, ts_end, "SUMMARY",
            _compute_summary(counters, ts_start, ts_end, message_timestamps),
        ))

    return entries


def write_traces(entries: list[TraceEntry], output_path: Path) -> None:
    """Write trace entries to a JSONL file."""
    with output_path.open("w") as f:
        for entry in entries:
            f.write(entry.to_jsonl() + "\n")
