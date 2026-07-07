---
name: source-control
description: "Git conventions for commit messages and workflow. Use for git commit, conventional commits, branch strategy, rebasing, merge conflicts, git workflow. Not for general code changes that happen to need a commit afterward."
allowed-tools: [Bash]
---

# ABOUTME: Git conventional commit format and version control best practices
# ABOUTME: Commit message standards, branch strategies, workflow patterns

# Source Control

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

## Commit Process

1. **Check state:**
   ```bash
   git status && git diff HEAD && git branch --show-current && git log --oneline -5
   ```

2. **Verify NOT on main/master** (abort if so, unless authorized)

3. **Stage specific files** (never `git add -A`):
   ```bash
   git add <specific-files>
   ```

4. **Commit with conventional format:**
   ```bash
   git commit -m "<type>(<scope>): <subject>"
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

| Use | When |
|-----|------|
| **Rebase** | Keep feature branch current, clean linear history |
| **Merge** | Integrate to main (via PR), preserve history |

---

## Post-PR Loop (babysitting)

After a PR is opened, CI failures and review comments arrive asynchronously. Instead of Max polling, offer a time-based loop:

```
/loop 10m check PR #<N>: if CI failed, diagnose and fix; if new review comments, address them; commit fixes on the PR branch and push; stop when CI is green and no comments are unaddressed
```

Rules for the loop:

- **Push authorization:** Max starting the `/loop` on a PR **is** the explicit push authorization, scoped to that PR branch and that loop session only. Outside a PR loop, the NEVER-push rule stands unchanged.
- Never force-push inside a loop; `--force-with-lease` only, and only for rebase-on-main conflicts Max asked for.
- Commits inside the loop follow the same conventional format and pre-commit gate (`make check && make test-e2e`); hooks are never bypassed under loop time pressure.
- Match the interval to the external system: CI that takes ~10 minutes doesn't need a 2-minute loop.
- Stop condition is part of the prompt (CI green + comments addressed); the loop must not idle-run after the PR merges: cancel it from the session that started it (interrupt, or ask the loop to stop).

---

## Rules

- NEVER push automatically (Max pushes manually; sole exception: an active Post-PR Loop, scoped to its PR branch, see above)
- NEVER work on `main`/`master` unless explicitly authorized
- Small, logical commits; no huge unrelated changes
- `--force-with-lease`, never bare `--force` on shared branches
- Run `make check && make test-e2e` before committing (see language skills for the expansion)
- Conflict resolution and recovery commands (reset, reflog, revert, amend): use standard git, no project-specific conventions here.
