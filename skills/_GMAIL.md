# ABOUTME: Shared Gmail configuration and commands for email skills
# ABOUTME: Account config, gog CLI operations, common search patterns

# Gmail Configuration

- **Account**: maroffo@gmail.com
- **Tool**: `gog` CLI

## Common Operations

| Operation | Command |
|---|---|
| Search | `gog gmail search "<query>" --account=maroffo@gmail.com --json` |
| Get thread | `gog gmail thread get <threadId> --account=maroffo@gmail.com --json` |
| Archive | `gog gmail thread modify <threadId> --account=maroffo@gmail.com --remove=INBOX` |
| Mark read | `gog gmail thread modify <threadId> --account=maroffo@gmail.com --remove=UNREAD` |
| Star | `gog gmail thread modify <threadId> --account=maroffo@gmail.com --add=STARRED` |
| Trash | `gog gmail thread modify <threadId> --account=maroffo@gmail.com --add=TRASH` |
| Open URL | `gog gmail url <threadId>` |
| Get message | `gog gmail get <messageId> --account=maroffo@gmail.com --json` |

## Search Operators

| Operator | Example |
|---|---|
| Unread | `is:unread` |
| Label | `label:newsletters` |
| From | `from:substack.com` |
| Category | `category:promotions` |
| Age | `older_than:7d` |
| Date range | `after:2025/01/01 before:2025/02/01` |
| Read status | `is:read` / `is:unread` |
| Combine | `is:unread (from:a.com OR from:b.com)` |
