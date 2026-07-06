# ABOUTME: Change contract for the on-demand codemap (CLI command + SessionStart awareness nudge)
# ABOUTME: Map generated on demand via `codemap`, printed to stdout; hook only advertises it, no scan

# Harness Change Contract: codemap on-demand — `codemap` CLI + awareness nudge

Supersedes `2026-07-06_codemap-ephemeral.md` (which superseded `2026-07-05_codemap-toolkit.md`);
none merged. Three /second-opinion passes converged here: keep the deterministic ast-grep
generator, deliver it on demand as a CLI command, and reduce the hook to a cheap awareness nudge.

## Component

- `codemap/codemap.sh` (new) — CLI wrapper, symlinked onto PATH as `codemap`; runs
  `generate.py --repo <cwd> --print`. No file, no cache, no state.
- `hooks/codemap-session.py` (rewritten) — SessionStart nudge only: manifest sniff
  (`generate.py:structural_summary`, no ast-grep scan), emits one imperative line naming `codemap`.
- `codemap/generate.py` — added `structural_summary()` (free stack/workspace facts); generator
  and rules otherwise unchanged.
- `hooks/settings.example.json` — SessionStart registration (unchanged shape, hook now trivial).

## Failure mode targeted

The prior (ephemeral) design generated a ~1.2k-token map and injected the whole body into context
at every SessionStart, even for sessions that never needed orientation: a recurring context tax,
plus an ast-grep scan on the session-start critical path. And the persisted out-of-tree file
carried slug-collision and cache-staleness surface. On-demand generation removes all of it: the
map is produced only when the agent runs `codemap`, fresh at that moment, printed to the tool
result; nothing is stored.

## Predicted improvement

Zero map cost on sessions that do not invoke `codemap` (down from ~1.2k tokens + a scan every
session). The nudge (a few dozen tokens, no scan) is the only unconditional cost. Over the next 10
sessions in mappable repos: the nudge appears at SessionStart; `codemap` returns a fresh map in
one Bash call when invoked; no file is ever written; no CODEMAP.md appears in any repo. Invocation
rate is observable in existing traces (`codemap` is a Bash call captured by session-end-trace),
so the next iteration is data-driven, not another round of priors.

## Invariants preserved

- Fail-open: hook and CLI exit cleanly on any error; a missing map never blocks or hangs a session.
- The nudge does NO ast-grep scan (manifest/glob sniff only), so SessionStart stays cheap.
- Deterministic generator, no LLM, no network (unchanged).
- Nothing written into any repo; the CLI only prints. No persisted artifact anywhere.
- Silent for non-git dirs and repos with no mappable stack.
- Serena (LSP) remains the symbol-navigation layer; the nudge explicitly delegates to it.

## Falsification

If traces over 10 sessions show agents never run `codemap` despite the nudge (awareness fails),
strengthen the nudge or reconsider an MCP tool (DeepSeek's alternative). If `codemap` runtime
regularly exceeds a few seconds on a real monorepo (blocking the agent's turn noticeably),
reintroduce a cache behind the CLI. If the nudge fires on repos with no real surface (false
positives from `structural_summary`), tighten detection.

## Rollback

`git revert <commit>`; `rm ~/.local/bin/codemap`; the SessionStart entry can stay (hook fail-opens
if the generator is gone) or be removed. Affects: codemap/codemap.sh, codemap/generate.py
(`structural_summary`), hooks/codemap-session.py, hooks/tests/test_codemap_session.py,
codemap/tests/test_cli.py, hooks/settings.example.json.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
