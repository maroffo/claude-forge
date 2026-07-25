# ABOUTME: Common issues and solutions for trace extraction and harness-trace tools
# ABOUTME: Read when trace extraction outputs null values, misses entries, or runs slowly

## Common Issues

| Issue | Solution |
|-------|----------|
| VERIFY outcomes all `null` | Session predates outcome capture, or results truncated: re-extract from the raw session JSONL with the current extractor |
| REVIEW findings `{}` despite a visible report | Async-launched reviewer (metadata-only tool_result): the report never passed through the Agent result; expected, not a bug |
| No SCORE entries | Step 6 must report `SCORE: <n>/100` literally (rules/orchestrator-protocol.md, Score Reporting) |
| No LOCALIZE/REPRODUCE/DRIFT_CHECK/BLAST_RADIUS entries | Session predates the 2026-07-15 report-line mandate, or the lines were not literal (rules/orchestrator-protocol.md, Sub-step report lines + Blast Radius); ast-grep usage alone never emits BLAST_RADIUS |
| Extraction slow or hangs | Session over ~500 MB or malformed JSONL: check file size, extractor scans bounded windows of tool output by design |
