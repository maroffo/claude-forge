# Claude Forge

Token-optimized skills for Claude Code. Language-specific best practices, architectural patterns, and workflows that auto-invoke when relevant.

## Quick Start

**Option 1: Symlink (recommended)**
```bash
git clone https://github.com/maroffo/claude-forge.git ~/Development/claude-forge

# Backup and symlink
mv ~/.claude/skills ~/.claude/skills.backup
ln -s ~/Development/claude-forge/skills ~/.claude/skills

mv ~/.claude/CLAUDE.md ~/.claude/CLAUDE.md.backup
ln -s ~/Development/claude-forge/CLAUDE.md.example ~/.claude/CLAUDE.md
```

**Option 2: Copy**
```bash
git clone https://github.com/maroffo/claude-forge.git
cp -r claude-forge/skills/* ~/.claude/skills/
cp claude-forge/CLAUDE.md.example ~/.claude/CLAUDE.md
```

## Skills

### Languages & Frameworks

| Skill | Description |
|-------|-------------|
| `golang/` | Code conventions, architecture, concurrency, performance |
| `python/` | uv, type checking, ruff, pytest, Docker |
| `rails/` | Service-oriented architecture, Dry-validation, Sidekiq |
| `ruby/` | Gem development, RSpec, RuboCop, publishing |
| `terraform/` | IaC patterns, modules, Terragrunt, OpenTofu |
| `react-nextjs/` | React 19, Next.js 16, App Router, Server Components |
| `android-kotlin/` | Kotlin 2.x, Jetpack Compose, Clean Architecture |
| `apple-swift/` | Swift 6, SwiftUI, async/await, TCA |
| `cloud-infrastructure/` | AWS/GCP Well-Architected, security, cost, observability |

### Utilities (cross-cutting)

| File | Description |
|------|-------------|
| `_AST_GREP.md` | Structural code search (mandates ast-grep over grep) |
| `_INDEX.md` | Quick skill lookup by language/task |
| `_PATTERNS.md` | Cross-language patterns (DI, errors, testing, jobs) |

### Support & Integrations

| Skill | Description |
|-------|-------------|
| `source-control/` | Conventional commits, git workflow, hooks |
| `project-analyzer/` | Generate CLAUDE.md for new codebases |
| `learning-docs/` | LEARNING.md retrospectives - architecture, bugs, lessons |
| `clickup/` | Task management via MCP |
| `gemini-review/` | Local code review with Gemini CLI |

### Personal Workflows

| Skill | Description |
|-------|-------------|
| `inbox-triage/` | Gmail inbox review and prioritization |
| `email-cleanup/` | Archive old emails, manage storage |
| `newsletter-digest/` | Process newsletters into Second Brain |
| `process-clippings/` | Web clippings to Second Brain |
| `process-email-bookmarks/` | Gmail bookmarks processing |

## How It Works

Skills auto-invoke based on project context. Working in Go? `golang/` loads. Need code search? `_AST_GREP.md` enforces ast-grep.

**Global `CLAUDE.md`** → Interaction style, code philosophy, git rules, TDD
**Skills** → Language idioms, framework patterns, tool workflows

## Token Optimization

Skills are aggressively optimized:
- Tables over verbose lists
- Condensed code examples
- No redundancy across files
- Essential patterns only

## Inspiration

Evolved from [Harper Reed's dotfiles](https://github.com/harperreed/dotfiles/tree/master/.claude) and [Matteo Vaccari's AI-assisted modernization series](https://matteo.vaccari.name/posts/plants-by-websphere/).

## License

MIT
