# ABOUTME: Change contract for the software-engineer-pi driver agent (registry-discoverable executor routing)
# ABOUTME: Targets the silent-native-fallback failure observed in the wishew #3027 pilot session

# Harness Change Contract: software-engineer-pi driver agent

## Component

- `agents/software-engineer-pi/AGENT.md` (new agent definition)
- `rules/orchestrator-protocol.md` (one bullet added to "Executor selection": agent is the preferred invocation in delegated prompts)

## Failure mode targeted

Executor routing carried only in prose gets ignored: the wishew #3027 implementing session (2026-07-22, pilot datapoint 2) searched for a "pi-exec" skill, found none, concluded the executor did not exist, and silently fell back to native implementation despite the prompt carrying the absolute wrapper path. Conclude-from-absence plus silent fallback.

## Predicted improvement

Zero undeclared native implementations of pi-designated subtasks across pilot datapoints 3-5 (delegated sessions launch `software-engineer-pi` from the agent registry instead of interpreting prose). Secondary: driver overhead stays small (haiku, effort low; the brief passes through once).

## Invariants preserved

- The driver never edits repository files, never runs build/test/package commands, never uses mutating git: all repository changes still come from pi, all verification and commits stay with the orchestrator.
- Decision 12 unchanged: the ORCHESTRATOR emits the literal `EXECUTOR:` transcript line; the driver's report line is the carrier it relays.
- DRIFT remains mandatory for pi-executed subtasks; review and spec roles remain native.
- No `--no-verify` paths added.

## Falsification

In datapoints 3-5: a session with this agent available still implements a pi-designated subtask natively without declaring it, OR the driver agent is observed editing repository files or running verification commands itself. Either observation: revert.

## Rollback

`git revert <commit>`. Affects: agents/software-engineer-pi/AGENT.md, rules/orchestrator-protocol.md.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| 2026-07-27 | 4 driver runs in a single session (2026-07-25), against a datapoints 3-5 window | the component was amended 3 days after merge by 2026-07-25_pi-driver-silent-completion.md, which added the step 5 report-delivery rule and the symlink anomaly check to the same AGENT.md, and its rule bullet moved into skills/orchestrator/SKILL.md; on the original prediction the registry route did work, the driver was launched as an agent rather than searched for as prose and no undeclared native implementation recurred, but 3 of the 4 runs delivered no report at all, which is the failure the superseding contract targets | modified |
