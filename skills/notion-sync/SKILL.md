---
name: notion-sync
description: "Sync Notion workspace to Obsidian vault with AI summaries. Use when user says notion sync, sync notion, pull from notion, push to notion, or /notion-sync. Not for direct Obsidian vault operations (use obsidian skill)."
compatibility: "Requires uv, .env with NOTION_TOKEN and ANTHROPIC_API_KEY at ~/Development/hikmaAI/automation/hikmaai_notion_obsidian_sync/"
---

# ABOUTME: Notion to Obsidian vault sync via hikma-sync CLI
# ABOUTME: Pull pages/databases, push notes, AI summaries, incremental sync

# Notion Sync

Wraps the `hikma-sync` CLI at `~/Development/hikmaAI/automation/hikmaai_notion_obsidian_sync/`.

## Commands

All commands run from the project directory:

```bash
cd ~/Development/hikmaAI/automation/hikmaai_notion_obsidian_sync
```

### Pull (Notion to vault)

```bash
# Everything configured in config.yaml
uv run hikma-sync pull

# Single page by name
uv run hikma-sync pull --page "Local dev"

# Single database (index + items)
uv run hikma-sync pull --db "Product Requirements"

# Force re-sync (ignore cached state)
uv run hikma-sync pull --force

# Skip AI summary generation
uv run hikma-sync pull --no-ai
```

### Push (vault to Notion)

```bash
# Push a vault note to a Notion database
uv run hikma-sync push --note "Projects/HikmaAI/Notion/My Note" --to "Engineering Wiki"

# With custom title
uv run hikma-sync push --note "path/to/note" --to "Engineering Wiki" --title "Custom Title"
```

### Status

```bash
uv run hikma-sync status
```

## Execution Flow

1. `cd` to project directory
2. Run the requested command
3. Present output to user (synced count, skipped, errors)
4. For `pull`: mention which pages got AI summaries (>2000 words)

## Configuration

Pages and databases are configured in `config.yaml`. To add a new one:

1. Get the Notion page/database UUID (from the URL or Notion API)
2. Add entry to `config.yaml` under `pages:` or `databases:`
3. For databases, set `sync_items: true` to sync individual pages

## Common Issues

| Issue | Solution |
|-------|----------|
| "Missing environment variable" | Check `.env` has `NOTION_TOKEN` and `ANTHROPIC_API_KEY` |
| 404 on database | Verify the UUID in `config.yaml`, ensure Notion integration has access |
| CLI write failed | Normal if Obsidian app not running; filesystem fallback handles it |
| No AI summary generated | Page under 2000 words, or `--no-ai` flag used |
