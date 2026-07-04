# ABOUTME: Pydantic models for orchestrator execution traces
# ABOUTME: Schema v1: one TraceEntry per orchestrator step, step-specific data payloads

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

SCHEMA_VERSION = 2

StepName = Literal[
    "REFINE",
    "RESEARCH",
    "LOCALIZE",
    "REPRODUCE",
    "IMPLEMENT",
    "DRIFT_CHECK",
    "VERIFY",
    "REVIEW",
    "FIX",
    "RE_VERIFY",
    "BLAST_RADIUS",
    "SCORE",
    "LOOP",
    "PRESENT",
    "UAT",
    "SUMMARY",
    # v2: cross-cutting events captured as first-class steps.
    "PERMISSION_EVENT",
    "ROUTE",
]


class RejectedAlternative(BaseModel):
    """A path the agent considered and discarded. Helps post-hoc decision analysis (paper §3.5.1)."""

    description: str
    reason_rejected: str
    cost_estimate: str | None = None  # e.g. "high tokens", "needs approval"


class TraceEntry(BaseModel):
    """A single orchestrator step captured as a trace line.

    `step` is intentionally a flat enum spanning both lifecycle phases
    (REFINE→SUMMARY) and cross-cutting events (PERMISSION_EVENT, ROUTE).
    Consumers that care about the distinction should filter by step name
    rather than expecting a discriminator field.
    """

    v: int = SCHEMA_VERSION
    session: str
    ts: datetime
    step: StepName
    data: dict[str, Any] = Field(default_factory=dict)
    # v2: optional, attaches to decision-bearing steps (RESEARCH, ROUTE, FIX, ...).
    # Default `None` (not []) so empty rows omit the field on the wire.
    rejected_alternatives: list[RejectedAlternative] | None = None

    def to_jsonl(self) -> str:
        return self.model_dump_json(exclude_none=True)


class RefineData(BaseModel):
    ambiguities_found: int = 0
    questions_asked: int = 0


class ResearchData(BaseModel):
    complexity: Literal["simple", "moderate", "complex"] = "simple"
    sources_consulted: int = 0


class LocalizeData(BaseModel):
    """Localization sub-protocol within IMPLEMENT (arxiv 2604.05013)."""

    files_planned: list[str] = Field(default_factory=list)
    files_proposed: list[str] = Field(default_factory=list)
    files_actually_changed: list[str] = Field(default_factory=list)  # from git diff post-VERIFY
    precision: float = 0.0  # len(correct) / len(proposed), vs plan
    recall: float = 0.0  # len(correct) / len(planned), vs plan
    mismatches: list[str] = Field(default_factory=list)  # files in proposed but not planned


class ReproduceData(BaseModel):
    """Issue reproduction step for bug-fix tasks (arxiv 2604.05013)."""

    script: str = ""  # path to reproduction script
    fails_before_fix: bool = False
    passes_after_fix: bool | None = None  # filled during VERIFY


class ImplementData(BaseModel):
    agents: list[str] = Field(default_factory=list)
    files_changed: int = 0
    subtask_count: int = 0
    localization_precision: float | None = None  # from LOCALIZE sub-protocol


class DriftCheckData(BaseModel):
    subtask_id: str = ""
    verdict: Literal["aligned", "minor_drift", "significant_drift"] = "aligned"
    deviations: list[dict[str, str]] = Field(default_factory=list)  # [{desc}]


class VerifyData(BaseModel):
    # Tri-state: True/False = outcome observed in the tool_result; None = unknown
    # (result missing from the stream, or the command says nothing about this axis).
    tests_pass: bool | None = None
    lint_clean: bool | None = None
    build_ok: bool | None = None
    retries: int = 0
    reproduction_confirmed: bool | None = None  # True if reproduce script passes after fix


class ReviewData(BaseModel):
    agents: list[str] = Field(default_factory=list)
    findings: dict[str, int] = Field(default_factory=dict)  # CRITICAL/MAJOR/MINOR -> count
    review_validity: float | None = None  # % of CRITICAL+MAJOR findings addressed in FIX


class FixData(BaseModel):
    findings_addressed: int = 0
    deviations: list[dict[str, str]] = Field(default_factory=list)  # [{rule, desc}]


class BlastRadiusData(BaseModel):
    triggered: bool = False
    trigger_reason: str = ""
    files_scanned: int = 0
    contradictions: dict[str, int] = Field(default_factory=dict)  # MAJOR/MINOR -> count


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


class PermissionEventData(BaseModel):
    """A permission request/decision. v2 step type (paper §3.5.1, §5.2.5).

    Note on `action`: callers are responsible for redacting secrets (API keys,
    tokens, env-var assignments) before populating this field. Traces are
    gitignored but still land on disk.
    """

    tool: str  # e.g. "Bash", "WebFetch", "Edit"
    action: str  # short representation of what was requested (command, url, path)
    outcome: Literal[
        "granted",
        "denied",
        "denied_by_settings",
        "auto_approved",
        "error",
        "timeout",
        "bypassed",  # e.g. --no-verify or other safety-skip flag
    ]
    reason: str = ""  # rule that fired, allowlist hit, etc.


class RouteData(BaseModel):
    """A routing decision. v2 step type (paper §3.5.1: branch decisions)."""

    router: str = ""  # which router fired (e.g. "routing-advisor", "review-pattern")
    target: str  # the agent/reviewer/path selected
    alternatives_considered: list[str] = Field(default_factory=list)
    decision_basis: str = ""  # file pattern matched, rule name, etc.


class HarnessMetrics(BaseModel):
    """End-of-task mini-report on the 6 harness dimensions from paper §5.2.1.

    Each field stays a flexible dict so callers can populate only what they have
    without breaking on missing measurements. None means "not measured".
    """

    trajectory_efficiency: dict[str, Any] | None = None
    # suggested keys: tool_calls, tokens, edits, executions, wall_clock_min
    verification_strength: dict[str, Any] | None = None
    # suggested keys: test_coverage_pct, oracles_count, false_accept_rate
    recovery_ability: dict[str, Any] | None = None
    # suggested keys: failures, recovered, escalations
    state_consistency: dict[str, Any] | None = None
    # suggested keys: memory_repo_synced, drift_detected
    safety_compliance: dict[str, Any] | None = None
    # suggested keys: permission_denials, hitl_gates_hit, sandbox_used
    replayability: dict[str, Any] | None = None
    # suggested keys: full_trace_captured, artifacts_persisted


class SummaryData(BaseModel):
    tokens_in: int = 0
    tokens_out: int = 0
    model: str = ""
    duration_min: int = 0
    files_changed: int = 0
    final_score: int = 0
    metrics: HarnessMetrics | None = None  # v2: end-of-task 6-dimension report


STEP_DATA_MODELS: dict[StepName, type[BaseModel]] = {
    "REFINE": RefineData,
    "RESEARCH": ResearchData,
    "LOCALIZE": LocalizeData,
    "REPRODUCE": ReproduceData,
    "IMPLEMENT": ImplementData,
    "DRIFT_CHECK": DriftCheckData,
    "VERIFY": VerifyData,
    "REVIEW": ReviewData,
    "FIX": FixData,
    "BLAST_RADIUS": BlastRadiusData,
    "SCORE": ScoreData,
    "LOOP": LoopData,
    "UAT": UatData,
    "SUMMARY": SummaryData,
    "PERMISSION_EVENT": PermissionEventData,
    "ROUTE": RouteData,
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
