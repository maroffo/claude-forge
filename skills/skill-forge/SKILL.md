---
name: skill-forge
description: "Create new skills or review and improve existing ones. Use when user says create skill, new skill, improve skill, review skill, audit skills, or skill quality."
---

# ABOUTME: Skill creation and improvement based on Anthropic's skills guide
# ABOUTME: Validates structure, descriptions, triggers, progressive disclosure, and conventions

# Skill Forge

Create new skills or audit/improve existing ones. Encodes Anthropic's official guide + our conventions.

## Modes

### Create: `/skill-forge create <name>`

1. **Gather context**: ask what the skill does, when to use it, what tools it needs
2. **Generate SKILL.md** following the template below
3. **Validate** against the checklist
4. **Present** for approval before writing

### Review: `/skill-forge review <name>` or `/skill-forge review all`

1. **Read** the skill's SKILL.md
2. **Score** against the checklist (0-100)
3. **Report** findings grouped by severity (critical, major, minor)
4. **Propose** fixes as diffs

---

## Skill Template

```markdown
---
name: kebab-case-name
description: "[What it does]. Use when [trigger conditions]. [Key capabilities]. Not for [negative triggers if overlapping skills exist]."
compatibility: "Only if external deps needed"
---

# ABOUTME: [One-line what]
# ABOUTME: [One-line key capabilities]

# Skill Title

## [Core Instructions]

[Outcomes, constraints with their reasons, and how to verify the result. Numbered steps only where order truly matters; exact commands only for fragile operations.]

## Common Issues

| Issue | Solution |
|-------|----------|

## References (if >150 lines needed)

For detailed patterns, consult `references/<topic>.md`
```

---

## Validation Checklist

### Structure (critical)

| Check | Rule |
|-------|------|
| Folder name | kebab-case, no spaces/capitals/underscores |
| File name | Exactly `SKILL.md` (case-sensitive) |
| Frontmatter | `---` delimiters, `name` + `description` required |
| ABOUTME | Two lines after frontmatter: what + capabilities |
| No README.md | All docs in SKILL.md or references/ |

### Description (critical)

| Check | Rule |
|-------|------|
| Formula | `[What] + [When/triggers] + [Capabilities]` |
| Trigger phrases | Include words users actually say |
| Negative triggers | "Not for X" if overlapping skills exist |
| Length | Under 1024 characters |
| No XML tags | No `<` or `>` in description |
| Quotes | Wrapped in double quotes |

**Test:** Ask yourself "When would you use the [name] skill?" If the description doesn't answer clearly, it needs work.

### Content (major)

| Check | Rule |
|-------|------|
| Specificity matches fragility | Exact commands for fragile or destructive operations; outcomes, constraints and reasons for judgment calls |
| Examples | Only where the output shape is format-sensitive: several varied examples, labeled illustrative; none for judgment the model already owns |
| Error handling | Common issues table for workflow skills |
| Progressive disclosure | SKILL.md <150 lines core; detailed content in references/ |
| Register | Instructions at normal volume with the reason attached; no anti-laziness notes or capitalized emphasis, which current models over-apply |

### Optional Fields (minor)

| Field | When to use |
|-------|-------------|
| `compatibility` | External deps (app, CLI, API key, MCP server) |
| `allowed-tools` | Restrict to specific tools |
| `tools` | Simpler tool restriction |
| `metadata` | Distribution (author, version, mcp-server) |

---

## Scoring

Start at 100, subtract per finding:

| Severity | Deduction | Examples |
|----------|-----------|----------|
| Critical | -25 | No frontmatter, no description, wrong file name |
| Major | -10 | No trigger phrases, vague instructions, no ABOUTME |
| Minor | -3 | Missing compatibility, no error handling, a single unlabeled gold example |

| Score | Verdict |
|-------|---------|
| 90+ | Ship it |
| 70-89 | Needs fixes |
| <70 | Rewrite |

---

## Our Conventions (beyond Anthropic's guide)

- **ABOUTME headers**: 2-line comment block after frontmatter (what + capabilities)
- **Cross-references**: link to `_AST_GREP.md`, `_PATTERNS.md`, `source-control` where relevant
- **_INDEX.md**: register new skills in the routing table
- **CLAUDE.md**: nothing to add. The harness injects every skill's name and description, so the file carries no skill catalog; discovery lives in your `description:` field, which is why it must state when to use the skill and when not to
- **Token budget**: every word in SKILL.md costs context on every trigger; cut what the model already knows, keep what only the author knows (reasons, environment facts, quality bar)
- **No em dashes**: use commas, colons, semicolons, or parentheses

## Quality Notes

- Compare against existing high-quality skills (rails, source-control, clickup)
- Propose concrete diffs, not vague suggestions
