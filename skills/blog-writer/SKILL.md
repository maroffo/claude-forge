---
name: blog-writer
description: "Write blog posts from Second Brain content, IDEAS.md, or free prompts. Use when user says write blog post, blog post, vault to blog, scrivi un post, blog ideas, what should I write about. Discovers topics from vault signals, drafts in Max's style, humanizes, generates cover. Not for processing content INTO the vault (use process-clippings, newsletter-digest)."
compatibility: "Requires Obsidian CLI (obsidian MCP commands). Blog repo at /Users/maroffo/Development/private/blog."
tools: Bash, Read, Write, Edit, AskUserQuestion, WebFetch, WebSearch
---

# ABOUTME: Write blog posts from Second Brain, IDEAS.md, or free prompts with vault-backed research
# ABOUTME: Discovers topics, drafts in Max's style, humanizes AI patterns, generates cover image

# Blog Writer

Write blog posts for Max's Hugo blog (PaperMod theme). Four entry points: discover topics, expand a vault note, develop an IDEAS.md idea, or write from a free prompt.

**Obsidian CLI:** See `../_OBSIDIAN.md` | **Second Brain:** See `../_SECOND_BRAIN.md`

## Quality Notes

- Take your time with each step. A blog post is public, permanent content.
- Quality over speed. Better to write 2500 sharp words than 4000 padded ones.
- Do not skip the humanizer pass. Max's voice is direct, opinionated, evidence-backed.
- Do not skip outline approval. The structure determines the post's quality.

---

## Blog Structure

```
/Users/maroffo/Development/private/blog/
├── content/posts/YYYY-MM-DD-slug-title.md   ← posts go here
├── static/images/                            ← cover images
├── IDEAS.md                                  ← structured idea backlog
└── hugo.toml                                 ← site config
```

### Vault Folder

Blog artifacts live in `maroffo-blog/` in the Obsidian vault (NOT `Mauro-Blog/`, that's a different person's blog).

```
maroffo-blog/
├── Blog Discovery - YYYY-MM.md   ← topic discovery results, updated incrementally
└── (future: drafts, outlines)
```

**Discovery note**: always read `maroffo-blog/Blog Discovery - <latest>.md` before scanning the full vault. If it exists and is <30 days old, only scan Timeline entries after the last scan date.

### Front Matter Template

```yaml
---
title: "..."
date: YYYY-MM-DD
summary: "1-2 sentences, concrete, no fluff"
tags: [from mapping + free tags]
draft: true
cover:
  image: "images/cover-<slug>.png"
  alt: "..."
  relative: false
---
```

### Tag Mapping (Second Brain -> Blog)

| Second Brain Category | Default Blog Tags |
|---|---|
| AI Agents and Tools | `ai`, `llm` |
| Claude Code | `ai`, `claude-code` |
| Development | language-specific: `golang`, `python`, `swift`, etc. |
| DevOps and Cloud | `devops`, `cloud` |
| Engineering Management | `engineering`, `leadership` |
| Politics and Economics | `politics`, `opinion` |
| Marketing | `marketing` |
| Media and Culture | `culture` |
| Health and Science | `science` |

Add post-specific free tags: project names (`hikmaai`, `wishew`), tools (`obsidian`, `pgvector`), themes (`side-project`, `security`).

---

## Entry Points

### Mode 1: Discover (no input)

Triggered when user invokes without a specific topic ("what should I write about?", "blog ideas").

**Step 0: Check cached discovery**

```bash
obsidian read path="maroffo-blog/Blog Discovery - 2026-03.md"
```

If a discovery note exists and is <30 days old, use it as baseline. Only scan new Timeline entries since the last scan date:

```bash
obsidian read path="Second Brain/Second Brain - Timeline.md"
# Filter entries after the "Last scan" date in the discovery note
```

Update the discovery note in-place with new findings. Skip full vault scan.

**Step 0a: Full scan (only if no cached discovery or >30 days old)**

```bash
# Recent additions
obsidian search query="added: 2026" path="Second Brain"

# Timeline for volume signals
obsidian read path="Second Brain/Second Brain - Timeline.md"

# Unprocessed clippings (potential raw material)
obsidian files folder=Clippings ext=md
```

Look for:
- **Accumulation signal**: 3+ entries on the same topic in the last 30 days
- **Opinion signal**: breadcrumbs or log entries where Max expressed a view
- **Gap signal**: vault topic with no corresponding blog post
- **Timeliness signal**: topic trending in recent newsletters/clippings

**Step 0b: Cross-check IDEAS.md**

```bash
cat /Users/maroffo/Development/private/blog/IDEAS.md
```

Check if any existing idea now has sufficient vault material to write.

**Step 0c: Cross-check published posts**

```bash
ls /Users/maroffo/Development/private/blog/content/posts/
```

Avoid proposing topics already covered (unless significant new angle).

**Step 0d: Save/update discovery note**

Save results to `maroffo-blog/Blog Discovery - YYYY-MM.md` via obsidian create/append. Include: published posts table, ranked candidates, secondary candidates, scan date.

**Step 0e: Present 3-5 ideas**

For each idea, show:

| Field | Content |
|-------|---------|
| **Title** | Working title |
| **Angle** | What makes this post unique (not another tutorial) |
| **Vault sources** | Which Second Brain entries, how many, how recent |
| **Signal strength** | Strong (5+ sources) / Medium (3-4) / Emerging (2) |
| **Gap** | What's missing in existing content on this topic |

Use `AskUserQuestion` to let Max pick one (or refine).

---

### Mode 2: From Vault Note

User provides a specific vault note path or topic.

```bash
obsidian read path="Second Brain/Second Brain - <Topic>.md"
```

Extract the relevant section, identify what's worth expanding into a post.

### Mode 3: From IDEAS.md

User references an idea by number or title. Read IDEAS.md, extract the structured idea (proposed angle, gap, unique value).

### Mode 4: Free Prompt

User describes the topic. Search vault for related content:

```bash
obsidian search query="<keywords>" path="Second Brain"
obsidian search query="<keywords>" path="Projects"
```

---

## Writing Workflow (all modes converge here)

### Step 1: Gather Context

Based on the chosen topic:
1. Read relevant Second Brain notes
2. Read project logs/solutions if applicable (`obsidian search query="..." path="Projects"`)
3. Read related published posts (for series linking)
4. If external research needed, use `WebSearch` / `WebFetch` for data, studies, citations

### Step 2: Outline (requires approval)

Present the outline to Max:

```
## Proposed Outline

**Title**: "..."
**Angle**: [what makes this post different from existing content]
**Target length**: ~XXXX words
**Language**: English (or Italian if requested)
**Tags**: [proposed tags]

### Sections
1. [Hook/opener] - personal anecdote or observation
2. [Problem statement] - why this matters
3. [Section N] - ...
4. [Practical examples] - code, metrics, real data
5. [Reflection] - what was learned, what's next
6. Methodology note + acknowledgments

**Series context**: [links to previous posts if part of a thread]
```

Wait for approval. Do NOT proceed without it.

### Step 3: Write Draft

Write the full post applying Max's style (see Style Guide below). Save to:

```
/Users/maroffo/Development/private/blog/content/posts/YYYY-MM-DD-<slug>.md
```

Use today's date. Slug: lowercase, hyphens, descriptive (match existing convention).

### Step 4: Second Opinion (mandatory)

Run `/second-opinion` on the draft. Ask Gemini to review for:
- Factual accuracy of cited studies
- Argument coherence and logical gaps
- Tone consistency (personal narrative vs literature review)
- Differentiation from previous posts
- Missing angles and counterarguments
- AI writing artifacts that survived the humanizer

Apply Gemini's feedback before proceeding.

### Step 5: Humanize

Apply humanizer patterns to the draft (re-run after second-opinion edits). Focus on:
- Kill AI vocabulary ("delve", "landscape", "tapestry", "foster", "crucial")
- No em dashes (use commas, colons, semicolons, parentheses)
- No rule of three unless natural
- No significance inflation ("pivotal", "testament", "game-changer")
- No sycophantic tone
- Vary sentence length; short punchy sentences mixed with longer ones
- Keep Max's voice: direct, opinionated, self-ironic, evidence-backed

Read the draft back, fix issues in-place with Edit.

### Step 6: Cover Image

Generate cover image via the cover-image skill workflow:

1. Distill the post into a visual metaphor
2. Craft prompt (black and white, hand-drawn sketch, ink strokes, 16:9)
3. Generate:
```bash
uv run ~/.claude/skills/_generate_image.py "<prompt>" --ar 16:9 -o /Users/maroffo/Development/private/blog/static/images/cover-<slug>.png
```

### Step 7: Report

```
Post written:
  File: content/posts/YYYY-MM-DD-<slug>.md
  Title: "..."
  Words: ~XXXX
  Tags: [...]
  Cover: static/images/cover-<slug>.png
  Status: draft: true
  Series: [links to related posts, if any]
```

---

## Style Guide (Max's Voice)

### Structure
- **Hook**: personal anecdote, observation, or callback to previous post (1-2 paragraphs)
- **Problem**: concrete problem statement, why it matters now
- **Sections**: 5-9 major sections with `###` headers
- **Separators**: `***` between conceptual blocks (3-6 per post)
- **Tables**: for comparisons, metrics, decision matrices
- **Code blocks**: with language identifiers, real examples from production
- **Bold**: key concepts and definitions only, not mechanical emphasis
- **Links**: `{{< ref "YYYY-MM-DD-slug" >}}` for internal, standard markdown for external

### Tone
- First person throughout ("I wrote", "I realized", "we shipped")
- Conversational but technical; assumes developer audience
- Opinionated with evidence ("This works because..." not "This might work")
- Self-aware humor and irony ("This is what happens when you have an AI that doesn't complain about scope creep")
- Honest about limitations ("I don't have this figured out", "Here's where it broke")

### Endings
- Reflection on what was learned (not generic "bright future")
- Practical next steps for readers (optional)
- `***` separator then methodology note if AI assisted
- Acknowledgments section if citing influences
- Author context (brief, contextual)

### Anti-patterns (never do)
- Generic introductions ("In today's fast-paced world...")
- Listicle-style without narrative thread
- Neutral reporting without opinion
- Padding sections to hit word count
- Concluding with "In conclusion" or summarizing what was just said

### Length
- Technical deep-dives: 2500-4000 words
- Opinion/reflection: 1500-2500 words
- Adjust based on content density; never pad

### Language
- Default: English
- Italian: only if explicitly requested or topic is Italy-specific
- Technical terms: never translate

---

## Common Issues

| Issue | Solution |
|-------|----------|
| Vault search returns too much | Filter by date range, use section anchors |
| No strong signal in discover mode | Check Clippings inbox, recent newsletters, project logs |
| Post overlaps existing article | Differentiate angle, reference previous post, or propose as update |
| Cover image generation fails | Check GEMINI_API_KEY, fall back to manual generation |
| Hugo build fails | Verify front matter YAML syntax, check for unescaped quotes in title/summary |
