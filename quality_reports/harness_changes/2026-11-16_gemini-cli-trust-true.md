# ABOUTME: Change contract: pr-watch exports GEMINI_CLI_TRUST_WORKSPACE=true so headless gemini keeps its tools in review clones
# ABOUTME: Targets Gemini segment claims refuted against source because Gemini never read the source

# Harness Change Contract: headless gemini keeps its file tools in the review clone

## Component

`scripts/pr-watch/pr-watch.sh` and `scripts/pr-watch/smoke-test.sh`: `GEMINI_CLI_TRUST_WORKSPACE=1` becomes `=true`.

## Failure mode targeted

The bot's Gemini segments judge diffs blind. Probe on 2026-11-16 in an untrusted directory: with `GEMINI_CLI_TRUST_WORKSPACE=1` the CLI prints `Approval mode overridden to "default" because the current folder is not trusted` and returns no answer; with `=true` the same `--yolo -p` call answers. The pr-review clone is always untrusted, so Gemini ran without the tools that read source. 26/50 of the last 50 pr-watch digests record a Gemini claim refuted against source.

## Predicted improvement

Refuted-Gemini digests fall from 26/50 (about 10 per 20) to at most 5 of the next 20. The Argon contract changes the model in the same window, so this measures both together; on a miss, check the segment output for tool calls before attributing it.

## Invariants preserved

- The trust value applies to the throwaway clone the review runs in; no new directory is trusted persistently.
- Segment prompts stay review-only; no new credential is exported.

## Falsification

Revert if a Gemini segment is observed writing outside the clone or running a cloud CLI it could not run before, or if more than 8 of the next 20 digests still record a refuted Gemini claim with tool calls confirmed running.

## Rollback

`git revert <commit>`. Affects: scripts/pr-watch/pr-watch.sh, scripts/pr-watch/smoke-test.sh.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
