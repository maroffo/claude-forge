---
name: freeze
description: "Restrict edits to one directory of the current repo for the rest of the session, so focused debugging cannot spill into unrelated files. Use when user says /freeze, freeze the boundary, freeze this dir, keep edits inside <dir>, unfreeze, or /freeze off. Writes a repo-local boundary file that the freeze-guard PreToolUse hook reads. Not a security boundary and not a scope mechanism for parallel subagents."
allowed-tools: [Bash, Read]
---

# ABOUTME: /freeze sets, shows and lifts the repo-local edit boundary read by hooks/freeze-guard.sh
# ABOUTME: Focus aid for long debugging sessions, deliberately not a security boundary

# /freeze

Keep Edit, Write and NotebookEdit inside one directory of the current repo. The boundary is a
single file, `.freeze-boundary`, at the git root, holding one absolute physical directory path.
`hooks/freeze-guard.sh` reads it on every mutating tool call and denies paths outside it.

## What this is not

- **Not a security boundary.** `Bash` is not gated: `sed -i`, `cat >`, `git checkout` and any
  other shell write go straight through. gstack, where this idea comes from, says the same thing
  about its own version. Treat it as a focus aid that makes an out-of-scope edit loud, not as
  containment.
- **Not per-agent.** The boundary is session-wide and repo-local. Parallel subagents share the
  process and therefore the boundary; it does **not** give each of them its own scope.
- **Not persistent policy.** Nothing re-applies it. A new session starts unfrozen unless the
  file survived on disk, which it will: `/freeze off` is a deliberate step, not an automatic one.

## Commands

### `/freeze <dir>`

1. Resolve the repo root and the target, both physical (`pwd -P`, so a symlinked checkout and the
   hook agree on one spelling):

   ```bash
   root=$(git rev-parse --show-toplevel) && root=$(cd "$root" && pwd -P)
   dir=$(cd "<dir>" && pwd -P)
   ```

   If either `cd` fails, stop and say why: an unresolvable path would write a boundary that denies
   everything.

2. Refuse a target outside the repo. A boundary the repo cannot contain freezes the whole repo
   while enforcing nothing elsewhere (the guard is repo-local by design):

   ```bash
   case "$dir/" in "$root"/*) ;; *) echo "refusing: $dir is outside $root"; exit 1 ;; esac
   ```

3. Write the boundary, with the trailing slash the guard's prefix match expects:

   ```bash
   printf '%s/\n' "${dir%/}" > "$root/.freeze-boundary"
   ```

4. Gitignore guard, exactly once (same idiom the orchestrator uses for `quality_reports/reviews/`:
   check first, append if absent, never rewrite the file):

   ```bash
   gi="$root/.gitignore"
   if ! grep -qxF '/.freeze-boundary' "$gi" 2>/dev/null; then
     nl=""
     # Command substitution strips trailing newlines, so a non-empty result means the
     # file does not end in one and the append would glue onto the last line, silently
     # corrupting an existing ignore rule in someone else's repo.
     [ -s "$gi" ] && [ -n "$(tail -c 1 "$gi")" ] && nl=$'\n'
     printf '%s/.freeze-boundary\n' "$nl" >> "$gi"
   fi
   ```

   The entry is anchored (`/.freeze-boundary`) because the file only ever lives at the root.

5. Report the boundary and the escape hatch in one line: `frozen: <dir> (lift with /freeze off)`.

### `/freeze status`

```bash
root=$(git rev-parse --show-toplevel 2>/dev/null) && cat "$root/.freeze-boundary" 2>/dev/null
```

Print the boundary path, or `no boundary set` when the file is absent or empty. Do not create it.

### `/freeze off`

```bash
root=$(git rev-parse --show-toplevel) && rm -f "$root/.freeze-boundary"
```

Report `boundary lifted`. Leave the `.gitignore` line alone: it is inert when the file is gone,
and removing it would just churn the diff on the next freeze.

## How the guard behaves

Read `hooks/freeze-guard.sh` before changing anything here; the two must stay in step, and
`hooks/tests/test_hook_constants_sync.py` asserts the basename quoted above matches
`FREEZE_BOUNDARY_BASENAME` in `hooks/_freeze_boundary.sh`.

| Situation | Guard |
|-----------|-------|
| No boundary file at the edited file's git root | allows, zero output |
| Edit inside the boundary | allows |
| Edit outside the boundary, same repo | denies, message names the boundary and `/freeze off` |
| Edit in a different repo | allows (the boundary is repo-local) |
| Edited path (`file_path`, or `notebook_path` for NotebookEdit) missing, empty or newline-bearing | allows, one-line stderr warning |
| Boundary file empty or whitespace-only | allows, one-line stderr warning |
| `jq` not installed | allows, one-line stderr warning |

Every failure path allows. A false deny would block every edit in the repo until someone notices
and lifts the boundary; a false allow shows up in the diff.

## When to use

- Long debugging sessions where the fix is known to live under one directory.
- Handing a scoped subtask to yourself after a `LOCALIZE` step: the file list is already decided.

## When NOT to use

- Anything that must be enforced rather than nudged. Use `permissions.deny` in settings for that.
- Multi-directory work. One boundary, one directory: freezing the repo root is a no-op.
