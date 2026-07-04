# ABOUTME: Mauro Medda's tone of voice, extracted from his published posts (mauro.medda.xyz)
# ABOUTME: Voice traits, register skeletons, signature phrases, and a pre-publish checklist

# Mauro's Tone of Voice

Extracted 2026-07-02 from 5 published posts in the `Mauro-Blog/` vault folder: Hello World (2025-11-10), Coding with AI Part I (2025-11-11), The Marathon Mindset (2026-01-03), Compile llama.cpp on DGX Spark (2026-02-07), Qwen3 quantization on DGX Spark (2026-02-07).

## Who is writing

Mauro Medda: co-founder at HikmaAI (AI security), endurance athlete (training is "a moving meditation"), husband and father, hands-on homelab guy (DGX Spark Founders Edition). Calls his Claude agent "Claudio". Topics: AI and security, entrepreneurship, developer workflows, local LLM inference, sustainable founder life. Handle: deftunix.

## Core traits (both registers)

- **Direct reader address.** Second person constantly, sometimes confrontational in a friendly way: "I know you've been here. Don't lie."
- **Short punchy fragments** mixed with longer explanatory sentences: "They're powerful. They're smart. You throw a problem at them... and they actually solve it."
- **Rhetorical question, then blunt answer:** "It's productive, right? Except it's not sustainable."
- **Contrast pairs as verdicts:** "That's not leadership. That's hypocrisy." / "Not talking about it. Doing it." / "This isn't soft. It's strategic."
- **"Here's the..." openers:** "Here's the uncomfortable truth:", "Here's what I've learned:", "Here's the catch:", "Here's the reframe:".
- **Concrete numbers, bolded:** "**72% of founders experience burnout**", "**273 GB/s** of memory bandwidth". Never bold vague claims.
- **Personal life woven in without ceremony:** wife, daughter, training, "probably more than I spend talking to real people (yes, including my wife)".
- **Casual asides in parentheses**, small jokes, occasional slang: "w00t moment", "code monkeys", "ship it and pray", "enjoy your toy".
- **Italics for the conceptual pivot word:** teach it *how to think*, it *fails* at complexity, what makes you *capable*.
- **One-line paragraphs for emphasis.** Frequent.
- **Warm, optimistic ground note.** Even when naming failure or hypocrisy, the ending reframes toward agency: "Build hard, but build to last."

## Register 1: founder essay

Examples: The Marathon Mindset, Coding with AI Part I.

Skeleton:
1. **Hook**: vivid metaphor or shared-pain scene in second person ("Building a startup in 2025 feels like running a marathon at sprint pace on terrain that's constantly shifting under your feet.").
2. **The uncomfortable truth**: name the myth or trap, back it with 2-4 bolded statistics with real sources.
3. **Personal turn**: "Over the past months, I've been experimenting...", what he tried, what failed.
4. **Numbered practices or pillars** (`### 1.`, `### 2.`): each one concrete, justified with a mechanism (neuroscience, ultradian rhythms, memory bandwidth), not authority.
5. **Naming his own hypocrisy or limits**: he includes himself in the critique.
6. **The reframe**: recap as a mindset shift with a bulleted "requires" list, then a two-sentence closing punch.
7. Sign-off: `— Mauro` on its own line.

Endings never summarize; they reframe. No "in conclusion".

## Register 2: technical how-to

Examples: the two DGX Spark posts.

Skeleton:
1. **Scope statement up front**: "No fluffy information, no fancy images. Just a set of shell commands that you might want to copy and paste."
2. **Skip link** for impatient readers ("If you just want the install steps, skip to section 3").
3. **Context sections** (formats, why this tool): bold-led definition lists ("**GGUF (`.gguf`)** ... This is the format you want."), then a summary table.
4. **Numbered steps**: every command in a fenced block, expected output shown, one-line justification per flag ("Don't skip this.", "Old-school, works every time.").
5. **Decision matrix table** + **"Golden Rules"** with bold imperatives ("Rule 1: Use the highest quant that fits.").
6. **Terse closer, no sign-off**: "That's it. ... Go download a model and start generating tokens." or "– enjoy your toy".

He links his own previous posts explicitly when a post is a follow-up.

## Vocabulary

Favors: uncomfortable truth, the catch, the reframe, compounding, sustainable, deep work, ship, iterate, "the key insight", "the key number", "what separates X from Y".

Avoids (enforce these): corporate hedging, "in today's fast-paced world", marketing adjectives, translated technical terms, neutral both-sides reporting, padding.

## Divergences from Max's blog-writer style (do NOT import these)

- No `***` separators between blocks; Mauro uses `---` rarely and plain `##` headings.
- No methodology note, no acknowledgments section, no author-context footer.
- No cover images; posts are text plus code plus tables.
- Warmer and more second-person than Max; Max is more self-ironic and evidence-citation heavy, Mauro is more coach-like.
- Essays sign off `— Mauro`; how-tos just stop.

## Em dash policy

Mauro's originals use em dashes constantly. Drafts do NOT (humanizer hard rule + house style). Reproduce the rhythm with the tools he also uses: periods and fragments, colons, parentheses. His contrast-pair pattern survives intact without dashes.

## Pre-publish voice checklist

- [ ] Reader addressed as "you" within the first two paragraphs
- [ ] At least one "Here's the..." pivot
- [ ] At least one contrast pair ("This isn't X. It's Y.")
- [ ] Every bolded claim is a concrete number or a rule imperative
- [ ] Essay: stats sourced, numbered practices, reframe ending, `— Mauro`
- [ ] How-to: scope statement, commands with expected output, table, terse closer
- [ ] Zero em dashes, zero "in conclusion", zero marketing adjectives
- [ ] Read aloud: does it sound like a sharp friend talking, not a report?
