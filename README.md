# Claude Code Skills

Token-optimized, modular skills for Claude Code. Language-specific best practices, architectural patterns, and workflows that auto-invoke when relevant.

## Quick Start

**Install skills:**
```bash
git clone https://github.com/maroffo/claude-forge.git
cp -r claude-forge/skills/* ~/.claude/skills/
```

**Add to your global `~/.claude/CLAUDE.md`:**
```markdown
# Skills
**Core:** golang, python, rails, terraform
**Utilities:** _INDEX.md, _AST_GREP.md, _PATTERNS.md
**Support:** source-control, project-analyzer
```

See `CLAUDE.md.example` for a complete global configuration template.

## Why Skills?

**Modular** - Load only relevant expertise per project (Go skills don't load in Rails projects)

**Token-efficient** - Smaller, focused files vs monolithic global config

**Discoverable** - `_INDEX.md` routes Claude to the right skill fast

**Cross-referenced** - `_PATTERNS.md` shows same pattern across languages; `_AST_GREP.md` mandates proper code search

**Real-world tested** - Evolved through production use across Go, Python, Rails, and Terraform projects

## Skills

### Languages
- **`golang/`** - Code conventions, architecture, concurrency, code review
- **`python/`** - uv package manager, type checking, linting, Docker deployment
- **`rails/`** - Service-oriented architecture, forms, contracts, Sidekiq, RSpec
- **`terraform/`** - IaC patterns, modules, state management, Terragrunt

### Utilities (cross-cutting)
- **`_AST_GREP.md`** - Structural code search patterns (mandates ast-grep over grep/ripgrep)
- **`_INDEX.md`** - Quick skill lookup by language/task/problem domain
- **`_PATTERNS.md`** - Cross-language patterns (DI, error handling, testing, background jobs)

### Support
- **`source-control/`** - Conventional commits, git workflow, branch strategies, hook protocols
- **`project-analyzer/`** - Generate CLAUDE.md for new codebases

## How It Works

Skills auto-invoke based on your project context. When working in a Go project, `golang/` skill loads automatically. When Claude needs to search code, `_AST_GREP.md` enforces ast-grep usage.

**Global `~/.claude/CLAUDE.md`** handles:
- Interaction style and personality
- Cross-project code philosophy
- Universal git workflow rules
- TDD requirements

**Skills** handle:
- Language-specific idioms and patterns
- Framework-specific best practices
- Tool-specific workflows

Both work together: global config sets the foundation, skills provide domain expertise.

## Inspiration

Evolved from [Harper Reed's dotfiles](https://github.com/harperreed/dotfiles/tree/master/.claude) and [Matteo Vaccari's AI-assisted modernization series](https://matteo.vaccari.name/posts/plants-by-websphere/), refined through production use.

## License

MIT
