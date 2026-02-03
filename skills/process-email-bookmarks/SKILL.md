---
name: process-email-bookmarks
description: Process bookmarks from Gmail. Use when user mentions email bookmarks, Gmail bookmarks, or wants to process saved links from email.
tools: Bash, Read, Write, Edit, Glob
---

# Process Email Bookmarks Skill

You process bookmarks sent via email (Gmail label "📑 Bookmarks") and integrate them into the Second Brain.

## Gmail Configuration

- **Account**: maroffo@gmail.com
- **Label**: 📑 Bookmarks (ID: Label_2765838113845362546)
- **Tool**: `gog` CLI

## Processing Workflow

### Step 1: Find Unread Bookmark Emails

```bash
gog gmail search "label:📑 Bookmarks is:unread" --account=maroffo@gmail.com --json
```

### Step 2: For Each Email Thread

1. **Get full thread content**:
```bash
gog gmail thread get <threadId> --account=maroffo@gmail.com --json
```

2. **Extract bookmark info**:
   - URL (from email body or links)
   - Title (from subject or link text)
   - Description (from email body)
   - Any notes added by user

3. **Categorize** - determine destination:
   - AI, LLM, agents → `Second Brain - AI Agents and Tools.md`
   - Claude Code, skills → `Second Brain - Claude Code.md`
   - Go, Python, Java, CLI → `Second Brain - Development.md`
   - Docker, K8s, Terraform, cloud → `Second Brain - DevOps and Cloud.md`
   - Productivity, leadership → `Second Brain - Engineering Management.md`
   - Reference only → `Bookmarks/` folder

4. **Decide content type**:
   - **Actionable** (tutorials, tools, patterns) → Fetch page, extract insights, add to Second Brain
   - **Reference** (articles, news, opinions) → Add to Bookmarks file

### Step 3: Fetch and Process (for actionable content)

If the bookmark contains actionable knowledge:
```bash
# Use WebFetch to get page content
```

Extract:
- Tool/library name
- Key features (bullet points)
- Code snippet if useful
- Source URL

### Step 4: Integration

**For Second Brain** - add distilled content:
```markdown
### [Tool Name]

Brief description.

| Feature | Description |
|---------|-------------|
| **Feature** | What it does |

- [Source](url)
```

**For Bookmarks** - add to appropriate file:
```markdown
- [Title](url) - Brief description
```

### Step 5: Update Timeline

Add entry to `Second Brain - Timeline.md`:
```markdown
- **YYYY-MM-DD** | [Title](url) | Source: Email | → Second Brain - [File].md
```

### Step 6: Mark Email as Read

```bash
gog gmail thread modify <threadId> --account=maroffo@gmail.com --remove-labels=UNREAD
```

## Output Format

After processing each bookmark:
```
✓ Processed: [Title]
  → Source: Email (thread: <threadId>)
  → Added to: Second Brain - [File].md#[Section]
  → Type: [Actionable/Reference]
  → Email marked as read
```

## Example

**Input email**: Subject "Interesting Go library for CLI" with link to charm.sh

**Processing**:
1. Search unread bookmarks
2. Get thread content
3. Extract URL: https://charm.sh
4. Fetch page content
5. Categorize: Development (Go, CLI)
6. Extract: Charm - Go libraries for CLI apps (Bubble Tea, Lip Gloss, etc.)
7. Add to Second Brain - Development.md
8. Log to Timeline
9. Mark email read

## Commands Reference

```bash
# Search unread bookmarks
gog gmail search "label:📑 Bookmarks is:unread" --account=maroffo@gmail.com --json

# Get thread
gog gmail thread get <threadId> --account=maroffo@gmail.com --json

# Mark as read
gog gmail thread modify <threadId> --account=maroffo@gmail.com --remove-labels=UNREAD

# Get single message
gog gmail get <messageId> --account=maroffo@gmail.com --json
```

## Rules

1. **Always fetch full content** - don't rely on email snippet alone
2. **Be concise** - extract only key insights
3. **Preserve URLs** - always include source link
4. **Update Timeline** - every processed item gets logged
5. **Mark as read** - only after successful integration
6. **Ask if unclear** - if categorization is ambiguous, ask user
