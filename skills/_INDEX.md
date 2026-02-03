# ABOUTME: Skills navigation index with task-based routing for fast lookups
# ABOUTME: Find the right skill by language, task, phase, or problem type

# Skills Index

## By Language

| Language   | Skill File        | Coverage                                          |
|------------|-------------------|---------------------------------------------------|
| Go         | `golang/*`        | Code, design, concurrency, performance, review    |
| Kotlin/Android | `android-kotlin/*` | Compose, MVVM, Hilt/Koin, testing, performance |
| Swift/Apple | `apple-swift/*`   | SwiftUI, Swift 6, async/await, TCA, SwiftData    |
| Python     | `python/*`        | uv, type checking, linting, Docker                |
| Ruby (gem) | `ruby/SKILL.md`   | Gem development, RSpec, RuboCop, publishing       |
| Ruby/Rails | `rails/SKILL.md`  | Services, forms, contracts, Sidekiq, architecture |
| Terraform  | `terraform/SKILL.md` | HCL, Terragrunt, modules, state, OpenTofu      |
| React/Next | `react-nextjs/SKILL.md` | Next.js 16, App Router, Server Components, Zustand |

## By Cloud/Infrastructure

| Platform   | Skill File                    | Coverage                                          |
|------------|-------------------------------|---------------------------------------------------|
| AWS/GCP    | `cloud-infrastructure/*`      | Well-Architected, ECS/EKS, security, FinOps       |
| IaC        | `terraform/SKILL.md`          | Terraform, OpenTofu, Terragrunt, state mgmt       |

## By Integration

| Integration | Skill File          | Coverage                                          |
|-------------|---------------------|---------------------------------------------------|
| ClickUp     | `clickup/SKILL.md`  | Tasks, comments, time tracking, workspace, search |

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
| Task management               | `clickup`               | `source-control`                  |
| Time tracking                 | `clickup`               | -                                 |
| AWS infrastructure            | `cloud-infrastructure`  | `terraform`                       |
| GCP infrastructure            | `cloud-infrastructure`  | `terraform`                       |
| Security scanning (IaC)       | `terraform`             | `cloud-infrastructure`            |
| Cost optimization             | `cloud-infrastructure`  | `terraform` (Infracost)           |
| Observability                 | `cloud-infrastructure`  | -                                 |

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
| "Ruby gem structure?"         | `ruby` → Gem Structure          |
| "Publish gem?"                | `ruby` → Publishing             |
| "RuboCop config?"             | `ruby` → RuboCop Configuration  |
| "Background jobs?"            | `rails` (Sidekiq), `python`     |
| "Goroutine leaks?"            | `golang` → Concurrency section  |
| "Terraform modules?"          | `terraform`                     |
| "Jetpack Compose?"            | `android-kotlin` → Compose      |
| "Android ViewModel?"          | `android-kotlin` → Architecture |
| "Kotlin coroutines?"          | `android-kotlin` → State        |
| "Baseline Profiles?"          | `android-kotlin` → Performance  |
| "SwiftUI @Observable?"        | `apple-swift` → SwiftUI         |
| "Swift concurrency?"          | `apple-swift` → Concurrency     |
| "SwiftData models?"           | `apple-swift` → SwiftUI         |
| "iOS NavigationStack?"        | `apple-swift` → SwiftUI         |
| "TCA architecture?"           | `apple-swift` → Architecture    |
| "Update ClickUp task?"        | `clickup` → Task Management     |
| "Track time on task?"         | `clickup` → Time Tracking       |
| "Find ClickUp task?"          | `clickup` → Searching Tasks     |
| "ECS vs EKS?"                 | `cloud-infrastructure` → Compute|
| "AWS security?"               | `cloud-infrastructure` → Security|
| "GuardDuty/Security Hub?"     | `cloud-infrastructure` → Security|
| "Cloud Run?"                  | `cloud-infrastructure` → GCP    |
| "Cost optimization?"          | `cloud-infrastructure` → FinOps |
| "OpenTelemetry?"              | `cloud-infrastructure` → Observability|
| "Checkov/TFLint?"             | `terraform` → Testing           |
| "Infracost?"                  | `terraform` → Testing           |
| "OpenTofu?"                   | `terraform` → What's New        |

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
├── clickup/ (task management)
│   └── Git workflow → source-control
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
├── ruby/ (Ruby gem development)
│   ├── RSpec → _PATTERNS.md
│   └── Gems → source-control
│
├── terraform/ (Infrastructure as Code)
│   ├── HCL → _AST_GREP.md
│   └── IaC testing → cloud-infrastructure
│
├── cloud-infrastructure/ (AWS/GCP)
│   ├── Security → terraform
│   └── IaC → terraform
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
├── android-kotlin/
│   └── SKILL.md        ← Kotlin, Compose, Android
├── apple-swift/
│   └── SKILL.md        ← Swift, SwiftUI, iOS/macOS
├── clickup/
│   └── SKILL.md        ← ClickUp MCP integration
├── cloud-infrastructure/
│   └── SKILL.md        ← AWS/GCP infrastructure
├── golang/
│   └── SKILL.md
├── python/
│   └── SKILL.md
├── rails/
│   └── SKILL.md
├── ruby/
│   └── SKILL.md        ← Ruby gems (NOT Rails)
├── terraform/
│   └── SKILL.md
├── react-nextjs/
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
