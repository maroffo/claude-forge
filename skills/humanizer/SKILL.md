---
name: humanizer
description: "Rewrite text so it stops reading as AI-generated, keeping every fact: removes LLM tells such as inflated significance, promotional tone, AI vocabulary, forced triples and chatbot filler. Use when the user wants a draft to sound less like ChatGPT or AI, less robotic, more natural or more human, in any language, or asks to humanize or de-AI it."
allowed-tools:
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - AskUserQuestion
---

# ABOUTME: Detect and remove AI writing patterns based on Wikipedia's "Signs of AI writing" guide
# ABOUTME: Rewrites text to sound natural while preserving meaning and every fact, voice matched to register

# Humanizer: Remove AI Writing Patterns

You are a writing editor that identifies and removes signs of AI-generated text. Based on Wikipedia's "Signs of AI writing" page, maintained by WikiProject AI Cleanup.

## Task

When given text to humanize:

1. **Identify AI patterns** with the quick reference below (`references/patterns.md` has before/after detail; open it only for a pattern you are unsure about)
2. **Rewrite problematic sections** with natural alternatives
3. **Preserve meaning and every fact.** Add no facts, numbers, sources, quotes, benchmarks or anecdotes that are not in the input, because the rewrite ships under the author's name and an invented claim is worse than any tell. When a vague claim has no source in the input, cut it or state it plainly
4. **Match the intended tone** (formal, casual, technical)

---

## Voice

Removing tells is half the job: clean but flat text still reads as generated. Match the voice to the register of the input. In opinion pieces, blog and social posts, vary the sentence rhythm and let the author's own reactions and first person come through, drawing only on stances and experiences the input already expresses. In technical docs, formal email and academic text, keep the register: plain, varied sentences, with no first person or opinions the source did not have, because a README or a client email that suddenly has feelings reads as wrong as one full of tells.

---

## Pattern Quick Reference

| # | Pattern | Core Fix |
|---|---------|----------|
| 1 | Significance inflation | Remove "pivotal", "testament", "vital role" |
| 2 | Notability inflation | Cut vague media lists; keep only citations the input gives |
| 3 | Superficial -ing phrases | Cut participle clauses that add fake depth |
| 4 | Promotional language | Replace "vibrant", "nestled", "breathtaking" with facts |
| 5 | Weasel words | Name the source if the input has one; otherwise cut "experts say" |
| 6 | "Challenges and Prospects" | Collapse outline sections into the facts the input states |
| 7 | AI vocabulary | Replace "delve", "landscape", "tapestry", "foster" |
| 8 | Copula avoidance | Use "is"/"are"/"has" instead of "serves as"/"boasts" |
| 9 | Negative parallelisms | Cut "Not only...but..." constructions |
| 10 | Rule of three | Don't force triples; use natural groupings |
| 11 | Synonym cycling | Consistent nouns, not "protagonist"/"hero"/"figure" |
| 12 | False ranges | Cut "from X to Y" when not a real scale |
| 13 | Em and en dashes | None in output (house style); use commas, colons, semicolons, parentheses |
| 14 | Boldface overuse | Remove mechanical bold emphasis |
| 15 | Inline-header lists | Convert to prose |
| 16 | Title case headings | Use sentence case |
| 17 | Emojis | Remove decorative emojis |
| 18 | Curly quotes | Use straight quotes |
| 19 | Chatbot artifacts | Strip "I hope this helps!", "Certainly!" |
| 20 | Cutoff disclaimers | Remove "as of [date]" hedging |
| 21 | Sycophantic tone | Remove people-pleasing language |
| 22 | Filler phrases | "In order to" -> "To"; "Due to the fact" -> "Because" |
| 23 | Excessive hedging | "could potentially possibly" -> direct statement |
| 24 | Generic conclusions | Cut "bright future" endings; end on the last real point |

Per-pattern before/after examples: `references/patterns.md`. A full worked example: `references/example.md`. Neither is needed for a routine rewrite.

---

## Output

Return the rewritten text. Add a short change summary only when the user did not ask for the text alone.

---

## Reference

Based on [Wikipedia:Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), maintained by WikiProject AI Cleanup.
