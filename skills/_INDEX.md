# ABOUTME: Skills navigation index with task-based routing
# ABOUTME: Find the right skill by language, task, or problem type

# Skills Index

## By Language/Platform

| Language | Skill | Coverage |
|----------|-------|----------|
| Go | `golang` | Code, design, concurrency, performance, review |
| Kotlin/Android | `android-kotlin` | Compose, Clean Architecture, Hilt/Koin, testing |
| Swift/Apple | `apple-swift` | SwiftUI, Swift 6, async/await, TCA, performance |
| Swift (Liquid Glass) | `swiftui-liquid-glass` | iOS 26+ glass effects |
| iOS Simulator | `ios-debugger` | Build, run, interact, logs via CLI |
| Python | `python` | uv, type checking, linting, Docker |
| Ruby (gem) | `ruby` | Gem development, RSpec, RuboCop, publishing |
| Ruby/Rails | `rails` | Services, forms, contracts, Sidekiq, Hotwire |
| React/Next | `react-nextjs` | Next.js 16, App Router, Server Components |
| Terraform | `terraform` | HCL, Terragrunt, modules, state, OpenTofu |
| AWS/GCP | `cloud-infrastructure` | Well-Architected, ECS/EKS, security, FinOps |

## By Task

| Task | Primary Skill | Related |
|------|---------------|---------|
| Refine requirements | `refine-requirements` | plan-first-workflow rule |
| Issue/analysis to plan + impl prompt | `plan-forge` | `second-opinion`, plan-first-workflow rule |
| Autonomous issue to PR loop (hikmaAI) | `issue-loop-hikma` | client repo (claude-hikma-skills), symlinked locally; `issue-triage-hikma`, `plan-forge` |
| Auto-triage open issues (hikmaAI) | `issue-triage-hikma` | client repo (claude-hikma-skills), symlinked locally; `issue-loop-hikma` |
| Autonomous issue to PR loop (Wishew) | `issue-loop-wishew` | private repo (claude-skills-wishew), symlinked locally; `plan-forge`, `work-next-wishew` |
| Work with legacy/untested code | `legacy-code-expert` | `verification-protocol`, language-specific |
| Write code | Language-specific | `_PATTERNS.md`, `_AST_GREP.md` |
| Search/refactor code | `_AST_GREP.md` | Language-specific |
| Commit changes | `source-control` | (`commit` redirects here) |
| Review code (pre-commit) | `gemini-review` | Language review sections |
| Review a PR (commit-aware) | `pr-review` | `gemini-review`, `second-opinion` |
| Deep multi-LLM review | `advanced-review` | deployed via symlink from the claude-advanced-review repo |
| Score commit/PR readiness | `score` | quality-gates rule |
| Second opinion | `second-opinion` | `gemini-review` |
| Assess test quality | `test-design-reviewer` | `gemini-review`, `_PATTERNS.md` |
| Verify UI changes end-to-end | `verify-frontend` | `verification-protocol` rule, chrome-devtools MCP |
| Setup/analyze project | `project-analyzer` | Language-specific |
| Scaffold make check targets | `project-checks` | - |
| Release/tag | `releasing-software` | `source-control` |
| Architecture decision record | `adr` | `refine-requirements` |
| Document learnings | `learning-docs` | - |
| Mine cross-repo failure modes | `learning-loop` | `learning-docs`, `harness-mechanic` |
| Optimize a prompt via evals | `autoresearch-prompt` | - |
| Sync vault knowledge to skills | `knowledge-sync` | `_VAULT_CONTEXT.md`, `learning-docs` |
| Task management | `clickup` | `source-control` |
| Bullet Journal (daily/weekly/monthly) | `bujo` | `obsidian`, `bujo-sync` |
| Sync BuJo with ClickUp/Linear | `bujo-sync` | `bujo`, `clickup` |
| AWS/GCP infra | `cloud-infrastructure` | `terraform` |
| Obsidian vault ops | `obsidian` | `_OBSIDIAN.md`, `_SECOND_BRAIN.md` |
| Notion to vault sync | `notion-sync` | `obsidian` |
| Save project artifacts | vault (see plan-first-workflow) | `_OBSIDIAN.md` |
| Check email | `inbox-triage` | private repo, symlinked locally |
| Process newsletters | `newsletter-digest` | private repo, symlinked locally |
| Process clippings | `process-clippings` | `_OBSIDIAN.md`, `_SECOND_BRAIN.md` |
| Process bookmarks | `process-email-bookmarks` | private repo, symlinked locally |
| Clean up email | `email-cleanup` | private repo, symlinked locally |
| Generate cover image | `cover-image` | `_generate_image.py` |
| Render table as image | `table-image` | `_generate_image.py` |
| Edit/review text for AI patterns | `humanizer` | - |
| Write blog posts (Max) | `blog-writer` | `humanizer`, `cover-image`, `_SECOND_BRAIN.md` |
| Write emails (Max) | `mail-writer` | `humanizer` |
| Write blog posts (Mauro Medda) | `mauro-blogger` | private repo, symlinked locally like `advanced-review` |
| Publish LinkedIn post | `linkedin-post` | private repo, symlinked locally |
| Analyze code cognitive load | `cognitive-load-analyzer` | `gemini-review`, language-specific |
| Create/improve skills | `skill-forge` | `_INDEX.md`, `CLAUDE.md.example` |
| Capture execution traces | `harness-trace` | orchestrator-protocol rule |
| Optimize harness (rules/skills) | `harness-mechanic` | `harness-trace` |

## Shared Reference Files

| File | Purpose |
|------|---------|
| `_AST_GREP.md` | ast-grep patterns by language |
| `_PATTERNS.md` | Cross-language code patterns |
| `_GMAIL.md` | Gmail account config, gog CLI commands (private repo, symlinked locally) |
| `_OBSIDIAN.md` | Obsidian CLI config, vault commands |
| `_SECOND_BRAIN.md` | Category routing, content templates, rules |
| `_VAULT_CONTEXT.md` | Vault context injection, token budget, breadcrumbs |
| `_generate_image.py` | Gemini image generation (used by cover-image, table-image) |
