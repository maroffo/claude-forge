---
name: releasing-software
description: "Release prep and tagging with pre-flight verification. Use when user says release, tag, ship it, push to production, create release, or bump version. Not for editing a version string outside a release, a lockfile or a changelog entry by hand, and not for reading what changed in a past release: those are ordinary edits, just do them."
compatibility: "Requires gh CLI. Optional: goreleaser."
---

# ABOUTME: Release preparation skill with pre-flight verification, prevents retag-four-times pattern
# ABOUTME: Invoked on "release", "tag", "ship it", "push to production"

# Releasing Software

## Rule
Tag only after CI is green on the release commit. Run full verification locally, fix everything, then tag: a tag cut before CI passes gets deleted and recut when CI fails, and every retag breaks whoever already pulled it.

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
2. Wait for pre-commit hooks
3. Push and WAIT: `git push origin main`
4. Check CI: `gh run list --limit 2`
5. **Only after green:** `git tag -a vX.Y.Z -m "vX.Y.Z" && git push origin vX.Y.Z`
6. Verify release workflow triggered

## Stop and reassess if you catch yourself
- Tagging before CI completes
- "CI will probably pass"
- Deleting/recreating tags
- Force-pushing tags

## Common Failures

| Symptom | Root Cause | Fix |
|---------|------------|-----|
| "couldn't find main file" | Wrong goreleaser path | Set `main: .` if main.go at root |
| "no such tool 'covdata'" | Package without tests | Add `_test.go` with placeholder |
| Had to retag | Tagged before CI passed | Tag only after CI is green |
| Build fails but tests pass | Wrong build path | Check Makefile/goreleaser match |

## Troubleshooting
```bash
# Verify goreleaser config
goreleaser check

# Dry run release
goreleaser release --snapshot --clean

# Check for packages without tests
find . -type d -not -path "*/.*" -exec sh -c 'ls {}/*_test.go 2>/dev/null || echo "No tests: {}"' \;
```
