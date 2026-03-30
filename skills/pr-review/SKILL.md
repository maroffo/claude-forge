---
name: pr-review
description: "Commit-by-commit PR review with specialized agents, /gemini-review, and /second-opinion. Use when user says review PR, review pull request, analyze PR, or /pr-review. Not for pre-commit review (use gemini-review)."
compatibility: "Requires gh CLI, Gemini CLI (GEMINI_API_KEY), and project CLAUDE.md for conventions."
---

# ABOUTME: Commit-aware PR review that reads each commit's intent before judging code.
# ABOUTME: Orchestrates review agents, Gemini batches, and second-opinion rounds with quality gate scoring.

# PR Review - Commit-by-Commit

## Trigger

Activate when user says: "review PR", "review pull request", "analyze PR", "pr review", or `/pr-review`.

## Arguments

```
/pr-review <number|url>           Review a specific PR
/pr-review <number> --quick       Skip second-opinion rounds (faster, less thorough)
/pr-review <number> --no-gemini   Skip Gemini batches (offline mode)
```

## Why Commit-by-Commit

A monolithic diff loses context. Each commit carries intent via its message:
- A "fix(security):" commit means the author knew about the vuln
- A "deferred to phase N" note means incomplete code is intentional
- A fix commit after a feature commit means the issue was caught and addressed

Reviewing commit-by-commit:
1. Reduces false positives (distinguishes intent from oversight)
2. Reveals the development narrative (feature -> review -> fix cycles)
3. Identifies incomplete fixes (fix attempted but insufficient)
4. Catches regressions (later commit breaks what earlier commit built)

## Execution Flow

### Phase 0: Gather PR metadata

```bash
# PR metadata
gh pr view <N> --json title,body,state,baseRefName,headRefName,additions,deletions,changedFiles,commits,labels,author

# Changed files
gh pr diff <N> --name-only

# Full diff (save locally for agents)
gh pr diff <N> > /tmp/pr<N>-diff.patch

# Commit list (chronological)
gh pr view <N> --json commits --jq '.commits[] | "\(.oid) \(.messageHeadline)"'
```

**Scope assessment:**
- < 300 lines, < 5 files: simple, standard review
- 300-1000 lines, 5-15 files: moderate, commit-by-commit adds value
- > 1000 lines or > 15 files: large, commit-by-commit essential + flag scope concern
- > 5000 lines or > 50 files: excessive, recommend reject-and-split

### Phase 1: Build verification

Checkout PR branch and run the project's build/test gate:

```bash
git fetch origin <branch> && git checkout <branch>
make check    # or equivalent from CLAUDE.md
```

If build fails, determine if pre-existing (check base branch) or introduced by PR.

### Phase 2: Commit narrative analysis

Read each commit in chronological order (oldest first). For each commit, extract:

| Field | Source |
|-------|--------|
| Intent | Commit message (subject + body) |
| Scope | `--stat` (files changed, insertions, deletions) |
| Type | Conventional commit prefix: feat/fix/refactor/docs/chore/perf/test |
| Review response? | Does the message reference a prior review? ("address findings", "fix Gemini review") |

Build a **commit graph** tracking:
- `introduced_in[finding] = commit_sha` - which commit introduced a pattern
- `fixed_in[finding] = commit_sha` - which commit attempted to fix it
- `still_open[finding] = true` - fix was incomplete or never attempted

Key signals to watch:
- **fix after feat**: the author caught and addressed something (verify completeness)
- **"deferred to"/"phase N"/"TODO"**: intentional incompleteness (note, don't penalize as bug)
- **duplicate commit messages**: rebase artifact or amend residue (process smell)
- **"address review findings"**: cross-reference with the review it responds to
- **shellcheck disable / nolint**: conscious suppression (verify justification)

### Phase 3: Specialized review agents (parallel)

Launch review agents based on file patterns (max 3 parallel per orchestrator rules):

| Pattern | Agents |
|---------|--------|
| `*.go`, `*.py`, `*.ts`, `*.rb`, `*.kt`, `*.swift` | architecture-reviewer + security-reviewer |
| Hot paths, queries, caching | + performance-reviewer |
| `*_test.*`, `*_spec.*` | + test-reviewer |
| `go.mod`, `Gemfile`, `package.json`, `pyproject.toml` | dependency-reviewer |
| `migrations/`, `schema.rb`, `*.sql` | database-reviewer |
| `docs/`, `README*`, `ADR/`, `*.md` | dx-reviewer |
| K8s manifests, Dockerfiles, CI configs | cloud-infrastructure (if available) |

Each agent receives:
- The full diff (`/tmp/pr<N>-diff.patch`)
- The project's CLAUDE.md conventions
- Instruction to read actual source files (not hallucinate)
- Instruction to classify as Critical/Major/Minor with exact file:line

### Phase 4: Gemini code review (parallel with Phase 3)

Segment the diff by package/area to stay under Gemini's effective context:

```bash
# Segment by top-level package (target: < 3000 lines per segment)
git diff <base>...<head> -- <package_path> > /tmp/pr<N>-<segment>.diff
```

For each segment, invoke `/gemini-review` with:
- Project context (language, conventions from CLAUDE.md)
- Segment-specific focus areas
- The prompt from `~/.claude/skills/pr-review/prompts/gemini-segment.md`

**Known Gemini hallucination patterns to filter:**
- Language feature availability (e.g., flagging Go 1.25+ features as errors)
- Database engine limitations (e.g., attributing MySQL limits to PostgreSQL)
- Standard library API existence (verify against actual Go/language version)

Cross-validate every Gemini CRITICAL against source code before accepting.

### Phase 5: Second opinion - plan adherence (round 1)

After Phases 2-4 complete, invoke `/second-opinion` with:

```
CONTEXT:
- The review plan (which agents ran, what areas covered)
- Consolidated findings so far (CRITICAL/MAJOR/MINOR counts by domain)
- Specific questions:
  1. Are we respecting the review plan? Missing any areas?
  2. Any blind spots for a PR of this scope?
  3. Which findings overlap and how to deduplicate?
  4. Any findings that smell like hallucinations needing source verification?
```

Act on Gemini's feedback: verify contested findings, investigate blind spots.

### Phase 6: Commit-context reclassification

Cross-reference Phase 3-4 findings with Phase 2 commit narrative:

For each finding, ask:
1. **Which commit introduced it?** (git log -S or blame)
2. **Was there a fix commit?** (search for "fix" commits touching the same file)
3. **Is the fix complete?** (read the fix diff)
4. **Was it intentional?** (commit message says "deferred", "TODO", "phase N")

Reclassification rules:

| Commit context | Effect on severity |
|----------------|-------------------|
| Bug with no fix attempt | Keep severity |
| Fix attempted but incomplete | Keep severity, note partial fix in description |
| Intentional deferral with TODO | Downgrade 1 level if tracked, keep if untracked |
| Intentional design choice with justification | Downgrade 1 level, note rationale |
| Pre-existing on base branch (not introduced by PR) | Note as pre-existing, still must fix per green-pipeline rule |
| Conscious suppression (nolint/shellcheck disable) with valid reason | Downgrade to MINOR |
| Conscious suppression without justification | Keep severity |

### Phase 7: Consolidation and scoring

**Deduplication**: when multiple reviewers find the same issue, keep one entry with cross-references: `[Security/Architecture]`.

**Presentation order**: by severity (CRITICAL first), then by component within severity bands. Not by domain.

**Scoring** (per quality-gates rules):

| Category | Rule |
|----------|------|
| CRITICAL | Auto-fail (score = 0). Must fix before merge. |
| MAJOR | -10 each. Start at 100. |
| MINOR | -3 each. |
| Threshold: commit | >= 80 |
| Threshold: PR merge | >= 90 |
| Threshold: excellence | >= 95 |

### Phase 8: Second opinion - final validation (round 2)

Invoke `/second-opinion` with the complete consolidated report:

```
CONTEXT:
- Full findings list with severity and commit context
- Scoring calculation
- Specific questions:
  1. Is the severity classification fair and accurate?
  2. Any findings misclassified (too harsh or too lenient)?
  3. Is the scoring methodology correct?
  4. Are we missing anything obvious?
```

Synthesize: adjust classifications based on Gemini's challenges.

### Phase 9: Present report

Structure:

```markdown
# PR Review: <title>

**Branch**: <head> -> <base>
**Scope**: <additions> additions, <deletions> deletions, <files> files, <commits> commits
**Score**: <N> (<gate status>)
**Reviewers**: <list of agents + Gemini batches + second-opinion rounds>
**Hallucinations caught**: <count> (<brief description>)

## Commit Narrative
<Brief story: how the PR evolved, review-fix cycles, intentional deferrals>

## CRITICAL (auto-fail)
<Table: #, Finding, File:Line, Introduced in, Fix attempted?, Source>

## MAJOR
<Table: #, Finding, File:Line, Commit context, Source>

## MINOR
<Summary count + notable items>

## Reclassifications (commit context)
<Table: Finding, Original severity, New severity, Reason>

## Dependencies
<CVE count, new deps, license status>

## Process Observations
<Scope concern if applicable, commit hygiene, review-fix pattern quality>

## Recommendation
<APPROVE / FIX BEFORE MERGE / REJECT AND SPLIT>
<If split: proposed PR breakdown>
```

## Quality Notes

- **Never relay raw agent output**: synthesize, deduplicate, verify
- **Every CRITICAL must be source-verified**: read the actual file:line before reporting
- **Gemini hallucinations are common**: cross-validate language features, DB engine capabilities
- **Commit context changes severity**: a conscious deferral is not the same as a bug
- **Pre-existing issues**: still block (green pipeline is everyone's responsibility) but don't penalize the PR author's score
- **Large PRs (> 50 files)**: always recommend reject-and-split, even if code quality is high

## Troubleshooting

| Issue | Solution |
|-------|----------|
| PR too large for Gemini | Segment by package, < 3000 lines per segment |
| Agent returns hallucinated findings | Verify against source; check language version, DB engine |
| Build fails on base branch too | Note as pre-existing; still blocks merge |
| Too many findings to present | Group MINOR as count; focus report on CRITICAL + MAJOR |
| Commit messages are useless ("fix", "wip") | Fall back to diff-only review; note poor commit hygiene |
