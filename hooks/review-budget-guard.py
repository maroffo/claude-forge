#!/usr/bin/env python3
# ABOUTME: Stop hook — blocks a SCORE claimed past the fix-round budget or with unreturned reviewers
# ABOUTME: Makes two prose invariants countable: the round ceiling, and the background review join

import json
import os
import re
import sys

# Literal forms from rules/orchestrator-protocol.md. Kept in sync by
# hooks/tests/test_hook_constants_sync.py — change one, change the rule.
SCORE_RE = re.compile(r"^SCORE:\s*\d{1,3}/100\b", re.MULTILINE)
ROUND_RE = re.compile(
    r"^REVIEW-ROUND:\s*n=(?P<n>\d{1,3})\s+budget=(?P<budget>\d{1,3})\b", re.MULTILINE
)
ARTIFACT_RE = re.compile(
    r"^REVIEW-ARTIFACT:[^\n]*?\bagents=(?P<returned>\d{1,3})/(?P<launched>\d{1,3})\b",
    re.MULTILINE,
)
# An escalation is what the protocol requires INSTEAD of another round once the
# budget is spent (step 7). Recognized loosely on purpose: the shape of an
# escalation is prose by design, so a narrow regex would block honest ones.
ESCALATION_RE = re.compile(
    r"\b(escalat\w+|budget (?:is )?(?:exhausted|spent|reached)|stopping (?:here|the loop)"
    r"|fix-round (?:budget|ceiling))\b",
    re.IGNORECASE,
)

MAX_LINE_BYTES = 1_048_576
TAIL_BYTES = 10_485_760


def is_human_message(obj):
    if obj.get("isMeta"):
        return False
    content = (obj.get("message") or {}).get("content")
    if isinstance(content, str):
        return bool(content.strip())
    if isinstance(content, list):
        return any(
            isinstance(c, dict) and c.get("type") == "text" and (c.get("text") or "").strip()
            for c in content
        )
    return False


def scan(transcript_path):
    """Return (score_lines, rounds, artifacts, escalation_lines, last_human).

    rounds:    [(line_idx, n, budget)] from REVIEW-ROUND lines.
    artifacts: [(line_idx, returned, launched)] from REVIEW-ARTIFACT lines.
    """
    score_lines, rounds, artifacts, escalations = [], [], [], []
    last_human = -1
    with open(transcript_path, encoding="utf-8", errors="ignore") as fh:
        size = os.fstat(fh.fileno()).st_size
        if size > TAIL_BYTES:
            fh.seek(size - TAIL_BYTES)
            fh.readline()
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
            if kind == "user":
                if is_human_message(obj):
                    last_human = i
                continue
            if kind != "assistant":
                continue
            content = (obj.get("message") or {}).get("content")
            if not isinstance(content, list):
                continue
            for c in content:
                if not isinstance(c, dict) or c.get("type") != "text":
                    continue
                text = c.get("text") or ""
                if SCORE_RE.search(text):
                    score_lines.append(i)
                for m in ROUND_RE.finditer(text):
                    rounds.append((i, int(m.group("n")), int(m.group("budget"))))
                for m in ARTIFACT_RE.finditer(text):
                    artifacts.append((i, int(m.group("returned")), int(m.group("launched"))))
                if ESCALATION_RE.search(text):
                    escalations.append(i)
    return score_lines, rounds, artifacts, escalations, last_human


def block(reason):
    print(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(0)


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
        score_lines, rounds, artifacts, escalations, last_human = scan(transcript_path)
    except Exception:
        sys.exit(0)  # fail-open: a broken transcript must never break a session

    # Only act when THIS turn reported a score.
    if not any(idx > last_human for idx in score_lines):
        sys.exit(0)

    # A transcript with no REVIEW-ROUND and no agents= field is pre-change (or a
    # SKIP_SET task): the legacy gates own it, this hook has nothing to say.
    if not rounds and not artifacts:
        sys.exit(0)

    # 1. Join barrier: every launched reviewer must have returned. Checked on the
    #    LAST artifact line, which is the one the SCORE is standing on.
    if artifacts:
        _idx, returned, launched = artifacts[-1]
        if returned < launched:
            block(
                f"This turn reports a SCORE, but its REVIEW-ARTIFACT line says "
                f"agents={returned}/{launched}: {launched - returned} reviewer(s) launched "
                "and never returned. A reviewer that has not reported is not a clean "
                "reviewer, and the join belongs at Finding Consolidation, before FIX or "
                "SCORE. Collect the outstanding results (TaskOutput), consolidate, then "
                "re-report. If a reviewer was stopped at the cap, record it as truncated "
                "with its Major finding so the count balances honestly."
            )

    # 2. Round budget: past the ceiling the protocol demands an escalation, not
    #    another round. Any escalation language after the offending round counts.
    if rounds:
        _idx, n, budget = max(rounds, key=lambda r: r[1])
        if budget and n > budget:
            offending = max(idx for idx, rn, _b in rounds if rn == n)
            if not any(e > offending for e in escalations):
                block(
                    f"This turn reports a SCORE at review round {n} with a declared budget "
                    f"of {budget}. The protocol spends the budget and then escalates (step 7): "
                    "present the current artifact, what is done, what is unresolved, and which "
                    "limit stopped you. A loop that keeps scoring past its ceiling is the "
                    "failure the budget exists to catch, and the measured worst sessions ran "
                    "8-15 rounds against a budget of 5. Escalate, or state explicitly why the "
                    "budget was raised."
                )

    sys.exit(0)


if __name__ == "__main__":
    main()
