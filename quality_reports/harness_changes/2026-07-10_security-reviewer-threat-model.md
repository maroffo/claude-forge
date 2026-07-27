# ABOUTME: Change-contract for adding threat-model + self-disproof gates to security-reviewer
# ABOUTME: Ports two ideas from Cloudflare's vulnerability harness (blog 2026), prompt-level only

# Harness Change Contract: threat-model-first + adversarial self-disproof in security-reviewer

## Component

`agents/security-reviewer/AGENT.md` — adds two pre-filing gates to the review prompt: (1) a mandatory threat-model statement per finding, (2) an adversarial self-disproof + reachability check before a finding is reported. Prompt-level only; no infra, no new tools, agent stays read-only.

## Failure mode targeted

`security-reviewer` files vacuous or non-reachable findings: issues that are theoretically true but cross no trust boundary ("if a user has DB write access, they can write to the DB") or are unreachable from untrusted input. These inflate MAJOR/MINOR counts, pull the quality-gate score down for no real risk, and cost fix rounds. Anticipated failure (no single-session cite yet); the pattern is the one Cloudflare reports driving their validation rejection rate from 40% to 11% once threat-model context was injected.

## Predicted improvement

Share of `security-reviewer` findings that are non-reachable or boundary-less drops materially. Numeric proxy: over the next 15 sessions that invoke security-reviewer, fewer than 1 finding per session survives to the report without a stated attacker + boundary. Qualitatively: findings gain a one-line threat model, making downstream triage (and the fix agent's job) cheaper.

## Invariants preserved

- Agent stays **read-only** — no PoC files written, no edits.
- Effort stays `medium`; the two gates are reasoning steps, not new tool calls.
- Output format unchanged (CRITICAL/MAJOR/MINOR + Summary); threat model rides inside the existing finding line.
- No new dependency on a second model or external service (that stays in advanced-review / second-opinion).
- Real reachable vulnerabilities are still reported — the gate downgrades/drops only boundary-less or unreachable claims, never a reproducible one.

## Falsification

If, over the next 10 security-reviewer runs, a genuine reachable vulnerability is suppressed because the reviewer over-applied the "not reachable" filter (false-negative introduced by the gate), revert. Checkable signal: any session where a later review path (advanced-review, human, prod incident) flags a reachable bug that security-reviewer saw but dropped as "theoretical". One such miss = revert; the gate must not trade recall for precision.

## Rollback

`git revert <commit>`. Affects a single file: `agents/security-reviewer/AGENT.md` (Scope/Rules additions).

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| 2026-07-27 | 2 security-reviewer runs post-contract against a 15-session target | insufficient data: only 2026-07-15 (1 Major, 2 Minor) and 2026-07-25 (no counts recorded) invoked security-reviewer after the change, and traces store finding counts but never whether a threat model was stated, so the precision claim is unmeasured; the recall falsification did not fire, no later review path flagged a reachable bug that security-reviewer had dropped | kept |
