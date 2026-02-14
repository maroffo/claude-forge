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

## Project Onboarding

To register a project in the vault, run these steps (automate, don't ask the user to do them manually):

1. **Detect project info** from CLAUDE.md or cwd: name, stack, repo path, purpose
2. **Create vault notes:**
   ```bash
   obsidian create name="Projects/<project>/<project> - Overview" content="---\ntags: [project, <project>, <language>]\ncreated: YYYY-MM-DD\nproject: <project>\nstatus: active\nrepo: <repo-path>\n---\n\n# <project>\n\n<purpose>. Stack: <stack>." silent
   obsidian create name="Projects/<project>/<project> - Log" content="---\ntags: [project, <project>, log]\ncreated: YYYY-MM-DD\n---\n\n# <project> - Log" silent
   obsidian create name="Projects/<project>/<project> - Solutions" content="---\ntags: [project, <project>, solutions]\ncreated: YYYY-MM-DD\n---\n\n# <project> - Solutions" silent
   ```
3. **Register in MOC:** `obsidian append file="Projects - MOC" content="| [[Projects/<project>/<project> - Overview|<project>]] | <stack> | active | <repo-path> |"`
4. **Add `## Vault Context`** to the project's CLAUDE.md (or create it if running via project-analyzer)

Skip any step where the note already exists. Idempotent.

## Vault Search for Unlisted Context

If the task needs context not linked in `## Vault Context`:

```
obsidian search query="<topic>" path="Projects"
obsidian search query="<topic>" path="Second Brain"
```

Search vault before searching externally. Internal knowledge is cheaper and more relevant.
