# ABOUTME: Full 8-properties x 5-bands scoring rubric for Farley test-quality assessment
# ABOUTME: Reference for the test-design-reviewer skill; anchor each property score to these bands

# Per-Property Scoring Bands

Anchor each of Farley's 8 properties to these bands when assigning the 0-10 LLM score. Properties: Understandable (U), Maintainable (M), Repeatable (R), Atomic (A), Necessary (N), Granular (G), Fast (F), First/TDD (T).

| Property | 9-10 | 7-8 | 5-6 | 3-4 | 1-2 |
|----------|-------|------|------|------|------|
| U | Reads like specs; behavior clear without reading impl | Clear with minor ambiguities | Requires code inspection to understand | Cryptic; relies on impl details | test1/test2; magic numbers throughout |
| M | Proper abstractions; verifies behavior not impl | Good separation; occasional brittleness | Some impl coupling; some over-specified mocks | Tightly coupled; verify with exact counts | Reflection for private fields; mirrors impl exactly |
| R | Fully deterministic; no external deps | Rarely flaky; minimal env deps | Occasional flakiness; timing deps | Filesystem, timing, env deps present | sleep, file I/O, network, system time, unseeded random |
| A | Fully isolated; no shared state; parallelizable | Mostly isolated; minor shared setup | Some shared state; order sometimes matters | Heavy interdeps; must run in order | Shared mutable statics; ordering annotations |
| N | Every test adds unique value; parameterized for variations | Most tests valuable; minor redundancy | Checkbox exercises; moderate redundancy | Redundant tests; framework testing; mock tautologies | assertTrue(true); disabled tests; tests verify only mocks |
| G | Each test verifies single outcome; pinpoints issues | Focused; occasional logical assertion groups | Multiple behaviors; failure diagnosis takes effort | Sprawling; multiple unrelated assertions | 20+ assertions; testEverything() methods |
| F | Pure computation; no I/O; milliseconds | Quick; minor optimization opportunities | Some slow tests; noticeable suite time | File I/O or database calls | sleep, network calls, heavy setup/teardown |
| T | Clear test-first evidence; tests drive design | Likely test-first; good design influence | Unclear; tests may be afterthoughts | Mirrors impl; likely test-after; mock-heavy | Clearly written after code; coverage patches |
