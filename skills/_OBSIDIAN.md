# ABOUTME: Shared Obsidian CLI configuration and commands for vault skills
# ABOUTME: Vault config, CLI operations by category, common patterns

# Obsidian CLI Configuration

- **Vault**: Documents
- **Binary**: `obsidian` (requires app running, PATH via `~/.zprofile`)
- **Syntax**: `obsidian [vault=Documents] <command> [params] [flags]`
- When cwd is vault root, `vault=` can be omitted.
- **Path fallback**: if CLI unavailable, vault root is `/Users/maroffo/Library/Mobile Documents/iCloud~md~obsidian/Documents/`

## Core Operations

| Operation | Command |
|---|---|
| Read note | `obsidian read file=<name>` |
| Create note | `obsidian create name=<name> content="<text>" silent` |
| Create from template | `obsidian create name=<name> template=<tpl> silent` |
| Append to note | `obsidian append file=<name> content="<text>"` |
| Prepend to note | `obsidian prepend file=<name> content="<text>"` |
| Move/rename | `obsidian move file=<name> to=<path>` |
| Delete note | `obsidian delete file=<name>` |
| Search vault | `obsidian search query="<text>" [path=<folder>] [matches] [format=json]` |
| List files | `obsidian files [folder=<path>] [ext=md]` |
| File info | `obsidian file file=<name>` |

## Daily Notes

| Operation | Command |
|---|---|
| Open daily note | `obsidian daily` |
| Read daily note | `obsidian daily:read` |
| Append to daily | `obsidian daily:append content="<text>" silent` |
| Prepend to daily | `obsidian daily:prepend content="<text>" silent` |

## Tags & Properties

| Operation | Command |
|---|---|
| All tags (with counts) | `obsidian tags all counts sort=count` |
| Tag info | `obsidian tag name=<tag> verbose` |
| File tags | `obsidian tags file=<name>` |
| Set property | `obsidian property:set name=<key> value=<val> file=<name>` |
| Read property | `obsidian property:read name=<key> file=<name>` |
| Remove property | `obsidian property:remove name=<key> file=<name>` |
| File properties | `obsidian properties file=<name>` |

## Knowledge Graph

| Operation | Command |
|---|---|
| Backlinks | `obsidian backlinks file=<name> counts` |
| Outgoing links | `obsidian links file=<name>` |
| Orphaned notes | `obsidian orphans` |
| Dead-end notes | `obsidian deadends` |
| Unresolved links | `obsidian unresolved verbose` |

## Tasks

| Operation | Command |
|---|---|
| All tasks | `obsidian tasks all` |
| Daily tasks | `obsidian tasks daily` |
| Incomplete | `obsidian tasks todo [all]` |
| Toggle task | `obsidian task file=<name> line=<n> toggle` |
| Mark done | `obsidian task file=<name> line=<n> done` |

## Templates & Bookmarks

| Operation | Command |
|---|---|
| List templates | `obsidian templates` |
| Read template | `obsidian template:read name=<tpl> resolve` |
| Add bookmark | `obsidian bookmark file=<path> [title=<title>]` |
| List bookmarks | `obsidian bookmarks verbose` |

## File Outline & History

| Operation | Command |
|---|---|
| Headings | `obsidian outline file=<name> format=md` |
| Word count | `obsidian wordcount file=<name>` |
| Version diff | `obsidian diff file=<name> from=1` |

## Vault Info

| Operation | Command |
|---|---|
| Vault info | `obsidian vault` |
| List vaults | `obsidian vaults verbose` |
| File count | `obsidian files total` |

## Tips

- **Multiline**: `\n` for newline, `\t` for tab
- **Spaces in values**: wrap in quotes: `content="Hello world"`
- **File targeting**: `file=Recipe` (wikilink resolution) vs `path=folder/Recipe.md` (exact path)
- **Silent mode**: `silent` flag on create/daily commands avoids opening in UI
- **Copy output**: `--copy` pipes to clipboard
