# ABOUTME: Classification engine - loads YAML rules, evaluates first-match priority
# ABOUTME: Persists classification state to /tmp for archive command

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import yaml

from .models import (
    ClassificationResult,
    ClassifiedThread,
    GogThread,
    RuleConfig,
)

DEFAULT_STATE_PATH = Path("/tmp/inbox-triage-state.json")


def load_rules(path: Path) -> RuleConfig:
    """Load classification rules from a YAML file."""
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    return RuleConfig.model_validate(data)


def classify_thread(thread: GogThread, rules: RuleConfig) -> ClassifiedThread:
    """Classify a single thread using first-match-wins evaluation.

    Order: sender exact -> sender domain -> label -> category -> default.
    """
    email_lower = thread.email.lower()
    domain_lower = thread.domain.lower()

    # 1. Sender rules: exact email match (case-insensitive)
    for rule in rules.sender_rules:
        match_lower = rule.match.lower()
        if not match_lower.startswith("@") and match_lower == email_lower:
            return ClassifiedThread(
                thread=thread,
                priority=rule.priority,
                matched_rule=f"sender:{rule.match}",
            )

    # 2. Sender rules: domain match (@domain, including subdomains, case-insensitive)
    for rule in rules.sender_rules:
        match_lower = rule.match.lower()
        if match_lower.startswith("@") and (
            domain_lower == match_lower or domain_lower.endswith("." + match_lower[1:])
        ):
            return ClassifiedThread(
                thread=thread,
                priority=rule.priority,
                matched_rule=f"sender:{rule.match}",
            )

    # 3. Label rules: check thread labels against rule labels
    for rule in rules.label_rules:
        for label in thread.labels:
            if label == rule.label:
                return ClassifiedThread(
                    thread=thread,
                    priority=rule.priority,
                    matched_rule=f"label:{rule.label}",
                )

    # 4. Category rules: check thread labels against category keys
    for label in thread.labels:
        if label in rules.category_rules:
            return ClassifiedThread(
                thread=thread,
                priority=rules.category_rules[label],
                matched_rule=f"category:{label}",
            )

    # 5. Default fallback
    return ClassifiedThread(
        thread=thread,
        priority=rules.default_priority,
        matched_rule="default",
    )


def classify_all(threads: list[GogThread], rules: RuleConfig) -> ClassificationResult:
    """Classify all threads and return a ClassificationResult."""
    classified = [classify_thread(t, rules) for t in threads]
    return ClassificationResult(
        date=date.today().isoformat(),
        total=len(threads),
        classified=classified,
    )


def save_state(result: ClassificationResult, path: Path | None = None) -> Path:
    """Serialize classification result to JSON. Returns the file path."""
    target = path or DEFAULT_STATE_PATH
    data = result.model_dump(mode="json")
    target.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return target


def load_state(path: Path | None = None) -> ClassificationResult:
    """Deserialize classification result from JSON.

    Raises FileNotFoundError if the state file does not exist.
    """
    target = path or DEFAULT_STATE_PATH
    if not target.exists():
        raise FileNotFoundError(f"State file not found: {target}")
    text = target.read_text(encoding="utf-8")
    data = json.loads(text)
    return ClassificationResult.model_validate(data)
