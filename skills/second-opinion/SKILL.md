---
name: second-opinion
description: "Get two independent second opinions (isolated Claude + isolated Gemini) on a problem Claude is analyzing. Use when user says second opinion, ask gemini, what does gemini think, another perspective, or /second-opinion. Gathers context, writes a focused prompt, calls both reviewers in isolated Docker containers, and synthesizes all viewpoints. Not for code review (use gemini-review)."
compatibility: "Requires Docker running, claude-reviewer:latest and gemini-reviewer:latest images built, OAuth volume for Claude, API key file for Gemini."
---

# ABOUTME: Two independent second opinions from isolated Docker containers (Claude + Gemini)
# ABOUTME: Same prompt/context to both, zero config contamination, three-way synthesis

# Second Opinion (Isolated)

Both reviewers run in Docker containers with NO access to your `~/.claude/` config,
memories, rules, or settings. This ensures genuinely independent opinions.

## Prerequisites

Images built and auth configured:
- `claude-reviewer:latest` (built from `claude-forge/docker/isolated-reviewer/`)
- `gemini-reviewer:latest` (built from `claude-forge/docker/isolated-gemini/`)
- Docker volume `claude-reviewer-auth` (populated via `docker run -it --rm -v claude-reviewer-auth:/home/node/.claude --entrypoint bash claude-reviewer:latest -c "claude login"`)
- API key file at `~/.config/gemini-api-key`

## Execution Flow

### Step 1: Understand the problem

Before calling reviewers, clearly articulate:
1. **The problem** - what is being analyzed or decided
2. **Your current analysis** - what you think so far
3. **Relevant context** - code snippets, error messages, architecture constraints
4. **Specific question** - what you want a second opinion on

### Step 2: Gather context

Collect all relevant material:
- Read the files involved (full content, not summaries)
- Include error messages/stack traces if debugging
- Include project constraints (from CLAUDE.md, architecture docs)
- Include what has been tried and why it didn't work (if applicable)

### Step 3: Build the prompt

Load the prompt template:

```bash
PROMPT_TEMPLATE=$(cat ~/.claude/skills/second-opinion/prompts/default.md)
```

Compose a `FULL_PROMPT` combining the template with a `## Problem Context` section containing:
- Problem description
- Your current analysis/hypothesis
- All gathered context (code, errors, docs)
- The specific question for the reviewer

The FULL_PROMPT must be identical for both reviewers. Write it to a temp file:

```bash
PROMPT_FILE=$(mktemp)
cat > "$PROMPT_FILE" <<'PROMPT_EOF'
<the composed prompt here>
PROMPT_EOF
```

### Step 4: Call both reviewers in parallel

Launch both containers simultaneously using **two parallel Bash tool calls in a single message**.

Credentials never touch the host filesystem: Claude auth is mounted directly from
the Docker volume, Gemini API key is read in-memory from a file.

Call 1 - Isolated Claude:
```bash
docker run --rm \
  -v claude-reviewer-auth:/home/node/.claude:ro \
  -v <PROJECT_ROOT>:/workspace:ro \
  claude-reviewer:latest \
  --print \
  --model opus \
  "$(cat <PROMPT_FILE>)"
```

Call 2 - Isolated Gemini:
```bash
docker run --rm \
  -e GEMINI_API_KEY="$(cat ~/.config/gemini-api-key)" \
  -v <PROJECT_ROOT>:/workspace:ro \
  gemini-reviewer:latest \
  -p "$(cat <PROMPT_FILE>)" \
  -m gemini-3.1-pro-preview \
  --sandbox false \
  2>&1 | grep -v "^\[WARN\] Skipping unreadable" | grep -v "^Warning: Could not read"
```

**Cleanup after both complete:**
```bash
rm -f "$PROMPT_FILE"
```

### Step 5: Synthesize

Present a three-way analysis:

| Aspect | Claude (you) | Isolated Claude | Isolated Gemini | Consensus |
|--------|-------------|-----------------|-----------------|-----------|
| Root cause | ... | ... | ... | agree/differ |
| Approach | ... | ... | ... | agree/differ |
| Risks | ... | ... | ... | complementary |

**Final recommendation:** Your updated position, incorporating both independent opinions.
Explain what changed (or didn't) and why. Flag any point where both independent
reviewers agree against your original analysis (strong signal to reconsider).

## When to Use

- Stuck on a debugging problem
- Weighing architectural trade-offs
- Unsure about root cause analysis
- Want to validate an approach before implementing
- Complex decisions with multiple valid paths

## When NOT to Use

- Code review before commit (use `gemini-review`)
- Simple, well-understood problems
- When you just need to read more code/docs first

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "docker: command not found" | Docker Desktop must be running |
| Image not found | Build images: see Prerequisites |
| Claude auth fails | Re-login: `docker run -it --rm -v claude-reviewer-auth:/home/node/.claude --entrypoint bash claude-reviewer:latest -c "claude login"` |
| Gemini API errors | Check `~/.config/gemini-api-key` exists and is valid |
| Timeout | Reduce context size; focus on the most relevant files |
| Both reviewers agree you're wrong | You're probably wrong. Reconsider. |
