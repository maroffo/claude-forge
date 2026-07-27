# ABOUTME: A green hook test suite certified a no-op enforcement surface because its payloads were fabricated
# ABOUTME: From the gstack-borrowings review (PR #109, the run's only Critical finding)

# Problem

A PreToolUse hook was registered and documented on NotebookEdit, and its test suite had a passing NotebookEdit case. But the test built every payload with the Edit shape (`tool_input.file_path`), while real NotebookEdit payloads carry `notebook_path` (plus `cell_id`, `new_source`) and no `file_path` at all. The hook read only `file_path`, so in production every notebook edit fell into the fail-open branch: the enforcement was a silent no-op, certified green by a payload the tool never sends.

# Solution

Two halves, both required:

1. Hook reads the union of real target keys: `jq -r '.tool_input.file_path // .tool_input.notebook_path // empty'` (precedent already existed in sibling hooks: `inp.get("file_path") or inp.get("notebook_path")`).
2. Tests build payloads per-tool from the real tool schema, via a `tool_payload(tool, target)` helper, never by reusing the nearest fixture. The NotebookEdit case sends `{"notebook_path": ..., "cell_id": "c1", "new_source": "x"}` and asserts deny/allow across the boundary.

Detection heuristic for reviews: a test that loops over tool names while feeding an identical input shape is one test wearing N labels; check each tool's actual `tool_input` schema.

# Why It Works

A hook's contract is with the tool's wire format, not with the test's convenience. Building payloads from the real schema makes the test fail the moment the hook and the format disagree, which is the only failure that matters for an enforcement surface. A fabricated payload is worse than a missing test: it converts an uncovered path into a certified one.
