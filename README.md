# Claude Forge

Token-optimized skills, orchestrated review agents, and always-on workflow rules for Claude Code. A three-tier system: **rules** (always active) + **agents** (on-demand reviewers) + **skills** (user-invoked).

## Quick Start

**Option 1: Symlink (recommended)**
```bash
git clone https://github.com/maroffo/claude-forge.git ~/Development/claude-forge

# Backup and symlink
mv ~/.claude/skills ~/.claude/skills.backup
ln -s ~/Development/claude-forge/skills ~/.claude/skills

mv ~/.claude/agents ~/.claude/agents.backup 2>/dev/null
ln -s ~/Development/claude-forge/agents ~/.claude/agents

mv ~/.claude/rules ~/.claude/rules.backup 2>/dev/null
ln -s ~/Development/claude-forge/rules ~/.claude/rules

mv ~/.claude/CLAUDE.md ~/.claude/CLAUDE.md.backup
ln -s ~/Development/claude-forge/CLAUDE.md.example ~/.claude/CLAUDE.md
```

**Option 2: Copy**
```bash
git clone https://github.com/maroffo/claude-forge.git
cp -r claude-forge/skills/* ~/.claude/skills/
cp -r claude-forge/agents/* ~/.claude/agents/
cp -r claude-forge/rules/* ~/.claude/rules/
cp claude-forge/CLAUDE.md.example ~/.claude/CLAUDE.md
cp claude-forge/MEMORY.md ~/.claude/MEMORY.md
```

## Architecture

```
~/.claude/
├── CLAUDE.md           → Identity, philosophy, routing tables
├── MEMORY.md           → Persistent [LEARN:x] corrections
├── rules/              → Always-on workflow guardrails (auto-loaded)
├── agents/             → On-demand review agents (launched by orchestrator)
└── skills/             → User-invoked language/tool skills
```

**Rules** auto-load every conversation — no invocation needed.
**Agents** are launched by the orchestrator based on which files changed.
**Skills** activate based on project context or user invocation.

## Rules (Always Active)

| Rule | Purpose |
|------|---------|
| `orchestrator-protocol` | Contractor mode: implement → verify → review → fix → score → loop |
| `plan-first-workflow` | Plan before build, save plans to disk, session logging |
| `verification-protocol` | TDD process, mandatory test/lint/build cycle |
| `quality-gates` | Scoring: 80 commit, 90 PR, 95 excellence |

## Agents (On-Demand)

Launched by the orchestrator based on file patterns. All review agents are **read-only** (report findings, never edit).

| Agent | Trigger | Role |
|-------|---------|------|
| `software-engineer` | Implementation subtasks, fix rounds | Scoped read-write, acts on reviewer findings |
| `security-reviewer` | Auth, input, API, secrets | OWASP, injection, credentials |
| `performance-reviewer` | Hot paths, queries, caching | N+1, memory, allocations |
| `architecture-reviewer` | Multi-file, new features | SOLID, coupling, API design |
| `test-reviewer` | Test files, pre-PR | Coverage gaps, flaky patterns |
| `dependency-reviewer` | go.mod, Gemfile, package.json | CVEs, licenses, outdated |
| `database-reviewer` | Migrations, schema | Lock safety, indexes, deadlocks |
| `dx-reviewer` | Docs, README, ADR | Documentation, error messages, onboarding |
| `tech-writer` | Post-milestone | Blog posts, changelogs, release notes |
| `project-analyzer` | New codebases | Generate CLAUDE.md documentation |

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
| `apple-swift/` | Swift 6, SwiftUI, async/await, TCA, concurrency, performance |
| `swiftui-liquid-glass/` | iOS 26+ Liquid Glass API |
| `ios-debugger/` | XcodeBuildMCP simulator workflow |
| `cloud-infrastructure/` | AWS/GCP Well-Architected, security, cost, observability |

### Shared Reference Files

| File | Description |
|------|-------------|
| `_AST_GREP.md` | Structural code search (mandates ast-grep over grep) |
| `_INDEX.md` | Quick skill lookup by language/task |
| `_PATTERNS.md` | Cross-language patterns (DI, errors, testing, jobs) |
| `_GMAIL.md` | Gmail account config, gog CLI commands |
| `_SECOND_BRAIN.md` | Category routing, content templates, rules |

### Support & Integrations

| Skill | Description |
|-------|-------------|
| `source-control/` | Conventional commits, git workflow, hooks |
| `commit/` | Redirects to `source-control/` |
| `learning-docs/` | LEARNING.md retrospectives, session analysis |
| `releasing-software/` | Pre-release checklist, no-tag-without-green-CI |
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

## Token Optimization

Everything is aggressively optimized:
- Tables over verbose lists
- Condensed code examples
- No redundancy across files
- Rules/agents reference each other, never duplicate

## Inspiration

Evolved from [Harper Reed's dotfiles](https://github.com/harperreed/dotfiles/tree/master/.claude), [Matteo Vaccari's AI-assisted modernization series](https://matteo.vaccari.name/posts/plants-by-websphere/), and [Pedro Santanna's orchestrated workflow](https://github.com/pedrohcgs/claude-code-my-workflow).

## License

MIT
