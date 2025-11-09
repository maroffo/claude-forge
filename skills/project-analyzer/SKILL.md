---
name: project-analyzer
description: "Analyze codebase and create CLAUDE.md documentation. Use when analyzing project, understanding codebase, or creating documentation."
allowed-tools: [Task]
---

# ABOUTME: Automated codebase analysis and CLAUDE.md generation
# ABOUTME: Project structure mapping, convention detection, documentation creation

# Project Analyzer

This skill analyzes a new codebase by invoking a specialized agent (using Haiku for speed) that generates comprehensive CLAUDE.md documentation.

## When to Use This Skill

- Starting work on a new project
- Asked to "analyze this project"
- Need to understand project structure
- Creating project documentation
- Onboarding to unfamiliar codebase
- Documenting existing project conventions

## How This Skill Works

This skill invokes the **project-analyzer agent** which:
- Uses **Haiku model** for fast, efficient analysis
- Analyzes codebase with ast-grep (language-aware)
- Maps project structure and dependencies
- Identifies code conventions and patterns
- Generates comprehensive CLAUDE.md documentation

## Quick Reference

```bash
# Analyze project
# Invoke via Task tool with subagent_type: "project-analyzer"
```

---

## § Manual Analysis Workflow

When agent is not available or for quick manual analysis:

### 1. Identify Language/Framework

```bash
# Check for language indicators
ls -la  # Look for:
# - go.mod, go.sum → Go
# - pyproject.toml, requirements.txt → Python
# - Gemfile, Rakefile → Ruby/Rails
# - package.json → JavaScript/TypeScript
# - *.tf → Terraform
# - Cargo.toml → Rust
# - pom.xml, build.gradle → Java
```

### 2. Check Project Structure

```bash
# Tree view (limit depth)
tree -L 2

# Or manual ls
ls -la
ls -la cmd/        # Go
ls -la src/        # General
ls -la app/        # Rails
```

### 3. Find Entry Points

**Go:**
```bash
find . -name "main.go"
ls cmd/*/
```

**Python:**
```bash
cat pyproject.toml  # Check [project.scripts]
find . -name "__main__.py"
```

**Rails:**
```bash
cat config/routes.rb
```

### 4. Identify Dependencies

**Go:**
```bash
cat go.mod
```

**Python:**
```bash
cat pyproject.toml
# or
cat requirements.txt
```

**Rails:**
```bash
cat Gemfile
```

**Node:**
```bash
cat package.json
```

### 5. Find Tests

```bash
# Go
find . -name "*_test.go"

# Python
find . -name "test_*.py"
ls tests/

# Rails
ls spec/

# JavaScript
ls __tests__/
ls *.test.js
```

### 6. Check CI/CD

```bash
ls .github/workflows/   # GitHub Actions
cat .gitlab-ci.yml      # GitLab CI
cat Jenkinsfile         # Jenkins
cat .circleci/config.yml # CircleCI
```

### 7. Analyze Code Conventions

**Use ast-grep (see `_AST_GREP.md`):**

```bash
# Go - Find all service patterns
sg --pattern 'type $NAME struct { $$$ }' --lang go

# Python - Find all classes
sg --pattern 'class $NAME: $$$' --lang python

# Rails - Find all services
sg --pattern 'class $NAME\n  def call' --lang ruby
```

---

## § Key Files Checklist

### Documentation
- [ ] README.md - Project overview
- [ ] CONTRIBUTING.md - Contribution guidelines
- [ ] CHANGELOG.md - Version history
- [ ] LICENSE - License information

### Configuration
- [ ] .gitignore - Git ignore patterns
- [ ] .env.example - Environment variables template
- [ ] docker-compose.yml - Docker setup

### Language-Specific
- [ ] go.mod (Go)
- [ ] pyproject.toml (Python)
- [ ] Gemfile (Rails)
- [ ] package.json (Node)

### CI/CD
- [ ] .github/workflows/*.yml
- [ ] .gitlab-ci.yml
- [ ] Jenkinsfile

### Quality Tools
- [ ] .golangci.yml (Go)
- [ ] ruff.toml / pyproject.toml (Python)
- [ ] .rubocop.yml (Rails)
- [ ] .eslintrc (JavaScript)

---

## § Framework Detection

### Go Frameworks

```bash
# Check go.mod for common frameworks
cat go.mod | grep -E "(gin|echo|fiber|chi|gorilla)"

# Web frameworks
# - gin-gonic/gin
# - labstack/echo
# - gofiber/fiber
# - go-chi/chi
# - gorilla/mux

# Check for structure patterns
ls -la internal/     # Clean architecture
ls -la pkg/          # Public libraries
ls -la cmd/          # Multiple binaries
```

### Python Frameworks

```bash
# Check pyproject.toml or requirements.txt
cat pyproject.toml | grep -E "(fastapi|flask|django|starlette)"

# Web frameworks
# - fastapi
# - flask
# - django
# - starlette

# Check for structure
ls -la app/          # FastAPI/Flask
ls -la project/      # Django
ls -la tests/        # pytest
```

### Rails

```bash
# Check Gemfile
cat Gemfile | grep rails

# Check structure
ls -la app/controllers/
ls -la app/models/
ls -la app/services/
ls -la config/routes.rb
```

---

## § Documentation Template

When creating CLAUDE.md, include:

```markdown
# Project Name

## Overview
Brief description of what the project does

## Architecture
- Language: [Go/Python/Rails/etc.]
- Framework: [Framework name]
- Pattern: [MVC/Service-oriented/Clean architecture/etc.]

## Project Structure
```
[Directory tree]
```

## Key Conventions
- Naming: [snake_case/camelCase/PascalCase]
- Testing: [Framework used]
- Linting: [Tools used]
- Git workflow: [Branch strategy]

## Setup
```bash
[Setup commands]
```

## Common Commands
```bash
[Build/test/run commands]
```

## Dependencies
[Key dependencies and their purpose]

## Testing
[How to run tests, coverage expectations]

## Deployment
[How the project is deployed]

## Resources
[Links to docs, wikis, etc.]
```

---

## § Agent Invocation

Use the Task tool with:

```
subagent_type: "project-analyzer"
prompt: "Analyze the project in [directory] and create comprehensive CLAUDE.md documentation"
```

The agent will:
1. Scan directory structure
2. Identify language and framework
3. Analyze code patterns with ast-grep
4. Detect conventions
5. Generate CLAUDE.md

---

## § Project Modernization Heuristics

When working on modernization or migration projects, apply these heuristics from Matteo Vaccari's AI-assisted methodology:

### Plan-Before-You-Code Heuristic

**Principle:** Ask the AI to develop plans and clarifying questions before implementation.

**Application:**
```
Instead of: "Migrate this to Spring Boot"
Better: "Analyze this codebase and provide 2-3 migration strategies with pros/cons"
```

Start in planning mode to ensure informed decisions rather than rushing into potentially problematic approaches.

### Goal Heuristic

**Principle:** State desired outcomes and let the AI iterate toward them autonomously.

**Application:**
```
Instead of: "Fix the MySQL driver error"
Better: "Make the application build and run successfully"
```

The AI will debug and adapt until succeeding, often finding unexpected solutions and cascading issues.

### Run-Locally Heuristic

**Principle:** First compile the legacy codebase, then ensure it runs locally.

**Why:** Fast feedback loops enable rapid iteration without cloud deployment overhead.

**Workflow:**
1. Get it to compile
2. Get it to run locally (docker-compose if needed)
3. Verify core functionality
4. Then modernize incrementally

### Value First Heuristic

**Principle:** Prioritize porting the most valuable user journeys first, not infrastructure.

**Application:**
- Identify highest-value features (e.g., purchase flow over admin panel)
- Port those first to deliver business value early
- Maintain stakeholder engagement with visible progress
- Skip "logical" prerequisites when demonstrating value

**Example:**
```
❌ Wrong priority: Authentication → Profile → Search → Purchase
✅ Value-first: Purchase (with pre-populated test users) → then Authentication
```

### Team Sport Heuristic

**Principle:** Involve people who work with the system regularly.

**Why:** Domain knowledge and organizational context aren't in the codebase.

**Actions:**
- Interview developers familiar with the legacy system
- Understand business priorities from stakeholders
- Document tribal knowledge that code doesn't reveal
- Validate AI-generated analysis with domain experts

### Keep CLAUDE.md Up To Date Heuristic

**Principle:** Periodically review and update project documentation to reflect current state.

**Workflow:**
1. After major milestones, review CLAUDE.md
2. Let AI update it (use "Get The AI To Program Itself" heuristic)
3. Remove duplications and inconsistencies
4. Verify accuracy against actual codebase

**Trigger points:**
- After completing a major feature
- Before switching to a different part of the codebase
- When onboarding new team members
- After architectural changes

**Example prompt:**
```
"Review CLAUDE.md for accuracy and remove any duplications or outdated information. 
Update it to reflect the current state after migrating the purchase flow to Spring Boot."
```

---

## § Common Patterns by Language

### Go Projects

**Typical structure:**
```
cmd/           # Executables
internal/      # Private code
pkg/           # Public libraries
api/           # API definitions
configs/       # Configurations
scripts/       # Build scripts
```

**Look for:**
- Constructor patterns (`New*`)
- Interface definitions
- Error handling patterns
- Dependency injection

### Python Projects

**Typical structure:**
```
src/           # Source code
tests/         # Tests
docs/          # Documentation
scripts/       # Utility scripts
```

**Look for:**
- Class definitions
- Type hints usage
- pytest fixtures
- async patterns

### Rails Projects

**Typical structure:**
```
app/
├── controllers/
├── models/
├── services/
├── forms/
└── jobs/
config/
db/
spec/
```

**Look for:**
- Service objects
- Form objects
- Dry-validation contracts
- Background jobs (Sidekiq)

---

## § Tips

1. **Start broad, then narrow**: Directory structure → Key files → Code patterns
2. **Use ast-grep**: Language-aware search is more accurate
3. **Check tests first**: Tests reveal expected behavior
4. **Look for README**: Often has setup instructions
5. **Check CI config**: Shows quality expectations
6. **Run the project**: Nothing beats actually running it

---

## § Resources

**Related Skills:**
- Language analysis: `_AST_GREP.md`
- Go projects: `golang/SKILL.md`
- Python projects: `python/SKILL.md`
- Rails projects: `rails/SKILL.md`
- Terraform: `terraform/SKILL.md`

---

**End of SKILL: Project Analyzer**
