#!/usr/bin/env python3
# ABOUTME: Tests for review-budget-guard.py — synthetic transcripts through the real hook process
# ABOUTME: Run with: uv run --no-project python3 hooks/tests/test_review_budget_guard.py

import json
import os
import subprocess
import sys
import tempfile

HOOK = os.path.join(os.path.dirname(__file__), "..", "review-budget-guard.py")

SCORE = "SCORE: 92/100 (threshold: 90, gate: pr)"


def human(text="do the thing"):
    return {"type": "user", "message": {"content": text}}


def assistant_text(text):
    return {"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}}


def run_hook(lines, stop_hook_active=False):
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as fh:
        for obj in lines:
            fh.write(obj if isinstance(obj, str) else json.dumps(obj))
            fh.write("\n")
        path = fh.name
    payload = json.dumps(
        {"hook_event_name": "Stop", "transcript_path": path, "stop_hook_active": stop_hook_active}
    )
    try:
        proc = subprocess.run(
            [sys.executable, HOOK], input=payload, capture_output=True, text=True, timeout=30
        )
    finally:
        os.unlink(path)
    assert proc.returncode == 0, proc.stderr
    out = proc.stdout.strip()
    return json.loads(out) if out else None


def expect_block(result, label):
    assert result is not None and result.get("decision") == "block", (
        f"{label}: expected block, got {result}"
    )


def expect_allow(result, label):
    assert result is None, f"{label}: expected allow, got {result}"


def artifact(returned, launched, round_n=1, findings="0/1/2"):
    return assistant_text(
        f"REVIEW-ARTIFACT: round={round_n} path=quality_reports/reviews/x/00{round_n}-findings.md "
        f"findings={findings} agents={returned}/{launched} converged=yes"
    )


def review_round(n, budget=5, scope="full"):
    return assistant_text(f"REVIEW-ROUND: n={n} budget={budget} scope={scope}")


def main():
    score = assistant_text(f"Done.\n{SCORE}\nReady.")

    # --- Row 1: within budget, all reviewers returned -> allow ---
    expect_allow(
        run_hook([human(), review_round(2), artifact(3, 3, 2), score]),
        "within-budget-all-returned",
    )

    # Row 1 edge: no REVIEW-ROUND and no agents= at all (legacy transcript) -> allow
    expect_allow(
        run_hook([human(), assistant_text("REVIEW-ARTIFACT: round=1 path=x findings=0/1/2 converged=yes"), score]),
        "legacy-transcript-untouched",
    )

    # --- Row 2: round count over budget with no escalation -> block ---
    expect_block(
        run_hook([human(), review_round(6, budget=5), artifact(2, 2, 6), score]),
        "over-budget-no-escalation",
    )

    # Row 2 edge: over budget BUT an escalation follows the offending round -> allow
    expect_allow(
        run_hook([
            human(), review_round(6, budget=5), artifact(2, 2, 6),
            assistant_text("Fix-round budget exhausted; escalating with the current artifact."),
            score,
        ]),
        "over-budget-with-escalation",
    )

    # Row 2 edge: escalation language appearing BEFORE the offending round does not count
    expect_block(
        run_hook([
            human(),
            assistant_text("If this drags on we will escalate."),
            review_round(7, budget=5), artifact(1, 1, 7), score,
        ]),
        "stale-escalation-before-round",
    )

    # Row 2 edge: exactly at budget -> allow (the ceiling is inclusive)
    expect_allow(
        run_hook([human(), review_round(5, budget=5), artifact(2, 2, 5), score]),
        "exactly-at-budget",
    )

    # Row 2 edge: malformed literal (non-numeric n) is unparseable -> hook stays quiet
    expect_allow(
        run_hook([human(), assistant_text("REVIEW-ROUND: n=many budget=5 scope=full"), score]),
        "malformed-round-line-fail-open",
    )

    # --- Row 3: a launched reviewer never returned -> block ---
    expect_block(
        run_hook([human(), review_round(1), artifact(2, 3, 1), score]),
        "unreturned-reviewer",
    )

    # Row 3 edge: the LAST artifact is what the SCORE stands on (an earlier imbalance
    # that a later round resolved must not block)
    expect_allow(
        run_hook([
            human(), review_round(1), artifact(1, 3, 1),
            review_round(2), artifact(3, 3, 2), score,
        ]),
        "earlier-imbalance-resolved-later",
    )

    # Row 3 edge: agents= absent from the artifact line (legacy) -> no join opinion
    expect_allow(
        run_hook([
            human(), review_round(2),
            assistant_text("REVIEW-ARTIFACT: round=2 path=x findings=0/0/1 converged=yes"),
            score,
        ]),
        "artifact-without-agents-field",
    )

    # --- Row 4: poisoned transcript lines -> fail-open, logic intact on good lines ---
    poison = "[" * 5000
    expect_block(
        run_hook([human(), poison, "not json at all", review_round(1), artifact(1, 2, 1), score]),
        "poisoned-lines-logic-intact",
    )

    # --- Row 5: stop_hook_active -> allow unconditionally (no double-block) ---
    expect_allow(
        run_hook([human(), review_round(9, budget=5), artifact(0, 3, 9), score], stop_hook_active=True),
        "stop-hook-active",
    )

    # --- Turn scoping: an offending round in a PREVIOUS turn does not block this one ---
    expect_allow(
        run_hook([
            human(), review_round(8, budget=5), artifact(1, 2, 8), score,
            human("next thing"), assistant_text("Just answering a question."),
        ]),
        "previous-turn-only",
    )

    # --- No SCORE this turn -> hook has no opinion ---
    expect_allow(
        run_hook([human(), review_round(9, budget=5), artifact(0, 3, 9)]),
        "no-score-line",
    )

    # --- Both violations at once: join checked first (it is the more specific signal) ---
    r = run_hook([human(), review_round(7, budget=5), artifact(1, 3, 7), score])
    expect_block(r, "both-violations")
    assert "agents=1/3" in r["reason"], f"expected the join reason first, got: {r['reason'][:120]}"

    print("test_review_budget_guard: all tests passed")


if __name__ == "__main__":
    main()
