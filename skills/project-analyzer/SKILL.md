---
name: project-analyzer
description: "Analyze codebase and create CLAUDE.md documentation. Use when analyzing project, understanding codebase, or creating documentation."
allowed-tools: [Task]
---

# ABOUTME: Automated codebase analysis and CLAUDE.md generation
# ABOUTME: Project structure mapping, convention detection, documentation creation

# Project Analyzer

Analyzes a codebase via a specialized agent that generates comprehensive CLAUDE.md documentation.

## When to Use

- Starting work on a new project
- Need to understand project structure
- Creating/updating project documentation

## Agent Invocation

Use the Agent tool with:

```
subagent_type: "project-analyzer"
prompt: "Analyze the project in [directory] and create CLAUDE.md with the Required Sections listed below: <paste the list>"
```

The agent will:
1. Scan directory structure
2. Identify language and framework
3. Analyze code patterns with ast-grep
4. Detect conventions
5. Generate CLAUDE.md

---

## CLAUDE.md Required Sections
- Project purpose (1-2 sentences)
- Tech stack + versions
- Build/test/lint commands
- Architecture overview (directory structure)
- Key conventions and patterns
- Environment setup
- Vault Context (if vault is configured; see `_VAULT_CONTEXT.md`)

---

## Resources

**Related Skills:**
- Language analysis: `_AST_GREP.md`
- Go projects: `golang/SKILL.md`
- Python projects: `python/SKILL.md`
- Rails projects: `rails/SKILL.md`
- Terraform: `terraform/SKILL.md`
