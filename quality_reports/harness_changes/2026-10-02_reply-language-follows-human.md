# ABOUTME: Change contract: replies use the human's language, repo artifacts keep the repo's language
# ABOUTME: One failure mode: replies arrive in a language other than the one the human is writing in

# Harness Change Contract: reply language follows the human

## Component

`rules/response-shape.md`: new "Language" bullet at the top of the list; ABOUTME header updated.

## Failure mode targeted

The harness text (CLAUDE.md, rules, skills) is all in English and states no reply-language rule, so a reply's language is left to the model's guess: when Max writes in Italian an agent can still answer in English, which adds translation effort on top of every context switch. Max asked on 2026-10-02 to drop "the rule that makes the agent always answer in English" and answer in the human's language instead. No such rule exists anywhere in the forge (CLAUDE.md.example, rules/, hooks, settings.json, git history: the only past "English" was a `clickup (English only)` skill-table row), so this contract adds the positive rule rather than removing one.

## Predicted improvement

Over the next 20 sessions, every reply to a message written in Italian is in Italian (target: 0 English replies to Italian prompts, outside quoted code, logs and tool output). Commit subjects and PR descriptions in English-language repos stay in English (target: 0 Italian commits there).

## Invariants preserved

- Repo artifacts (code, comments, commits, PR descriptions, docs) keep the repo's existing language; the rule covers conversation only.
- Orchestrator literal report lines and other machine-read formats stay as specified (English keywords).
- Skills with their own content-language rule (blog-writer, humanizer) keep it: that is the language of the deliverable, not of the reply.
- No em dashes in the new text.

## Falsification

Within 10-20 sessions, either of these means revert or modify:
- A commit, PR description or repo doc written in Italian in a repo whose existing artifacts are English (the rule leaked from chat into artifacts).
- A literal report line or a machine-read format translated (for example `PUNTEGGIO:` in place of `SCORE:`), breaking trace extraction.

## Rollback

`git revert <commit>` in claude-forge; affects only `rules/response-shape.md` (and this contract).

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| (after 10-20 sessions) | | | |
