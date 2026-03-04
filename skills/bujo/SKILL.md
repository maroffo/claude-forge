---
name: bujo
description: "Bullet Journal management: daily/weekly/monthly logs, task migration, reviews. Use when user says daily log, bujo, weekly review, monthly log, journal, migrate tasks, what's on my plate. Not for task sync with external tools (use bujo-sync)."
compatibility: "Requires Obsidian CLI (obsidian MCP commands)."
---

# ABOUTME: Bullet Journal orchestration for daily/weekly/monthly logs and task migration
# ABOUTME: Creates notes from templates, aggregates completed/migrated tasks, handles reviews

# Bullet Journal

**Vault path:** `Journal/` in Obsidian vault
**Templates:** `Journal/Templates/` (Daily Note, Weekly Review, Monthly Log)
**Obsidian skill:** See `../obsidian/SKILL.md` for vault CLI commands

## Commands

### `bujo daily`

Create today's daily note from template (if it doesn't exist). Show summary of today's tasks.

```bash
# Check if today's note exists
obsidian read file="Journal/Daily/$(date +%Y-%m-%d)"

# If not found, create from template
obsidian template:create template="Journal/Templates/Daily Note" name="Journal/Daily/$(date +%Y-%m-%d)"

# Show summary
obsidian read file="Journal/Daily/$(date +%Y-%m-%d)"
```

If the daily note already exists, just read and summarize it. Highlight:
- Open tasks count per section (Wishew, HikmaAI, Personal)
- Events for today
- Any notes

### `bujo weekly`

Create weekly review for current week. Scan all daily notes from the week.

1. Determine current ISO week: `date +%Y-W%V`
2. Read all daily notes for the week (Mon-Sun)
3. Aggregate:
   - `[x]` completed tasks per project
   - `[>]` migrated tasks
   - `[-]` cancelled tasks
   - Open `[ ]` tasks (carried forward)
4. Create `Journal/Weekly/YYYY-Www.md` from template
5. Pre-populate "Accomplished" with completed tasks
6. Pre-populate "Carried Forward" with open tasks
7. Calculate metrics (completed, migrated, cancelled counts)

```bash
# Read daily notes for the week
for day in $(python3 -c "
from datetime import date, timedelta
import sys
today = date.today()
start = today - timedelta(days=today.weekday())
for i in range(7):
    d = start + timedelta(days=i)
    if d <= today:
        print(d.isoformat())
"); do
  obsidian read file="Journal/Daily/$day" 2>/dev/null
done
```

### `bujo monthly`

Create monthly log for current month. Summarize week by week.

1. Determine current month: `date +%Y-%m`
2. Read all weekly reviews for the month
3. Create `Journal/Monthly/YYYY-MM.md` from template (if not exists)
4. Populate weekly summaries
5. Migrate incomplete tasks from previous month

### `bujo migrate`

Scan yesterday's daily note for open tasks. For each one, ask what to do.

1. Read yesterday's daily note
2. Find all `- [ ]` items
3. For each task:
   - **Task with sync ID** (`[CU-xxx]` or `[LIN-xxx]`): mark as `[>]` in yesterday's note. It will reappear via `bujo sync`.
   - **Personal task**: ask Max what to do:
     - **Migrate**: copy to today's daily note, mark `[>]` in yesterday's
     - **Cancel**: mark `[-]` in yesterday's
     - **Future Log**: move to `Journal/Future Log.md`, mark `[>]` in yesterday's
     - **Complete**: mark `[x]` (did it but forgot to check off)
4. Update yesterday's note with `[>]` or `[-]` markers

**Migration format:**
```markdown
# Yesterday's note:
- [>] Task that was migrated [CU-abc]
- [-] Task that was cancelled
- [x] Task completed

# Today's note (Personal section):
- [ ] Migrated personal task
```

### `bujo review`

Show today's daily note with highlights on overdue/blocked items.

1. Read today's daily note
2. Highlight:
   - Tasks marked `**BLOCKS**`: these are blocking others
   - Tasks that appeared in previous days but are still open
   - Total counts per project
3. Present a quick summary

## Bullet Key

| Symbol | Meaning |
|--------|---------|
| `- [ ]` | Open task |
| `- [x]` | Completed task |
| `- [>]` | Migrated (moved forward) |
| `- [-]` | Cancelled |
| `- [!]` | Event |
| `- [i]` | Note/info |

## File Paths

| Type | Pattern | Example |
|------|---------|---------|
| Daily | `Journal/Daily/YYYY-MM-DD.md` | `Journal/Daily/2026-02-22.md` |
| Weekly | `Journal/Weekly/YYYY-Www.md` | `Journal/Weekly/2026-W08.md` |
| Monthly | `Journal/Monthly/YYYY-MM.md` | `Journal/Monthly/2026-02.md` |
| Future Log | `Journal/Future Log.md` | |
| Collections | `Journal/Collections/*.md` | |

## Sync Integration

Task sync is handled by the `bujo-sync` skill. This skill only manages note creation, migration, and review.

Sync markers in daily notes (HTML comments) delimit zones where `bujo-sync` writes. This skill NEVER modifies content between sync markers.

```
<!-- bujo-sync:clickup:start -->
(bujo-sync writes here)
<!-- bujo-sync:clickup:end -->
```
