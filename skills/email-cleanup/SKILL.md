---
name: email-cleanup
description: Clean up Gmail - archive old emails, delete promotions, manage storage. Use when user wants to clean inbox, archive emails, or free up space.
tools: Bash, Read
---

# Email Cleanup Skill

Bulk cleanup operations for Gmail - archive, delete, organize.

## Gmail Configuration

- **Account**: maroffo@gmail.com
- **Tool**: `gog` CLI

## Safety Rules

1. **NEVER delete without confirmation** - always show what will be affected first
2. **Archive over delete** - prefer archiving (recoverable) over trash
3. **Show counts first** - before any bulk operation, show how many emails
4. **Batch in chunks** - process max 50 at a time to avoid timeouts

## Cleanup Operations

### 1. Archive Old Promotions

```bash
# Count first
gog gmail search "category:promotions older_than:30d" --account=maroffo@gmail.com --json | jq '.resultSizeEstimate'

# Get thread IDs
THREADS=$(gog gmail search "category:promotions older_than:30d" --account=maroffo@gmail.com --json --max=50 | jq -r '.threads[].id')

# Archive (remove from inbox)
for tid in $THREADS; do
  gog gmail thread modify $tid --account=maroffo@gmail.com --remove-labels=INBOX
done
```

### 2. Clean Social Updates

```bash
# Count
gog gmail search "category:social older_than:14d" --account=maroffo@gmail.com --json | jq '.resultSizeEstimate'

# Archive
THREADS=$(gog gmail search "category:social older_than:14d" --account=maroffo@gmail.com --json --max=50 | jq -r '.threads[].id')
for tid in $THREADS; do
  gog gmail thread modify $tid --account=maroffo@gmail.com --remove-labels=INBOX
done
```

### 3. Archive Read Notifications

```bash
# Count read notifications older than 7 days
gog gmail search "category:updates is:read older_than:7d" --account=maroffo@gmail.com --json | jq '.resultSizeEstimate'

# Archive
THREADS=$(gog gmail search "category:updates is:read older_than:7d" --account=maroffo@gmail.com --json --max=50 | jq -r '.threads[].id')
for tid in $THREADS; do
  gog gmail thread modify $tid --account=maroffo@gmail.com --remove-labels=INBOX
done
```

### 4. Delete Large Attachments (Free Storage)

```bash
# Find large emails
gog gmail search "larger:10M" --account=maroffo@gmail.com --json

# Review each before deciding
gog gmail thread get <threadId> --account=maroffo@gmail.com --json | jq '{from: .messages[0].payload.headers[] | select(.name=="From") | .value, subject: .messages[0].payload.headers[] | select(.name=="Subject") | .value}'
```

### 5. Unsubscribe Candidates

Find senders you never open:

```bash
# Newsletters always marked as read (auto-archived?)
gog gmail search "unsubscribe is:read older_than:30d" --account=maroffo@gmail.com --json --max=20

# Group by sender to identify patterns
```

## Standard Cleanup Routine

When user asks to "clean up email":

### Step 1: Analyze

```bash
echo "=== Email Cleanup Analysis ==="

# Promotions
echo "Promotions (>30d):"
gog gmail search "category:promotions older_than:30d" --account=maroffo@gmail.com --json | jq '.resultSizeEstimate'

# Social
echo "Social (>14d):"
gog gmail search "category:social older_than:14d" --account=maroffo@gmail.com --json | jq '.resultSizeEstimate'

# Updates (read)
echo "Read updates (>7d):"
gog gmail search "category:updates is:read older_than:7d" --account=maroffo@gmail.com --json | jq '.resultSizeEstimate'

# Large emails
echo "Large emails (>10MB):"
gog gmail search "larger:10M" --account=maroffo@gmail.com --json | jq '.resultSizeEstimate'
```

### Step 2: Present Options

```
## Cleanup Recommendations

| Category | Count | Suggested Action |
|----------|-------|------------------|
| Old promotions (>30d) | X | Archive |
| Old social (>14d) | X | Archive |
| Read updates (>7d) | X | Archive |
| Large emails (>10MB) | X | Review individually |

**Estimated space saved:** ~X MB

Which would you like to proceed with?
1. Archive all (safe, recoverable)
2. Review large emails first
3. Custom selection
```

### Step 3: Execute with Confirmation

Always confirm before executing:

```
Archiving X promotions older than 30 days...
- Processing batch 1/3 (50 emails)...
- Processing batch 2/3 (50 emails)...
- Processing batch 3/3 (23 emails)...

Done! 123 emails archived.
```

## Quick Commands

```bash
# Count by category
gog gmail labels get CATEGORY_PROMOTIONS --account=maroffo@gmail.com
gog gmail labels get CATEGORY_SOCIAL --account=maroffo@gmail.com
gog gmail labels get CATEGORY_UPDATES --account=maroffo@gmail.com

# Inbox size
gog gmail labels get INBOX --account=maroffo@gmail.com

# Spam (auto-clean)
gog gmail labels get SPAM --account=maroffo@gmail.com

# Trash (will be auto-deleted after 30 days)
gog gmail labels get TRASH --account=maroffo@gmail.com
```

## Dangerous Operations (Require --force)

```bash
# Permanently delete (NOT recoverable!)
gog gmail batch delete <msgId1> <msgId2> --account=maroffo@gmail.com --force

# Empty trash
# (Not directly supported - trash auto-empties after 30 days)
```

**NEVER run delete without explicit user confirmation.**
