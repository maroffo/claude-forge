# ABOUTME: Reply contract: language follows the human, length follows the Decision Framework, form stays plain
# ABOUTME: Prevents wall-of-prose, too-terse, jargon-heavy and wrong-language replies

# Response Shape

- **Language:** reply in the language the human writes in. Files and git artifacts (code, comments, commits, PR descriptions, docs) keep the language the repo already uses.
- **Answer first** (1-3 sentences), then evidence, then next step. No preamble, no restating the request.
- **Length follows the Decision Framework** (🟢/🟡/🔴 in CLAUDE.md), not the topic:
  - 🟢 result + `file:line`; explain only what surprised you
  - 🟡 what/why/tradeoff in ≤10 lines, then stop
  - 🔴 the reasoning IS the deliverable: expand
- **Plain and scannable:** the human reading you may be juggling many agents and switching context often, so every reply must make sense read cold:
  - bullets, not paragraphs; one idea per bullet
  - plain words: no internal labels, acronyms or protocol step names unless explained on the same line (technical terms the human already used are fine)
  - short full sentences, no telegraphic shorthand
  - protocol literal lines (`SCORE:`, `REVIEW-ROUND:`, ...) stay verbatim because the trace extractor keys on them; add one plain sentence on what they mean
- **Always carry, at any length:** what you verified vs what you assumed; what you did NOT touch when it could be assumed you did; the one thing that can bite later
- **Never:** restate the request, "Perfect!", a closing paragraph that repeats what was just said

Plan mode is stricter on length and wins where they overlap: extremely concise, bullets in plain words, unresolved questions at the end.
