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
2. **Categorize** - determine which Second Brain file it belongs to:
   - AI, LLM, agents, context engineering → `Second Brain - AI Agents and Tools.md`
   - Claude Code, skills, subagents, MCP → `Second Brain - Claude Code.md`
   - Go, Python, Java, CLI, data tools, APIs → `Second Brain - Development.md`
   - Docker, K8s, Terraform, cloud, monitoring, security → `Second Brain - DevOps and Cloud.md`
   - Productivity, tech debt, leadership, management → `Second Brain - Engineering Management.md`

3. **Decide content type**:
   - **Actionable knowledge** (tutorials, patterns, code examples, frameworks) → Extract and add to Second Brain
   - **Reference only** (product announcements, news, opinion pieces) → Add link to Bookmarks

4. **Extract key insights** - distill into:
   - Tool/library name and description (1 line)
   - Key features or patterns (bullet points)
   - Code snippet if relevant (keep minimal)
   - Link to source

### Step 3: Integration

**For Second Brain** - find the appropriate section and add:
```markdown
### [Tool/Concept Name]

Brief description of what it does.

| Feature | Description |
|---------|-------------|
| **Feature 1** | What it does |

```go/python/etc
// Minimal useful code example
```

- [Source](url)
```

**For Bookmarks** - add to appropriate file:
```markdown
- [Title](url) - Brief description
```

### Step 4: Archive Clipping

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

1. **Be concise** - Second Brain should be scannable, not verbose
2. **Preserve links** - always include source URL
3. **Code examples** - only if genuinely useful, keep minimal
4. **No duplication** - check if topic already exists before adding
5. **Ask if unclear** - if categorization is ambiguous, ask user
