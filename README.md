# Claude Forge

![Claude Forge](blog/cover.png)

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

mv ~/.claude/MEMORY.md ~/.claude/MEMORY.md.backup 2>/dev/null
ln -s ~/Development/claude-forge/MEMORY.md ~/.claude/MEMORY.md
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
├── agents/             → On-demand agents (launched by orchestrator)
├── skills/             → User-invoked language/tool skills
├── docs/solutions/     → Categorized solved problems (searchable knowledge base)
│
Obsidian Vault (Documents/)
├── Projects/           → Per-project artifacts (overview, log, solutions)
├── Plans/              → Cross-project plans (vault-first, local fallback)
└── Second Brain/       → Topic files with Skill Candidates for knowledge-sync
```

**Rules** auto-load every conversation — no invocation needed.
**Agents** are launched by the orchestrator based on which files changed.
**Skills** activate based on project context or user invocation.

## Rules (Always Active)

| Rule | Purpose |
|------|---------|
| `orchestrator-protocol` | Contractor mode: research → implement → verify → review → fix → score → loop |
| `plan-first-workflow` | Requirements refinement, plan before build, checkpoints, context preservation |
| `verification-protocol` | TDD process, mandatory test/lint/build cycle |
| `quality-gates` | Scoring: 80 commit, 90 PR, 95 excellence |

## Agents (On-Demand)

Launched by the orchestrator based on file patterns. All review agents are **read-only** (report findings, never edit).

| Agent | Trigger | Role |
|-------|---------|------|
| `software-engineer` | Implementation subtasks, fix rounds | Scoped read-write, deviation rules (R1-R4), incremental commits |
| `research-analyst` | Pre-plan unknowns, tech evaluation | Best practices, external repos, docs, prior art |
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

Skills are markdown files that teach Claude domain-specific patterns. They load automatically when relevant or on demand via `/skill-name` in Claude Code.

**How invocation works:**
- Type `/obsidian` to activate the Obsidian vault skill
- Type `/commit` to use the source-control commit workflow
- Type `/knowledge-sync` to run the vault-to-skills sync
- Some skills auto-activate based on project context (e.g., `golang/` loads when working in a Go project)

**Shared reference files** (`_*.md`) are not invocable. They provide configuration and patterns that other skills reference internally.

### Languages & Frameworks

| Skill | Description |
|-------|-------------|
| `golang/` | Go conventions, architecture, concurrency, performance |
| `python/` | uv, type checking, ruff, pytest, Docker |
| `rails/` | Service-oriented Rails, Dry-validation, Sidekiq, Hotwire |
| `ruby/` | Gem development, RSpec, RuboCop, publishing |
| `terraform/` | IaC patterns, modules, Terragrunt, OpenTofu |
| `react-nextjs/` | React 19, Next.js 16, App Router, Server Components |
| `android-kotlin/` | Kotlin 2.x, Jetpack Compose, Clean Architecture |
| `apple-swift/` | Swift 6, SwiftUI, async/await, TCA, concurrency, performance |
| `swiftui-liquid-glass/` | iOS 26+ Liquid Glass API |
| `ios-debugger/` | Build, run, debug iOS apps via CLI (Xcode + Simulator) |
| `cloud-infrastructure/` | AWS/GCP Well-Architected, security, cost, observability |

Large skills use a `references/` subdirectory for detailed patterns (progressive disclosure: core in SKILL.md, details on demand). Currently: `apple-swift/`, `android-kotlin/`, `rails/`.

### Shared Reference Files

| File | Description |
|------|-------------|
| `_AST_GREP.md` | Structural code search (mandates ast-grep over grep) |
| `_INDEX.md` | Quick skill lookup by language/task |
| `_PATTERNS.md` | Cross-language patterns (DI, errors, testing, jobs) |
| `_GMAIL.md` | Gmail account config, gog CLI commands |
| `_OBSIDIAN.md` | Obsidian CLI config, vault commands |
| `_SECOND_BRAIN.md` | Category routing, content templates, rules |
| `_VAULT_CONTEXT.md` | Vault context injection, token budget, breadcrumbs |
| `_generate_image.py` | Gemini image generation (used by cover-image, table-image) |

### Support & Integrations

| Skill | Description |
|-------|-------------|
| `source-control/` | Conventional commits, git workflow, hooks |
| `commit/` | Redirects to `source-control/` |
| `learning-docs/` | LEARNING.md retrospectives, session analysis, docs/solutions/ capture, vault pattern annotation |
| `knowledge-sync/` | Vault-to-skills sync: scan Second Brain for recurring patterns, propose skill updates |
| `releasing-software/` | Pre-release checklist, no-tag-without-green-CI |
| `obsidian/` | Obsidian vault operations via CLI (CRUD, search, daily notes, graph, tasks) |
| `refine-requirements/` | Structured requirements gathering before planning |
| `clickup/` | Task management via MCP |
| `gemini-review/` | Local code review with Gemini CLI |
| `skill-forge/` | Create new skills or review/improve existing ones against quality checklist |
| `notion-sync/` | Notion workspace to Obsidian vault sync (pull, push, AI summaries) |

### Content & Images

| Skill | Description |
|-------|-------------|
| `cover-image/` | Generate editorial cover images via Gemini |
| `table-image/` | Render tables/diagrams as hand-drawn sketch images |

### Personal Workflows

| Skill | Description |
|-------|-------------|
| `inbox-triage/` | Gmail inbox review and prioritization |
| `email-cleanup/` | Archive old emails, manage storage |
| `newsletter-digest/` | Process newsletters into Second Brain (via Obsidian CLI) |
| `process-clippings/` | Web clippings to Second Brain (via Obsidian CLI) |
| `process-email-bookmarks/` | Gmail bookmarks processing (via Obsidian CLI) |

## Vault Integration (Obsidian)

An optional layer that turns an Obsidian vault into a knowledge backbone for Claude Code. Works across three layers; each is useful alone but they compound together.

### Prerequisites

- [Obsidian](https://obsidian.md/) app installed and running (the CLI is built-in, see `_OBSIDIAN.md` for config)
- A vault named "Documents" (configurable in `_OBSIDIAN.md`)
- **Without Obsidian:** everything degrades gracefully to local `quality_reports/` paths. No vault = no breakage.

### Layer 1: Structured Storage

Plans, session logs, and solutions go to the vault instead of project-local folders.

```
Documents/
├── Projects/<project>/          Overview, Log, Solutions per project
├── Plans/                       Cross-project plans (draft → approved → done)
└── Second Brain/                Topic files (existing, unchanged)
```

| Artifact | Vault destination | Local fallback |
|----------|-------------------|----------------|
| Plan | `Plans/YYYY-MM-DD - description.md` | `quality_reports/plans/` |
| Session log | `<project> - Log.md` (append) | `quality_reports/session_logs/` |
| Solution | `<project> - Solutions.md` (append) | `docs/solutions/` |

Configured in `rules/plan-first-workflow.md` and `rules/orchestrator-protocol.md`.

### Layer 2: Context Injection

Project CLAUDE.md files can reference vault notes via a `## Vault Context` section:

```markdown
## Vault Context
- Architecture: [[Projects/feed-brain/feed-brain - Overview]]
- Go patterns: [[Second Brain - Development#Go (Golang)]]
```

Claude reads linked notes on demand via `obsidian read`. Token budget rules prevent context bloat (< 5KB: read fully; 5-20KB: outline first; > 20KB: section only). See `_VAULT_CONTEXT.md`.

### Layer 3: Knowledge Feedback Loop

Recurring patterns accumulate in Second Brain topic notes as `## Skill Candidates` tables. The `/knowledge-sync` skill (run monthly) scans for strong signals (3+ projects) and proposes additions to skill files, with mandatory human approval.

```
learning-docs retrospective → annotate pattern (weak signal)
  → seen in 3+ projects → signal becomes strong
    → /knowledge-sync proposes skill update → human approves → skill improved
```

### Onboarding a Project

Ask Claude to onboard the current project to the vault:

```
"Onboard this project to the vault"
```

Claude reads the project's CLAUDE.md (or asks for basics), then automatically:
1. Creates Overview, Log, and Solutions notes in `Projects/<project>/`
2. Registers in the Projects MOC
3. Adds `## Vault Context` to the project's CLAUDE.md

This also runs automatically when using `/project-analyzer` on a new codebase.

The protocol is defined in `_VAULT_CONTEXT.md` (Project Onboarding section). It's idempotent: skips notes that already exist.

### Obsidian Skills Map

| Skill/File | Type | Purpose |
|------------|------|---------|
| `obsidian/` | Invocable (`/obsidian`) | Vault CRUD, search, daily notes, graph, tasks |
| `newsletter-digest/` | Invocable (`/newsletter-digest`) | Process newsletters into Second Brain |
| `process-clippings/` | Invocable (`/process-clippings`) | Web clippings to Second Brain |
| `process-email-bookmarks/` | Invocable (`/process-email-bookmarks`) | Gmail bookmarks to Second Brain |
| `knowledge-sync/` | Invocable (`/knowledge-sync`) | Vault-to-skills sync (monthly) |
| `learning-docs/` | Invocable (`/learning-docs`) | Retrospectives + vault pattern annotation |
| `_OBSIDIAN.md` | Reference | CLI config and commands |
| `_SECOND_BRAIN.md` | Reference | Category routing, content templates |
| `_VAULT_CONTEXT.md` | Reference | Context injection protocol, token budget |

## Skill Conventions

Skills follow [Anthropic's Complete Guide to Building Skills for Claude](https://www.anthropic.com/engineering/claude-code-best-practices), with additional project conventions. Use `/skill-forge` to create or audit skills.

| Convention | Detail |
|------------|--------|
| **Frontmatter** | `name` (kebab-case) + `description` (what + when/triggers + capabilities) |
| **ABOUTME** | 2-line comment header after frontmatter |
| **Progressive disclosure** | Core in SKILL.md (< 150 lines), details in `references/` |
| **Trigger phrases** | Description includes words users actually say |
| **Negative triggers** | "Not for X (use Y skill)" when skills overlap |
| **Compatibility** | `compatibility` field for external deps (CLI, API key, MCP) |
| **Quality Notes** | Anti-laziness section for multi-step workflow skills |

## Token Optimization

Everything is aggressively optimized:
- Tables over verbose lists
- Condensed code examples
- No redundancy across files
- Rules/agents reference each other, never duplicate

## Inspiration

Evolved from [Harper Reed's dotfiles](https://github.com/harperreed/dotfiles/tree/master/.claude), [Matteo Vaccari's AI-assisted modernization series](https://matteo.vaccari.name/posts/plants-by-websphere/), [Pedro Santanna's orchestrated workflow](https://github.com/pedrohcgs/claude-code-my-workflow), [Every's compound-engineering-plugin](https://github.com/EveryInc/compound-engineering-plugin) (solutions directory, research agent, incremental commits), [Get Shit Done](https://github.com/gsd-build/get-shit-done) (requirements refinement, deviation rules), and [Anthropic's Complete Guide to Building Skills](https://www.anthropic.com/engineering/claude-code-best-practices) (progressive disclosure, trigger phrases, skill-forge).

## License

MIT
