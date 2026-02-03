---
name: source-control
description: "Git conventions for commit messages and workflow. Use for git commit, conventional commits, commit format, feat fix docs, git workflow."
allowed-tools: [mcp__acp__Bash]
---

# ABOUTME: Git conventional commit format and version control best practices
# ABOUTME: Commit message standards, branch strategies, workflow patterns

# Source Control

## CRITICAL: Never run `git push` automatically. Push is ALWAYS done manually by Max.

## Quick Reference

```bash
git commit -m "feat: add user authentication"
git checkout -b feat/user-auth
git fetch origin && git rebase origin/main
git stash && git stash pop
```

---

## Conventional Commits

**Format:** `<type>(<scope>): <subject>` (scope/body/footer optional)

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
| `revert` | Revert commit |

**Rules:** Imperative mood, present tense, lowercase, no period, max 50 chars

```bash
# Good
git commit -m "feat(auth): add JWT validation"
git commit -m "fix: resolve race condition"

# Bad
git commit -m "Fixed stuff"      # Not conventional
git commit -m "Feat: Add thing"  # Capital letter
```

---

## Branch Naming

| Type | Pattern |
|------|---------|
| Feature | `feat/user-auth`, `feature/dashboard` |
| Fix | `fix/login-bug`, `bugfix/api-error` |
| Hotfix | `hotfix/security-patch` |
| Chore | `chore/update-deps` |

---

## Workflow

```bash
# Start feature
git checkout main && git pull origin main
git checkout -b feat/user-auth

# Keep up to date
git fetch origin && git rebase origin/main

# After PR merged
git checkout main && git pull
git branch -d feat/user-auth
```

### Rebase vs Merge

| Use | When |
|-----|------|
| **Rebase** | Keep feature branch current, clean linear history |
| **Merge** | Integrate to main (via PR), preserve history |

---

## Recovery

```bash
# Amend last commit
git commit --amend -m "new message"
git add file && git commit --amend --no-edit

# Undo commit (keep changes)
git reset --soft HEAD~1

# Undo commit (discard)
git reset --hard HEAD~1

# Revert pushed commit
git revert abc1234

# Recover lost commit
git reflog
git checkout -b recovery abc1234
```

---

## Conflicts

```bash
git status                    # See conflicts
# Edit files, remove markers
git add resolved_file
git rebase --continue         # or merge --continue
git rebase --abort            # if needed
```

---

## Hooks

**Pre-commit:** `.git/hooks/pre-commit`
```bash
#!/bin/bash
set -e
# Go: goimports -w . && go vet ./... && go test -race ./...
# Python: uv run ruff check . && uvx ty check && uv run pytest -q
# Rails: bundle exec lefthook run all
```

**Commit-msg:** Validate conventional format
```bash
#!/bin/bash
if ! grep -qE "^(feat|fix|docs|style|refactor|perf|test|chore|ci|build|revert)(\(.+\))?: .+" "$1"; then
    echo "Error: Use conventional commit format"
    exit 1
fi
```

---

## Best Practices

| DO | DON'T |
|----|-------|
| Conventional commits | Generic messages ("fix", "update") |
| Small, logical commits | Huge unrelated changes |
| Run tests before commit | Push broken code |
| Use branches | Commit to main directly |
| `--force-with-lease` | `--force` on shared branches |
| Never `--no-verify` | Skip pre-commit hooks |

---

## Resources

- https://www.conventionalcommits.org/
- https://git-scm.com/doc
- Tools: commitlint, husky, lefthook
