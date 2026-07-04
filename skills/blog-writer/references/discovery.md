# ABOUTME: Topic-discovery sub-workflow for the blog-writer skill (Mode 1, no input)
# ABOUTME: Vault-scan steps, signal heuristics, and the idea-presentation table

# Discovery Mode (Mode 1)

Triggered when the user invokes without a specific topic ("what should I write about?", "blog ideas").

## Step 0: Check cached discovery

```bash
obsidian read path="maroffo-blog/Blog Discovery - <latest>.md"
```

If a discovery note exists and is <30 days old, use it as baseline. Only scan new Timeline entries since the last scan date:

```bash
obsidian read path="Second Brain/Second Brain - Timeline.md"
# Filter entries after the "Last scan" date in the discovery note
```

Update the discovery note in-place with new findings. Skip full vault scan.

## Step 0a: Full scan (only if no cached discovery or >30 days old)

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

## Step 0b: Cross-check IDEAS.md

```bash
cat /Users/maroffo/Development/private/blog/IDEAS.md
```

Check if any existing idea now has sufficient vault material to write.

## Step 0c: Cross-check published posts

```bash
ls /Users/maroffo/Development/private/blog/content/posts/
```

Avoid proposing topics already covered (unless significant new angle).

## Step 0d: Save/update discovery note

Save results to `maroffo-blog/Blog Discovery - YYYY-MM.md` via obsidian create/append. Include: published posts table, ranked candidates, secondary candidates, scan date.

## Step 0e: Present 3-5 ideas

For each idea, show:

| Field | Content |
|-------|---------|
| **Title** | Working title |
| **Angle** | What makes this post unique (not another tutorial) |
| **Vault sources** | Which Second Brain entries, how many, how recent |
| **Signal strength** | Strong (5+ sources) / Medium (3-4) / Emerging (2) |
| **Gap** | What's missing in existing content on this topic |

Use `AskUserQuestion` to let Max pick one (or refine).
