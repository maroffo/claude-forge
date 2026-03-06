---
name: second-opinion
description: "Get a second opinion from Gemini CLI on a problem Claude is analyzing. Use when user says second opinion, ask gemini, what does gemini think, another perspective, or /second-opinion. Gathers context, writes a focused prompt, and synthesizes both viewpoints. Not for code review (use gemini-review)."
compatibility: "Requires Gemini CLI installed and GEMINI_API_KEY in environment."
---

# ABOUTME: Second opinion from Gemini CLI to help Claude analyze problems
# ABOUTME: Gathers context, writes prompt, calls Gemini, synthesizes both viewpoints

# Second Opinion

**MANDATORY: Always use `--model gemini-3.1-pro-preview`. No other model. No fallback. No substitution.**

## Quality Notes

- Invest time in writing a good prompt; garbage in, garbage out
- Include ALL relevant context: files, errors, constraints, what you've tried
- Synthesize thoughtfully; don't just relay Gemini's output

## Execution Flow

### Step 1: Understand the problem

Before calling Gemini, Claude MUST clearly articulate:
1. **The problem** - what is being analyzed or decided
2. **Claude's current analysis** - what Claude thinks so far
3. **Relevant context** - code snippets, error messages, architecture constraints
4. **Specific question** - what Claude wants a second opinion on

### Step 2: Gather context

Collect all relevant material:
- Read the files involved (full content, not summaries)
- Include error messages/stack traces if debugging
- Include project constraints (from CLAUDE.md, architecture docs)
- Include what has been tried and why it didn't work (if applicable)

### Step 3: Build the prompt

Load the prompt template and compose the full request:

```bash
PROMPT=$(cat ~/.claude/skills/second-opinion/prompts/default.md)
```

Claude writes a `CONTEXT` block containing:
- Problem description
- Claude's current analysis/hypothesis
- All gathered context (code, errors, docs)
- The specific question for Gemini

### Step 4: Call Gemini CLI

```bash
cd <project_root>

gemini --model gemini-3.1-pro-preview --yolo <<EOF
$PROMPT

## Problem Context

$CONTEXT
EOF
```

### Step 5: Synthesize

After receiving Gemini's response, Claude presents a unified analysis:

| Aspect | Claude | Gemini | Consensus |
|--------|--------|--------|-----------|
| Root cause | ... | ... | agree/differ |
| Approach | ... | ... | agree/differ |
| Risks | ... | ... | complementary |

**Final recommendation:** Claude's updated position, incorporating Gemini's input where it adds value. Explain what changed (or didn't) and why.

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
| "gemini: command not found" | Install Gemini CLI: see https://github.com/google-gemini/gemini-cli |
| API errors | Check `GEMINI_API_KEY` is set |
| Timeout | Reduce context size; focus on the most relevant files |
| Unhelpful response | Sharpen the specific question; vague asks get vague answers |
