# ABOUTME: Living plan — Serena adoption + CODEMAP toolkit (fresh per-repo orientation maps for agents)
# ABOUTME: Two-layer design: live LSP symbols (adopt Serena) + committed CODEMAP.md with freshness stamp (build)

# Plan: Serena + CODEMAP (2026-07-05)

**Goal**: agents get (a) fresh symbol navigation and (b) a token-cheap, always-verifiable orientation map (endpoints, public surface, directory intent) per repo. Staleness must be detectable mechanically, never trusted on prose (see post "Stale Evidence Sounds Exactly Like Fresh Evidence").

**Research**: research-analyst 2026-07-05, verdict moderate. Adopt Serena for symbols (never build a symbol index); build thin ast-grep layer for orientation; DeepWiki rejected (staleness by design, private-repo constraint).

## Target matrix (scanned 2026-07-05)

| Repo | Stack | Extractor |
|------|-------|-----------|
| hikma-ai | Python/FastAPI | ast-grep: decorator routes |
| hikma-wasit | Go/chi + gRPC | ast-grep: chi mounts; regex: proto `service/rpc` |
| hikma-pgpilot | Go/net-http | ast-grep: HandleFunc |
| hikma-mirsad, hikma-weaponizer | Go/gRPC | regex: proto |
| wishew-monorepo | TS/Hono + NestJS, pnpm workspaces | ast-grep: app.get/post, @Controller/@Get; workspace map from pnpm-workspace.yaml |
| hikmaai-frontend | Next.js | glob: app/**/{page,route}.* |
| all | exported symbols per lang | ast-grep, capped |

## Workstreams

### A. Serena adoption (zero-build, separable)
1. `claude mcp add` Serena (uvx, project-scoped to ONE pilot repo first: hikma-wasit) — context cost per session is the risk, measure before enabling globally
2. Change contract A (settings mutation): failure mode "symbol questions answered from stale grep/map instead of live LSP"
3. Evaluate after ~5 sessions on pilot: token overhead vs. navigation wins → widen or drop

### B. CODEMAP toolkit (in claude-forge, source of truth)
Files (new dir `codemap/`):
1. `codemap/rules/<framework>.yml` — ast-grep rule-pack (fastapi, chi, net-http, hono, nestjs, exported-symbols per Go/Py/TS/Ruby)
2. `codemap/generate.py` — uv script: `sg scan --json` + proto regex + Next.js glob → `CODEMAP.md` with header `<!-- codemap: <commit-sha> <utc-ts> -->`; hard token cap (~1.2k tokens, rank: endpoints > workspace map > exported surface)
3. `hooks/codemap-freshness.py` + `.sh` — SessionStart advisory: if repo has CODEMAP.md and stamp SHA is behind HEAD for covered paths → one-line nudge "map stale, run make codemap". Fail-open, tests in hooks/tests/
4. Regeneration: PostToolUse hook on `git commit` (harness-level, NOT .git/hooks — deny-listed): repo opted in via `codemap/` marker or Makefile target → regenerate after commit; map lags max 1 commit, lag detectable via stamp
5. `make codemap` target scaffold (extend project-checks skill)
6. project-analyzer skill: reference CODEMAP.md instead of regenerating structure prose
7. Change contract B: failure mode "agents re-derive repo structure/endpoints on every complex task; stored maps rot silently"
8. Tests: rule-pack fixtures per framework (golden CODEMAP snippets), hook tests

### C. Pilot rollout (order)
1. hikma-wasit (richest: chi + gRPC) → validate Go rules
2. hikma-ai (FastAPI) → Python rules
3. wishew-monorepo (Hono/NestJS + workspace map) → TS rules + monorepo shape
4. hikmaai-frontend (Next.js glob)
5. Remaining hikmaAI repos mechanically

<!-- checkpoint:verify --> after B+C.1: Max eyeballs the wasit CODEMAP.md before multi-repo rollout.

## Decisions

| # | Decision | Choice | Rationale | Revisit if |
|---|----------|--------|-----------|-----------|
| 1 | Scope v1 | Serena + CODEMAP both | Complementary layers; Serena zero-build | Serena context cost too high |
| 2 | Targets | hikmaAI (all) + wishew-monorepo | Max 2026-07-05 | — |
| 3 | Regen trigger | post-commit (PostToolUse on git commit) + advisory freshness hook | Max 2026-07-05; no diff churn, staleness detectable | advisory ignored in practice → move into pre-commit gate |
| 4 | Symbol index | never build; Serena/LSP only | live > stored for symbol truth | — |
| 5 | Map size | hard cap ~1.2k tokens | aider lesson: unbounded maps get skipped | pilot shows cap too tight |

## Progress

- 2026-07-05: plan drafted post-research.
- 2026-07-05: contract B written; codemap toolkit built TDD (4 rules, generate.py, 8 test groups + 12 hook cases, all green); hooks codemap-freshness (SessionStart advisory) + codemap-regen (PostToolUse on git commit, opt-in = CODEMAP.md presence) registered in settings.example.json; Makefile runs codemap tests in test-e2e.
- 2026-07-05: pilot map generated for hikma-wasit (mount table survives the cap, inner routes truncated first). Awaiting Max checkpoint:verify before rollout.
- 2026-07-05: contract A written; Serena MCP registered local-scope on hikma-wasit (uvx, ide-assistant context), connection verified. Evaluate after ~5 sessions (context overhead < ~5k tokens/session).

## Surprises & Discoveries

- ast-grep trailing `$$$REST` after named metavars requires >= 1 extra argument (does not match empty): hono rule needed `any:` of 2-arg and 3+-arg forms. Evidence: probe on fixtures, 0 vs 3 matches.
- chi `Route("/x", func(r chi.Router) {...})` drags the whole closure body into the handler capture: generator collapses handlers to one line capped at 60 chars, or the token cap is eaten by function bodies (wasit map went from truncating at Endpoints to fitting mounts + more).
- Opt-in marker = presence of CODEMAP.md turned out cleaner than a config file: first generation is a human act, regen is automatic afterwards.

## Outcomes & Retrospective

- (open)
