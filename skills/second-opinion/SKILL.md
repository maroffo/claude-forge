---
name: second-opinion
description: "Get three independent second opinions (isolated Claude + isolated Gemini + isolated DeepSeek) on a problem Claude is analyzing. Use when user says second opinion, another perspective, challenge this approach, or asks gemini/deepseek about a decision, approach, or diagnosis. Gathers context, writes a focused prompt, calls all reviewers in isolated Docker containers, and synthesizes all viewpoints. Not for reviewing code or changes, even phrased as 'ask gemini to review' (use gemini-review)."
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

**Set an explicit Bash-tool timeout per call.** These `docker run` commands are inline,
not the `.sh` scripts, so the only wall-clock bound is the Bash-tool `timeout`. The default
(120s) will kill `deepseek-reasoner` mid-reasoning. Pass `timeout: 600000` (600s) for the
DeepSeek call and at least `timeout: 300000` for Claude and Gemini.

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

**Cleanup.** Set the trap right after creating the temp file in Step 3, so it is
removed even if a call times out before this point is reached:
```bash
trap 'rm -f "$PROMPT_FILE"' EXIT
```

**Degrade gracefully on reviewer failure. This is a procedure, not a suggestion.**
A reviewer can fail independently: expired Claude OAuth in the volume (`401`), a
missing/invalid API key, a rate limit, or a timeout.

1. **Classify each reviewer as OK or FAILED** before synthesizing. A reviewer is
   FAILED if its Bash call exited non-zero OR its output matches `401`,
   `timed out`, `API Error`, `No API key`, or is empty. Do NOT treat a `401`
   body or an error trace as if it were an opinion.
2. **Never abort if at least one reviewer is OK.** Synthesize from the survivors.
   A two-of-three (or one-of-three) synthesis is useful; a silent drop is not.
3. **Account for every reviewer in the output** via the status line in Step 5.
4. If Claude returns `401`, surface the re-login command from Troubleshooting.

### Step 5: Synthesize

**Required first line: reviewer status.** Before the table, state which reviewers
responded, so a missing one can never be glossed over:

```
Reviewer status: Claude ✅ | Gemini ✅ | DeepSeek ❌ (401, expired OAuth; see Troubleshooting)
```

Then present a four-way analysis (drop the column of any FAILED reviewer):

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
| Claude `401` recurs across runs | The OAuth token in the volume expires periodically. Optional preflight before a run: `docker run --rm -v claude-reviewer-auth:/home/node/.claude:ro claude-reviewer:latest --print "ping"`; a non-zero/`401` means re-login first. Skip it for speed; structured degradation (Step 4) handles a mid-run `401` anyway. |
| Gemini API errors | Check `~/.config/gemini-api-key` exists and is valid |
| Gemini "not running in a trusted directory" | Image predates the trust fix. Rebuild: `docker/isolated-gemini/isolated-gemini-review.sh --build` (the Dockerfile sets `GEMINI_CLI_TRUST_WORKSPACE=true`) |
| DeepSeek "No API key found" | Check `~/.config/deepseek-api-key` exists and is valid; it is passed as `DEEPSEEK_API_KEY` |
| DeepSeek image not found | Build it: `docker/isolated-deepseek/isolated-deepseek-review.sh --build` |
| Timeout | Reduce context size; focus on the most relevant files |
| Both reviewers agree you're wrong | You're probably wrong. Reconsider. |
