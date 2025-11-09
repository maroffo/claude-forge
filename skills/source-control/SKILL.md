---
name: source-control
description: "Git conventions for commit messages and workflow. Use for git commit, conventional commits, commit format, feat fix docs, git workflow."
allowed-tools: [mcp__acp__Bash]
---

# ABOUTME: Git conventional commit format and version control best practices
# ABOUTME: Commit message standards, branch strategies, workflow patterns

# Source Control

## CRITICAL RULES

**NEVER run `git push` automatically. Push is ALWAYS done manually by Max.**

## Quick Reference

```bash
# Commit with conventional format
git commit -m "feat: add user authentication"
git commit -m "fix: resolve race condition in cache"

# Branch workflow
git checkout -b feat/user-auth
git checkout -b fix/login-bug

# Rebase workflow
git fetch origin
git rebase origin/main

# Interactive rebase (clean up commits)
git rebase -i HEAD~3

# Stash changes
git stash
git stash pop
git stash list
```

---

## § Conventional Commits

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Required:** `type` and `subject`  
**Optional:** `scope`, `body`, `footer`

### Types

| Type       | Description                          | Example                              |
|------------|--------------------------------------|--------------------------------------|
| `feat`     | New feature                          | `feat: add user authentication`      |
| `fix`      | Bug fix                              | `fix: resolve login timeout`         |
| `docs`     | Documentation only                   | `docs: update API documentation`     |
| `style`    | Code style (formatting, etc.)        | `style: fix indentation`             |
| `refactor` | Code refactoring                     | `refactor: simplify error handling`  |
| `perf`     | Performance improvement              | `perf: optimize database queries`    |
| `test`     | Adding or updating tests             | `test: add unit tests for auth`      |
| `chore`    | Maintenance tasks                    | `chore: update dependencies`         |
| `ci`       | CI/CD changes                        | `ci: add GitHub Actions workflow`    |
| `build`    | Build system changes                 | `build: update webpack config`       |
| `revert`   | Revert a previous commit             | `revert: revert "feat: add feature"` |

### Rules

1. **Imperative mood**: "add feature" not "added feature"
2. **Present tense**: "change" not "changed"
3. **Lowercase**: No capital letter at start
4. **No period**: Don't end subject with period
5. **Max 50 chars**: Keep subject concise

### Examples

**✅ GOOD:**
```bash
git commit -m "feat: add user authentication"
git commit -m "fix: resolve race condition in cache"
git commit -m "docs: update API documentation"
git commit -m "refactor: simplify error handling"
git commit -m "test: add unit tests for payment service"
git commit -m "chore: update dependencies"
```

**❌ BAD:**
```bash
git commit -m "Fixed stuff"                    # Not conventional, not descriptive
git commit -m "Added new feature"              # Not conventional format
git commit -m "Updated the code"               # Too vague
git commit -m "fixing bugs"                    # Not imperative mood
git commit -m "Feat: Add feature"              # Capital letter
git commit -m "feat: add feature."             # Period at end
```

### With Scope

```bash
git commit -m "feat(auth): add JWT token validation"
git commit -m "fix(api): handle null response"
git commit -m "refactor(user): simplify profile update"
```

### Multi-line Commits

```bash
git commit -m "feat: add user authentication" -m "
- Implement JWT token generation
- Add login and logout endpoints
- Create user session management
"
```

Or use editor:
```bash
git commit
# Opens editor with template:
feat: add user authentication

- Implement JWT token generation
- Add login and logout endpoints  
- Create user session management

Closes #123
```

---

## § Branch Strategies

### Branch Naming

**Feature branches:**
```bash
feat/user-authentication
feat/payment-gateway
feature/add-dashboard
```

**Bug fix branches:**
```bash
fix/login-timeout
fix/memory-leak
bugfix/api-error-handling
```

**Hotfix branches:**
```bash
hotfix/critical-security-patch
hotfix/production-crash
```

**Chore/maintenance:**
```bash
chore/update-dependencies
chore/cleanup-logs
```

### Workflow Pattern

```bash
# Start new feature
git checkout main
git pull origin main
git checkout -b feat/user-auth

# Work on feature (multiple commits)
git add .
git commit -m "feat: add login endpoint"
git commit -m "feat: add JWT validation"

# Keep up to date with main
git fetch origin
git rebase origin/main

# Push to remote
git push origin feat/user-auth

# After PR merged, cleanup
git checkout main
git pull origin main
git branch -d feat/user-auth
```

---

## § Git Workflow Best Practices

### Frequent Commits

**✅ DO:**
- Commit often (small, logical changes)
- Each commit should be a complete thought
- Commits should pass tests

```bash
git commit -m "feat: add user model"
git commit -m "feat: add user repository"
git commit -m "feat: add user service"
git commit -m "test: add user service tests"
```

**❌ DON'T:**
- Huge commits with unrelated changes
- Commits that break tests
- "WIP" or "temp" commits in main branch

### Rebase vs Merge

**Use rebase for:**
- Keeping feature branch up to date with main
- Clean, linear history

```bash
git checkout feat/user-auth
git fetch origin
git rebase origin/main
```

**Use merge for:**
- Integrating feature branches into main (via PR)
- Preserving complete history

```bash
# Usually done via PR, but manually:
git checkout main
git merge --no-ff feat/user-auth
```

### Interactive Rebase

**Clean up commits before PR:**
```bash
git rebase -i HEAD~5

# Editor opens with:
pick abc1234 feat: add user model
pick def5678 fix: typo
pick ghi9012 feat: add validation
pick jkl3456 fix: another typo
pick mno7890 test: add tests

# Change to:
pick abc1234 feat: add user model
squash def5678 fix: typo
pick ghi9012 feat: add validation
squash jkl3456 fix: another typo
pick mno7890 test: add tests

# Results in 3 clean commits
```

---

## § Git Hooks

### Pre-commit Hook

**Location:** `.git/hooks/pre-commit`

**Example (Go project):**
```bash
#!/bin/bash
set -e

echo "Running pre-commit checks..."

# Format
goimports -w .

# Vet
if ! go vet ./...; then
    echo "go vet failed"
    exit 1
fi

# Tests
if ! go test -race ./...; then
    echo "Tests failed"
    exit 1
fi

echo "✓ Pre-commit checks passed"
```

**Example (Python project):**
```bash
#!/bin/bash
set -e

echo "Running pre-commit checks..."

# Lint
uv run ruff check .

# Type check
uvx ty check

# Tests
uv run pytest -q

echo "✓ Pre-commit checks passed"
```

**Example (Rails project):**
```bash
#!/bin/bash
set -e

echo "Running pre-commit checks..."

bundle exec lefthook run all

echo "✓ Pre-commit checks passed"
```

**Make executable:**
```bash
chmod +x .git/hooks/pre-commit
```

### Commit-msg Hook

**Validate conventional commits:**
```bash
#!/bin/bash
# .git/hooks/commit-msg

commit_msg=$(cat "$1")

# Check conventional commit format
if ! echo "$commit_msg" | grep -qE "^(feat|fix|docs|style|refactor|perf|test|chore|ci|build|revert)(\(.+\))?: .+"; then
    echo "Error: Commit message doesn't follow conventional format"
    echo "Format: <type>(<scope>): <subject>"
    echo "Example: feat: add user authentication"
    exit 1
fi

echo "✓ Commit message valid"
```

---

## § Common Workflows

### Fixing Mistakes

**Amend last commit:**
```bash
git commit --amend -m "feat: add user authentication"

# Or amend without changing message
git add forgotten_file.go
git commit --amend --no-edit
```

**Undo last commit (keep changes):**
```bash
git reset --soft HEAD~1
```

**Undo last commit (discard changes):**
```bash
git reset --hard HEAD~1
```

**Revert a pushed commit:**
```bash
git revert abc1234
git push origin main
```

### Stashing

```bash
# Stash current changes
git stash

# Stash with message
git stash save "WIP: working on feature"

# List stashes
git stash list

# Apply most recent stash
git stash pop

# Apply specific stash
git stash apply stash@{1}

# Drop stash
git stash drop stash@{0}
```

### Cherry-picking

```bash
# Apply specific commit from another branch
git cherry-pick abc1234

# Cherry-pick without committing
git cherry-pick -n abc1234
```

---

## § Recovery Patterns

### Lost Commits

```bash
# Show reflog (all changes)
git reflog

# Recover lost commit
git checkout abc1234

# Or create branch from it
git checkout -b recovery-branch abc1234
```

### Merge Conflicts

```bash
# See conflicted files
git status

# Edit files to resolve conflicts
# Remove conflict markers (<<<<<<<, =======, >>>>>>>)

# Mark as resolved
git add conflicted_file.go

# Continue rebase/merge
git rebase --continue
# or
git merge --continue

# Abort if needed
git rebase --abort
# or
git merge --abort
```

### Accidentally Committed to Wrong Branch

```bash
# On wrong-branch
git log  # Note the commit hash

# Reset wrong branch
git reset --hard HEAD~1

# Switch to correct branch
git checkout correct-branch

# Apply the commit
git cherry-pick abc1234
```

---

## § .gitignore Patterns

### Go
```gitignore
# Binaries
*.exe
*.exe~
*.dll
*.so
*.dylib
bin/
dist/

# Test
*.test
coverage.out

# Go workspace
go.work
```

### Python
```gitignore
# Byte-compiled
__pycache__/
*.py[cod]
*$py.class

# Virtual environments
.venv/
venv/
ENV/

# uv
.uv/

# Testing
.coverage
htmlcov/
.pytest_cache/
```

### Rails
```gitignore
# Dependencies
/vendor/bundle

# Database
/db/*.sqlite3
/db/*.sqlite3-*

# Logs
/log/*
!/log/.keep

# Temporary files
/tmp/*
!/tmp/.keep

# Credentials
/config/master.key
/config/credentials/*.key

# Uploads
/storage/*
!/storage/.keep
```

### Terraform
```gitignore
.terraform/
*.tfstate
*.tfstate.*
*.tfvars
.terragrunt-cache/
```

---

## § Git Aliases

**Add to ~/.gitconfig:**
```ini
[alias]
    co = checkout
    ci = commit
    st = status
    br = branch
    lg = log --oneline --graph --decorate --all
    last = log -1 HEAD
    unstage = reset HEAD --
    amend = commit --amend --no-edit
    pushf = push --force-with-lease
```

**Usage:**
```bash
git co main
git ci -m "feat: add feature"
git lg
git amend
```

---

## § Best Practices Summary

### ✅ DO

- Use conventional commit format
- Commit frequently with logical changes
- Write descriptive commit messages
- Keep commits focused (single responsibility)
- Rebase to keep history clean
- Use branches for features/fixes
- Run tests before committing (pre-commit hook)
- Never use `--no-verify` flag

### ❌ DON'T

- Push broken code
- Commit directly to main
- Use generic messages ("fix", "update")
- Commit large unrelated changes together
- Force push to shared branches (use --force-with-lease)
- Ignore pre-commit hook failures
- Push without running `git push` manually (never auto-push)

---

## § Resources

**Official:**
- https://www.conventionalcommits.org/
- https://git-scm.com/doc

**Tools:**
- commitlint: Lint commit messages
- husky: Git hooks manager
- lefthook: Fast git hooks manager

**Related Skills:**
- Code quality: Language-specific skills
- Testing: Language-specific skills

---

**End of SKILL: Source Control**
