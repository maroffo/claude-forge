# ABOUTME: Shared conventions for the language skills - version discovery and pre-commit gate
# ABOUTME: Referenced by golang, python, rails, ruby, react-nextjs, android-kotlin, apple-swift

# Language Skill Commons

## Version: determine, don't assume

Never trust memory for a language, runtime, or framework version: it rots fast and you miss CVE fixes. Before answering anything version-sensitive, fetch the actual version the project uses (manifest, pin file, lockfile, toolchain command) and, for a new project, the latest upstream stable. Each language skill lists the exact commands. Prefer idioms gated to the project's version or lower.

## Pre-commit verification

The `pre-commit-gate` hook runs `make check && make test-e2e` on every commit; both MUST pass (see `rules/verification-protocol.md`). Per-language check commands (what `make check` expands to) live inline in each language skill. If `make check` is missing, scaffold it with the `project-checks` skill. If there is no e2e target, do NOT silently skip: flag it and ask whether to proceed or add one.
