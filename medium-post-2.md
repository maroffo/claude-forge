# When Your AI Skills Library Gets Too Smart for Its Own Context Window
## From Token Optimization to an Orchestrated Development Workflow with Claude Code

**Massimiliano Aroffo**
*20 min read*

---

A follow-up to my previous article on building modular AI skills for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (Anthropic's CLI tool for agentic coding), where I discovered that teaching an AI your patterns is only half the battle: the other half is fitting those patterns into a finite context window — and then making them *do something*.

![Skills optimization: 28 files, +352/-2009 lines](https://via.placeholder.com/800x400?text=Skills+Optimization+352+added+2009+deleted)

*The final diff: 352 lines added, 2,009 deleted. Sometimes the best code you write is the code you delete.*

## Part 1: The Bloat Problem

In my [previous article](https://medium.com/@maroffo), I described building [claude-forge](https://github.com/maroffo/claude-forge): a modular skills library that teaches Claude Code your development patterns. The repo symlinks into `~/.claude/` (Claude Code's config directory), so everything loads automatically. Go idioms, Python conventions, Rails architecture, Terraform modules: each encoded in a token-optimized markdown file that auto-loads based on project context.

It worked great. Too great, actually.

The collection grew from 9 skills to 27. The original 5,761 lines of carefully crafted knowledge expanded to over 7,000 as I added Android/Kotlin, React/Next.js, Apple/Swift, cloud infrastructure, ClickUp integration, Gmail workflows, and a constellation of iOS sub-skills borrowed from [Harper Reed's dotfiles](https://github.com/harperreed/dotfiles/tree/master/.claude).

And then I hit the wall that every developer eventually hits: **the thing I built to solve a problem had become the problem**.

Skills were loading into Claude's context window and eating tokens like a teenager at an all-you-can-eat buffet. The Go skill alone was 299 lines. The `_INDEX.md` navigation file was 238 lines of verbose routing tables, dependency graphs, and "How to Use This Index" sections that Claude didn't need because, well, it already knows how to read an index.

Worse: I was duplicating information everywhere. The Gmail account configuration (`maroffo@gmail.com`, `gog` CLI commands) appeared identically in five different email skills. The ast-grep patterns were copy-pasted into every language skill. The Second Brain category routing table was repeated across three newsletter/clipping processors.

Every duplicated line is a stolen token. Every stolen token is context that could have been used for actual thinking.

## The Irony: Using AI to Optimize AI Instructions

Here's where it gets meta. I asked Claude to optimize its own skill files.

Not just "make them shorter." I wanted a systematic analysis: identify duplication across all 27 skills, find content that's redundant with the system prompt or MCP tool schemas, compress verbose sections without losing functionality, and merge skills that should never have been separate.

Here's the actual prompt I gave Claude (condensed):

> Analyze all 27 skill files in ~/.claude/skills/. For each file: (1) identify content duplicated across multiple skills, (2) find content redundant with your own system prompt or MCP tool schemas you already receive, (3) flag verbose sections that could be compressed to table or one-liner form without losing the architectural decision, (4) identify skills that overlap enough to merge. Then propose a phased optimization plan and execute it.

The key insight in that prompt: I explicitly told Claude to look for content redundant with *its own system prompt*. I couldn't do that analysis myself because I don't see the full system prompt. But Claude knows what it already receives, and it can identify when a skill file is repeating information it gets for free.

The approach was surgical. Claude Code has a `Task` tool that launches specialized subagent processes: lightweight, focused agents that run in parallel, each with access to the filesystem but scoped to a specific job. I used these to analyze clusters of skills simultaneously: one subagent on the Swift family, another on email workflows, a third on language skills. Each returned a duplication report. Then I reviewed the reports, approved the plan, and let Claude execute a 5-phase optimization.

This is *not* multiple Claude Code sessions or some orchestration layer. It's a single conversation using Claude Code's built-in `Task` tool — which spawns lightweight subprocesses that can read, write, and search the filesystem independently — to parallelize the analysis. Think of it like spawning goroutines for the research phase, then serializing for the execution phase.

**Phase 1: The Swift Mega-Merge**

I had five separate Swift/iOS skills: `apple-swift`, `swift-concurrency`, `swiftui-performance`, `swiftui-refactor`, and `native-app-performance`. Each was a focused, standalone file. Each loaded separately. Each repeated the same `@available(iOS 17, *)` boilerplate.

The analysis revealed they should have been one skill all along. The concurrency fixes table, the view property ordering rules, the performance killers checklist, the Instruments xctrace commands: these weren't separate domains. They were different facets of "Apple platform development."

Four skills merged into one. Four deleted files. Zero lost functionality.

**Phase 2: The Shared Reference Pattern**

Five email-related skills (inbox-triage, email-cleanup, newsletter-digest, process-clippings, process-email-bookmarks) all contained the same Gmail configuration block:

```markdown
## Gmail Configuration
- **Account**: maroffo@gmail.com
- **Tool**: `gog` CLI
```

And the same operations table. And the same search operators. Multiplied by five files.

The fix was obvious in retrospect: extract shared content into reference files. `_GMAIL.md` holds the account config and command reference. `_SECOND_BRAIN.md` holds the category routing table, content template, and integration rules. Each skill now says `See _GMAIL.md` instead of repeating 35 lines of identical content.

This is just the DRY principle applied to AI instructions. We've known this for decades. I just forgot it because "it's just markdown."

**Phase 3: Killing Sacred Cows**

The ClickUp skill had 155 lines. Seventy of those were tables describing MCP tool parameters: what `clickup_create_task` accepts, what `clickup_get_task` returns. Useful documentation, except Claude already has access to the MCP tool schemas. It literally receives them in every conversation. Those 70 lines were telling Claude things it already knew.

Stripped them. Replaced with: `All tools available via MCP: clickup_* prefix. See tool schemas for parameters.` ([MCP](https://modelcontextprotocol.io/) — Model Context Protocol — is the standard through which Claude Code discovers external tools and their schemas at runtime.)

Similarly, the `commit/` skill was a 59-line wrapper around conventions that already existed in `source-control/`. Merged the commit process into source-control, reduced commit to a 10-line redirect.

The `project-analyzer/` skill went from 396 lines to 90. The original had a 115-line manual analysis workflow, a 52-line framework detection guide, and a 46-line documentation template. The compressed version uses two tables and a list of required CLAUDE.md sections.

Same knowledge. A quarter of the tokens.

**Phase 4: The Compound Effect**

The remaining optimizations were less dramatic but collectively massive:

- **Every language skill** had ast-grep patterns duplicated from `_AST_GREP.md`. Replaced with `See _AST_GREP.md`.
- **Ruby's HTTP Client section**: 31 lines of `Net::HTTP` boilerplate compressed to one line describing the pattern. Claude knows how to write a Ruby HTTP client; it needs to know your *architectural convention*, not the stdlib API.
- **Email cleanup**: Three identical archive loops (promotions, social, updates) with different queries but identical logic. Replaced with a query parameter table and one template loop.
- **The `_INDEX.md`**: 238 lines of navigation tables, dependency graphs, file tree listings, "How to Use" instructions, and a "Quick Command Reference" section that duplicated commands from the skills it was routing to. Rewritten to 49 lines: two tables (by language, by task) and a shared files reference.

**Phase 5: The README and Config Update**

Updated the repository README to reflect the new structure: removed references to deleted skills, added the new shared reference files, reorganized the skills table. Updated `CLAUDE.md.example` so new users get the correct skills routing.

## The Numbers

Here's what the optimization produced:

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Total skill files | 31 | 27 | -4 (merged) |
| New shared files | 0 | 2 | `_GMAIL.md`, `_SECOND_BRAIN.md` |
| Total lines | ~6,050 | ~4,050 | -33% |
| Lines added | - | 352 | New content |
| Lines deleted | - | 2,009 | Redundancy eliminated |

The `_INDEX.md` alone went from 238 to 49 lines. The email-cleanup skill from 175 to 53. The project-analyzer from 396 to 90.

And here's the thing: **nothing was lost**. Every pattern, every convention, every workflow is still there. It's either in the skill itself (compressed), in a shared reference file (deduplicated), or was redundant with information Claude already receives (deleted).

## What I Learned About Optimization

### 1. AI Instructions Have the Same Technical Debt as Code

Skills accumulate cruft exactly like source code. You add a section "temporarily." You copy-paste because it's faster than extracting a shared module. You add verbose examples because you're not sure the AI will understand the terse version.

Before you know it, you have five files with identical Gmail configs and three files with the same category routing table.

The fix is the same as for code: periodic refactoring. Review your skills with fresh eyes. Ask: "If I were writing this from scratch today, would I include this section?" If not, cut it.

### 2. Context Window Is Your Scarcest Resource

Every token in a skill file is a token that can't be used for reasoning about your actual problem. A 300-line Go skill means 300 lines less context for the complex refactoring you're asking Claude to perform.

This realization changed how I think about skill authoring. Here's a real before/after from the Ruby skill:

---

**Before** (31 lines in the skill file):

```ruby
# HTTP Client Pattern
module MyGem
  class Client
    def initialize(base_url:, token:, timeout: 10)
      @uri = URI.parse(base_url)
      @token, @timeout = token, timeout
    end
    def get(path)
      request = Net::HTTP::Get.new(path)
      execute(request)
    end
    private
    def execute(request)
      request["Authorization"] = "Bearer #{@token}"
      # ... 15 more lines of Net::HTTP setup
    end
  end
end
```

**After** (1 line in the skill file):

```
HTTP: Net::HTTP + JSON.parse, set use_ssl/open_timeout/read_timeout.
Auth via request["Authorization"]. Client class: initialize(base_url:,
token:, timeout:) + private execute.
```

---

Same architectural decision. One-thirtieth the tokens.

Claude knows the Ruby stdlib. It doesn't need a tutorial. What it needs is your *architectural decision*: "We use `Net::HTTP`, not `httparty` or `faraday`, and here's the class structure."

### 3. Don't Document What the AI Already Knows

This was the most counterintuitive lesson. I was writing detailed tool parameter tables for ClickUp MCP tools, explaining how `git commit` works in the source-control skill, and describing basic HCL syntax in the Terraform skill.

Claude *already knows these things*. It receives MCP tool schemas in its system prompt. It understands git deeply. It can write Terraform in its sleep.

Your skills should contain **the delta**: what's specific to your workflow, your architectural decisions, your team's conventions. Not generic knowledge.

The test: "Would a senior developer who knows this language need this information to follow our conventions?" If yes, keep it. If it's just teaching the language itself, cut it.

### 4. Shared Reference Files Are a Force Multiplier

The `_GMAIL.md` and `_SECOND_BRAIN.md` pattern was the highest-ROI change. Two small files (33 and 52 lines) eliminated roughly 200 lines of duplication across five skills each.

But the benefit goes beyond token savings. When I change the Gmail account or add a new gog CLI command, I update one file instead of five. When I add a new Second Brain category, it propagates to all skills that reference it.

This is the same reason we use shared libraries in code. The only surprise is that it took me this long to apply it to AI instructions.

### 5. Let the AI Optimize Itself (But Verify)

Having Claude analyze and compress its own instruction set is powerfully meta. It finds duplication patterns across files that humans miss because we don't hold 27 files in memory simultaneously. It identifies content that's redundant with its own system prompt: information you thought was necessary but that Claude already receives.

But verify the output. In one case, the analysis flagged a "contradictory" architecture recommendation (MVVM vs MV patterns in Swift) that was actually intentional: MVVM for UIKit legacy, MV for modern SwiftUI. Context matters, and the AI doesn't always know which "contradictions" are deliberate trade-offs.

---

## Part 2: From Skills to an Orchestrated Workflow

The optimization left me with a lean, token-efficient skills library. But it also exposed a fundamental limitation: **skills are passive**. They load knowledge into context. They don't *do* anything with it.

Skills tell Claude *what to know*. But nothing tells it *how to behave* across a development session — when to plan, when to test, when to review, when to stop and score the work. I was still manually driving every step: "now run the tests," "now review this for security," "now check the architecture."

The missing piece wasn't more knowledge. It was orchestration.

### The Inspiration

I stumbled on [Pedro Santanna's claude-code-my-workflow](https://github.com/pedrohcgs/claude-code-my-workflow), a repo from a professor who'd built an orchestrated Claude Code workflow for academic slide development. LaTeX, R, Quarto — not my stack. But the architecture was immediately recognizable.

He had a three-tier system:

- **Rules** (`~/.claude/rules/`): Always-on guardrails that auto-load every conversation. No invocation needed.
- **Agents** (`~/.claude/agents/`): Specialized reviewers launched on demand. Each focused on one thing — proofreading, pedagogy, visual layout, TikZ diagrams.
- **Skills** (`~/.claude/skills/`): User-invoked commands. What I already had.

The key innovation was an **orchestrator rule** — an always-active protocol that defined an autonomous development loop: implement, verify, review with parallel agents, fix findings, re-verify, score against quality gates, loop until done. He called it "contractor mode."

For his academic workflow, this meant: translate Beamer slides to Quarto, compile, launch proofreader + slide-auditor + pedagogy-reviewer in parallel, fix their findings, re-compile, score, repeat until 90/100.

For software development, this could mean: implement a feature, run tests, launch security-reviewer + architecture-reviewer + test-reviewer in parallel, fix their findings, re-test, score, repeat until quality gates pass.

Same pattern. Different agents. Same orchestration.

### Building the Three-Tier System

I adapted Pedro's architecture for software development. The result:

```
~/.claude/
├── CLAUDE.md           → Identity, philosophy, routing tables (70 lines)
├── MEMORY.md           → Persistent [LEARN:x] corrections
├── rules/              → Always-on workflow guardrails
│   ├── orchestrator-protocol.md
│   ├── plan-first-workflow.md
│   ├── verification-protocol.md
│   └── quality-gates.md
├── agents/             → On-demand agents (launched by orchestrator)
│   ├── software-engineer/
│   ├── research-analyst/
│   ├── security-reviewer/
│   ├── performance-reviewer/
│   ├── architecture-reviewer/
│   ├── test-reviewer/
│   ├── dependency-reviewer/
│   ├── database-reviewer/
│   ├── dx-reviewer/
│   ├── tech-writer/
│   └── project-analyzer/
└── skills/             → User-invoked (unchanged from Part 1)
```

#### Rules: The Always-On Layer

Rules auto-load every conversation. They replaced content I used to cram into `CLAUDE.md`, which was getting bloated with process instructions that didn't belong next to interaction preferences.

The **orchestrator protocol** defines the autonomous loop:

```
0. RESEARCH  → (optional) Launch research-analyst for unknowns
1. IMPLEMENT → Launch software-engineer(s) with scoped subtasks
2. VERIFY    → Run tests, lint, build
3. REVIEW    → Launch review agents by file pattern
4. FIX       → Pass findings to software-engineer (findings are requirements)
5. RE-VERIFY → Rebuild, retest
6. SCORE     → Apply quality-gates thresholds
7. LOOP      → Repeat 3-7 until score ≥ threshold or max 5 rounds
8. PRESENT   → Structured summary
```

The **plan-first workflow** mandates planning before implementation and — critically — saves plans to disk. Plans in context evaporate when the window auto-compresses. Plans on disk survive.

The **verification protocol** formalizes TDD as an always-on rule, not a suggestion in CLAUDE.md that gets ignored when things get busy.

The **quality gates** create numeric thresholds: 80/100 to commit, 90/100 to open a PR, 95/100 for excellence. A CRITICAL finding (failing tests, security vulnerability) auto-fails to 0. This replaces the vague "looks good to me" with a clear, repeatable definition of done.

#### Agents: The On-Demand Specialists

The key design decision: agents are launched by the orchestrator **based on which files changed**, not manually selected. Touch a migration and a controller? The orchestrator fires `database-reviewer` + `architecture-reviewer` + `security-reviewer` in parallel. Touch only test files? Just `test-reviewer`.

The routing table:

| File pattern | Agents launched |
|-------------|----------------|
| `*.go`, `*.rb`, `*.py`, `*.ts` | architecture-reviewer + security-reviewer |
| Hot paths, queries, caching | + performance-reviewer |
| `*_test.go`, `*_spec.rb` | + test-reviewer |
| `go.mod`, `Gemfile`, `package.json` | dependency-reviewer |
| `migrations/`, `schema.rb` | database-reviewer |
| `docs/`, `README*`, `ADR/` | dx-reviewer |

Seven review agents, all **read-only**. They report findings ranked by severity (CRITICAL / MAJOR / MINOR), with exact file locations and proposed fixes. They never edit files — more on why in Lesson 8 below.

Then there's the odd one out: `tech-writer`. Not a reviewer — a content creator. It reads project context (commits, decisions, code changes) and produces blog posts, changelogs, release notes. Different pattern, same agent system.

### The Software Engineer Agent

Here's where it gets interesting. All the agents above are either reviewers (read-only) or content creators. But who writes the actual code?

My first instinct was to create `backend-engineer` and `frontend-engineer` agents. A full-stack feature could launch both in parallel: backend writes the API endpoint while frontend writes the React component.

I talked myself out of it. The backend/frontend split is too rigid. Consider:

- "Add auth middleware + rate limiting" — both backend, but independent workstreams
- "Refactor package ordering + package catalog" — both backend, parallelizable
- "Migrate endpoint from REST to gRPC" — backend, but not parallelizable

The real dimension isn't technology stack. It's **independence of the workstream**.

So instead of specialized developer agents, I created a single `software-engineer` agent that the orchestrator configures per-task with:

- **Scope**: Which files/directories it owns (no cross-boundary edits)
- **Plan**: Specific subtask with acceptance criteria
- **Context**: Which language/framework skill applies

For a full-stack feature, the orchestrator launches three `software-engineer` instances in parallel, each scoped to its workstream:

```
1. software-engineer: "Add /api/orders endpoint"  → scope: internal/ordering/
2. software-engineer: "Add OrderList component"    → scope: src/components/orders/
3. software-engineer: "Add orders migration"       → scope: db/migrations/
```

For a single-file fix, the orchestrator implements directly. No subagent overhead for simple tasks.

The critical design decision: **reviewer findings are requirements, not suggestions**. When a security-reviewer flags a SQL injection at line 42, that finding flows back to the software-engineer as a non-negotiable fix. CRITICAL and MAJOR findings must be addressed. The software-engineer can deviate from the reviewer's *proposed fix* if it has a better solution, but it must explain why.

This closes the loop. Reviewers find issues. The engineer fixes them. Reviewers verify the fixes. The orchestrator scores the result. No findings fall through the cracks because someone decided "eh, it's fine."

### MEMORY.md: The Quick-Learn Pattern

Pedro's repo had a `MEMORY.md` concept: a lightweight file for persistent corrections across sessions. Format:

```
[LEARN:docker] Alpine needs musl, not glibc — use bookworm-slim
[LEARN:postgres] pgx v5 uses pgxpool, not pgx.Connect directly
```

I already had `learning-docs`, a skill that maintains full LEARNING.md retrospectives — architectural decisions, bugs fixed, lessons learned. That's great for deep knowledge capture. But it's heavy for quick corrections.

MEMORY.md is the complement: one-line corrections that accumulate over sessions. Claude makes a wrong assumption about your stack? Append a `[LEARN:x]` entry. Next session, it loads automatically and the mistake doesn't repeat.

Think of LEARNING.md as your engineering journal. MEMORY.md is your sticky notes.

### Optimizing Continuously

The same session where I built the orchestrated workflow, I also evolved individual skills. The Go skill got 5 new patterns from a talk on "mechanical sympathy" in embedded Go:

- **Synchronous libraries**: don't launch goroutines from library code — let the caller decide concurrency
- **Useful zero values**: uninitialized structs should be safe to use or obviously invalid
- **Stack-friendly hot paths**: `var s MyStruct` over `&MyStruct{}` in loops to avoid heap allocations
- **Struct composition by value**: embed structs directly for data locality and nil safety
- **Build tags for test simulation**: swap real drivers with simulators at compile time

Then I optimized the entire Go skill: 410 lines → 189 lines. **Added knowledge and reduced tokens in the same pass.** That's the optimization philosophy in action: it's not about having less. It's about having more signal per token.

### What CLAUDE.md Became

With rules handling process (TDD, planning, quality gates) and agents handling review, CLAUDE.md could finally be what it should have been all along: **identity and philosophy**.

The file went from 91 lines to 70. It contains:

- How to interact with me (tone, pushback, naming conventions)
- Code philosophy (simple > clever, style consistency)
- The decision framework (green/yellow/red)
- A one-line reference to the workflow system: "Rules in `rules/` auto-load. Agents in `agents/` launched by orchestrator."
- The skills routing table

No more TDD instructions embedded between git rules and interaction preferences. No more "Before Writing Code" checklist competing with "Code Quality" for attention. Each concern lives in its own file, loaded at the right time.

## The Numbers (Complete Picture)

| Component | Files | Total lines |
|-----------|-------|-------------|
| CLAUDE.md | 1 | 71 |
| MEMORY.md | 1 | 16 |
| Rules | 4 | 142 |
| Agents | 11 | 576 |
| Skills | 27 | ~4,080 |
| **Total** | **44** | **~4,885** |

But the numbers that matter aren't line counts. They're:

- **Rules auto-load**: 142 lines of always-on behavior, zero manual invocation
- **Agents load on-demand**: only the relevant ~50 lines load per review, not all 576
- **CLAUDE.md is 23% leaner**: 91 → 70 lines, with more actual content (gained "describe approach first" and ">3 files break into tasks" back, lost the bloated routing tables)

## What I Learned (Part 2)

### 6. Skills Tell Claude What to Know. Rules Tell It How to Behave. Agents Tell It Who to Ask.

This three-tier separation is the single most important architectural insight. Before, everything was either in CLAUDE.md (bloated, always loaded, mixing identity with process) or in skills (passive, knowledge-only).

Rules handle process: "always plan before building," "always run tests," "score work against quality gates." They're the engineering manager.

Agents handle specialized review: "check this for security vulnerabilities," "check this migration won't lock the table." They're the senior engineers on the team.

Skills handle knowledge: "here's how we write Go," "here's our Rails architecture." They're the team wiki.

CLAUDE.md handles identity: "push back when you're right," "pick unhinged project names." It's the team culture doc.

### 7. The Orchestrator Turns a Knowledge Library into a Development Workflow

Before the orchestrator, my skills library was a reference manual. Useful, but passive. I'd ask Claude to write code, manually ask it to review, manually tell it to fix issues, manually check if tests pass.

The orchestrator turns that into: "implement this feature" → autonomous loop until quality gates pass. Plan, implement with scoped agents, verify with tests, review with parallel specialists, fix findings, re-verify, score, present.

The human stays in the loop for plan approval and final sign-off. Everything between is autonomous.

### 8. Read-Only Agents Are a Feature, Not a Limitation

My first instinct was to let review agents fix what they find. More efficient, right?

No. A reviewer that can edit code bypasses your approval loop. It might "fix" a security issue by deleting the test that caught it. It might "fix" a performance problem with a workaround that breaks the API contract.

Read-only agents force a separation of concerns: finding problems is separate from fixing them. The orchestrator mediates: reviewer reports findings, software-engineer implements fixes, reviewer verifies the fix. Three steps, not one. Slower, but each fix is intentional.

### 9. Scope Boundaries Prevent Agent Conflicts

When you launch multiple software-engineer instances in parallel, they could theoretically edit the same file and produce conflicts. The solution is trivially simple: each agent gets a scope (directories/files it owns) and cannot edit outside it.

This is just filesystem-level encapsulation. The same principle that makes microservices work: clear ownership boundaries prevent coordination overhead.

### 10. Evaluate Other Configurations by Signal, Not Size

The compound-engineering-plugin has 29 agents and 25 commands. We adopted exactly 3 patterns. The instinct is to be impressed by scale, but a 29-agent configuration means 29 agents loading context, 29 agents to maintain, and 29 agents that might give contradictory advice.

When evaluating someone else's Claude Code setup, ask: "Does this solve a problem I actually have?" If 26 out of 29 agents don't, the three that do are gold. The other 26 are token tax.

### 11. Plans Must Survive Context Compression

Claude Code auto-compresses context when it gets large. This is usually transparent. But if your implementation plan exists only in context, it evaporates during compression, and Claude loses the thread of what it's doing.

Saving plans to `quality_reports/plans/YYYY-MM-DD_description.md` solves this. The plan is on disk. If context compresses, Claude can re-read the plan. Session logs serve the same purpose: decisions and progress persist beyond any single context window.

## Part 3: Stealing from the Competition (Selectively)

Before publishing this article, I found [Every's compound-engineering-plugin](https://github.com/EveryInc/compound-engineering-plugin): a massive Claude Code configuration with 29 agents, 25 commands, and 16 skills. Their tagline: "compound engineering" — the idea that solved problems should compound into organizational knowledge, not vanish when the session ends.

It's the largest Claude Code configuration I've seen. And it taught me something about the difference between comprehensive and effective.

### What They Built

The plugin has a marketplace format with a CLI converter that generates configurations for OpenCode and Codex. It includes persona-based reviewers ("DHH Rails Reviewer" that mimics David Heinemeier Hansson's opinions), swarm mode for parallel agent execution, file-based todo tracking with YAML frontmatter, and a knowledge capture system called "compound-docs."

It's impressive engineering. But it's also 29 agents where most projects need 5-6, and persona-based reviewers that prioritize entertainment over reliability. A reviewer that simulates DHH's opinions is fun; a reviewer with an OWASP checklist is useful.

### What We Stole (Three Patterns)

**1. The Solutions Directory**

Their `compound-docs` system (`/workflows:compound`) launches parallel subagents that document solved problems in `docs/solutions/[category]/`. This is their best idea. Most knowledge capture is either too heavy (full retrospective documents) or too light (one-line notes). A categorized directory of solved problems hits the sweet spot: searchable, specific, low-friction.

I already had `LEARNING.md` (deep retrospectives) and `MEMORY.md` (one-line corrections). The solutions directory fills the gap between them. The agents are trained to create and search a `docs/solutions/` structure in the *target project* — not in claude-forge itself. Each project accumulates its own knowledge base: "We solved this specific problem. Here's the problem, the fix, and why it works."

```
docs/solutions/
├── auth/           → Authentication fixes
├── performance/    → Profiling results, caching decisions
├── infrastructure/ → CI/CD, Docker, deployment
├── database/       → Migration gotchas, query optimization
└── testing/        → Flaky test patterns, fixture strategies
```

Each file is a problem-solution-rationale triple. When the research agent (more on that below) needs to check if the team has solved a similar problem before, it searches here first.

**2. The Research Agent**

Their setup includes several research agents: best-practices-researcher, framework-docs-researcher, learnings-researcher. Our workflow was all implementation and review — no structured research step.

The gap was obvious once I saw it. The orchestrator loop starts with IMPLEMENT. But what happens when the plan involves a technology the team hasn't used before? Or when there are three valid approaches and no clear winner?

The new `research-analyst` agent slots in as Step 0 in the orchestrator: before implementation, when there are unknowns. It searches internal knowledge first (`docs/solutions/`, `LEARNING.md`, `MEMORY.md`), then external sources. It returns a comparison table with a clear recommendation.

The key constraint: **opinionated, not neutral.** Research that presents three options with equal weight is useless. The agent picks a winner and explains why. You can override it, but at least you're overriding a reasoned recommendation rather than staring at a blank page.

**3. Incremental Commits**

Their `/workflows:work` command makes logical commits after each completed subtask, not one mega-commit at the end. Simple idea, but we hadn't specified commit strategy in our software-engineer agent.

Now the agent commits after each coherent unit of work: one endpoint, one component, one migration. Each commit must pass tests independently. If something breaks in the third commit, you know exactly what changed.

### What We Rejected (And Why)

**File-based todos**: Claude Code already has a TodoWrite tool, and we use ClickUp for task management. Duplicating state in YAML-frontmatter files is fragile and adds another source of truth to keep in sync.

**Swarm mode**: Orchestrating N parallel agents sounds powerful. In practice, coordination overhead grows faster than throughput. Our max-3 cap exists for a reason.

**Persona-based reviewers**: "What would DHH think of this code?" is a fun party trick. But a reviewer that role-plays a personality can generate plausible-sounding but wrong advice. An architecture-reviewer with a SOLID checklist gives consistent, verifiable feedback.

**Plugin marketplace format**: They optimize for distribution across tools (OpenCode, Codex, Claude Code). We optimize for one tool, done well.

### The Takeaway

When evaluating other people's configurations, don't count features. Count the ones that solve a problem you actually have. Out of 29 agents and 25 commands, exactly three architectural patterns were worth adopting. That's not a criticism of their work — it's a reminder that more isn't better. **Signal per token is what matters.**

## The Bigger Picture

Six months into this experiment, the skills library has evolved from a flat collection of markdown files into a three-tier system with orchestrated agents, quality gates, and persistent memory. The token count is lower than when I started with 9 skills, despite now covering 11 languages, 11 agents, 4 rules, a searchable solutions directory, and 5 productivity workflows.

The progression was:

1. **Skills** — teach Claude your patterns (passive knowledge)
2. **Optimization** — compress skills to fit the context window (same knowledge, fewer tokens)
3. **Rules** — define always-on behavior (active process)
4. **Agents** — specialized reviewers and implementers (active delegation)
5. **Orchestrator** — autonomous development loop (active workflow)
6. **Knowledge compounding** — solutions directory, research agent, incremental commits (active learning)

Each step built on the previous. You can't orchestrate bloated skills (step 2 enables step 5). You can't route agents without rules (step 3 enables step 4). And none of it works if you haven't first encoded your actual development patterns (step 1).

The lesson: **treat your AI instructions with the same engineering rigor you apply to your code.** Refactor. Deduplicate. Compress. Architect. Test. Iterate.

Your context window will thank you. And then it will start writing your code.

---

**The complete system is at [github.com/maroffo/claude-forge](https://github.com/maroffo/claude-forge). Key commits: [496aa4d](https://github.com/maroffo/claude-forge/commit/496aa4d) (optimization: +352/-2,009), [599572c](https://github.com/maroffo/claude-forge/commit/599572c) (orchestrated workflow: +766), [da51731](https://github.com/maroffo/claude-forge/commit/da51731) (final token optimization: +53/-189). The compound-engineering-inspired additions (research agent, solutions directory, incremental commits) came last.**

---

*Massimiliano Aroffo is a Cloud Engineer and Architect at Wishew, where he builds infrastructure automation and occasionally uses AI to optimize AI instructions about AI that orchestrate other AI. The turtles are getting recursive.*
