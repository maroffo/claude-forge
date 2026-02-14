# From Asking Claude to Code to Teaching Claude Our Patterns: Building Modular AI Skills

**Massimiliano Aroffo**
*10 min read*

---

A follow-up to my journey back to hands-on development at Wishew, where I discovered that the best way to work with AI isn't to ask it to write code: it's to teach it your patterns first.

![A collection of markdown files that became my AI's institutional memory](https://via.placeholder.com/800x400?text=Claude+Skills+Repository)

*My skills collection: where architectural patterns meet token optimization.*

## Back to the Trenches (Again)

In my [previous articles](https://maroffo.medium.com/), I shared how returning to an Individual Contributor role at Wishew after years as CTO has been refreshing. I've been building infrastructure automation, deployment notifiers, and AI-powered code reviews: real, hands-on technical work that I genuinely missed.

But here's what I didn't anticipate: I'd spend as much time teaching an AI how to code as I would actually coding.

Over the past few weeks, I've built two substantial projects with Claude Code as my pair programmer:

1. **Wishew Outpost API** (Go): A high-performance, read-only feed API with Redis caching, PostgreSQL read replicas, and a sophisticated Stale-While-Revalidate pattern
2. **Notification Manager** (Python): A serverless email notification service using AWS Lambda, SQS, and SES with strict dependency injection patterns

Different languages. Different architectures. Different cloud services. But the same patterns kept emerging: rigorous testing, security-first design, type safety, and obsessive documentation.

And I found myself repeating the same instructions to Claude. Over. And over. And over.

"Use parameterized queries, not fmt.Sprintf."
"Implement dependency injection, no global singletons."
"Separate unit tests from integration tests with build tags."
"Always use ast-grep for code search, never grep or ripgrep."

That's when I realized: I wasn't just building software. I was building institutional knowledge. And I was doing it the hard way.

## The Problem: Repeating Yourself to an AI

Working with Claude Code is remarkably effective. It writes solid code, understands context, and can architect complex systems. But here's the catch: **every session is a blank slate**.

When I started the Go project, I spent hours explaining our testing strategy, security practices, and architectural patterns. Then, when I moved to the Python project, I had to explain it all again. Different syntax, sure, but the same underlying principles: test-driven development, security by default, clear separation of concerns.

The patterns were consistent across both projects:

- **Testing Philosophy**: Unit tests with mocking, integration tests with real databases, clear separation via build tags (Go) or directory structure (Python)
- **Security First**: Parameterized queries everywhere, never string interpolation in SQL
- **Dependency Injection**: Constructor injection, no global state or singletons
- **Type Safety**: Leverage the type system (Go's interfaces, Python's MyPy + BasedPyright)
- **Documentation Obsession**: CLAUDE.md files, ADRs, C4 diagrams

But without a way to codify these patterns, I was essentially re-teaching Claude our institutional knowledge with every conversation.

## Discovering Matteo & Harper: The Lightbulb Moment

That's when I discovered [Matteo Vaccari's excellent series](https://matteo.vaccari.name/posts/ai-assisted-modernization-of-java-part-i/) on AI-assisted modernization of legacy Java applications. Matteo wasn't just using AI to write code; he was developing a **methodology** for effective AI collaboration.

His heuristics, synthesized from experts like Federico Feroldi (Goal Heuristic), Uberto Barbini (One-Prompt-One-Commit), and Andrej Karpathy (Ask For Options), described exactly the workflow patterns I'd been discovering through trial and error:

- **Goal Heuristic**: State desired outcomes, let AI iterate ("make it build" vs "fix this error")
- **Ask For Options**: Request multiple approaches before implementing
- **One-Prompt-One-Commit**: Create checkpoints after each successful task
- **Manage Context**: Monitor context window usage, restart before degradation

Reading Matteo's work was transformative. But he was focused on **how to work** with AI. I still had the problem of **what to teach** it.

That's when Matteo's references led me to [Harper Reed's dotfiles](https://github.com/harperreed/dotfiles/tree/master/.claude). Harper had solved the configuration problem in a brilliantly simple way: **teach the AI once, reuse everywhere**.

Harper's approach: modular configuration files that encode patterns, conventions, and workflows. The AI loads the relevant expertise based on project context.

**This was the missing piece.** Matteo showed me the methodology. Harper showed me the architecture.

## The Solution: Modular Skills

The core idea is deceptively simple: instead of putting all your instructions in a single, monolithic `~/.claude/CLAUDE.md` file, break them into **modular, reusable skills** that auto-invoke based on your project context.

Think of it as giving Claude a library of specialized expertise that it can reference when needed.

Here's what I built:

```
skills/
├── _AST_GREP.md      # Universal code search patterns
├── _INDEX.md         # Smart navigation router
├── _PATTERNS.md      # Cross-language architectural patterns
├── golang/           # Complete Go development guidelines
├── python/           # Python with uv, type checking, Docker
├── rails/            # Service-oriented Rails architecture
├── terraform/        # Terraform/Terragrunt IaC patterns
├── source-control/   # Git workflow, conventional commits
└── project-analyzer/ # Codebase analysis
```

Each skill is a standalone markdown file containing:

1. **Language-specific idioms** (how to structure a Go service, Python's dependency injection)
2. **Architectural patterns** (Repository pattern, SWR caching, Service Objects)
3. **Tool-specific workflows** (ast-grep for code search, pre-commit hook protocols)
4. **Non-obvious knowledge** (gotchas that require reading multiple files to understand)

The skills are installed in `~/.claude/skills/` and referenced in your global `~/.claude/CLAUDE.md`:

```markdown
# Skills
**Core:** golang, python, rails, terraform
**Utilities:** _INDEX.md, _AST_GREP.md, _PATTERNS.md
**Support:** source-control, project-analyzer
```

When Claude works on a Go project, the `golang/` skill loads automatically. When it needs to search code, `_AST_GREP.md` enforces the use of ast-grep over grep. The AI becomes context-aware, loading only the expertise it needs.

## Implementing Matteo's Heuristics: From Methodology to Skills

Reading Matteo's series gave me the "how" of AI collaboration. But here's what I realized: **heuristics are useless if you have to remember to apply them**.

So I built them directly into the skills system, ensuring that both Claude and I follow them automatically.

### Three Layers of Heuristic Implementation

**1. Global CLAUDE.md - Workflow Heuristics**

The universal collaboration patterns went into the global config as an "AI Collaboration Heuristics" section:

- **Ask For Options Heuristic** (Andrej Karpathy): Request multiple approaches before implementing
- **Goal Heuristic** (Federico Feroldi): State outcomes, let AI iterate to solve cascading issues
- **Iteration Heuristic**: Critically analyze outputs, don't accept first results
- **Break the Loop Heuristic**: Intervene when AI gets stuck repeating failures
- **Let the AI Do the Testing Heuristic**: Have AI verify its own work with tools
- **One-Prompt-One-Commit** (Uberto Barbini): Commit after each successful task
- **Manage Context Heuristic**: Monitor context window, clear before hitting 70-80%

These apply to every project, regardless of language or framework.

**2. _PATTERNS.md - Testing Heuristics**

The testing principles went into cross-language patterns because they apply universally:

- **Observable Design Heuristic**: Make small production changes to improve testability (often improves UX too)
- **Multiple Test Cases Heuristic**: If you only have one test, you've missed interesting behavior
- **Testing Important Things Heuristic**: Focus on business outcomes, not implementation details
- **Avoid Change Detector Test Heuristic**: Tests should survive refactoring

Each heuristic includes examples in Go, Python, and Rails showing the anti-pattern and the correct approach.

**3. Language & Project Skills - Specific Heuristics**

Some heuristics needed language-specific implementations:

**Makefile Heuristic** (golang/, python/ skills):
Matteo showed how a Makefile prevents AI from guessing commands or using ineffective shortcuts like `docker-compose restart` when rebuild is needed.

I added Makefile templates to both Go and Python skills with standardized targets:
```makefile
# Go
make fmt lint test build

# Python
make fmt lint typecheck test
```

**Project Modernization Heuristics** (project-analyzer/ skill):
For legacy modernization work, I added Matteo's strategic heuristics:

- **Plan-Before-You-Code**: Get multiple migration strategies before implementing
- **Goal Heuristic**: "Make it build" instead of "Fix this specific error"
- **Run-Locally Heuristic**: Get it running locally first for fast feedback
- **Value First Heuristic**: Port high-value features first, not infrastructure
- **Team Sport Heuristic**: Involve domain experts, don't rely on code alone

### The Meta-Heuristic: Get The AI To Program Itself

The most powerful heuristic is meta: **delegate documentation to the AI**.

Instead of manually writing CLAUDE.md files for new projects, I tell Claude:
> "Analyze this codebase and generate comprehensive CLAUDE.md documentation following the patterns in project-analyzer/SKILL.md"

The AI produces better documentation than I would write manually because:
1. It's more thorough (doesn't skip "obvious" things)
2. It's more consistent (follows templates exactly)
3. It's faster (minutes vs hours)
4. It updates itself when asked

This approach applies to all documentation: ADRs, API specs, migration plans. Describe the outcome, let the AI generate it.

### Why This Matters

Before implementing these heuristics, I *knew* I should ask for options, manage context, and test business outcomes. But in the flow of work, I'd forget. I'd accept the first solution. I'd let context bloat to 90%. I'd write change detector tests.

Now the skills enforce these practices automatically. When Claude starts a task, it knows to ask for options. When tests fail, it knows to focus on business outcomes. When approaching context limits, it knows to compact or restart.

**The heuristics became muscle memory for the AI and, by extension, for me.**

## The Architecture: How Skills Work

The skills system has three layers:

### 1. Global CLAUDE.md (Foundation)
Your `~/.claude/CLAUDE.md` sets the universal rules:
- Interaction style and personality
- Cross-project code philosophy
- Git workflow rules (NEVER use `--no-verify`)
- TDD requirements
- AI Collaboration Heuristics

### 2. Skills (Domain Expertise)
Each skill provides language/framework-specific guidance:
- `golang/` - Go idioms, concurrency patterns, testing strategies, Makefile
- `python/` - uv package manager, type checking, Lambda best practices, Makefile
- `rails/` - Service Objects, Dry-validation, Sidekiq patterns
- `terraform/` - Module design, state management, Terragrunt

### 3. Utilities (Cross-Cutting Concerns)
- `_AST_GREP.md` - Mandates ast-grep for code search (never grep/ripgrep)
- `_INDEX.md` - Routes Claude to the right skill by task/language
- `_PATTERNS.md` - Shows same pattern across multiple languages, includes Testing Heuristics

**Example workflow:**

1. You ask: "Find all function calls to `fetchUser` in this Go codebase"
2. `_INDEX.md` routes to `_AST_GREP.md`
3. `_AST_GREP.md` says: "MUST use ast-grep, not grep"
4. Claude runs: `sg -p 'fetchUser($$$)' --lang go`

No explanation needed. The skill encodes the institutional knowledge.

## Real Examples from Production

Let me show you how this works in practice with concrete examples from the two projects I built.

### Example 1: Security Refactoring in Go

When building the Wishew Outpost API, I needed to refactor all SQL queries from `fmt.Sprintf` to parameterized queries. This is a security best practice, but it's also tedious and error-prone.

**Before skills**, I would have had to explain:
- Why parameterized queries matter
- How PostgreSQL positional parameters work ($1, $2, etc.)
- The exact refactoring pattern
- How to update tests

**With the `golang/` skill**, I just said: "Refactor all queries to use parameterized execution."

The skill contains this pattern:

```markdown
## Security: SQL Injection Prevention

**Anti-Pattern (SQL Injection Risk):**
```go
// AVOIDED - SQL injection vulnerability
query := fmt.Sprintf("SELECT * FROM users WHERE id = %d", userID)
db.Query(query)
```

**Correct Pattern (Parameterized Queries):**
```go
// CURRENT - Safe parameterized execution
query := "SELECT * FROM users WHERE id = $1"
db.Query(query, userID)
```

**Benefits:**
- Prevents SQL injection attacks
- Query plan caching by PostgreSQL
- Type safety through driver
```

Claude immediately understood the pattern, refactored all 7 query methods (some with up to 11 parameters), and even caught a mismatch I had missed in the tests. The skill provided the context; I just pointed at the problem.

### Example 2: Dependency Injection in Python

For the Notification Manager Lambda, I wanted to avoid global singletons and implement proper dependency injection. This is an architectural shift that requires touching multiple files.

**Before skills**: Multi-hour conversation explaining SOLID principles, singleton anti-patterns, and how to structure AWS Lambda handlers for testability.

**With the `python/` skill**: "Implement this using dependency injection, no singletons."

The skill encodes the exact pattern:

```markdown
## Dependency Injection Pattern

**Anti-Pattern (Global Singleton):**
```python
# config.py - AVOIDED
_settings = None
def get_settings():
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
```

**Correct Pattern (Constructor Injection):**
```python
# handler.py - CURRENT
def handler(event, context):
    # Create dependencies at entry point
    settings = Settings()
    db_service = DatabaseService(settings)
    ses_service = SESService(settings)

    # Inject explicitly
    process_notifications(db_service, ses_service)
```

**Benefits:**
- Easy to test with mocked dependencies
- No global state
- Clear dependency graph
- Follows SOLID principles
```

Claude implemented the entire service architecture with proper DI, created matching test fixtures, and even suggested improvements to the connection pooling strategy. The skill gave it the architectural foundation; I just described the business logic.

### Example 3: Cross-Language Error Handling with Testing Heuristics
The real power emerged when I started using `_PATTERNS.md` for patterns that apply across multiple languages. For example, both projects needed robust error handling that follows the **Testing Important Things Heuristic** (focus on outcomes, not implementation).

**Go (Outpost API):**
```go
// Nested error handling preserves original error
if err := fetchData(); err != nil {
    logger.Error("fetch failed", "error", err)

    // Try to update cache, but don't mask original error
    if cacheErr := updateCache(); cacheErr != nil {
        logger.Error("cache update failed", "error", cacheErr)
    }

    return fmt.Errorf("fetch data: %w", err) // Original error preserved
}
```

**Python (Notification Manager):**
```python
# Exception preservation in nested try/except
try:
    ses_service.send_email(...)
    db_service.update_status("sent")
except Exception as e:
    logger.error(f"Send failed: {e}", exc_info=True)

    # Nested try prevents exception masking
    try:
        db_service.update_status("failed", error=str(e))
    except Exception as db_error:
        logger.error(f"DB update failed: {db_error}")

    raise  # Re-raises original 'e', not 'db_error'
```

Same principle, different syntax. By encoding this in `_PATTERNS.md` with the testing heuristics, Claude applies consistent error handling philosophy regardless of the language. It's institutional knowledge, codified.

**The tests focus on business outcomes:**
- Did the order get created?
- Was the email sent?
- Is the error state correct?

Not on implementation details like "was logger.error called twice?"

## Key Learnings

### 1. Token Optimization Is Critical

Skills load into Claude's context window. Every word counts. I spent hours condensing my `golang/` skill from a verbose tutorial into dense, example-driven documentation:

**Bad (verbose):**
```markdown
When writing tests in Go, it's important to separate unit tests
from integration tests. Unit tests should be fast and not require
external dependencies like databases. Integration tests, on the
other hand, need real databases and should be tagged separately...
```

**Good (dense):**
```markdown
## Testing Strategy

**Unit tests:** Fast, no DB, default `go test`
**Integration tests:** Real DB, tagged `//go:build integration`

Run separately:
- `go test ./...` (unit only)
- `go test -tags=integration ./...` (integration)
```

From 50 words to 20. Same information, 60% fewer tokens.

### 2. Concrete Examples > Generic Advice

Claude learns best from examples, not principles. Compare:

**Generic (useless):**
```markdown
Always validate user input and handle errors properly.
```

**Concrete (actionable):**
```markdown
// Validate input
if userID <= 0 {
    return nil, fmt.Errorf("invalid user ID: %d", userID)
}

// Query with context timeout
ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
defer cancel()
```

The second version gives Claude an exact pattern to follow.

### 3. Cross-Reference Aggressively

Skills should reference each other. My `golang/` skill says:

```markdown
For code search, see _AST_GREP.md.
For error handling patterns across languages, see _PATTERNS.md.
For git workflow, see source-control/.
```

This creates a knowledge graph instead of isolated documents. Claude can navigate between related concepts.

### 4. Skills Complement, Don't Replace, Global Config

I initially tried to put *everything* in skills. Big mistake.

**Global `CLAUDE.md` handles:**
- Your personality preferences ("Address me as Max")
- Universal rules ("NEVER use --no-verify when committing")
- Cross-project philosophy ("Prefer simple over clever")
- AI Collaboration Heuristics

**Skills handle:**
- Language-specific idioms
- Framework-specific patterns
- Tool-specific workflows
- Domain-specific heuristics (Makefile, Testing, Modernization)

The global config sets the foundation. Skills provide domain expertise.

### 5. The "Summer Work Ethic" Works (Thanks, Harper)

Harper Reed had a rule in his CLAUDE.md that I adopted immediately: "Work efficiently to maximize vacation time: hard work now = more vacation later."

It sounds absurd. You're telling an AI to work hard so *you* can go on vacation. But it's genius.

Framing productivity as a means to an end (vacation!) genuinely changes how Claude approaches problems. It works harder upfront to avoid rework later. It's more thorough with tests. It's less likely to suggest shortcuts that create technical debt.

Why does this work? Because AI models are trained on human text where "work hard now for future reward" is a common motivational frame. By anchoring the work to a concrete, positive outcome (vacation), the AI optimizes for thoroughness over speed.

Anthropomorphizing? Absolutely. Effective? Also absolutely.


## When Your AI Becomes Your Institutional Memory

Here's something unexpected: these skills aren't just for Claude. They've become documentation for our human team.

When a new developer joins Wishew, I can point them to the `golang/` skill and say, "This is how we structure services." When someone asks, "Why do we use ast-grep instead of grep?", the answer is in `_AST_GREP.md` with examples.

The skills are living documentation that both humans and AI can reference. They encode the "why" and the "how" in a format that's useful for both audiences.

More importantly, they force me to codify patterns I've internalized. Writing the `python/` skill made me realize I have strong opinions about dependency injection that I'd never articulated. Creating `_PATTERNS.md` revealed that my error handling philosophy is consistent across languages; I just hadn't named it before.

Teaching an AI made me a better teacher for humans.

## The Road Ahead: A Pattern Library for the Community

This skills collection started as a personal tool, but I'm open-sourcing it at [github.com/maroffo/claude-forge](https://github.com/maroffo/claude-forge).

The next steps:

1. **More Language Skills**: Adding skills for JavaScript/TypeScript, Rust, and Kotlin
2. **Framework-Specific Patterns**: Deeper dives into Rails, Django, FastAPI, NestJS
3. **Tool-Specific Workflows**: Skills for Docker, Kubernetes, CircleCI, GitHub Actions
4. **Community Contributions**: Accepting PRs for new skills and pattern improvements

The vision is to create a **community-driven pattern library** where developers can share their institutional knowledge in a format that's useful for both AI assistants and human developers.

Imagine:
- A `security/` skill with OWASP Top 10 patterns across languages
- A `performance/` skill with profiling and optimization strategies
- An `accessibility/` skill with WCAG compliance patterns

Each skill, token-optimized, example-driven, and battle-tested in production.

## Conclusion

Building software with AI isn't about asking it to write code. It's about teaching it your patterns first.

Over the past few weeks, I've gone from repeating the same instructions in every conversation to having a modular, reusable knowledge base that makes Claude a genuinely effective pair programmer. The skills system has:

- **Saved countless hours** of re-explaining the same patterns
- **Improved code consistency** across Go and Python projects
- **Codified institutional knowledge** that benefits both AI and humans
- **Forced me to articulate** architectural decisions I'd internalized
- **Systematized AI collaboration heuristics** so they become automatic, not manual

The key insights:

1. **Modular beats monolithic**: break skills into focused, reusable files
2. **Token optimization matters**: every word in a skill costs context
3. **Examples over principles**: show, don't tell
4. **Cross-reference aggressively**: build a knowledge graph, not isolated docs
5. **Skills complement global config**: foundation vs. domain expertise
6. **Heuristics must be automatic**: encode methodology into the system itself

Whether you're managing two projects or twenty, building a skills library transforms AI from a helpful assistant into a true pair programmer that knows your patterns, your philosophy, and your institutional knowledge.

Want to try it yourself? Check out the [claude-forge repository](https://github.com/maroffo/claude-forge) for the full skills collection and installation instructions.

## Acknowledgments

This system wouldn't exist without standing on the shoulders of giants:

**Matteo Vaccari** - His [series on AI-assisted modernization](https://matteo.vaccari.name/posts/ai-assisted-modernization-of-java-part-i/) provided the methodological foundation. The heuristics he synthesized from Federico Feroldi, Uberto Barbini, Andrej Karpathy, and others transformed how I think about AI collaboration.

**Harper Reed** - His [Claude dotfiles](https://github.com/harperreed/dotfiles/tree/master/.claude) were the architectural inspiration. Seeing his approach to modular AI configuration was the lightbulb moment.

**Federico Feroldi, Uberto Barbini, Andrej Karpathy** - For their contributions to AI collaboration methodology that Matteo documented and I've encoded into reusable skills.

**The Wishew Team** - For giving me the space to experiment with AI-assisted development and the real-world projects to test these patterns in production.

And a special thanks to **Claude itself**: for being patient while I figured out how to teach it, and for occasionally suggesting improvements to the very skills I was writing to teach it. Meta.

---

**Tools & References:**

- [Claude Code](https://claude.ai/code) - The AI pair programmer
- [claude-forge](https://github.com/maroffo/claude-forge) - The open-source skills collection
- [ast-grep](https://ast-grep.github.io/) - Structural code search tool
- [Harper Reed's dotfiles](https://github.com/harperreed/dotfiles/tree/master/.claude)
- [Matteo Vaccari's AI-assisted modernization series](https://matteo.vaccari.name/posts/ai-assisted-modernization-of-java-part-i/)
- [All the heuristics summary](https://matteo.vaccari.name/posts/ai-assisted-java-modernization-all-the-heuristics/)

This skills system was built for my work at Wishew but is applicable to any development workflow. The repository includes skills for Go, Python, Rails, Terraform, and cross-language patterns.

---

*Massimiliano Aroffo is a Cloud Engineer and Architect at Wishew, where he builds infrastructure automation and occasionally teaches AIs how to write better code than him.*


Credit: Armin Ronacher and Shrivu Shankar
