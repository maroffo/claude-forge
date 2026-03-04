---
name: process-clippings
description: "Process web clippings into Second Brain. Use when user mentions clippings, asks to process articles, or wants to integrate saved content. Not for newsletters (use newsletter-digest) or email bookmarks (use process-email-bookmarks)."
compatibility: "Requires Obsidian CLI (obsidian MCP commands)."
tools: Bash, Read, WebFetch
---

# ABOUTME: Process web clippings from Obsidian vault into Second Brain via CLI
# ABOUTME: Reads clippings, categorizes, extracts knowledge, integrates, archives

# Process Clippings Skill

Process web clippings from the Clippings folder and integrate them into the Second Brain.

**Obsidian CLI:** See `../_OBSIDIAN.md` | **Integration:** See `../_SECOND_BRAIN.md`

## Vault Structure

```
Documents/                        (vault)
├── Clippings/                    ← Inbox (unprocessed)
│   └── Processed/                ← Archive
├── Second Brain/                 ← Destination for actionable knowledge
│   ├── Second Brain - AI Agents and Tools.md
│   ├── Second Brain - Claude Code.md
│   ├── Second Brain - Development.md
│   ├── Second Brain - DevOps and Cloud.md
│   └── Second Brain - Engineering Management.md
└── Bookmarks/                    ← Reference links only
```

## Processing Workflow

### Step 1: Find Clippings
```bash
obsidian files folder=Clippings ext=md
```

### Step 2: For Each Clipping

1. **Read the clipping**:
```bash
obsidian read path="Clippings/<file>.md"
```

2. **Categorize** per `../_SECOND_BRAIN.md` routing table
3. **Decide**: Actionable (tutorials, patterns, code) -> Second Brain | Reference only -> Bookmarks
4. **Extract & integrate** per `../_SECOND_BRAIN.md` content template:
```bash
# Append to destination
obsidian append file="Second Brain - <Topic>" content="<extracted>"
# Update timeline
obsidian append file="Second Brain - Timeline" content="- **YYYY-MM-DD** | [Topic] | Source: Clipping | -> Second Brain - <File>.md"
```

### Step 3: Archive Clipping

After successful integration:
```bash
obsidian move path="Clippings/<file>.md" to="Clippings/Processed/<file>.md"
```

Or if user prefers, delete:
```bash
obsidian delete path="Clippings/<file>.md"
```

## Output Format

After processing each clipping, report:
```
Processed: [Clipping Title]
  -> Added to: Second Brain - [File].md
  -> Type: [Actionable/Reference]
  -> Key insight: [1-line summary]
```

## Rules

See `../_SECOND_BRAIN.md` for shared rules. Additional:
- **Code examples**: only if genuinely useful, keep minimal
