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

FINDINGS_PATTERN = re.compile(r"(CRITICAL|MAJOR|MINOR)\s*[:\-]?\s*(\d+)", re.IGNORECASE)
SCORE_PATTERN = re.compile(r"score\s*[:\-=]?\s*(\d+)", re.IGNORECASE)
FILES_CHANGED_PATTERN = re.compile(r"(\d+)\s+files?\s+changed", re.IGNORECASE)
AGENT_PATTERN = re.compile(
    r"(software-engineer|research-analyst|security-reviewer|performance-reviewer|"
    r"architecture-reviewer|test-reviewer|dependency-reviewer|database-reviewer|"
    r"dx-reviewer|tech-writer|project-analyzer)",
    re.IGNORECASE,
)
COMPLEXITY_PATTERN = re.compile(
    r"complexity\s*[:\-]?\s*(simple|moderate|complex)", re.IGNORECASE
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

# Bash command substrings indicating blast-radius analysis.
BLAST_BASH_PATTERNS = ["ast-grep", "sg --pattern", "sg -p ", "ast_grep"]

# Bash command substrings indicating a git commit (signals end of FIX/IMPLEMENT round).
COMMIT_BASH_PATTERNS = ["git commit", "git push"]


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
    """Yield (name, input_dict) for every tool_use block in an assistant message."""
    content = msg.get("message", {}).get("content")
    if not isinstance(content, list):
        return
    for block in content:
        if isinstance(block, dict) and block.get("type") == "tool_use":
            yield block.get("name", ""), block.get("input", {}) or {}


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
    name: str,
    tool_input: dict[str, Any],
    ts: datetime,
    session_slug: str,
    counters: dict[str, int],
    entries: list[TraceEntry],
    tool_signaled_steps: set[str],
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
        # If the agent is a reviewer, also emit a REVIEW entry.
        if subagent.endswith("-reviewer"):
            entries.append(_new_entry(
                session_slug, ts, "REVIEW",
                {"agents": [subagent], "findings": {}},
            ))
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
        if _matches_any(cmd, VERIFY_BASH_PATTERNS):
            counters["verify_runs"] += 1
            entries.append(_new_entry(
                session_slug, ts, "VERIFY",
                # Tool-use signal can't tell pass/fail from the call alone; leave defaults.
                {"tests_pass": False, "lint_clean": False, "build_ok": False},
            ))
            tool_signaled_steps.add("VERIFY")
        elif _matches_any(cmd, BLAST_BASH_PATTERNS):
            entries.append(_new_entry(
                session_slug, ts, "BLAST_RADIUS",
                {"triggered": True, "trigger_reason": "ast-grep invoked"},
            ))
            tool_signaled_steps.add("BLAST_RADIUS")
        elif _matches_any(cmd, COMMIT_BASH_PATTERNS):
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
            if msg.get("type") != "assistant":
                continue

            ts = _extract_timestamp(msg)
            if ts_start is None:
                ts_start = ts
            ts_end = ts
            message_timestamps.append(ts)

            for name, tool_input in _iter_tool_uses(msg):
                _process_tool_use(
                    name, tool_input, ts, session_slug,
                    counters, entries, tool_signaled_steps,
                )

            text = _get_message_text(msg)
            if text:
                text_candidates.append((ts, text))

    # Second pass: text fallback for steps the tool stream did not cover.
    # Apply ONLY to steps that benefit from regex (REFINE, SCORE, FIX, UAT, LOOP,
    # REVIEW/VERIFY if no tool signal). This avoids the v1 problem where prose
    # like "tests pass" in a casual chat would create false steps.
    text_only_eligible = {
        "REFINE", "RESEARCH", "IMPLEMENT", "VERIFY", "REVIEW",
        "FIX", "SCORE", "LOOP", "UAT",
    }

    for ts, text in text_candidates:
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
