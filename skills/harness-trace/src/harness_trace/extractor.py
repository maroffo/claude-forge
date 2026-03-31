# ABOUTME: Extracts structured traces from raw Claude Code session JSONL files
# ABOUTME: Heuristic parser that identifies orchestrator steps from assistant messages

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from harness_trace.models import SCHEMA_VERSION, TraceEntry

# Patterns that identify orchestrator steps in assistant messages.
# Each maps a regex (searched in message text) to the step name and a data extractor.
STEP_PATTERNS: list[tuple[str, str, str]] = [
    # (regex_pattern, step_name, description)
    (r"requirements?\s+refinement|refin(?:e|ing)\s+requirements?", "REFINE", "requirements"),
    (r"complexity.*?:\s*(simple|moderate|complex)", "RESEARCH", "research"),
    (r"implementation\s+report|implementing\s+(?:step|phase)", "IMPLEMENT", "implementation"),
    (r"(?:tests?|lint|build)\s+(?:pass|fail|clean|ok|broken)", "VERIFY", "verification"),
    (r"(?:architecture|security|performance|test|dependency|database|dx)\s+review", "REVIEW", "review"),  # noqa: E501
    (r"fix(?:ing|ed)?\s+(?:critical|major)\s+findings?|findings?\s+addressed", "FIX", "fix"),
    (r"score:\s*(\d+)|quality.*?score.*?(\d+)", "SCORE", "scoring"),
    (r"round\s+(\d+)\s+of\s+(\d+)|loop(?:ing)?\s+back", "LOOP", "loop"),
    (r"uat|goal-backward\s+verification|user\s+acceptance", "UAT", "uat"),
]

# Findings severity pattern
FINDINGS_PATTERN = re.compile(
    r"(CRITICAL|MAJOR|MINOR)\s*[:\-]?\s*(\d+)", re.IGNORECASE
)

# Score extraction pattern
SCORE_PATTERN = re.compile(r"score\s*[:\-=]?\s*(\d+)", re.IGNORECASE)

# Files changed pattern
FILES_CHANGED_PATTERN = re.compile(r"(\d+)\s+files?\s+changed", re.IGNORECASE)

# Agent name pattern (from review routing)
AGENT_PATTERN = re.compile(
    r"(software-engineer|research-analyst|security-reviewer|performance-reviewer|"
    r"architecture-reviewer|test-reviewer|dependency-reviewer|database-reviewer|"
    r"dx-reviewer|tech-writer|project-analyzer)",
    re.IGNORECASE,
)

# Complexity pattern
COMPLEXITY_PATTERN = re.compile(
    r"complexity\s*[:\-]?\s*(simple|moderate|complex)", re.IGNORECASE
)


def _extract_timestamp(msg: dict[str, Any]) -> datetime:
    """Extract timestamp from a session JSONL message."""
    ts = msg.get("timestamp")
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(ts / 1000, tz=UTC)
    if isinstance(ts, str):
        return datetime.fromisoformat(ts)
    return datetime.now(tz=UTC)


def _get_message_text(msg: dict[str, Any]) -> str:
    """Extract text content from a session JSONL message."""
    # Assistant messages can have content as string or list of blocks
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


def _extract_step_data(step: str, text: str) -> dict[str, Any]:
    """Extract step-specific data from message text using heuristics."""
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
        text_lower = text.lower()
        data["tests_pass"] = bool(
            re.search(r"tests?\s+pass", text_lower)
            and not re.search(r"tests?\s+fail", text_lower)
        )
        data["lint_clean"] = bool(
            re.search(r"lint\s+(?:clean|pass|ok)", text_lower)
            and not re.search(r"lint\s+(?:fail|error)", text_lower)
        )
        data["build_ok"] = bool(
            re.search(r"build\s+(?:ok|pass|success)", text_lower)
            and not re.search(r"build\s+(?:fail|broken|error)", text_lower)
        )

    elif step == "REVIEW":
        agents = list({a.lower() for a in AGENT_PATTERN.findall(text)})
        if agents:
            data["agents"] = agents
        findings: dict[str, int] = {}
        for severity_match in FINDINGS_PATTERN.finditer(text):
            severity = severity_match.group(1).upper()
            count = int(severity_match.group(2))
            findings[severity] = findings.get(severity, 0) + count
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


def extract_traces(session_path: Path, session_slug: str | None = None) -> list[TraceEntry]:
    """Extract structured traces from a raw session JSONL file.

    Scans assistant messages for orchestrator step indicators and extracts
    structured data from each matched message.

    Args:
        session_path: Path to the session JSONL file.
        session_slug: Optional session identifier. Defaults to filename stem.

    Returns:
        List of TraceEntry objects, one per detected orchestrator step.
    """
    if session_slug is None:
        session_slug = session_path.stem

    entries: list[TraceEntry] = []
    seen_steps: set[str] = set()

    with session_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Only process assistant messages
            msg_type = msg.get("type", "")
            if msg_type != "assistant":
                continue

            text = _get_message_text(msg)
            if not text:
                continue

            # Try each step pattern against the message
            for pattern, step_name, _desc in STEP_PATTERNS:
                if re.search(pattern, text, re.IGNORECASE):
                    # All steps can repeat across orchestrator rounds.
                    # Use count suffix to allow repetition while preventing
                    # duplicate extraction from the same message.
                    count = sum(1 for e in entries if e.step == step_name)
                    step_key = f"{step_name}_{count}"

                    if step_key in seen_steps:
                        continue
                    seen_steps.add(step_key)

                    data = _extract_step_data(step_name, text)
                    entry = TraceEntry(
                        v=SCHEMA_VERSION,
                        session=session_slug,
                        ts=_extract_timestamp(msg),
                        step=step_name,
                        data=data,
                    )
                    entries.append(entry)
                    break  # One step per message

    return entries


def write_traces(entries: list[TraceEntry], output_path: Path) -> None:
    """Write trace entries to a JSONL file."""
    with output_path.open("w") as f:
        for entry in entries:
            f.write(entry.to_jsonl() + "\n")
