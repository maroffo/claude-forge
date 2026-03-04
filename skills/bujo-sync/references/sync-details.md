# ABOUTME: Detailed sync state format, conflict resolution, and push flow for BuJo sync
# ABOUTME: Reference companion to bujo-sync SKILL.md with JSON schema and edge cases

# BuJo Sync Details

## Sync State File

`Journal/.bujo-sync-state.json` tracks last sync timestamp and per-task state. Initialize as empty object `{}` on first run.

```json
{
  "lastSync": "2026-02-22T10:30:00Z",
  "tasks": {
    "CU-abc123": {
      "title": "Task name",
      "status": "in progress",
      "lastSeen": "2026-02-22"
    },
    "LIN-xyz789": {
      "title": "Issue title",
      "status": "todo",
      "lastSeen": "2026-02-22"
    }
  }
}
```

---

## Push Flow (`bujo sync push`)

### 1. Scan daily note

Read today's daily note. For each task with a sync ID:

| BuJo State | Action |
|-----------|--------|
| `[x]` with `[CU-xxx]` | Mark complete in ClickUp |
| `[x]` with `[LIN-xxx]` | Mark done in Linear |
| `[-]` with `[CU-xxx]` | Mark cancelled in ClickUp |
| `[-]` with `[LIN-xxx]` | Mark cancelled in Linear |
| New task in sync zone (no ID) | Create in corresponding system, append ID |

### 2. Update source systems

Use ClickUp MCP to update task status, Linear MCP to update issue state.

### 3. Update sync state

Reflect the pushed changes in `Journal/.bujo-sync-state.json`.

---

## Conflict Resolution

| Scenario | Winner | Rationale |
|----------|--------|-----------|
| Status differs (BuJo vs source) | Source wins | ClickUp/Linear are team source of truth |
| Annotations/notes differ | BuJo wins | Max's personal notes are authoritative |
| Both status AND text changed | Report conflict | Ask Max to decide |

When a conflict is detected:
1. Show the conflicting values
2. Ask Max which version to keep
3. Apply the decision to both systems

---

## Error Handling

- MCP server unreachable: skip that source, warn Max, sync the other
- Task ID not found upstream: warn, keep in daily note with `[?]` marker
- Rate limits: back off, report partial sync results
