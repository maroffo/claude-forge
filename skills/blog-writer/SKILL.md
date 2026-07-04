---
name: blog-writer
description: "Write blog posts from Second Brain content, IDEAS.md, or free prompts. Use when user says write blog post, blog post, vault to blog, scrivi un post, blog ideas, what should I write about. Discovers topics from vault signals, drafts in Max's style, humanizes, generates cover. Not for processing content INTO the vault (use process-clippings, newsletter-digest)."
compatibility: "Requires Obsidian CLI (obsidian MCP commands). Blog repo at /Users/maroffo/Development/private/blog."
allowed-tools: [Bash, Read, Write, Edit, AskUserQuestion, WebFetch, WebSearch]
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

### Front Matter and Tags

Hugo front matter template and the Second Brain -> Blog tag mapping live in `references/front-matter.md`. Apply them when writing the draft.

---

## Entry Points

### Mode 1: Discover (no input)

Triggered when the user invokes without a specific topic ("what should I write about?", "blog ideas"). Scan the vault for signals (cached discovery note first, then full scan), cross-check IDEAS.md and published posts, then present 3-5 ranked ideas via `AskUserQuestion`. Full step-by-step procedure in `references/discovery.md`.

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

Write the full post applying Max's style (see `references/style-guide.md`). Save to:

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

Run the humanizer skill on the draft (see `../humanizer/SKILL.md`), re-running after second-opinion edits. Keep Max's voice: direct, opinionated, self-ironic, evidence-backed. Read the draft back, fix issues in-place with Edit.

### Step 6: Cover Image

Generate the cover via the cover-image skill (see `../cover-image/SKILL.md`); output to `/Users/maroffo/Development/private/blog/static/images/cover-<slug>.png`.

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

## Style Guide and Common Issues

Max's voice (structure, tone, endings, anti-patterns, length, language) and the troubleshooting table live in `references/style-guide.md`. Read it during Step 3 (Write Draft) and when debugging output.
