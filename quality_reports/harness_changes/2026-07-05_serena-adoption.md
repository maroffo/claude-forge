# ABOUTME: Change contract for adopting the Serena MCP server (LSP-based symbol tools), pilot-scoped
# ABOUTME: Symbol questions answered live by LSP instead of stale grep/stored maps; evaluated on one repo

# Harness Change Contract: Serena MCP adoption (pilot: hikma-wasit)

## Component

Settings fragment: local-scope MCP server registration (`claude mcp add serena`, scope local,
project hikma-wasit). No repo files change. Toolkit counterpart lives in the separate
2026-07-05_codemap-toolkit contract; per plan `quality_reports/plans/active/2026-07-05_codemap-serena.md`.

## Failure mode targeted

Symbol-level questions ("who calls X", "where is Y defined", "what implements Z") get answered
from grep heuristics or stored artifacts that can be stale, instead of from the live LSP, which
is fresh by construction. Research 2026-07-05: never build or store a symbol index.

## Predicted improvement

On hikma-wasit sessions, cross-file symbol navigation happens through Serena tools instead of
repeated Grep/Read rounds. Qualitative, sample: ~5 sessions on the pilot repo. Secondary metric
to watch: per-session context overhead added by the MCP tool schemas (measured via harness-trace
token baseline) stays under ~5k tokens.

## Invariants preserved

- Registration is local-scoped to the pilot repo: other projects see no new tools and pay no
  context cost.
- Serena runs read-only in spirit for our use (navigation); its editing tools are not part of
  the workflow (software-engineer edits stay with native tools).
- No secrets in the registration; server runs locally via uvx, no network service exposed.

## Falsification

If after ~5 pilot sessions the context overhead exceeds ~5k tokens/session without measurable
navigation wins (trace inspection: Serena tools unused or duplicating Grep), remove the
registration. Also remove if the server proves flaky (startup failures blocking sessions).

## Rollback

`claude mcp remove serena` from the pilot project (or delete the entry from ~/.claude.json for
that project path). One line, no repo changes.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| 2026-07-07 | 0 pilot sessions on this workstation (registration absent from global and per-project `~/.claude.json`) | The piloted role (live LSP symbol navigation) is covered natively by first-party Claude Code LSP plugins, available for every language in the target matrix: `gopls-lsp` (Go) and `swift-lsp` (Swift) already enabled, `pyright-lsp` (Python) and `typescript-lsp` (TS) enabled 2026-07-07. Native plugins integrate into the `LSP` tool at zero per-session MCP schema cost, avoiding the ~5k-token falsification threshold entirely, and carry no `uvx`/external-server startup-flake risk. | **not adopted (superseded by native LSP plugins)** |

Verdict: **reverted** (never adopted). The prediction (Serena navigation wins outweigh MCP context cost) was overtaken: native LSP plugins landed and deliver the same live-symbol-truth guarantee (Decision #4 of plan `2026-07-05_codemap-serena.md`: "never build; Serena/LSP only") without the context tax the contract itself flagged as the risk. Serena remains an optional on-demand `uvx` fallback for a language with no native LSP plugin; not the case for the current stack. The complementary CODEMAP layer is unaffected (tracked in `2026-07-06_codemap-ephemeral`).
