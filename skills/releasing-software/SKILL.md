<!-- ABOUTME: Release preparation skill - prevents retag-four-times pattern -->
<!-- ABOUTME: Invoked on "release", "tag", "ship it", "push to production" -->
---
name: releasing-software
description: Release prep & tagging - invokes on "release", "tag", "ship it", "push to production". Prevents retag failures via pre-flight verification
---

# Releasing Software

## Iron Law
**NO TAG WITHOUT GREEN CI**

Run full verification locally → Fix everything → THEN tag. Never tag before CI passes.

## Pre-Release Checklist

| Check | Items | Why |
|-------|-------|-----|
| **Build Paths** | goreleaser.yml `main:`, workflows, Makefile, Dockerfile | Wrong path = build failure |
| **Test Coverage** | Every package has ≥1 test file | Go 1.23+ covdata fails without tests |
| **Local CI** | `make test && make lint && make build` | Catch failures before push |
| **Docs** | README.md, CHANGELOG.md, version refs | Professional releases |
| **Release Config** | goreleaser description, homepage URL, .gitignore | Proper artifact generation |
| **Git State** | `git status`, `git diff --stat`, `git log` | Clean history |

## Release Procedure
**Only after ALL checks pass:**

1. Commit: `git add -A && git commit -m "release: prepare vX.Y.Z"`
2. Wait for pre-commit hooks (NEVER use --no-verify)
3. Push and WAIT: `git push origin main`
4. Check CI: `gh run list --limit 2`
5. **Only after green:** `git tag -a vX.Y.Z -m "vX.Y.Z" && git push origin vX.Y.Z`
6. Verify release workflow triggered

## Red Flags - STOP IMMEDIATELY
- Tagging before CI completes
- "CI will probably pass"
- Deleting/recreating tags
- Force-pushing tags
- Skipping pre-commit hooks

## Common Failures

| Symptom | Root Cause | Fix |
|---------|------------|-----|
| "couldn't find main file" | Wrong goreleaser path | Set `main: .` if main.go at root |
| "no such tool 'covdata'" | Package without tests | Add `_test.go` with placeholder |
| Had to retag | Tagged before CI passed | **WAIT FOR GREEN CI** |
| Build fails but tests pass | Wrong build path | Check Makefile/goreleaser match |

## Semver Quick Ref
- **Patch** (0.0.X): Bug fixes only
- **Minor** (0.X.0): New features, backwards compatible
- **Major** (X.0.0): Breaking changes

## Troubleshooting
```bash
# Verify goreleaser config
goreleaser check

# Dry run release
goreleaser release --snapshot --clean

# Check for packages without tests
find . -type d -not -path "*/.*" -exec sh -c 'ls {}/*_test.go 2>/dev/null || echo "No tests: {}"' \;
```

## Remember
Every retag erodes trust. Fix problems before tagging, not after.
