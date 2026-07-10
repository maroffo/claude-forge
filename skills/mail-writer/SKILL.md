---
name: mail-writer
description: "Write clear, direct emails in Max's voice. Use when user says write email, draft email, scrivi una mail, scrivi una email, rispondi a questa mail, reply to this email, mail-writer, clean up this email draft. Applies Castonguay's email rules, Max's distilled voice, and a humanizer pass. Outputs email text in chat, never sends. Not for blog posts (blog-writer), LinkedIn (linkedin-post), or inbox triage (inbox-triage)."
allowed-tools: [Read, AskUserQuestion]
---

# ABOUTME: Write short, direct emails combining Castonguay's rules, Max's distilled voice, and a humanizer pass
# ABOUTME: Three input modes (intent, reply-to-thread, raw draft); outputs email text in chat, never sends

# Mail Writer

Write emails that lead with the point, cost the reader as little attention as possible, and still sound like Max wrote them. Three sources drive every draft: the email rules in `references/email-rules.md`, the voice in `references/voice.md`, and an email-scoped humanizer pass (also in `references/voice.md`).

**Output is always text in this conversation.** This skill never touches an inbox: it does not fetch, create, or send mail. Max pastes any thread he wants a reply to, and copies the output where he needs it.

## Input Modes

Pick the mode from what the user gives you. If ambiguous, ask.

### Mode 1: From intent or bullets

The user states a goal or a few bullet points. Turn them into a full email. Ask only for facts you cannot infer and that the rules demand (a specific deadline, an owner, a number). Do not invent specifics: if a date or name is missing and load-bearing, ask for it rather than guessing.

### Mode 2: Reply to a thread

The user pastes the thread (or the message to reply to). Draft the reply in context: answer the open question, match the thread's language, and keep the subject unless the topic changed (email rule 13). If the pasted context is missing something load-bearing (an earlier message, a specific number), ask for it rather than guessing. Do not go looking for the thread yourself; work only from what the user pasted.

### Mode 3: Clean up a raw draft

The user pastes rough notes or a messy draft. Rewrite it clean: apply the rules, the voice, and the humanizer pass. Preserve the user's facts and intent, cut everything the rules cut.

## Workflow

1. **Detect language.** Match the language of the intent or the thread. If genuinely unclear, default to the language the user is writing to you in. Never translate proper nouns or technical terms.
2. **Draft against the rules.** Write the email applying every rule in `references/email-rules.md`. The first sentence carries the ask, decision, risk, or update. Bad news first. One job per email.
3. **Apply the voice.** Run the draft through `references/voice.md`: keep Max's directness, opinion-with-evidence, and honesty about limits; drop all blog-length structure (no hooks, no section headers, no separators, no padding).
4. **Humanize.** Apply the email-scoped humanizer subset in `references/voice.md`. The em dash ban is a hard rule: use commas, colons, semicolons, or parentheses. Strip "I hope this email finds you well" and every chatbot or sycophantic artifact.
5. **Length check.** If the body is longer than one screen, lead with the point then break into short blocks. If it is a debate or high-emotion topic, say so and suggest a call plus a short summary email instead (email rule: when to avoid email).
6. **Output.** Present subject and body as plain text, ready to copy. Offer one alternative only if a real fork exists (for example: more formal vs. more casual register).

## Output Format

```
Subject: [Action|Decision|Update|Risk]: <topic>

<body>
```

Keep it to what Max can send as-is. No commentary inside the email. Put any notes to Max (assumptions made, a missing fact you filled with a placeholder) below the email, not inside it.
