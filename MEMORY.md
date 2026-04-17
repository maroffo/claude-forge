# ABOUTME: Persistent corrections across sessions — lightweight complement to LEARNING.md
# ABOUTME: Format: [LEARN:category] wrong assumption → correct fact

# Memory

Corrections and learnings that persist across sessions. When Claude makes a mistake or user corrects, append here.

## Format

```
[LEARN:category] Incorrect assumption → correct fact
```

## Entries

<!-- Append new learnings below this line -->
[LEARN:writing] Never use em dashes (—) → use Italian punctuation: commas, colons, semicolons, parentheses
[LEARN:go-workflow] Skipped go fix in verification loop → always run `go fix ./... && go vet ./...` before `go test` at every iteration, not just final verification
[LEARN:python] Invoked Python via bare `python3` → always `uv run python3 script.py` (or `uv run --script` with PEP 723), even for stdlib-only scripts. Consistent Python entry point, no shadow envs.
[LEARN:architecture] Treated rules/ as the only source of behavior → four-tier architecture is now explicit: identity (CLAUDE.md/rules) + agents + skills + extensions (hooks). Prose tells Claude what to do; hooks make sure it happens.
[LEARN:versions] Pinned language versions in skill descriptions → fetch at runtime with `go version`, `curl go.dev/VERSION`, `npm view`, etc. Pins invecchia and point to the wrong CVE-patched release.
[LEARN:hooks-scope] Scanned entire diff for stub markers (TODO/FIXME/NotImplementedError) → scope-aware scan: skip .md/docs, require comment-context for TODO/FIXME/XXX (not string literals), match `raise NotImplementedError` only as a statement. Detectors otherwise catch their own regex patterns and documentation.
[LEARN:enforcement-tiers] Jumped straight to Tier C (agent-type LLM intent verification) for commit checks → measure first with `scripts/metrics-weekly.sh` (revert rate, fix-up rate, median time-to-next-touch). Tier A mechanical checks cover ~70% cheaply. Escalate only on data.
[LEARN:compat] Claude Code reads `CLAUDE.md` only → install.sh creates relative symlink `AGENTS.md → CLAUDE.md` so cross-tool AGENTS.md convention also resolves. Zero duplication.
[LEARN:second-opinion-isolation] Ran Gemini CLI with host config access → isolate both reviewers in Docker containers without `~/.claude` mount. Genuinely independent opinions; confirmation-bias proof.
