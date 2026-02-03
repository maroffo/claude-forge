---
name: clickup
description: "ClickUp task management via MCP. Use for task updates, comments, time tracking, workspace navigation. Always interact in English."
allowed-tools: [mcp__clickup__*]
---

# ABOUTME: ClickUp MCP integration for task management and workflow automation
# ABOUTME: Task CRUD, comments, time tracking, workspace hierarchy, search

# ClickUp MCP Integration

## Critical Rules

1. **ALL content in English** - task names, descriptions, comments
2. **Never guess IDs** - always search or ask
3. **Read before update** - understand current state
4. **Check comments** - automation adds branch names, CI links

---

## Quick Reference

```
# Search → Get → Update flow
clickup_search → keywords: "task name"
clickup_get_task → task_id: "abc123"
clickup_update_task → task_id, status: "in progress"
clickup_get_task_comments → task_id (check for branch name)
clickup_create_task_comment → task_id, comment_text: "..."
```

---

## Task Tools

| Tool | Use |
|------|-----|
| `clickup_search` | Find tasks (keywords, filters, dates) |
| `clickup_get_task` | Get details (subtasks=true for children) |
| `clickup_create_task` | Create (requires list_id - ask user!) |
| `clickup_update_task` | Update status/priority/dates/assignees |
| `clickup_get_task_comments` | Read comments (branch names!) |
| `clickup_create_task_comment` | Add comment (notify_all=true) |
| `clickup_attach_task_file` | Attach via URL or base64 |
| `clickup_add_tag_to_task` | Add existing tag |
| `clickup_remove_tag_from_task` | Remove tag |

### Search Filters

```
filters:
  asset_types: ["task"]
  task_statuses: ["active", "in progress"]
  assignees: ["me"]  # or user ID
  due_date_from: "2025-01-01"
  due_date_to: "2025-01-31"
```

---

## Time Tracking

| Tool | Use |
|------|-----|
| `clickup_start_time_tracking` | Start timer (task_id, description, billable) |
| `clickup_stop_time_tracking` | Stop current timer |
| `clickup_get_current_time_entry` | Check running timer |
| `clickup_add_time_entry` | Manual entry (start + duration or end) |
| `clickup_get_task_time_entries` | Get entries for task |

---

## Workspace Tools

| Tool | Use |
|------|-----|
| `clickup_get_workspace_hierarchy` | Get structure (max_depth: 0-2) |
| `clickup_get_list` / `clickup_create_list` | List operations |
| `clickup_get_folder` / `clickup_create_folder` | Folder operations |
| `clickup_get_workspace_members` | All members |
| `clickup_find_member_by_name` | Find by name/email |
| `clickup_resolve_assignees` | Convert names to IDs |

---

## Documents

| Tool | Use |
|------|-----|
| `clickup_create_document` | Create doc (parent: type 4=space, 5=folder, 6=list) |
| `clickup_list_document_pages` | List pages |
| `clickup_get_document_pages` | Get content (text/md or text/html) |
| `clickup_create_document_page` | Add page |
| `clickup_update_document_page` | Edit (replace/append/prepend) |

---

## Chat

```
clickup_get_chat_channels
clickup_send_chat_message → channel_id, content, content_format: "text/md"
```

---

## Workflow: Starting a Task

1. **Search:** `clickup_search` → keywords
2. **Get details:** `clickup_get_task` → task_id
3. **Check comments:** `clickup_get_task_comments` → find branch name
4. **Update status:** `clickup_update_task` → status: "in progress"
5. **Create branch** using name from comment

## Workflow: Completing a Task

1. **Add comment:** `clickup_create_task_comment` → "Completed. MR: https://..."
2. **Update status:** `clickup_update_task` → status: "ready for review"

---

## Status Values (vary by list)

| Status | Use |
|--------|-----|
| `to do` | Not started |
| `in progress` | Active work |
| `ready for review` | Awaiting review |
| `blocked` | Cannot proceed |
| `complete` | Done |

---

## Common Errors

| Error | Fix |
|-------|-----|
| Task not found | Search by name to get correct ID |
| List not found | Use hierarchy or search |
| Invalid status | Check list's available statuses |
| Tag not found | Use existing tags only |

---

## Git Integration

Branch format from automation: `<type>/<task-name>_CU-<task-id>`

Example: `feature/user-auth_CU-abc123`

1. Task created → automation adds branch comment
2. Read comment → get branch name
3. Work & commit → reference task ID
4. Create MR → link to task
5. Update status → "ready for review" → "complete"
