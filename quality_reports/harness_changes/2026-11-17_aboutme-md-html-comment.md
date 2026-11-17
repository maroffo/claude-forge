# ABOUTME: Change contract: aboutme-enforcer accepts closed HTML-comment ABOUTME headers in Markdown files
# ABOUTME: Removes the conflict with repos (infra-ops runbooks) whose .md convention is <!-- ABOUTME: -->

# Harness Change Contract: aboutme-enforcer accepts `<!-- ABOUTME: ... -->` in Markdown

## Component

Hook `hooks/aboutme-enforcer.py` (PreToolUse Write deny, PostToolUse Edit advisory) and its test `hooks/tests/test_aboutme_enforcer.py`.

## Failure mode targeted

Markdown files written under the hook must start with `# ABOUTME:` lines. GitHub renders those as two H1 headings at the top of every new doc. Repos that already use the invisible `<!-- ABOUTME: ... -->` form (all infra-ops runbooks) then get one new runbook in a different style.

Observed 2026-11-17: agent aws-w3, infra-ops PR #127 `docs/runbooks/aws-config-periodic-recording.md`, reported as an open item. Owner decision the same day: "Hook accetta <!-- -->".

## Predicted improvement

New `.md` files in repos with the HTML-comment convention match that convention: 0 new `# ABOUTME:` H1 pairs in infra-ops runbooks over the next 10 sessions that write runbooks. Currently every agent-written runbook gets one.

## Invariants preserved

- Non-Markdown files accept only their language's comment prefix. `<!-- ABOUTME:` in a `.py` is still denied (test `html-not-for-py`).
- The `# ABOUTME:` form stays valid for Markdown (test `md-hash`).
- Both header lines must use the same form (test `md-mixed`), and each HTML line must close its comment on the same line (test `md-unclosed`). An open comment would hide the document body.
- Exemptions are unchanged: front matter docs, memory paths, lock files.
- The Edit advisory still fires when an edit removes a header, in either form (test `md-html-edit-advisory`).

## Falsification

Revert if, over the next 10 sessions, any of these happens:

- a Markdown file passes the hook with a header that GitHub renders visibly, or that hides content (an unclosed comment);
- the hook denies a `.md` whose first two non-empty lines are closed `<!-- ABOUTME: -->` comments.

## Rollback

`git revert <commit>`. Affects: `hooks/aboutme-enforcer.py`, `hooks/tests/test_aboutme_enforcer.py`, this contract.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
