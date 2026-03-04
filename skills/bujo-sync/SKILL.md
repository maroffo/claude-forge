---
name: bujo-sync
description: "Bidirectional task sync between Bullet Journal and project tools (ClickUp, Linear). Use when user says sync tasks, bujo sync, pull from clickup, pull from linear, push tasks. Not for daily logs or reviews (use bujo)."
compatibility: "Requires Obsidian CLI. Optional: ClickUp MCP server, Linear MCP server."
---

# ABOUTME: Bidirectional sync between BuJo daily notes and ClickUp (Wishew) + Linear (HikmaAI)
# ABOUTME: Pulls assigned/blocking tasks, pushes completions/cancellations, respects sync markers

# BuJo Sync

**Sync state:** `Journal/.bujo-sync-state.json`
**MCP config:** `.mcp.json` (vault root)
**Daily note sync zones:** HTML comment markers per project

## MCP Servers

| Project | Tool | MCP Server |
|---------|------|------------|
| Wishew | ClickUp | `clickup` (via `.mcp.json`) |
| HikmaAI | Linear | `linear` (via `.mcp.json`) |

## Sync Markers

Daily notes contain sync zones delimited by HTML comments:

```markdown
### Wishew (ClickUp)
<!-- bujo-sync:clickup:start -->
- [ ] Task name [CU-abc123]
- [ ] **BLOCKS** @persona: Blocking task [CU-def456]
<!-- bujo-sync:clickup:end -->

### HikmaAI (Linear)
<!-- bujo-sync:linear:start -->
- [ ] Issue title [LIN-xyz789]
<!-- bujo-sync:linear:end -->
```

**CRITICAL:** Only modify content BETWEEN the start/end markers. Never touch anything outside.

## Pull Flow (`bujo sync pull` or `bujo sync`)

### 1. Fetch tasks from sources

**ClickUp (Wishew):** Search for tasks where assignee = Max OR I am a blocker, status != closed/done.

**Linear (HikmaAI):** Search for issues where assignee = Max OR blocking/blocked by me, state != done/cancelled.

### 2. Diff against sync state

Read `Journal/.bujo-sync-state.json` to determine:
- **New tasks**: not in sync state, add to daily note
- **Changed tasks**: status changed upstream, update in daily note
- **Completed upstream**: mark `[x]` in daily note if still open

### 3. Inject into daily note

Format rules:
- Task ID in square brackets at end: `[CU-xxx]` or `[LIN-xxx]`
- Blocking tasks prefixed with `**BLOCKS** @persona:`
- Preserve any manual annotations Max added after the task line

### 4. Update sync state

Write updated state to `Journal/.bujo-sync-state.json`.

## Push Flow

Scan today's daily note. `[x]` = complete, `[-]` = cancelled, new task in sync zone = create upstream. Update source systems via MCP, then update sync state.

For detailed push flow, sync state JSON format, conflict resolution, and error handling, see `references/sync-details.md`.

## Commands Summary

| Command | Action |
|---------|--------|
| `bujo sync` | Pull from all sources, update daily note |
| `bujo sync pull` | Same as `bujo sync` |
| `bujo sync push` | Push BuJo changes to source systems |
| `bujo sync full` | Pull then push (full bidirectional sync) |
