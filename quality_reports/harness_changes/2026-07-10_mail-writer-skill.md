# ABOUTME: Change-contract for the new mail-writer skill
# ABOUTME: New skill = 🔴 required contract; controls a new auto-trigger surface

# Harness Change Contract: mail-writer skill

## Component

New skill `skills/mail-writer/` (SKILL.md + references/email-rules.md + references/voice.md). Registered in `skills/_INDEX.md`, `README.md`, `CLAUDE.md.example`. The SKILL.md `description` field adds a new auto-trigger surface.

## Failure mode targeted

Max drafts emails by hand or via generic prompts, producing inconsistent results: buried asks (context before the point), AI-generic openers ("I hope this email finds you well"), em dashes (a standing hard rule), and length that ignores the reader's attention. No skill encoded a repeatable email standard combining Castonguay's rules with Max's voice. Scope note: an earlier draft wired the skill into Gmail (`gog`) for reply mode; Max rejected that. The skill stays inbox-free and works only from pasted text.

## Predicted improvement

Emails drafted through the skill lead with the ask in sentence 1, contain zero em dashes and zero "hope this finds you well" openers, and stay within one screen unless content demands otherwise. Qualitative target over the first 10 uses: Max sends the draft with only minor edits (no structural rewrite) in the majority of cases.

## Invariants preserved

- **Never touches an inbox.** No fetch, no create, no send. Output is text in the conversation. `allowed-tools` is `[Read, AskUserQuestion]`, with no Gmail/`gog`/Bash path. Reply mode works only from a thread the user pastes.
- Em dash ban holds in every draft (Max's global rule + humanizer #13).
- Does not shadow `blog-writer`, `linkedin-post`, or `inbox-triage`: the description names each as out of scope.
- No external dependency, no CLI, no MCP.

## Falsification

Revert or fix if, over the first 10 invocations: (a) the skill emits an em dash or a "hope this finds you well" opener, or (b) it triggers on requests meant for `blog-writer`/`linkedin-post`/`inbox-triage` (trigger bleed), or (c) it ever creates/sends a Gmail message. Any (c) is an immediate hard revert (invariant breach).

## Rollback

`git revert <commit>` (or `rm -rf skills/mail-writer/`) and revert the four registry edits: `skills/_INDEX.md`, `README.md` (two lines), `CLAUDE.md.example`.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| 2026-07-27 | 17 days live, 0 recorded invocations | insufficient data: drafts are conversation text so no invocation leaves an artifact in traces or on disk and the em-dash and opener predictions cannot be checked post hoc; the hard invariant is structurally safe since allowed-tools is Read and AskUserQuestion only with no Gmail or Bash path, making create-or-send impossible; re-check needs Max's own count over the first 10 drafts | kept |
