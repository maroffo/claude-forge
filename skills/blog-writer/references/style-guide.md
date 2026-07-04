# ABOUTME: Max's blog voice reference: structure, tone, endings, anti-patterns, length, language
# ABOUTME: Loaded by the blog-writer skill during the Write Draft step and when debugging common issues

# Style Guide (Max's Voice)

## Structure
- **Hook**: personal anecdote, observation, or callback to previous post (1-2 paragraphs)
- **Problem**: concrete problem statement, why it matters now
- **Sections**: 5-9 major sections with `###` headers
- **Separators**: `***` between conceptual blocks (3-6 per post)
- **Tables**: for comparisons, metrics, decision matrices
- **Code blocks**: with language identifiers, real examples from production
- **Bold**: key concepts and definitions only, not mechanical emphasis
- **Links**: `{{< ref "YYYY-MM-DD-slug" >}}` for internal, standard markdown for external

## Tone
- First person throughout ("I wrote", "I realized", "we shipped")
- Conversational but technical; assumes developer audience
- Opinionated with evidence ("This works because..." not "This might work")
- Self-aware humor and irony ("This is what happens when you have an AI that doesn't complain about scope creep")
- Honest about limitations ("I don't have this figured out", "Here's where it broke")

## Endings
- Reflection on what was learned (not generic "bright future")
- Practical next steps for readers (optional)
- `***` separator then methodology note if AI assisted
- Acknowledgments section if citing influences
- Author context (brief, contextual)

## Anti-patterns (never do)
- Generic introductions ("In today's fast-paced world...")
- Listicle-style without narrative thread
- Neutral reporting without opinion
- Padding sections to hit word count
- Concluding with "In conclusion" or summarizing what was just said

## Length
- Technical deep-dives: 2500-4000 words
- Opinion/reflection: 1500-2500 words
- Adjust based on content density; never pad

## Language
- Default: English
- Italian: only if explicitly requested or topic is Italy-specific
- Technical terms: never translate

## Common Issues

| Issue | Solution |
|-------|----------|
| Vault search returns too much | Filter by date range, use section anchors |
| No strong signal in discover mode | Check Clippings inbox, recent newsletters, project logs |
| Post overlaps existing article | Differentiate angle, reference previous post, or propose as update |
| Cover image generation fails | Check GEMINI_API_KEY, fall back to manual generation |
| Hugo build fails | Verify front matter YAML syntax, check for unescaped quotes in title/summary |
