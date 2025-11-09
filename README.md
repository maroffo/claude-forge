# Claude Code Skills

Token-optimized skills collection for Claude Code with language-specific best practices and architectural patterns.

## Background

This configuration was inspired by [Harper Reed's dotfiles](https://github.com/harperreed/dotfiles/tree/master/.claude) after reading Matteo Vaccari's excellent series on [AI-assisted codebase modernization](https://matteo.vaccari.name/posts/plants-by-websphere/).

What started as exploring Reed's approach evolved into a comprehensive, token-optimized skills system through real-world usage across Go, Python, Rails, and Terraform projects. The focus shifted from just having skills to making them **efficient**, **discoverable**, and **cross-referenced**.

## Structure

```
skills/
├── _AST_GREP.md      # Universal code search (use instead of grep)
├── _INDEX.md         # Smart navigation router
├── _PATTERNS.md      # Cross-language patterns
├── golang/           # Complete Go development
├── python/           # Python with uv, Docker
├── rails/            # Service-oriented Rails
├── terraform/        # Terraform/Terragrunt IaC
├── source-control/   # Git workflow, conventional commits
└── project-analyzer/ # Codebase analysis
```

## Skills Overview

### Language Skills

**Go (`golang/`)** - Code conventions, architecture, concurrency, review
**Python (`python/`)** - uv package manager, type checking, linting, Docker
**Rails (`rails/`)** - Services, forms, contracts, Sidekiq, testing
**Terraform (`terraform/`)** - IaC patterns, modules, Terragrunt

### Utilities

**`_AST_GREP.md`** - CRITICAL: Always use ast-grep for code search (not grep)
**`_INDEX.md`** - Find the right skill fast by language/task/problem
**`_PATTERNS.md`** - DI, error handling, testing, jobs across languages

### Support

**`source-control/`** - Conventional commits, branches, hooks, recovery
**`project-analyzer/`** - Automated and manual codebase analysis

## Add to CLAUDE.md

```markdown
# Skills

**Core:** golang, python, rails, terraform
**Utilities:** \_INDEX.md, \_AST_GREP.md, \_PATTERNS.md
**Support:** source-control, project-analyzer

# Tool Preferences

- **ast-grep (sg)**: MUST use for code search (not grep/ripgrep)
  - See ~/.claude/skills/\_AST_GREP.md for patterns
```

## Acknowledgments

- [Harper Reed](https://github.com/harperreed) - Original inspiration from his Claude dotfiles
- [Matteo Vaccari](https://matteo.vaccari.name) - Insightful articles on Claude Code workflows
- The Claude Code community for pushing the boundaries of AI-assisted development

## License

MIT
