---
name: knowledge-sync
description: "Sync vault knowledge patterns to skills. Scans Second Brain for strong signals, proposes skill updates. Use when user says knowledge sync, sync skills, update skills from vault, or promote patterns."
compatibility: "Requires Obsidian CLI (obsidian MCP commands)."
---

# ABOUTME: Vault-to-skills sync, promotes recurring patterns from Second Brain to skill files
# ABOUTME: Scan/filter/group/propose/approve/apply cycle with signal strength tracking

# Knowledge Sync

Promotes recurring patterns from vault Second Brain notes into skill files. The APPLY step runs on human approval only, never autonomously. The scan-and-propose phase MAY run on a schedule (see Scheduled Mode).

## Signal Strength

| Signal | Criteria | Action |
|--------|----------|--------|
| weak | 1 project or 1 source | Track, don't propose |
| strong | 3+ projects OR 2+ independent sources | Propose to human |
| applied | Already synced to skill | Skip |

## Annotation Schema

Second Brain notes use a `## Skill Candidates` table:

```markdown
## Skill Candidates
<!-- Updated by learning-docs during retrospectives -->

| Pattern | Target Skill | Seen In | First Seen | Signal |
|---------|-------------|---------|------------|--------|
| Go error wrapping with %w | golang | feed-brain, bbp | 2026-01-15 | weak |
| Token bucket rate limiting | cloud-infrastructure | feed-brain, nur, clawdbot | 2026-01-10 | strong |
```

Table-based: easy to append via CLI, readable in Obsidian, parseable by Claude.

## Process

1. **SCAN**: `obsidian search query="## Skill Candidates" path="Second Brain" matches`
2. **FILTER**: only `strong` signals; skip rows where signal = `applied` or pattern already exists in target skill
3. **GROUP**: candidates by target skill with vault source citations
4. **PROPOSE**: draft exact text to add to each skill file (show diff-style)
5. **APPROVE**: human gate (always RED in decision framework)
6. **APPLY**: edit skill file + add backlink + update signal

## Apply Step Details

After human approval for each candidate:

1. Edit target skill file with the proposed addition
2. Add source backlink as HTML comment: `<!-- vault: [[Second Brain - Development#Pattern Name]] -->`
3. Update the Skill Candidates table: change signal from `strong` to `applied`

```bash
# Example: update signal in vault
obsidian read file="Second Brain - Development"
# Find the row, replace "strong" with "applied" in the table
obsidian append file="Second Brain - Development" content="..."
```

## Presentation Format

```markdown
## Knowledge Sync Report

### Candidates Found: N strong, M weak (skipped)

#### golang (2 candidates)

**1. Go error wrapping with %w**
- Source: [[Second Brain - Development#Go Error Handling]]
- Seen in: feed-brain, bbp
- Proposed addition to `skills/golang/SKILL.md`:
  ```
  [exact text to add]
  ```
- [ ] Approve  [ ] Skip  [ ] Modify

#### cloud-infrastructure (1 candidate)
...
```

## Scheduled Mode (propose-only)

The scan half of this skill may run unattended; the APPLY gate never does. A scheduled run executes SCAN → FILTER → GROUP → PROPOSE, writes the report to `quality_reports/knowledge_sync/report-YYYY-MM-DD.md` in the forge repo, and STOPS. Max reviews the report later and triggers APPLY interactively.

Runner: a user crontab entry (1st of the month, 09:23 local). **The human installs it manually**: persisting a headless autonomous run is a user-authorized action, Claude only documents the line (`crontab -l` to inspect, `crontab -r` or edit to remove). Replace `<forge-repo>` and `<claude-bin>` with your paths (`which claude`), and `mkdir -p ~/.claude/logs` first (cron fails silently on a missing redirect target):

```
23 9 1 * * cd <forge-repo> && <claude-bin> -p "Run the knowledge-sync skill in Scheduled Mode: SCAN, FILTER, GROUP, PROPOSE only. Write the report to quality_reports/knowledge_sync/report-$(date +\%Y-\%m-\%d).md. Do NOT apply any skill changes." >> ~/.claude/logs/knowledge-sync-cron.log 2>&1
```

Caveats:

- cron does not catch up on runs missed while the machine sleeps: if the report is missing after the 1st, kick the same prompt manually.
- The headless run depends on the settings.json allowlist covering the `obsidian` CLI; a permission denial shows up in the log file, not on screen.
- The report lands on whatever branch is currently checked out in the forge repo. Reports are tracked in git (review history), not gitignored.
- CronCreate (in-session scheduler) is NOT suitable here: its jobs are session-only and expire within 7 days.

## Quality Notes

- Take your time scanning every Skill Candidates table thoroughly
- Read the target skill file before proposing additions (avoid duplicates)
- Quality of proposals matters more than quantity
- Do not skip validation steps

## Rules

- **Never auto-apply.** Always present proposals and wait for approval.
- **One skill at a time.** Don't batch across skills without per-skill approval.
- **Preserve existing content.** Additions only, never modify existing skill text.
- **Backlinks are mandatory.** Every applied pattern traces back to its vault source.
- **Cadence:** monthly or after major project milestones. Not after every session.
