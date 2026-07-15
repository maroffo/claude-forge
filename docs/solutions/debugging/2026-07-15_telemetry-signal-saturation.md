# ABOUTME: Telemetry keyed on tool usage saturates when a rule mandates the tool; key on literal report lines
# ABOUTME: BLAST_RADIUS 15 noise events to 0, sub-steps 0 to instrumented; detection and capture share one regex

# Problem

A trace telemetry signal (BLAST_RADIUS) was keyed on tool usage: any `ast-grep`/`sg` Bash invocation emitted an event. When the global "ALWAYS use sg for code search" rule landed, every ordinary code search fired the event: 15 noise events in one session, 0 events in the three sessions where the step's actual trigger (>3 changed files) held. The signal measured compliance with the search rule, not execution of the protocol step, and the events looked plausible enough that nobody noticed. The sibling failure: steps with NO signal at all (LOCALIZE/REPRODUCE/DRIFT, 0 events in 12/12 sessions), where "skipped" and "performed but unparseable" are indistinguishable.

# Solution

Key extraction on mandated literal one-line report formats instead of behavior proxies:

```
LOCALIZE: planned=<n> proposed=<m> precision=<p> recall=<r> mismatches=none|<f1,f2>
REPRODUCE: script=<path> fails_before_fix=true|false
DRIFT: subtask=<id> verdict=aligned|minor_drift|significant_drift
BLAST-RADIUS: clean|MAJOR=<n> MINOR=<m> (files_checked=<k>)   or: skipped (<reason>)
```

Mandate the format in the protocol rule; in the extractor, detection and capture share the same compiled regex (no drift between "line seen" and "line parsed"); check literal lines independently per message (the protocol co-locates them, so first-match-wins would shadow); strip fenced code blocks first so quoted lines cannot forge events; bound every free-text capture.

# Why It Works

A literal format converts an unfalsifiable ambiguity into a clean dichotomy: events appear (step runs, now measurable) or stay absent (step is skipped, next fix is behavioral not parser-side). Proxies inherit every rule and habit that touches the proxied behavior; an explicit report line has exactly one producer. Third application of this pattern in this repo (SCORE 2026-07-05: 0 to 9 events; sub-steps and blast-radius 2026-07-15), each with before/after numbers. Contracts: `quality_reports/harness_changes/2026-07-15_substep-report-formats.md`, `2026-07-15_blast-radius-report-keyed.md`.
