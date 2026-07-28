#!/usr/bin/env python3
# ABOUTME: Drift guard — asserts the constants duplicated across Stop hooks stay identical
# ABOUTME: Run with: uv run --no-project python3 hooks/tests/test_hook_constants_sync.py

import importlib.util
import os
import re

HOOKS_DIR = os.path.join(os.path.dirname(__file__), "..")
REPO_ROOT = os.path.join(HOOKS_DIR, "..")
SYNCED_CONSTANTS = ("SOURCE_EXTS", "EXEMPT_PATH_SUBSTRINGS", "NON_VERIFY_PREFIXES")

FREEZE_HOOK = os.path.join(HOOKS_DIR, "_freeze_boundary.sh")
FREEZE_SKILL = os.path.join(REPO_ROOT, "skills", "freeze", "SKILL.md")
FREEZE_TOKEN_RE = re.compile(r"\.freeze[-\w]*")


def load(filename):
    path = os.path.join(HOOKS_DIR, filename)
    module_name = filename.replace("-", "_").removesuffix(".py")
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def check_freeze_boundary_basename():
    """The /freeze skill writes the boundary file that freeze-guard.sh reads. gstack,
    where the idea comes from, ships that pair with two independent path sources that
    only accidentally agree; here the basename has one home and the skill quotes it."""
    with open(FREEZE_HOOK) as fh:
        m = re.search(r'^FREEZE_BOUNDARY_BASENAME="([^"]+)"', fh.read(), re.M)
    assert m, "FREEZE_BOUNDARY_BASENAME not found in hooks/_freeze_boundary.sh"
    basename = m.group(1)

    with open(FREEZE_SKILL) as fh:
        skill = fh.read()
    assert basename in skill, (
        f"skills/freeze/SKILL.md never names {basename!r}: the write path and the read path can drift"
    )
    strays = sorted(set(FREEZE_TOKEN_RE.findall(skill)) - {basename})
    assert not strays, (
        f"skills/freeze/SKILL.md names {strays} besides {basename!r}: "
        "the skill would write a boundary file the hook never reads"
    )


def check_score_literal_sync():
    """The SCORE literal's evidence field has four consumers: the protocol rule
    (canonical form), the guard hook (SCORE_RE evidence group), the trace
    extractor (evidence_path), and score-log.sh (--evidence). A consumer that
    forgets the field silently drops the evidence link."""
    seg = load("score-evidence-guard.py")
    assert "evidence" in seg.SCORE_RE.groupindex, (
        "score-evidence-guard SCORE_RE lost its named 'evidence' group"
    )
    with open(os.path.join(REPO_ROOT, "rules", "orchestrator-protocol.md")) as fh:
        rule = fh.read()
    assert "evidence: <bundle-path>" in rule, (
        "orchestrator-protocol.md SCORE literal no longer documents the evidence field"
    )
    # Parse-equivalence probes: the same fixture strings must yield the same
    # evidence capture in the hook's SCORE_RE (functional) and stay compatible
    # with the extractor's anchored pattern (source-level: same core char class
    # and SCORE-line anchor — the divergence that shipped unanchored first).
    fixtures = {
        "SCORE: 92/100 (threshold: 90, gate: pr)": None,
        "SCORE: 92/100 (threshold: 90, gate: pr, evidence: quality_reports/evidence/x)": (
            "quality_reports/evidence/x"
        ),
        "SCORE: 92/100 (threshold: 90, gate: pr). Note the evidence: prose here.": None,
        "| evidence: CWE-79 |\nSCORE: 90/100 (threshold: 90, gate: pr, evidence: qr/e/y)": "qr/e/y",
    }
    for text, want in fixtures.items():
        matches = list(seg.SCORE_RE.finditer(text))
        got = (matches[-1].group("evidence") or "").strip() if matches else ""
        got = got or None
        assert got == want, f"SCORE_RE evidence capture drifted on {text!r}: {got!r} != {want!r}"
    with open(os.path.join(REPO_ROOT, "skills", "harness-trace", "src", "harness_trace", "extractor.py")) as fh:
        extractor_src = fh.read()
    assert "evidence_path" in extractor_src, "harness-trace extractor dropped evidence_path"
    assert r"\bevidence:\s*([^,)\n]+)" in extractor_src and "^SCORE:" in extractor_src, (
        "extractor evidence pattern lost the SCORE-line anchor or the shared char class"
    )
    with open(os.path.join(REPO_ROOT, "skills", "harness-trace", "src", "harness_trace", "models.py")) as fh:
        assert "evidence_path" in fh.read(), "harness-trace ScoreData dropped evidence_path"
    with open(os.path.join(REPO_ROOT, "scripts", "score-log.sh")) as fh:
        assert "--evidence" in fh.read(), "score-log.sh dropped the --evidence flag"


def check_review_literals_sync():
    """REVIEW-ROUND and the agents= field on REVIEW-ARTIFACT have three homes: the protocol
    rule (canonical form), the guard hook (regexes), and the orchestrator skill (the text
    that tells the loop to print them). A home that forgets the literal silently disables
    the gate — the same failure the SCORE literal had before it was pinned."""
    rbg = load("review-budget-guard.py")
    fixtures = [
        ("REVIEW-ROUND: n=3 budget=5 scope=full", (3, 5)),
        ("REVIEW-ROUND: n=12 budget=5 scope=fix-diff", (12, 5)),
        ("REVIEW-ROUND: n=many budget=5 scope=full", None),
    ]
    for text, want in fixtures:
        m = rbg.ROUND_RE.search(text)
        got = (int(m.group("n")), int(m.group("budget"))) if m else None
        assert got == want, f"ROUND_RE drifted on {text!r}: {got} != {want}"
    # Anchoring is the property, not just the shape: this repo shipped an
    # unanchored-vs-anchored divergence once. A literal quoted mid-line must not match.
    for embedded in ("we are still at REVIEW-ROUND: n=9 budget=5",
                     "quoting ESCALATION: budget=5 rounds_used=9 in prose"):
        assert not rbg.ROUND_RE.search(embedded) and not rbg.ESCALATION_RE.search(embedded), (
            f"a literal quoted mid-line must not match: {embedded!r}"
        )
    multi = "some prose\nREVIEW-ROUND: n=4 budget=5 scope=full\nmore prose"
    assert rbg.ROUND_RE.search(multi), "ROUND_RE must match on a later line (re.MULTILINE)"
    assert rbg.ESCALATION_RE.search("x\nESCALATION: budget=5 rounds_used=6 reason=y"), (
        "ESCALATION_RE must be the anchored literal, never a prose match"
    )
    for prose in ("privilege escalation via unchecked role", "the user escalated the ticket"):
        assert not rbg.ESCALATION_RE.search(prose), (
            f"prose must not satisfy the escalation gate: {prose!r}"
        )
    m = rbg.ARTIFACT_RE.search(
        "REVIEW-ARTIFACT: round=2 path=p findings=0/1/2 agents=2/3 converged=no"
    )
    assert m and (int(m.group("returned")), int(m.group("launched"))) == (2, 3), (
        "ARTIFACT_RE lost the agents=<returned>/<launched> capture"
    )
    with open(os.path.join(REPO_ROOT, "rules", "orchestrator-protocol.md")) as fh:
        rule = fh.read()
    assert "ESCALATION: budget=<b> rounds_used=<n>" in rule, (
        "orchestrator-protocol.md no longer documents the ESCALATION literal"
    )
    assert "REVIEW-ROUND: n=<n> budget=<b>" in rule, (
        "orchestrator-protocol.md no longer documents the REVIEW-ROUND literal"
    )
    assert "agents=<returned>/<launched>" in rule, (
        "orchestrator-protocol.md REVIEW-ARTIFACT literal lost the agents= field"
    )
    with open(os.path.join(REPO_ROOT, "skills", "orchestrator", "SKILL.md")) as fh:
        skill = fh.read()
    for token in ("agents=<returned>/<launched>", "run_in_background", "15 minutes per reviewer",
                  "REVIEW-ROUND: n=<n> budget=<b>", "SendMessage", "TaskStop"):
        assert token in skill, f"orchestrator SKILL.md no longer states {token!r}"


def main():
    vbs = load("verify-before-stop.py")
    seg = load("score-evidence-guard.py")

    for name in SYNCED_CONSTANTS:
        a, b = getattr(vbs, name), getattr(seg, name)
        assert a == b, f"{name} drifted between verify-before-stop.py and score-evidence-guard.py"

    assert vbs.VERIFY_RE.pattern == seg.VERIFY_RE.pattern, (
        "VERIFY_RE drifted between verify-before-stop.py and score-evidence-guard.py"
    )

    check_freeze_boundary_basename()
    check_score_literal_sync()
    check_review_literals_sync()

    print("test_hook_constants_sync: all tests passed")


if __name__ == "__main__":
    main()
