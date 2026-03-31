# ABOUTME: Pydantic models for orchestrator execution traces
# ABOUTME: Schema v1: one TraceEntry per orchestrator step, step-specific data payloads

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

SCHEMA_VERSION = 1

StepName = Literal[
    "REFINE",
    "RESEARCH",
    "IMPLEMENT",
    "VERIFY",
    "REVIEW",
    "FIX",
    "RE_VERIFY",
    "SCORE",
    "LOOP",
    "PRESENT",
    "UAT",
    "SUMMARY",
]


class TraceEntry(BaseModel):
    """A single orchestrator step captured as a trace line."""

    v: int = SCHEMA_VERSION
    session: str
    ts: datetime
    step: StepName
    data: dict[str, Any] = Field(default_factory=dict)

    def to_jsonl(self) -> str:
        return self.model_dump_json()


class RefineData(BaseModel):
    ambiguities_found: int = 0
    questions_asked: int = 0


class ResearchData(BaseModel):
    complexity: Literal["simple", "moderate", "complex"] = "simple"
    sources_consulted: int = 0


class ImplementData(BaseModel):
    agents: list[str] = Field(default_factory=list)
    files_changed: int = 0
    subtask_count: int = 0


class VerifyData(BaseModel):
    tests_pass: bool = False
    lint_clean: bool = False
    build_ok: bool = False
    retries: int = 0


class ReviewData(BaseModel):
    agents: list[str] = Field(default_factory=list)
    findings: dict[str, int] = Field(default_factory=dict)  # CRITICAL/MAJOR/MINOR -> count


class FixData(BaseModel):
    findings_addressed: int = 0
    deviations: list[dict[str, str]] = Field(default_factory=list)  # [{rule, desc}]


class ScoreData(BaseModel):
    score: int = 0
    threshold: int = 80
    gate: Literal["commit", "pr", "excellence"] = "commit"


class LoopData(BaseModel):
    round: int = 0
    total_rounds: int = 0
    exit_reason: str = ""


class UatData(BaseModel):
    performed: bool = False
    items: int = 0
    passed: int = 0
    failed: int = 0


class SummaryData(BaseModel):
    tokens_in: int = 0
    tokens_out: int = 0
    model: str = ""
    duration_min: int = 0
    files_changed: int = 0
    final_score: int = 0


STEP_DATA_MODELS: dict[StepName, type[BaseModel]] = {
    "REFINE": RefineData,
    "RESEARCH": ResearchData,
    "IMPLEMENT": ImplementData,
    "VERIFY": VerifyData,
    "REVIEW": ReviewData,
    "FIX": FixData,
    "SCORE": ScoreData,
    "LOOP": LoopData,
    "UAT": UatData,
    "SUMMARY": SummaryData,
}


def parse_trace_entry(line: str) -> TraceEntry:
    """Parse a single JSONL line into a TraceEntry."""
    return TraceEntry.model_validate_json(line)


def validate_step_data(step: StepName, data: dict[str, Any]) -> BaseModel | None:
    """Validate step-specific data against its model. Returns validated model or None."""
    model_cls = STEP_DATA_MODELS.get(step)
    if model_cls is None:
        return None
    return model_cls.model_validate(data)
