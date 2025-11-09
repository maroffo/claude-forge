# ABOUTME: Skills navigation index with task-based routing for fast lookups
# ABOUTME: Find the right skill by language, task, phase, or problem type

# Skills Index

## By Language

| Language   | Skill File        | Coverage                                          |
|------------|-------------------|---------------------------------------------------|
| Go         | `golang/*`        | Code, design, concurrency, review                 |
| Python     | `python/*`        | uv, type checking, linting, Docker                |
| Ruby/Rails | `rails/SKILL.md`  | Services, forms, contracts, Sidekiq, architecture |
| Terraform  | `terraform/SKILL.md` | HCL, Terragrunt, modules, state                |

## By Task

| Task                          | Primary Skill           | Related Skills                    |
|-------------------------------|-------------------------|-----------------------------------|
| Setup new project             | `project-analyzer`      | Language-specific skill           |
| Write code                    | Language-specific       | `_PATTERNS.md`, `_AST_GREP.md`    |
| Review code                   | Language `review`       | `source-control`                  |
| Commit changes                | `source-control`        | Language-specific                 |
| Search/refactor code          | `_AST_GREP.md`          | Language-specific                 |
| Deploy/containerize           | Language `docker`       | `docker-uv` (Python)              |
| Architecture design           | Language `design`       | `_PATTERNS.md`                    |
| Background jobs               | `rails`, `python`       | `_PATTERNS.md`                    |
| Concurrency                   | `golang/concurrency`    | `python` (async)                  |
| Testing                       | Language-specific       | `_PATTERNS.md`                    |

## By Development Phase

### 1. Project Start
- `project-analyzer` - Understand existing codebase
- Language setup (golang, python, rails)
- `source-control` - Initialize git workflow

### 2. Development
- Language-specific skill - Code conventions
- `_AST_GREP.md` - Code search and analysis
- `_PATTERNS.md` - Common patterns

### 3. Review
- Language `review` section - Code review checklist
- `source-control` - Commit and PR workflow

### 4. Deploy
- `docker-uv` - Python containerization
- `terraform` - Infrastructure as code
- Language-specific deployment sections

## By Problem Type

| Problem                       | Solution Skill                  |
|-------------------------------|---------------------------------|
| "How do I search code?"       | `_AST_GREP.md`                  |
| "What's the pattern for X?"   | `_PATTERNS.md`                  |
| "How to commit?"              | `source-control`                |
| "Project structure?"          | `project-analyzer`              |
| "Go formatting?"              | `golang` → Formatting section   |
| "Python package management?"  | `python` → uv section           |
| "Rails validation?"           | `rails` → Forms & Contracts     |
| "Background jobs?"            | `rails` (Sidekiq), `python`     |
| "Goroutine leaks?"            | `golang` → Concurrency section  |
| "Terraform modules?"          | `terraform`                     |

## Quick Command Reference

### Code Search (Use ast-grep!)
```bash
# ALWAYS use ast-grep for code, NOT grep
sg --pattern 'PATTERN' --lang LANGUAGE
```
See `_AST_GREP.md` for patterns.

### Project Analysis
```bash
# Analyze codebase structure
# See project-analyzer skill
```

### Quality Checks
```bash
# Go
gofmt -w . && go vet ./... && go test -race ./...

# Python  
uv run ruff check && uvx ty check && uv run pytest

# Rails
bundle exec lefthook run all
```

### Git Workflow
```bash
# Conventional commits
git commit -m "feat: add feature"
git commit -m "fix: resolve bug"
```
See `source-control` for details.

## Skill Dependencies

```
_INDEX.md (you are here)
├── _AST_GREP.md (code search foundation)
├── _PATTERNS.md (cross-language patterns)
│
├── golang/ (Go development)
│   ├── Code section → _AST_GREP.md
│   ├── Design section → _PATTERNS.md
│   └── Review section → source-control
│
├── python/ (Python development)
│   ├── uv section → docker-uv
│   └── Code section → _AST_GREP.md
│
├── rails/ (Rails development)
│   ├── Services → _PATTERNS.md
│   └── Testing → _PATTERNS.md
│
├── terraform/ (Infrastructure)
│   └── HCL → _AST_GREP.md
│
├── project-analyzer (codebase analysis)
├── source-control (git workflow)
└── docker-uv (Python containerization)
```

## How to Use This Index

1. **Start here**: Find your task in "By Task" section
2. **Jump to skill**: Open the recommended skill file
3. **Cross-reference**: Use related skills as needed
4. **Search code**: Always use `_AST_GREP.md` for code search

## Skill File Locations

All skills are in: `~/.claude/skills/`

```
.claude/skills/
├── _INDEX.md           ← You are here
├── _AST_GREP.md        ← Code search guide
├── _PATTERNS.md        ← Common patterns
├── golang/
│   └── SKILL.md
├── python/
│   └── SKILL.md
├── rails/
│   └── SKILL.md
├── terraform/
│   └── SKILL.md
├── project-analyzer/
│   └── SKILL.md
├── source-control/
│   └── SKILL.md
└── docker-uv/
    └── SKILL.md
```

---

**Remember**: This index is your starting point. It routes you to the right skill fast, saving token consumption and cognitive load.
