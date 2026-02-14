---
name: inbox-triage
description: Review and prioritize Gmail inbox. Use when user wants to check email, review inbox, or see what needs attention.
tools: Bash, Read, Write, Edit
---

# ABOUTME: Gmail inbox triage - categorize unread by priority, suggest actions
# ABOUTME: P1-P4 priority system with batch operations

# Inbox Triage Skill

**Gmail:** See `../_GMAIL.md` for account config and commands.

## Workflow

### Step 1: Get Inbox Overview

```bash
# Get unread count
gog gmail labels get INBOX --account=maroffo@gmail.com --json

# Get unread emails (most recent first)
gog gmail search "is:unread in:inbox" --account=maroffo@gmail.com --max=30 --json
```

### Step 2: Categorize Emails

For each unread thread, categorize by:

**Priority Levels:**
- **P1 - Urgent**: Direct messages from known contacts, time-sensitive, action required
- **P2 - Important**: Work-related, personal correspondence, bills/receipts
- **P3 - Normal**: Newsletters worth reading, notifications to review
- **P4 - Low**: Promotions, social updates, automated notifications

**Quick Filters:**
```bash
# People emails (likely important)
gog gmail search "is:unread -category:promotions -category:social -category:updates" --account=maroffo@gmail.com --json

# Promotions (batch process)
gog gmail search "is:unread category:promotions" --account=maroffo@gmail.com --json

# Updates/notifications
gog gmail search "is:unread category:updates" --account=maroffo@gmail.com --json
```

### Step 3: Present Summary

Format output as:

```
## Inbox Triage - [Date]

**Unread:** X messages

### P1 - Urgent (X)
- [ ] From: [sender] - [subject] - [snippet]

### P2 - Important (X)
- [ ] From: [sender] - [subject] - [snippet]

### P3 - Normal (X)
- [ ] From: [sender] - [subject]

### P4 - Low Priority (X)
- Promotions: X
- Social: X
- Updates: X

### Suggested Actions
- Archive all promotions older than 7 days
- [Other suggestions based on content]
```

### Step 4: Handle User Actions

See `../_GMAIL.md` for modify commands (mark read, archive, star, trash).

**Useful filters:**
```bash
gog gmail search "is:unread -category:{promotions social updates forums}" --account=maroffo@gmail.com --json  # Real people
gog gmail search "is:unread to:me -category:promotions" --account=maroffo@gmail.com --json                   # Needs reply
```

## Rules

1. **Summarize first** - don't read full content unless asked
2. **Respect privacy** - don't read personal emails in detail without permission
3. **Batch operations** - group similar actions (archive all promos, etc.)
4. **Confirm destructive actions** - always confirm before trash/delete
5. **Open in browser** - use `gog gmail url <threadId>` for user to read full email
