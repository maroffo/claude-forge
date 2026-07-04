# ABOUTME: Full audit of all skills and hooks (4 parallel reviewers, 2026-07-04), findings verified and ranked
# ABOUTME: Source reports: hooks, language skills, workflow/review skills, personal/content skills

# Skill & Hook Audit, 2026-07-04

Four parallel read-only auditors covered hooks/ (+settings), 13 language/tech skills, 20 workflow/review/meta skills, 16 personal/content skills + underscore shared files. Key claims re-verified in the main session before ranking. Always-loaded surface: 592 lines (rules 478 + CLAUDE.md.example 114). Total SKILL.md surface: 5,835 lines.

## Verified silent breakages (fix first, all small)

1. **`git -C <path> commit` bypasses ALL four commit gates** (pre-commit-gate, main-branch-guard, commit-intent-guard, gitignore-anchor-lint). Trigger regex `(^|[;&|\s])git\s+commit(\s|$)` does not match `-C` form; verified NO-MATCH. `_commit_target.sh` even parses `git -C`, but that code is dead because the gates never fire. Fix: extend the shared trigger regex in all four gates + regression test.
2. **ABOUTME-above-frontmatter steals the registry description in 4 skills**: legacy-code-expert, cognitive-load-analyzer, harness-trace, harness-mechanic. The registry publishes the ABOUTME line instead of the authored `description:` with the trigger phrases (confirmed against the live session skill list). Fix: move ABOUTME below the closing `---`.
3. **autoresearch-prompt is unroutable**: frontmatter has no `description:` (uses non-standard `triggers:`/`version:`); absent from the runtime registry. newsletter-digest step 2 depends on it. Fix frontmatter or retire.
4. **linkedin-post has no frontmatter at all** (starts with `# ABOUTME`): cannot trigger, also not deployed.
5. **email-cleanup archive command is broken**: `--remove-labels=INBOX` (SKILL.md:44) vs canonical `--remove=INBOX` (_GMAIL.md:15, inbox-triage formatter). Verified mismatch. Fix flag; reference _GMAIL.md instead of inlining (that inlining is how the drift happened).
6. **Missing `jq` silently disables the safety gates** (fail-open on main-branch-guard and pre-commit-gate). Fix: fail-closed `command -v jq || deny` on the two safety gates.
7. **`--no-verify` is FORBIDDEN in CLAUDE.md but nothing enforces it.** Fix: small PreToolUse deny on `--no-verify|--no-hooks|--no-pre-commit-hook`.
8. **swiftui-liquid-glass teaches an apparently fabricated API** (`intensity:`, `GlassEffectStyle.adaptive`, `interactive:` label do not match shipped iOS 26 `glassEffect`), and **ios-debugger's `simctl io tap/type/swipe` subcommands don't exist**. Verify against Apple docs and rewrite, or quarantine with a warning.

## Structural findings (decisions needed)

9. **Repo and deployed skill trees have diverged** (`~/.claude/skills` is a copy, verified not a symlink). Deployed-only: mauro-blogger (unversioned!), advanced-review. Repo-only (not deployed): linkedin-post, pr-review, autoresearch-prompt. Single highest-leverage fix: one source of truth (symlink per README Option 2, or an install-step sync), then commit mauro-blogger into the repo.
10. **Three overlapping heavyweight review paths with no selection rule**: orchestrator Step 3 fleet, pr-review (which re-runs that fleet, plus gemini-review, plus second-opinion TWICE = 6 Docker launches), advanced-review (3 LLMs + Semgrep + SonarQube). Fix: define three explicit tiers (gemini-review = fast pre-commit; orchestrator agents = in-loop; advanced-review = deep isolated) and rewrite pr-review to compose instead of duplicate.
11. **advanced-review severities (CRITICAL/WARNING/INFO) don't map to quality-gates (Critical/Major/Minor)**, so `/score`'s instruction to deduct from its findings cannot execute. Define the mapping once in rules; skills reference it (pr-review currently re-inlines and has already drifted from both).
12. **Frontmatter tool-key inconsistency**: 8 content skills use `tools:` (the subagent field, silently ignored for skills → they run with full tool access); others use `allowed-tools:`; the acp-namespaced `allowed-tools` in gemini-review/source-control breaks if the acp provider isn't active. Standardize.

## Efficiency findings

13. **pre-commit-gate runs full `make check && make test-e2e` on every commit** including docs-only (auditor measured: uv startup is NOT the bottleneck at ~15-20ms warm; the e2e run is). Fix: source-gate, skip e2e when `git diff --cached --name-only` has no source files.
14. **~30 lines of identical Version + Pre-Commit boilerplate in 7 language skills** (golang, python, rails, ruby, react-nextjs, android-kotlin, apple-swift), largely restating the always-loaded verification rule and the gate hook. Collapse to per-language command lists + 2 lines of prose.
15. **Oversized SKILL.md without progressive disclosure**: blog-writer 333 (style guide + humanizer/cover-image re-inlined), adr 269 (stale `Claude Opus 4.6` co-author string), cognitive-load-analyzer 206 (formula math belongs in references; calculator is source of truth), android-kotlin 184 (inlines code already in its refs), pr-review 299 (duplicated rule tables).
16. **Three uv processes per Edit on the doom branch** (aboutme + routing + doom). Candidate: one dispatcher process. Also: routing-advisor never GCs its state files (45 stale found; doom-loop-detector has sweep_stale, port it), duplicated exempt-path lists across hooks.
17. **Zero tests for the five main-branch hooks** (commit-intent-guard, gitignore-anchor-lint, aboutme-enforcer, routing-advisor, session-end-trace); only the two in-flight hooks ship tests. Add table-driven tests in hooks/tests/.

## Minor hygiene

- _INDEX.md stale (missing linkedin-post, mauro-blogger).
- Stale literals: blog-writer `Blog Discovery - 2026-03.md`, process-email-bookmarks raw label ID, ruby 3.3/3.4 pins, apple-swift/ios-debugger iPhone 16 hardcoded, adr `Opus 4.6`, linkedin-post `LinkedIn-Version: 202602`.
- test-design-reviewer uses bare `python` (rule says `uv run python3`).
- main-branch-guard misses detached HEAD; gitignore-anchor-lint unquoted paths under shell=True; routing-advisor `**` crude substring match.
- commit-intent-guard false-positives on legitimate `NotImplementedError` (abstract methods, tests asserting the raise).
- session-end-trace hardcodes Max's path (silent no-op for other installers).
- terraform vs cloud-infrastructure boundary implicit; second-opinion "ask gemini" vs gemini-review trigger ambiguity; CLAUDE.md.example table omits advanced-review/score/project-checks and mislabels second-opinion as Gemini-only.
- skill-forge's own rules (<150 lines, frontmatter-first) violated by several skills: extend `skill-forge review all` to lint missing description, inverted ABOUTME, tool-key mismatch, so the doc-gardening scan catches these classes mechanically.

## Suggested batches

- **A. Silent breakages** (items 1-8): small, each restores something that is broken today.
- **B. One skill tree** (item 9): symlink + commit mauro-blogger; unblocks 3 undeployed skills.
- **C. Hook efficiency + coverage** (items 13, 16, 17 + minor hook hygiene): source-gated e2e, GC, tests for main hooks.
- **D. Review topology + skill trims** (items 10-12, 14-15): tier definition, severity mapping, boilerplate extraction, oversize restructuring.

Each accepted batch item that touches a trigger surface gets its own change contract per rules/harness-changes.md.
