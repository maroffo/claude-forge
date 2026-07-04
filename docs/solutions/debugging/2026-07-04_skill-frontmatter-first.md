# ABOUTME: Solution note for SKILL.md publishing the wrong registry description (ABOUTME above frontmatter)
# ABOUTME: Category debugging; from the 2026-07-04 skill/hook audit

# Problem

Skills with `# ABOUTME:` lines ABOVE the YAML `---` block advertised the ABOUTME text as their registry description; the authored `description:` (with all the trigger phrases) was silently discarded. Worse variants: a frontmatter using non-standard keys (`triggers:`, no `description:`) or no frontmatter at all makes the skill unregistered and invisible, including to other skills that depend on it.

# Solution

SKILL.md must OPEN with the frontmatter; ABOUTME lines go after the closing `---`. Detection is mechanical: `scripts/check_repo.py` check mode now fails any SKILL.md whose first non-blank line is not `---` ("frontmatter first" lint), so the class cannot ship again.

# Why It Works

The skill registry parses the file head for the frontmatter block; anything above it becomes (or breaks) the published metadata. Diagnosis shortcut: compare the descriptions in a live session's skill list against the `description:` fields on disk; any mismatch is this bug.
