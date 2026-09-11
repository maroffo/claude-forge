# ABOUTME: Change contract for adding .jsonl/.ndjson to the commit-intent-guard stub-scan exclusions
# ABOUTME: Data files carry TODO strings as content, not as unfinished work

# Harness Change Contract: exclude line-delimited JSON from the stub scan

## Component

`hooks/commit-intent-guard.py`, constant `STUB_SCAN_SKIP_SUFFIXES`.

```diff
-STUB_SCAN_SKIP_SUFFIXES = (".md", ".txt", ".rst", ".adoc")
+STUB_SCAN_SKIP_SUFFIXES = (".md", ".txt", ".rst", ".adoc", ".jsonl", ".ndjson")
```

## Failure mode targeted

The guard blocks a commit of a **data file** because a TODO marker appears inside the data as content rather than as an unfinished-work marker in code.

Observed 2026-09-11 committing `poc_training_material/` to hikma-mirsad: a captured customer red-team prompt contains a source-code snippet with a `TODO` comment, and the guard refused the commit with "Diff introduces unfinished work". Nothing in the diff was unfinished; the string was the payload of an attack prompt in a corpus.

The constant's own comment already states the intent this change completes: "Files where TODO etc. can legitimately appear as documentation or data, not stubs". Prose formats were enumerated; line-delimited JSON, the standard format for prompt corpora and evaluation sets in this workspace, was not.

## Predicted improvement

Commits of `.jsonl`/`.ndjson` corpora and evaluation sets stop being blocked on their contents. Expected frequency is low but rising: `hikma-classifiers` stores every split and test set as JSONL per its `DATA_CONVENTIONS.md`, and hikma-mirsad now carries `poc_training_material/`. Prior to this change the only compliant options were to rename the data into an excluded path, which games the guard, or to bypass with `--no-verify`, which is forbidden.

Qualitative, sample size 1 so far. Success is measured by the guard firing zero times on data-only commits over the next 10-20 sessions while continuing to fire on code.

## Invariants preserved

- The guard still scans every code extension it scanned before. No `.py`, `.go`, `.ts`, `.tsx`, `.sh`, `.yaml`, `.toml` file is newly excluded.
- The exclusion is by suffix only. A `.jsonl` file is data by format; this does not weaken the `/docs/`, `/examples/`, `/fixtures/`, `/testdata/` path exclusions or add new ones.
- Every other check in the hook is untouched: the change is one tuple entry.

## Falsification

A real stub or unfinished implementation ships inside a `.jsonl` or `.ndjson` file and reaches a commit because the guard no longer looks there.

This would require executable or configuration logic to live in a line-delimited JSON file that the project treats as source. If that pattern appears, the suffix exclusion is too coarse and the correct fix is a path-based exclusion for data directories instead. Revert and re-approach.

Weaker signal, also worth watching: someone renames a source file to `.jsonl` to get past the guard. That is misuse rather than a flaw in the change, but if it happens the exclusion should become path-based.

## Rollback

Remove `".jsonl", ".ndjson"` from `STUB_SCAN_SKIP_SUFFIXES` in `hooks/commit-intent-guard.py`.
