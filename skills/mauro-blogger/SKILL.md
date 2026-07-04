---
name: mauro-blogger
description: "Write blog posts in Mauro Medda's voice for mauro.medda.xyz. Use when user says mauro blog, post per mauro, write as mauro, mauro blogger. Two registers: founder/reflective essays and no-fluff technical how-tos, tone extracted from his published posts. Drafts to Mauro-Blog vault folder, humanizes. Not for Max's blog (use blog-writer)."
compatibility: "Reference posts in the Obsidian vault folder Mauro-Blog/. Follows blog-writer workflow rules and humanizer patterns."
tools: Bash, Read, Write, Edit, AskUserQuestion, WebFetch, WebSearch
---

# ABOUTME: Write blog posts in Mauro Medda's voice, drafted into the Mauro-Blog vault folder
# ABOUTME: Reuses blog-writer workflow (outline approval, second opinion, humanize) with Mauro's tone

# Mauro Blogger

Write posts for Mauro's blog (Hugo, mauro.medda.xyz). Voice is extracted from his published posts, clipped into the vault at:

```
/Users/maroffo/Library/Mobile Documents/iCloud~md~obsidian/Documents/Mauro-Blog/
```

**Workflow rules:** inherited from `../blog-writer/SKILL.md` (Quality Notes, outline approval, second opinion, humanizer pass). **Voice:** see `references/tone-of-voice.md` (read it BEFORE outlining). **Humanizer:** `../humanizer/SKILL.md` patterns apply, with one override noted below.

## Quality Notes

- Read `references/tone-of-voice.md` and at least 2 reference posts before drafting. The voice is the deliverable.
- Pick the register first (essay vs how-to); they have different structures. Do not mix.
- Do not skip outline approval or the humanizer pass.
- English only. Mauro publishes in English; never translate technical terms.

## Workflow

### Step 1: Gather context

1. Read `references/tone-of-voice.md`.
2. Read the reference posts in `Mauro-Blog/` closest to the requested topic (essay topic: read Marathon Mindset + Coding with AI; technical topic: read the two DGX Spark posts).
3. Collect material: user-provided notes, vault search, `WebSearch`/`WebFetch` for data and citations. Essays lean on named statistics (Mauro bolds real numbers with sources); how-tos lean on exact commands with expected output.

### Step 2: Pick the register

| Register | When | Skeleton |
|----------|------|----------|
| Founder essay | Opinion, work practices, AI-era reflections | Hook (shared pain, direct address) -> uncomfortable truth + bold stats -> numbered personal practices -> reframe ending -> signed `— Mauro` |
| Technical how-to | Install, benchmark, homelab, infra | Scope statement ("No fluffy information...") + skip link -> short context sections -> numbered steps with commands AND expected output -> tables/decision matrix -> terse closer, no sign-off |

### Step 3: Outline (requires approval)

Present title, register, target length, sections, sources. Wait for approval. Do NOT proceed without it.

Length: essays 1200-1800 words, how-tos as long as the commands require, zero padding.

### Step 4: Draft

Save to the vault folder as `Mauro-Blog/Draft - <Title>.md` with Hugo front matter:

```yaml
---
title: "..."
date: YYYY-MM-DD
summary: "1-2 concrete sentences"
tags: [...]
draft: true
---
```

Apply the voice checklist in `references/tone-of-voice.md` while writing, not after.

### Step 5: Second opinion (mandatory, as per blog-writer)

Run `/second-opinion` on the draft: factual accuracy, argument coherence, voice fidelity vs the reference posts, AI artifacts.

### Step 6: Humanize

Apply humanizer patterns. **Override note:** Mauro's originals use em dashes heavily, but drafts follow the humanizer hard rule (no em dashes): reproduce his punchy rhythm with periods, colons, and short fragments instead ("That's not leadership. That's hypocrisy.").

### Step 7: Report

File path, title, word count, register, tags, open questions for Mauro. No cover image by default (his posts are text-only: "no fancy images"); offer one only if asked.

## Common Issues

| Issue | Solution |
|-------|----------|
| Voice drifts into Max's style | Re-read reference posts; Mauro is warmer, more second-person, fewer separators, no methodology notes |
| Essay reads like a listicle | Convert bullets to second-person narrative scenes; keep numbered sections only for practices/rules |
| How-to gets wordy | Cut to commands + one-line justification each ("Old-school, works every time.") |
| No real statistics available | Drop the stat, do not invent; Mauro bolds only concrete numbers |
| Draft location unclear | Vault `Mauro-Blog/Draft - <Title>.md`; Mauro moves it to his Hugo repo himself |
