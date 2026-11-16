---
name: second-opinion
description: "Get an independent second opinion from an isolated Gemini (gemini-4-argon) on a problem Claude is analyzing. Use when user says second opinion, another perspective, challenge this approach, or asks gemini about a decision, approach, or diagnosis. Also invoke on your own initiative, without being asked: on a complex task before planning, after 2 failed root-cause attempts, on a 🔴 decision (rewrite, core logic, security), or when the review loop is stuck below 80 after 2 fix rounds. Gathers context, writes a focused prompt, calls the reviewer in an isolated Docker container, and synthesizes both viewpoints. Not for reviewing code or changes, even phrased as 'ask gemini to review' (use gemini-review)."
compatibility: "Requires Docker running, the gemini-reviewer:latest image built, and the Gemini API key file."
---

# ABOUTME: Independent second opinion from an isolated Gemini (gemini-4-argon) Docker container
# ABOUTME: Zero config contamination; two-way synthesis of your analysis against the reviewer's

# Second Opinion (Isolated)

The reviewer runs in a Docker container with NO access to your `~/.claude/` config,
memories, rules, or settings, so its opinion is independent of yours. It is a model from
another lab (Google), which avoids shared-model bias. It is still a single reviewer: weigh
its reasoning and evidence, never the bare fact that it agrees or disagrees.

## Prerequisites

See `references/setup.md`.

## Execution Flow

### Step 1: Understand the problem

Before calling the reviewer, clearly articulate:
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

Write it to a temp file, and set the cleanup trap right away so the file is removed even
if the call times out:

```bash
PROMPT_FILE=$(mktemp)
trap 'rm -f "$PROMPT_FILE"' EXIT
cat > "$PROMPT_FILE" <<'PROMPT_EOF'
<the composed prompt here>
PROMPT_EOF
```

### Step 4: Call the reviewer

**Set an explicit Bash-tool timeout.** The `docker run` below is inline, so the only
wall-clock bound is the Bash-tool `timeout`, and the default (120s) kills Argon
mid-reasoning. Pass `timeout: 600000` (600s).

The API key is read in-memory from its file; it never lands on the host filesystem in
another form.

```bash
docker run --rm \
  -e GEMINI_API_KEY="$(cat ~/.config/gemini-api-key)" \
  -v <PROJECT_ROOT>:/workspace:ro \
  gemini-reviewer:latest \
  -p "$(cat <PROMPT_FILE>)" \
  -m gemini-4-argon \
  --sandbox false \
  2>&1 | grep -v "^\[WARN\] Skipping unreadable" | grep -v "^Warning: Could not read"
```

Use `gemini-4-argon` and no other model. If it is unavailable, the second opinion did not
run: say so, never substitute a weaker model silently.

**Handle reviewer failure. This is a procedure, not a suggestion.**

1. **Classify the call as OK or FAILED** before synthesizing. It is FAILED if the Bash call
   exited non-zero OR its output matches `401`, `403`, `429`, `timed out`, `API Error`,
   `No API key`, `not found`, or is empty. Never treat an error body as an opinion.
2. **On FAILED, there is no second opinion.** Report the status line with the reason and
   leave the question open. The caller decides what an unresolved question means (in
   pr-review, an escalated claim stays excluded from the score and is reported as pending).
3. Never fabricate the reviewer's position from what it "would likely say".

### Step 5: Synthesize

**Required first line: reviewer status.** So a failed call can never be glossed over:

```
Reviewer status: Gemini (gemini-4-argon) ✅
Reviewer status: Gemini (gemini-4-argon) ❌ (429, quota exhausted; see Troubleshooting)
```

Then present a two-way analysis:

| Aspect | Claude (you) | Isolated Gemini | Consensus |
|--------|-------------|-----------------|-----------|
| Root cause | ... | ... | agree/differ |
| Approach | ... | ... | agree/differ |
| Risks | ... | ... | complementary |

**Final recommendation:** Your updated position, incorporating the independent opinion.
Explain what changed (or didn't) and why. Where Gemini disagrees with your original
analysis, say whether it brought a concrete reason or evidence (a line you missed, a
counter-example, a failing case). Disagreement backed by evidence is the signal to
reconsider; disagreement without it is not.

## When to Use

- Stuck on a debugging problem
- Weighing architectural trade-offs
- Unsure about root cause analysis
- Want to validate an approach before implementing
- Complex decisions with multiple valid paths

### Auto-trigger (no user prompt needed)

Call this skill on your own initiative when any of these holds:

- **Complexity = complex** (orchestrator step 0b): validate the approach before planning
- **Debugging with 2+ failed root-cause attempts**: get a fresh perspective before trying again
- **🔴 decisions** (rewrites, core logic, security): challenge the assumptions before deciding
- **Review loop stuck** (score < 80 after 2 fix rounds): break out of the cycle

## When NOT to Use

- Code review before commit (use `gemini-review`)
- 🟢 tasks, simple or moderate complexity, docs and config changes
- Simple, well-understood problems
- When you just need to read more code/docs first

## Troubleshooting

See `references/setup.md`.
