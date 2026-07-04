# ABOUTME: Hugo front matter template and Second Brain -> Blog tag mapping for the blog-writer skill
# ABOUTME: Reference for the Write Draft step; keeps the SKILL.md focused on workflow

# Front Matter and Tag Mapping

## Front Matter Template

```yaml
---
title: "..."
date: YYYY-MM-DD
summary: "1-2 sentences, concrete, no fluff"
tags: [from mapping + free tags]
draft: true
cover:
  image: "images/cover-<slug>.png"
  alt: "..."
  relative: false
---
```

## Tag Mapping (Second Brain -> Blog)

| Second Brain Category | Default Blog Tags |
|---|---|
| AI Agents and Tools | `ai`, `llm` |
| Claude Code | `ai`, `claude-code` |
| Development | language-specific: `golang`, `python`, `swift`, etc. |
| DevOps and Cloud | `devops`, `cloud` |
| Engineering Management | `engineering`, `leadership` |
| Politics and Economics | `politics`, `opinion` |
| Marketing | `marketing` |
| Media and Culture | `culture` |
| Health and Science | `science` |

Add post-specific free tags: project names (`hikmaai`, `wishew`), tools (`obsidian`, `pgvector`), themes (`side-project`, `security`).
