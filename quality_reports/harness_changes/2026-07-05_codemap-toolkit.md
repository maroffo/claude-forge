# ABOUTME: Change contract for the codemap toolkit (rule-pack, generator, freshness + regen hooks)
# ABOUTME: Agents get a token-cheap, commit-stamped orientation map whose staleness is mechanically detectable

# Harness Change Contract: codemap toolkit — fresh per-repo orientation maps

## Component

- New directory `codemap/`: ast-grep rule-pack (`rules/*.yml`), generator (`generate.py`), tests (`tests/`)
- Hooks: `hooks/codemap-freshness.py` + `.sh` (SessionStart advisory), regen wiring on `git commit` (PostToolUse)
- Settings fragment: `hooks/settings.example.json` (two registrations)
- Makefile: test wiring for `codemap/tests/`

Plan: `quality_reports/plans/active/2026-07-05_codemap-serena.md`. Research: research-analyst 2026-07-05
(adopt Serena for symbols, build only the orientation layer; Serena adoption is a separate contract).

## Failure mode targeted

Agents starting a complex task in a work repo re-derive structure, endpoints, and public surface
from scratch every session (repeated glob/grep/read cycles), or worse, trust a hand-written
CLAUDE.md/project-analyzer output that has silently drifted from the code. There is no
token-cheap orientation artifact whose freshness is verifiable rather than assumed.

## Predicted improvement

On piloted repos, a fresh session answers "what are this repo's endpoints and public surface"
from one file read (~1.2k tokens) instead of an exploration round. Qualitative, sample: next 10
sessions on piloted repos, zero cases of an agent acting on a stale map without the staleness
being surfaced first (the SessionStart advisory fires whenever CODEMAP.md's stamp is behind HEAD
for covered paths).

## Invariants preserved

- Generator is deterministic: same tree in, same map out; no LLM in the loop; no network.
- CODEMAP.md carries the generating commit SHA; staleness is detectable by hooks and humans.
- Hard token cap (~1.2k tokens): endpoints > workspace map > exported surface; overflows truncated, never grown.
- Both hooks fail-open; advisory only (no blocking); regen never runs in repos that have not opted in.
- No writes to `.git/hooks` (deny-listed); regen rides the harness PostToolUse event.
- Test files (`*_test.go`, `test_*.py`, `*.spec.ts`) never contribute endpoints.
- Freshness is a commit-boundary check (`<stamp-sha>..HEAD`): uncommitted working-tree edits to
  covered files are NOT surfaced by the advisory. Regen fires PostToolUse on commit, so the map is
  current as of the last commit, never lagging behind it.
- `make check`/`make test-e2e` in claude-forge stay green; existing hooks untouched.

## Falsification

If over the pilot (first 3 repos, ~10 sessions) the advisory fires more than twice per session on
maps that are actually current (false staleness from path-coverage misdetection), or agents
demonstrably ignore CODEMAP.md and re-explore anyway (trace inspection), the design is wrong:
revert hooks and demote the generator to an on-demand tool inside project-analyzer.

## Rollback

`git revert <commit>`; remove the two Stop/SessionStart symlink(s) and settings entries; delete
per-repo CODEMAP.md files (they are generated artifacts). Affects: codemap/**, hooks/codemap-freshness.*,
hooks/settings.example.json, Makefile.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|

| 2026-07-06 | 1 session | design manufactured the stale-artifact anti-goal; 3 isolated reviewers unanimous | **reverted** — superseded by [[2026-07-06_codemap-ephemeral]] |
