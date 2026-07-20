# ABOUTME: Change contract for the Response Shape section in the global CLAUDE.md
# ABOUTME: Targets answer-length miscalibration (verbose or terse-without-context)

# Harness Change Contract: Response Shape section in global CLAUDE.md

## Component

`CLAUDE.md.example` (tracked template) and `~/.claude/CLAUDE.md` (live private copy): new `# Response Shape` section inserted between `# Interaction` and `# Code Philosophy`.

## Failure mode targeted

Answer length is uncalibrated: replies land either over-long (walls of prose, restated request, closing paragraph repeating the body) or too short to act on (a result with no statement of what was verified vs assumed, no mention of what was left untouched). Reported by Max on 2026-07-20: "mi dai sempre risposte estremamente verbose oppure troppo concise senza abbastanza contesto". Root cause: the global CLAUDE.md had no response-format contract at all outside `## Plan Mode`, so length was left to per-turn judgment.

## Predicted improvement

Over the next 20 sessions, zero unprompted complaints about answer length from Max (baseline: at least 1 explicit complaint, plus the implicit ones behind this change). Secondary, checkable by reading any 5 consecutive assistant turns: no turn opens by restating the request, and every turn reporting completed work names what was verified.

## Invariants preserved

- `## Plan Mode` stays the stricter rule inside plan mode (extremely concise, sacrifice grammar); Response Shape does not loosen it.
- Length is bound to the existing 🟢/🟡/🔴 Decision Framework, so no second, competing taxonomy enters the harness.
- 🔴 tasks stay expandable: the rule must never be read as a global "be shorter" instruction.
- Writing rule holds: no em dashes in the new text.
- The tracked template and the live copy stay byte-identical for this section.

## Falsification

Either of these means the change made things worse, revert:
- Max reports that answers have become too terse, or that a needed caveat/assumption was dropped, on 2 or more occasions within 20 sessions (over-compression: the "Always carry" bullet is not doing its job).
- A 🔴 decision gets answered with a Decision-Framework-sized 🟡 reply, i.e. the length rule overrides depth on a high-stakes call, observed even once.

## Rollback

`git revert <commit>` in claude-forge, then delete the same `# Response Shape` block from `~/.claude/CLAUDE.md` (untracked, must be undone by hand). Affects: `CLAUDE.md.example`, `~/.claude/CLAUDE.md`.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|

Verdict: **kept** / **reverted** / **modified** (link to follow-up contract). If reverted, write one line on why the prediction missed.
