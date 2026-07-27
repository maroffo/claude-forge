---
name: project-checks
description: "Scaffold a Makefile with language-specific check targets (lint, vet, fmt, vuln, test). Auto-detects project languages from marker files. Use when user says project checks, scaffold checks, add make check, or /project-checks. Not for running checks (the advanced-review preflight does that)."
compatibility: "Any project. Generated Makefile assumes standard tooling is installed (golangci-lint, ruff, eslint, etc.)."
---

# ABOUTME: Scaffold Makefile with language-specific check targets
# ABOUTME: Auto-detect, generate, ask before modifying existing Makefiles

# Project Checks (Makefile Scaffolding)

Generates a `Makefile` with a `check` target that runs lint, vet, format
checks, vulnerability scanning, and tests specific to the project's
language(s). The result is committed to the repo and used by CI, pre-commit
hooks, and the advanced-review preflight gate.

## Trigger

Activate when the user says: "project checks", "scaffold checks",
"add make check", or `/project-checks`.

## Execution Flow

### Step 1 - Detect languages

Scan the project root for marker files:

| Marker | Language |
|--------|----------|
| `go.mod` | Go |
| `pyproject.toml` or `setup.py` | Python |
| `package.json` | JavaScript/TypeScript |
| `Gemfile` | Ruby |
| `Cargo.toml` | Rust |

Multiple languages can be detected (e.g., Go backend + Python scripts).

### Step 2 - Generate Makefile

Load the template for each detected language from `templates/<lang>.mk`.
Combine into a single Makefile with:

- `check` target that depends on all language-specific sub-targets
- Sub-targets: `lint`, `vet`, `fmt-check`, `vuln`, `test`
- Each sub-target runs the appropriate tool for the language

### Step 3 - Handle existing Makefile

If a `Makefile` already exists:
1. Show the diff (what targets would be added)
2. Ask the user before modifying
3. Merge new targets without touching existing ones

If no `Makefile` exists: generate it directly.

### Step 4 - Report

Show what was generated and suggest next steps:
- `make check` to run all checks
- Add to CI pipeline
- The advanced-review preflight will auto-detect and use it

## Language Templates

Each template defines the standard tooling for that language. Templates are
in `templates/<lang>.mk` and use Make variables for tool paths so users can
override them.

### Advisory targets (Go)

`templates/go.mk` also ships two targets that are deliberately **outside**
`check`, run by hand when a review needs a number instead of an argument:

| Target | Tool | Purpose |
|--------|------|---------|
| `crap` | crap4go | CC, coverage and CRAP per function, from the standard coverage profile. Evidence for a finding, not a gate: no threshold (see `rules/quality-gates.md`, Finding Contract) |
| `mutation` | gremlins | `make mutation PKG=./internal/foo`. Surviving mutants are evidence of tautological tests. Slow (recompiles and reruns the suite per mutant), so never in `check` or the inner loop |

Both install their tool on demand via `go install` when it is missing.

## When to Use

- New project that needs a standardized check target
- Existing project without a unified lint/test/vuln command
- After the advanced-review preflight says "no make check target found"

## When NOT to Use

- Project already has a working `make check` or equivalent
- CI-only checks that don't make sense locally
