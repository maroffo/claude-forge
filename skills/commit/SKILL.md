---
name: commit
description: "Create a git commit using conventional commit format. Use for committing staged changes."
allowed-tools: [Bash]
---

# ABOUTME: Git commit with conventional commit format
# ABOUTME: Wrapper around source-control conventions

# Commit

## CRITICAL RULES
- **NEVER push** - Max does that manually
- **NEVER use** `--no-verify`, `--no-hooks`
- **NEVER commit on main/master** unless explicitly authorized
- Use conventional commit format (see source-control skill)

## Process

1. Check current state:
   ```bash
   git status
   git diff HEAD
   git branch --show-current
   git log --oneline -5
   ```

2. Verify NOT on main/master (abort if so, unless authorized)

3. Stage changes (specific files, not `git add -A`):
   ```bash
   git add <specific-files>
   ```

4. Commit with conventional format:
   ```bash
   git commit -m "<type>(<scope>): <subject>"
   ```

## Conventional Commit Types

| Type | Use |
|------|-----|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation |
| `style` | Formatting |
| `refactor` | Code restructure |
| `perf` | Performance |
| `test` | Tests |
| `chore` | Maintenance |
| `ci` | CI/CD |
| `build` | Build system |

## Rules
- Imperative mood, present tense
- Lowercase, no period
- Max 50 chars subject line
- Reference source-control skill for full conventions
