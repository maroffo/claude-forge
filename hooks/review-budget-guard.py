#!/usr/bin/env python3
# ABOUTME: Stop hook — blocks a SCORE claimed past the fix-round budget or with unreturned reviewers
# ABOUTME: Makes two prose invariants countable: the round ceiling, and the background review join

import json
import os
import re
import sys

# Literal forms from rules/orchestrator-protocol.md, all line-anchored: a literal
# quoted mid-sentence (a reviewer report, a pasted plan) must never arm the gate.
# Kept in sync by hooks/tests/test_hook_constants_sync.py — change one, change the rule.
SCORE_RE = re.compile(r"^SCORE:\s*\d{1,3}/100\b", re.MULTILINE)
ROUND_RE = re.compile(
    r"^REVIEW-ROUND:\s*n=(?P<n>\d{1,3})\s+budget=(?P<budget>\d{1,3})\b", re.MULTILINE
)
ARTIFACT_RE = re.compile(
    r"^REVIEW-ARTIFACT:(?=[^\n]*\bround=(?P<round>\d{1,3}))"
    r"[^\n]*?\bagents=(?P<returned>\d{1,3})/(?P<launched>\d{1,3})\b",
    re.MULTILINE,
)
# Spending the budget is reported on its own literal line, never in prose: an
# `escalat\w+` prose match let ordinary review text ("privilege escalation")
# disarm the gate, and the gate was weakest on exactly the rounds a security
# reviewer took part in.
ESCALATION_RE = re.compile(
    r"^ESCALATION:\s*budget=(?P<budget>\d{1,3})\s+rounds_used=(?P<used>\d{1,3})\b", re.MULTILINE
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
    """Return (scores, rounds, artifacts, escalations, last_human).

    Positions are (line_idx, char_offset) so that literals sharing one assistant
    message stay ordered: production writes several protocol lines in a single
    block, and a line-index-only comparison rejected an escalation written
    alongside its round line.

    rounds:      [(pos, n, budget)]
    artifacts:   [(pos, round_no, returned, launched)]
    escalations: [pos]
    """
    scores, rounds, artifacts, escalations = [], [], [], []
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
                for m in SCORE_RE.finditer(text):
                    scores.append((i, m.start()))
                for m in ROUND_RE.finditer(text):
                    rounds.append(((i, m.start()), int(m.group("n")), int(m.group("budget"))))
                for m in ARTIFACT_RE.finditer(text):
                    artifacts.append((
                        (i, m.start()), int(m.group("round")),
                        int(m.group("returned")), int(m.group("launched")),
                    ))
                for m in ESCALATION_RE.finditer(text):
                    escalations.append((i, m.start()))
    return scores, rounds, artifacts, escalations, last_human


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
        scores, rounds, artifacts, escalations, last_human = scan(transcript_path)
    except Exception:
        sys.exit(0)  # fail-open: a broken or unreadable transcript never breaks a session

    # Only act when THIS turn reported a score, and judge only THIS turn's numbers:
    # a previous turn's round count or roster must not block an unrelated later turn.
    if not any(pos[0] > last_human for pos in scores):
        sys.exit(0)
    rounds = [r for r in rounds if r[0][0] > last_human]
    artifacts = [a for a in artifacts if a[0][0] > last_human]
    escalations = [e for e in escalations if e[0] > last_human]

    # A turn with neither literal is pre-change (or SKIP_SET): the legacy gates own it.
    if not rounds and not artifacts:
        sys.exit(0)

    # 1. Join barrier: every launched reviewer must have returned. Keyed on the
    #    HIGHEST round number, not transcript position: PRESENT recaps earlier
    #    artifact lines, and a recap must not be what the SCORE is judged against.
    if artifacts:
        _pos, round_no, returned, launched = max(artifacts, key=lambda a: (a[1], a[0]))
        if returned < launched:
            block(
                f"This turn reports a SCORE, but its REVIEW-ARTIFACT line for round {round_no} "
                f"says agents={returned}/{launched}: {launched - returned} reviewer(s) launched "
                "and never returned. A reviewer that has not reported is not a clean reviewer, "
                "and the join belongs at Finding Consolidation, before FIX or SCORE. Collect the "
                "outstanding reports (wait for the completion notification, then SendMessage the "
                "agent by name to request its findings; backgrounded reviewers do not reliably "
                "self-deliver), consolidate, then re-report. A reviewer stopped at the cap counts "
                "as returned only once its truncation Major finding exists."
            )

    # 2. Round budget. The declared n= is a claim; the count of round lines this
    #    turn is an observation. Gate on the larger: a loop that prints n=1 every
    #    round would otherwise run unbounded past its ceiling.
    if rounds:
        declared = max(r[1] for r in rounds)
        budget = max(r[2] for r in rounds)
        counted = len(rounds)
        effective = max(declared, counted)
        if budget and effective > budget:
            offending = max(pos for pos, _n, _b in rounds)
            if not any(e > offending for e in escalations):
                how = "declared" if declared >= counted else "counted from REVIEW-ROUND lines"
                block(
                    f"This turn reports a SCORE at review round {effective} ({how}) with a "
                    f"declared budget of {budget}. The protocol spends the budget and then "
                    "escalates (step 7): print the ESCALATION: literal with the current artifact, "
                    "what is done, what is unresolved, and which limit stopped you. A loop that "
                    "keeps scoring past its ceiling is the failure the budget exists to catch: "
                    "the measured worst sessions ran 8-15 rounds against a budget of 5. Escalate, "
                    "or state on the ESCALATION line why the budget was raised."
                )

    sys.exit(0)


if __name__ == "__main__":
    main()
