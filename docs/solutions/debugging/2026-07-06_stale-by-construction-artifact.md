# ABOUTME: When a generated artifact keeps sprouting lifecycle bugs, question whether it needs storing at all
# ABOUTME: On-demand generation + inline return deletes cache/collision/staleness bug classes by construction

# Problem

A generated/derived artifact (cache, map, index, report) is meant to help, but keeps sprouting
bugs around its lifecycle: it goes stale, two writers collide, a freshness check fights a
regenerator, the stored copy disagrees with reality. Line-level review of each component passes,
yet the whole thing misbehaves. Symptom shape: you are adding machinery (stamps, hooks, caches,
advisories) to keep a stored copy fresh, and the machinery itself is where the bugs are.

# Solution

Ask whether the artifact needs to be *stored* at all before adding more freshness machinery.

1. **Is it fresh by construction, or fresh only at a moment nobody reads it?** A committed/generated
   file stamped at commit-time is stale for the whole editing session, i.e. exactly when it is
   read. If freshness matters, generate at *read* time, not at write/commit time.
2. **Can you delete the storage?** Generating on demand and returning the result inline (`--print`
   to stdout, an in-memory return) removes the persisted file, and with it the collision,
   atomic-write, and cache-staleness bug classes *by construction*. The cheapest fix for a class of
   storage bugs is to stop storing.
3. **Split awareness from delivery.** If the concern is "the consumer won't know the artifact
   exists," a tiny always-fresh nudge/pointer (awareness) plus on-demand generation (delivery) beats
   a heavy always-generated payload.
4. **Two independent hooks/jobs touching the same artifact** (one regenerates, one validates
   freshness) can fight into a permanent-dirty / crying-wolf steady state. Trace the interaction
   across a full cycle, not each in isolation.
5. **Reach for the design-level second opinion.** File reviewers check "is this code correct," not
   "does this design contradict a principle I hold." Emergent misbehavior lives in the seams
   between components; ask the architectural question explicitly.

# Why It Works

Most artifact-lifecycle bugs are the cost of *keeping a copy in sync with a source of truth*.
Remove the copy (generate on demand) and the sync problem, and its whole bug class, disappears.
When you genuinely need the copy (expensive to regenerate), make it fresh-by-construction relative
to the thing it claims about, and never let two jobs mutate it without tracing their interaction.

Seen live 2026-07-06 (claude-forge codemap): a committed, commit-stamped map + regen hook +
freshness advisory took three review rounds and collapsed to a single on-demand `codemap --print`
CLI + a cheap awareness nudge, deleting the cache, the file, and every storage bug at once.
