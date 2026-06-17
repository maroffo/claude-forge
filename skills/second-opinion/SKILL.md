---
name: second-opinion
description: "Get three independent second opinions (isolated Claude + isolated Gemini + isolated DeepSeek) on a problem Claude is analyzing. Use when user says second opinion, ask gemini, ask deepseek, what does gemini think, another perspective, or /second-opinion. Gathers context, writes a focused prompt, calls all reviewers in isolated Docker containers, and synthesizes all viewpoints. Not for code review (use gemini-review)."
compatibility: "Requires Docker running, claude-reviewer:latest, gemini-reviewer:latest and deepseek-reviewer:latest images built, OAuth volume for Claude, API key files for Gemini and DeepSeek."
---

# ABOUTME: Three independent second opinions from isolated Docker containers (Claude + Gemini + DeepSeek)
# ABOUTME: Same prompt/context to all, zero config contamination, four-way synthesis

# Second Opinion (Isolated)

All reviewers run in Docker containers with NO access to your `~/.claude/` config,
memories, rules, or settings. This ensures genuinely independent opinions. The three
reviewers span three labs (Anthropic, Google, DeepSeek), so agreement across them is a
strong signal rather than shared-model bias.

## Prerequisites

Images built and auth configured:
- `claude-reviewer:latest` (built from `claude-forge/docker/isolated-reviewer/`)
- `gemini-reviewer:latest` (built from `claude-forge/docker/isolated-gemini/`)
- `deepseek-reviewer:latest` (built from `claude-forge/docker/isolated-deepseek/`)
- Docker volume `claude-reviewer-auth` (populated via `docker run -it --rm -v claude-reviewer-auth:/home/node/.claude --entrypoint bash claude-reviewer:latest -c "claude login"`)
- API key file at `~/.config/gemini-api-key`
- API key file at `~/.config/deepseek-api-key`

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

### Step 4: Call all reviewers in parallel

Launch all containers simultaneously using **parallel Bash tool calls in a single message**.

Credentials never touch the host filesystem: Claude auth is mounted directly from
the Docker volume, Gemini and DeepSeek API keys are read in-memory from files.

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

Call 3 - Isolated DeepSeek (pi):
```bash
docker run --rm \
  -e DEEPSEEK_API_KEY="$(cat ~/.config/deepseek-api-key)" \
  -v <PROJECT_ROOT>:/workspace:ro \
  deepseek-reviewer:latest \
  --provider deepseek \
  --model deepseek-reasoner \
  -p \
  -t read \
  --no-session \
  "$(cat <PROMPT_FILE>)"
```

**Cleanup after all complete:**
```bash
rm -f "$PROMPT_FILE"
```

**Degrade gracefully on reviewer failure.** A reviewer can fail independently:
expired Claude OAuth in the volume (`401`), a missing/invalid API key, a rate
limit, or a hang (each `docker run` is bounded by the Bash-tool timeout). If one
reviewer errors, do NOT abort: proceed to synthesize from the reviewers that did
respond and explicitly flag which one is missing and why. A two-of-three synthesis
is still useful; a silent drop is not. If Claude returns `401`, surface the
re-login command from Troubleshooting.

### Step 5: Synthesize

Present a four-way analysis:

| Aspect | Claude (you) | Isolated Claude | Isolated Gemini | Isolated DeepSeek | Consensus |
|--------|-------------|-----------------|-----------------|-------------------|-----------|
| Root cause | ... | ... | ... | ... | agree/differ |
| Approach | ... | ... | ... | ... | agree/differ |
| Risks | ... | ... | ... | ... | complementary |

**Final recommendation:** Your updated position, incorporating all independent opinions.
Explain what changed (or didn't) and why. Flag any point where the independent
reviewers agree against your original analysis (the more of the three that agree, the
stronger the signal to reconsider).

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
| Gemini "not running in a trusted directory" | Image predates the trust fix. Rebuild: `docker/isolated-gemini/isolated-gemini-review.sh --build` (the Dockerfile sets `GEMINI_CLI_TRUST_WORKSPACE=true`) |
| DeepSeek "No API key found" | Check `~/.config/deepseek-api-key` exists and is valid; it is passed as `DEEPSEEK_API_KEY` |
| DeepSeek image not found | Build it: `docker/isolated-deepseek/isolated-deepseek-review.sh --build` |
| Timeout | Reduce context size; focus on the most relevant files |
| Both reviewers agree you're wrong | You're probably wrong. Reconsider. |
