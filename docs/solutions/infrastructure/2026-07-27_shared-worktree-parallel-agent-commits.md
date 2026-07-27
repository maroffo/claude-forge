# ABOUTME: Why parallel subagents sharing one git worktree must never commit, and the serialization that fixes it
# ABOUTME: From the gstack-borrowings run (PR #109), plan decision 14

# Problem

Multiple subagents implementing disjoint workstreams in the SAME git worktree, each instructed to commit its own work. The git index is per-worktree, not per-process: `git commit` snapshots whatever is staged, so agent B's commit silently sweeps in agent A's freshly staged files. With a pre-commit gate that runs the full test suite, a concurrent commit can also fire the gate against a sibling's half-edited tree.

# Solution

Subagents get a hard "no `git add`, no `git commit`, no stash/checkout/switch" rule in their briefs; they only edit files in their declared scope. The orchestrator is the sole committer: after a wave of parallel agents completes, it verifies the combined tree (`make check && make test-e2e`), then commits one workstream at a time by explicit pathspec, with a `git branch --show-current` guard in the same Bash call as each commit.

```
[ "$(git branch --show-current)" = "feat/x" ] || { echo WRONG BRANCH; exit 1; }
git add <explicit paths for workstream N only>
git commit -m "..."
```

# Why It Works

Serializing commits through one process removes the index race entirely, and committing only after the wave completes means the pre-commit gate always runs against a stable, fully-integrated tree. Side benefit: every commit is contract-paired and gate-green by construction. The alternative (worktree-per-agent) buys real isolation but costs merge integration; for disjoint file scopes, sole-committer is cheaper and sufficient.
