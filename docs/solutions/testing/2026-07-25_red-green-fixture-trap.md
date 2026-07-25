# ABOUTME: A red-green proof where the red is an ImportError proves nothing; rebuild old behaviour in new structure
# ABOUTME: 1 collection error looked like a passing proof; the real red was 5 of 12 assertions failing for their reasons

# Problem

New tests were written for a checker whose bugs had just been fixed. To prove they were meaningful, the obvious move is to run them against the old implementation:

```sh
git stash push scripts/check_skills.py       # restore the buggy version
uv run --no-project python3 -m unittest discover -s scripts
```

```
ImportError: cannot import name 'check_all' from 'check_skills'
Ran 1 test in 0.000s
FAILED (errors=1)
```

That is a failing run, and it demonstrates nothing. The fix had restructured the module (a global `FAILURES` list became a `check_all(root)` return value) so the tests could run against a temp directory at all. Reverting the file reverted the structure too, so collection died before a single assertion executed. Every one of the twelve tests was equally "red", including tests for behaviour the old code got right.

The same trap applies to any red-green where the fix touched signatures, imports, fixtures or configuration: the harness fails, and the failure is indistinguishable from the bug being demonstrated.

# Solution

Reconstruct the old *behaviour* inside the new *structure*, then run. Patch back only the specific defects, keeping everything the tests need to load:

```python
src = pathlib.Path("scripts/check_skills.py").read_text()
src = src.replace('root.glob("**/SKILL.md")', 'root.glob("*/SKILL.md")')     # depth bug
src = src.replace(                                                            # one-line ABOUTME
    '        head = text.splitlines()[:2]\n'
    '        if len(head) < 2 or not all(line.startswith("# ABOUTME:") for line in head):',
    '        if not text.startswith("# ABOUTME:"):')
src = re.sub(r'    elif len\(desc\) < MIN_DESC:\n.*?\n    elif len\(desc\) > MAX_DESC:\n.*?\n',
             '', src, flags=re.S)                                             # no length bounds
(sandbox/"check_skills.py").write_text(src)
```

Run the unmodified test file against that, in a scratch directory:

```
FAIL: test_description_too_long_fails
FAIL: test_description_too_short_fails
FAIL: test_nested_skill_is_counted
FAIL: test_nested_skill_without_frontmatter_fails
FAIL: test_reference_with_one_aboutme_line_fails
Ran 12 tests
FAILED (failures=5)
```

Five failures, `failures` not `errors`, each naming the defect it was written for. The other seven pass both before and after: they guard checks that already worked, so a later refactor cannot silently drop them. That asymmetry is itself information, and a run where all twelve go red would have been the signal that the harness broke rather than the code.

# Why It Works

A red-green pair is an argument with two premises: the test fails on the broken code, and it fails *for the claimed reason*. An import or collection error satisfies the first and destroys the second, which is why `references/evidence.md` requires reading the failure output rather than the exit code. Separating "revert the behaviour" from "revert the file" keeps the test harness constant across the comparison, so the only variable left is the defect.

Cheap tell: if reverting produces `errors` rather than `failures`, or if the count of red tests equals the count of all tests, the proof has not run yet.
