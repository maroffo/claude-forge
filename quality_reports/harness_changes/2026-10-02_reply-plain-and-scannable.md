# ABOUTME: Change contract: replies become bulleted, plain-worded and readable without prior context
# ABOUTME: One failure mode: agent replies cost too much attention when Max supervises many agents at once

# Harness Change Contract: plain and scannable replies

## Component

`rules/response-shape.md`: new "Plain and scannable" bullet; the plan-mode line drops "sacrifice grammar" for "bullets in plain words". ABOUTME header updated to the wider scope.

## Failure mode targeted

Max works with many agents in parallel and switches context between them often. Replies written as dense paragraphs, with harness-internal labels (step names, acronyms, protocol terms) or telegraphic shorthand, force him to rebuild context before he can act, and give the impression of being overwhelmed. Reported by Max on 2026-10-02: "gli agenti devono parlare sempre nel modo più chiaro e conciso possibile, evitando jargon, esponendo le cose per punti, per non dare l'impressione di essere sopraffatto all'umano che deve interagire con molti agenti e avere un sacco di context switch". The plan-mode instruction "sacrifice grammar" pushed in the opposite direction: shorter text, but harder to read cold.

## Predicted improvement

Over the next 20 sessions, zero complaints from Max about replies being hard to follow, jargon-heavy or overwhelming. Checkable by reading any 5 consecutive replies: multi-item content is bulleted, and no internal label or acronym appears without an explanation on the same line.

## Invariants preserved

- Length still follows the 🟢/🟡/🔴 Decision Framework; the rule does not make replies longer.
- The "Always carry" items (verified vs assumed, what was not touched, what can bite later) are not dropped for brevity.
- Orchestrator literal report lines (`SCORE:`, `REVIEW-ROUND:`, `LOCALIZE:`, ...) are still emitted verbatim: the trace extractor keys on them.
- Technical terms the human already uses are still allowed; the rule targets internal labels, not domain vocabulary.
- No em dashes in the new text.

## Falsification

Any of these within 10-20 sessions means revert or modify:
- Max reports, 2 or more times, that a reply dropped information he needed (over-compression).
- A traced session that ran the orchestrator loop shows no `SCORE:` or `REVIEW-ROUND:` line where one was due (the literal lines got "explained away").
- Replies get longer on 🟢 tasks: explanations of terms padding answers that were one line before.

## Rollback

`git revert <commit>` in claude-forge; affects only `rules/response-shape.md` (and this contract).

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| (after 10-20 sessions) | | | |
