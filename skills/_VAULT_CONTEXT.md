# ABOUTME: Vault context injection into Claude Code sessions via CLAUDE.md wikilinks
# ABOUTME: Token budget rules, breadcrumb protocol, cross-project discovery

# Vault Context Injection

## How It Works

Project CLAUDE.md files may include a `## Vault Context` section with wikilinks to vault notes. At session start (or when context is needed), read linked notes via `obsidian read`.

```markdown
## Vault Context
<!-- Follow these links via `obsidian read` for deeper context -->
- Architecture: [[Projects/feed-brain/feed-brain - Overview]]
- Decisions: [[Projects/feed-brain/feed-brain - Log#Decisions]]
- Solved problems: [[Projects/feed-brain/feed-brain - Solutions]]
- Go patterns: [[Second Brain - Development#Go (Golang)]]
```

## Rules

- 3-7 links max per project (token budget)
- Use section anchors (`#Section`) for large notes
- Read vault context on demand, not eagerly at session start
- Only read sections relevant to the current task

## Token Budget

| Note size | Strategy |
|-----------|----------|
| < 5KB | Read fully |
| 5-20KB | Read outline first (`obsidian outline file=<name>`), then target sections |
| > 20KB | Section-only via anchor links |

## Breadcrumb Protocol

When discovering something useful during a session, append an HTML comment to the relevant vault note:

```
obsidian append file="<note>" content="\n<!-- breadcrumb: YYYY-MM-DD | <insight> -->"
```

Invisible in Obsidian preview, readable by future Claude sessions. Use sparingly: only for non-obvious discoveries worth preserving.

## Vault Search for Unlisted Context

If the task needs context not linked in `## Vault Context`:

```
obsidian search query="<topic>" path="Projects"
obsidian search query="<topic>" path="Second Brain"
```

Search vault before searching externally. Internal knowledge is cheaper and more relevant.
