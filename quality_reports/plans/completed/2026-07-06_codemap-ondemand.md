# ABOUTME: Living plan — on-demand codemap (agent-invoked tool + cheap SessionStart nudge)
# ABOUTME: Supersedes the unconditional full-body injection; freshness at call time, near-zero idle cost

# Plan: On-demand code map (2026-07-06)

**Goal**: the agent gets a fresh orientation map (endpoints, routes, RPC, workspaces, layout)
**when it asks for one**, not force-fed every session. A cheap SessionStart nudge tells the agent
the capability exists; the full map is generated on demand, fresh against the working tree at call
time. Replaces the current unconditional map-body injection (2026-07-06_codemap-ephemeral).

**Why** (from the 2nd /second-opinion pass, 3 isolated reviewers): two of three converged on
"tiny nudge + on-demand tool" as the ideal end-state. It removes the per-session ~1.2k-token
context tax and the scan on sessions that never need orientation, and the map is fresh at *read*
time, not merely at session start. This plan builds that end-state deliberately.

**Non-goals**: symbol navigation (Serena/LSP owns that, unchanged); PageRank ranking (that needs a
resolved symbol graph = the LSP; out of scope); focused module slices (v2, see Deferred).

---

## Design decisions (some to be resolved by /second-opinion before implementing)

| # | Decision | Proposed | Alternatives | Resolve via |
|---|----------|----------|--------------|-------------|
| D1 | On-demand delivery mechanism | **Skill `codemap`** (model-invocable, no server process, idiomatic to this skill-heavy harness) | MCP tool (cleaner call, returns data directly, but a running server + per-project registration like Serena); user-only slash command (doesn't satisfy "agent calls it") | /second-opinion |
| D2 | SessionStart nudge content | **Stack-only, no counts, no sg scan**: "this repo exposes HTTP/RPC surfaces; invoke `codemap` to orient" | Counts ("53 endpoints") — needs a scan or a cached count, reintroducing per-session cost | /second-opinion |
| D3 | Keep SessionStart hook? | **Yes, but demoted to the nudge** (drop full-body injection + per-session generation) | Drop entirely (agent may never learn the map exists) | proposed |
| D4 | Generation freshness | On demand, against the working tree, with the (HEAD, porcelain) cache reused from the current hook | — | settled |
| D5 | Cache ownership | Extract the tree-cache into `codemap/cache.py`, shared by the skill | Duplicate in skill | settled |

---

## Proposed architecture

1. **`codemap/cache.py`** — extract `tree_key()` + atomic read/write/slug from `codemap-session.py`
   into a shared module. Pure functions, unit-tested. Both the skill and the (slim) hook import it.
2. **Skill `codemap`** (`skills/codemap/SKILL.md` + `skills/codemap/generate_map.sh` or a thin
   wrapper): when invoked, runs `codemap/generate.py` against the working tree (cache-backed),
   prints the map markdown. Description tuned so the model auto-invokes it when orienting in an
   unfamiliar repo / before complex multi-file work. Also usable as `/codemap` by Max.
3. **`hooks/codemap-session.py`** reworked: on SessionStart, cheap `detect_stacks()` (no sg scan);
   if a mappable stack exists, emit a ~1-line nudge naming the `codemap` skill. No generation, no
   body injection, near-zero idle cost. Fail-open, silent otherwise.
4. **Generator + rules**: unchanged (`generate.py`, `rules/*.yml`).
5. **Contract**: new `2026-07-06_codemap-ondemand.md` supersedes `2026-07-06_codemap-ephemeral.md`
   (which never merged; superseding keeps the reasoning trail honest per harness-changes rule).

<!-- checkpoint:decide --> after /second-opinion: lock D1 (skill vs MCP tool) and D2 (nudge
content) before writing code.

---

## Steps (observable outcomes, Progress-tracked)

1. `codemap/cache.py` exists; `uv run codemap/tests/test_cache.py` green (slug no-collision, tree_key
   stable on unchanged tree, atomic write).
2. `skills/codemap/` exists; invoking the skill's script in a Go fixture repo prints a map
   containing the fixture's endpoints; second invocation on an unchanged tree is a cache hit.
3. `codemap-session` emits ONLY a nudge (no `sg` in its process trace) and names the `codemap`
   skill; test asserts nudge present for a mappable repo, silent for a docs-only repo.
4. Contract + this plan + `settings.example.json`/live settings reflect the nudge-only hook.
5. `make check` + `make test-e2e` green; live e2e: SessionStart prints the nudge, the skill returns
   a fresh map for hikma-wasit.
6. PR #61 updated to the on-demand design.

---

## Decisions log (append-only)

| # | Decision | Choice | Rationale | Revisit if |
|---|----------|--------|-----------|-----------|
| 1 | Build the on-demand tool "for real" | yes | Max 2026-07-06; 2/3 reviewers' ideal end-state | — |
| 2 | (resolves D1) On-demand mechanism | **CLI command `codemap`**, not skill, not MCP | 3rd /second-opinion: skill = 2-turn indirection (DeepSeek, Gemini); MCP = server overkill for a 180ms stateless script (Gemini, Claude); CLI is the Condorcet winner, native to Claude's Bash tool, single-turn, zero registration | agent proves unable to run a bare command |
| 3 | (resolves cache) Drop caching + out-of-tree file entirely | `codemap --print` to stdout, no file | Unanimous: on-demand generation (~180ms) is masked by inference latency; no persisted file → slug-collision/atomic-write/stale-cache bugs vanish by construction | monorepo where a scan exceeds ~3s in practice |
| 4 | (resolves D2/D3) Keep SessionStart hook as an imperative nudge with FREE structural counts | yes | Unanimous: nudge is load-bearing (a passive command is invisible); counts must be free (workspace/stack sniff, never the endpoint count that needs an sg scan); phrase imperatively ("before you grep, run `codemap`") | trace shows agents invoke off no nudge |
| 5 | (resolves cache.py) Do NOT extract codemap/cache.py | dropped | Premature (single consumer), and mooted by Decision #3 (no cache at all) | — |

## Revised architecture (post 3rd /second-opinion)

1. **`codemap` CLI** (`codemap/codemap.sh`, symlinked onto PATH): runs `generate.py --repo <cwd>
   --print`, emits the token-capped map to stdout. No file, no cache, no state.
2. **`hooks/codemap-session.py`** demoted to a pure nudge: cheap `detect_stacks()` (no sg scan);
   if a mappable stack exists, emit one imperative line with free structural counts (stacks +
   workspace count) naming the `codemap` command. No generation, no file, no body injection.
3. Generator + rules unchanged. Deleted from the hook: out-of-tree write, slug, tree-cache, atomic
   write (all obsolete under Decision #3).
4. Instrumentation is free: `codemap` invocations are Bash calls already captured by
   `session-end-trace`, so the next round can be data-driven (isolated-Claude's ask).

## Progress

- 2026-07-06: plan drafted, /second-opinion run (3 isolated reviewers). Verdict shifted the design
  off skill+cache onto a CLI command + nudge, no cache, no file. Decisions #2-5 recorded.
- 2026-07-06: IMPLEMENTED. `codemap` CLI (codemap/codemap.sh, symlinked ~/.local/bin/codemap, --print,
  no file); `generate.py:structural_summary` (free stack/workspace facts); `codemap-session` rewritten
  to a nudge-only hook (no scan). Tests: codemap-cli 1, codemap-session 5, codemap-generate 8, all green.
  Live: `codemap` prints the wasit map; nudge fires "(Go) ... run `codemap`". Obsolete out-of-tree maps
  removed. Contract 2026-07-06_codemap-ondemand supersedes the ephemeral one (both marked). PR #61 next.

## Surprises & Discoveries

- (none yet)

## Deferred ideas

- Focused slices: `codemap --module auth` returning only that subtree's surface (reviewer Q).
- Counts in the nudge, cache-backed, only if a cached map already exists (zero-scan).

## Outcomes & Retrospective

(closed 2026-07-27, retroactively during the issue #103 contract-result pass; work had landed on 2026-07-06)

- **Shipped:** `codemap` CLI (no cache, no file, --print), `structural_summary`, nudge-only codemap-session hook; all tests green, live-verified on wasit, obsolete out-of-tree maps removed. Contract 2026-07-06_codemap-ondemand supersedes the ephemeral one.
- **Gaps:** adoption is invisible in telemetry (traces record no Bash commands), so the contract's Result row reads insufficient data; the deferred ideas (focused slices, cache-backed counts) remain unfiled.
- **Lessons:** the second opinion moved the design from skill+cache to a plain CLI before implementation, cheaper than pivoting after; measuring adoption needs an extractor step or an invocation counter, not hope.
