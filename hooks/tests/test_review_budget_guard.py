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
            assistant_text("ESCALATION: budget=5 rounds_used=6 reason=findings not converging"),
            score,
        ]),
        "over-budget-with-escalation",
    )

    # Row 2 edge: escalation language appearing BEFORE the offending round does not count
    expect_block(
        run_hook([
            human(),
            assistant_text("If this drags on we will escalate."),  # prose, not the literal
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

    # --- TEST-1 (Critical): escalation sharing ONE assistant block with its round line.
    # Production writes several protocol literals per block (8 of 10 real blocks do);
    # a line-index-only comparison rejected the honest escalation.
    expect_allow(
        run_hook([human(), assistant_text(
            "REVIEW-ROUND: n=6 budget=5 scope=full\n"
            "ESCALATION: budget=5 rounds_used=6 reason=stalled on flaky suite\n"
            f"{SCORE}\n"
        ), artifact(2, 2, 6)]),
        "escalation-same-block-after-round",
    )
    # ...and the same block with the escalation BEFORE the round line does not count.
    expect_block(
        run_hook([human(), assistant_text(
            "ESCALATION: budget=5 rounds_used=1 reason=stale, from an earlier round\n"
            "REVIEW-ROUND: n=6 budget=5 scope=full\n"
            f"{SCORE}\n"
        ), artifact(2, 2, 6)]),
        "escalation-same-block-before-round",
    )

    # --- SEC-1: prose containing escalat* must NOT satisfy the gate (it used to) ---
    for prose in ("MAJOR: privilege escalation via unchecked role.",
                  "The user escalated the ticket to support.",
                  "Escalating privileges is denied by policy."):
        expect_block(
            run_hook([human(), review_round(7, budget=5), artifact(1, 1, 7),
                      assistant_text(prose), score]),
            f"prose-escalation-does-not-disarm: {prose[:28]}",
        )

    # --- ARCH-1: self-reported n= cannot buy unlimited rounds; the LINES are counted ---
    expect_block(
        run_hook([human()] + [review_round(1, budget=5) for _ in range(8)]
                 + [artifact(2, 2, 1), score]),
        "eight-rounds-all-declared-n1",
    )

    # --- ARCH-minor: a PRESENT recap of an earlier artifact must not gate the SCORE ---
    expect_allow(
        run_hook([human(), review_round(1), artifact(2, 3, 1),
                  review_round(2), artifact(3, 3, 2),
                  assistant_text("Recap:\nREVIEW-ARTIFACT: round=1 path=x findings=0/1/2 agents=2/3 converged=no"),
                  score]),
        "recap-of-earlier-artifact-ignored",
    )

    # --- TEST-2: a literal quoted mid-line must never arm the gate ---
    expect_allow(
        run_hook([human(),
                  assistant_text("We are still at REVIEW-ROUND: n=9 budget=5 scope=full per the plan."),
                  artifact(2, 2, 1), score]),
        "mid-line-literal-not-a-report",
    )

    # --- TEST-3: an isMeta user record (Stop-hook feedback) must not reset turn scoping ---
    meta = {"type": "user", "isMeta": True, "message": {"content": "Stop hook feedback:\nsomething"}}
    expect_block(
        run_hook([human(), review_round(7, budget=5), artifact(1, 2, 7), meta, score]),
        "ismeta-does-not-reset-turn",
    )

    # --- TEST-3b: a human turn whose content is a LIST of text blocks counts as human ---
    human_list = {"type": "user", "message": {"content": [{"type": "text", "text": "new task"}]}}
    expect_allow(
        run_hook([human(), review_round(9, budget=5), artifact(0, 3, 9),
                  human_list, review_round(1), artifact(2, 2, 1), score]),
        "list-content-human-resets-turn",
    )

    # --- TEST-5: rounds printed out of order; the block must name the highest ---
    r = run_hook([human(), review_round(6, budget=5), review_round(2, budget=5),
                  artifact(2, 2, 6), score])
    expect_block(r, "out-of-order-rounds")
    assert "round 6" in r["reason"], f"expected the highest round named, got: {r['reason'][:100]}"

    # --- TEST-7: reason content is asserted for BOTH gates, not just the join ---
    r = run_hook([human(), review_round(7, budget=5), artifact(2, 2, 7), score])
    expect_block(r, "round-gate-reason")
    assert "round 7" in r["reason"] and "budget of 5" in r["reason"], (
        f"round-gate reason must name both numbers, got: {r['reason'][:140]}"
    )

    # --- TEST-4: outer fail-open — an unreadable transcript must exit 0 silently ---
    import stat
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as fh:
        fh.write(json.dumps(human()) + "\n")
        unreadable = fh.name
    try:
        os.chmod(unreadable, 0)
        proc = subprocess.run(
            [sys.executable, HOOK],
            input=json.dumps({"hook_event_name": "Stop", "transcript_path": unreadable}),
            capture_output=True, text=True, timeout=30,
        )
        assert proc.returncode == 0 and not proc.stdout.strip(), (
            f"unreadable transcript must fail open silently: rc={proc.returncode} out={proc.stdout!r}"
        )
    finally:
        os.chmod(unreadable, stat.S_IRUSR | stat.S_IWUSR)
        os.unlink(unreadable)

    print("test_review_budget_guard: all tests passed")


if __name__ == "__main__":
    main()
