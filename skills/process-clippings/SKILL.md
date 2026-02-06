---
name: process-clippings
description: Process web clippings into Second Brain. Use when user mentions clippings, asks to process articles, or wants to integrate saved content.
tools: Read, Write, Edit, Glob, Bash
---

# Process Clippings Skill

You process web clippings from the Clippings folder and integrate them into the Second Brain.

## Vault Structure

```
Documents/
├── Clippings/                 ← Inbox (unprocessed clippings)
├── Second Brain/              ← Destination for actionable knowledge
│   ├── Second Brain - AI Agents and Tools.md
│   ├── Second Brain - Claude Code.md
│   ├── Second Brain - Development.md
│   ├── Second Brain - DevOps and Cloud.md
│   └── Second Brain - Engineering Management.md
└── Bookmarks/                 ← Destination for reference links only
```

## Processing Workflow

### Step 1: Find Clippings
```
Glob pattern: **/*.md
Path: /Users/maroffo/Library/Mobile Documents/iCloud~md~obsidian/Documents/Clippings
```

### Step 2: For Each Clipping

1. **Read the clipping** - understand the content
2. **Categorize** per `_SECOND_BRAIN.md` routing table
3. **Decide**: Actionable (tutorials, patterns, code) -> Second Brain | Reference only -> Bookmarks
4. **Extract & integrate** per `_SECOND_BRAIN.md` content template

### Step 3: Archive Clipping

After successful integration:
```bash
mv "Clippings/filename.md" "Clippings/Processed/filename.md"
```

Or if user prefers, delete:
```bash
rm "Clippings/filename.md"
```

## Output Format

After processing each clipping, report:
```
✓ Processed: [Clipping Title]
  → Added to: Second Brain - [File].md#[Section]
  → Type: [Actionable/Reference]
  → Key insight: [1-line summary]
```

## Example

**Input clipping**: Docker Compose SDK documentation

**Output**:
- Category: Development (Go) + DevOps (Docker)
- Type: Actionable (Go SDK, code examples)
- Add to: `Second Brain - Development.md` under Go section OR `Second Brain - DevOps and Cloud.md` under Docker section

**Extracted content**:
```markdown
### Compose SDK (Go)

Go library to programmatically manage Docker Compose applications without CLI.

| Feature | Description |
|---------|-------------|
| **NewComposeService()** | Initialize SDK with Docker daemon connection |
| **LoadProject()** | Load Compose file into project |
| **Up/Down** | Start/stop services |
| **EventProcessor** | Monitor operations in real-time |

```go
service, _ := compose.NewComposeService(dockerCLI)
project, _ := service.LoadProject(ctx, api.ProjectLoadOptions{
    ConfigPaths: []string{"compose.yaml"},
})
service.Up(ctx, project, api.UpOptions{})
```

- [Compose SDK Docs](https://docs.docker.com/compose/compose-sdk/)
```

## Rules

See `_SECOND_BRAIN.md` for shared rules. Additional:
- **Code examples** - only if genuinely useful, keep minimal
