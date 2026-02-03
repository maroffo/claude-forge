---
name: newsletter-digest
description: Process newsletters into Second Brain digest. Use when user wants to process newsletters, create digest, or catch up on subscriptions.
tools: Bash, Read, Write, Edit, WebFetch
---

# Newsletter Digest Skill

Process unread newsletters, extract actionable content for Second Brain, archive processed emails.

## Gmail Configuration

- **Account**: maroffo@gmail.com
- **Tool**: `gog` CLI

## Newsletter Sources

**All newsletters are processed** - categorize by content, not by sender.

### Common Platforms

```bash
# Search for unread newsletters from common platforms
gog gmail search "is:unread (from:substack.com OR from:beehiiv.com OR from:convertkit.com OR from:mailchimp.com OR from:buttondown.email)" --account=maroffo@gmail.com --json --max=20
```

### Known Newsletter Labels

| Label | Description |
|-------|-------------|
| `📰Newsletter/🔴 Substack` | Substack newsletters |
| `📰Newsletter` | General newsletters |
| `👨🏻‍💻work-related` | Work-related content (higher priority) |

### Key Newsletters by Category

| Newsletter | Author | Category |
|------------|--------|----------|
| ByteByteGo | Alex Xu | AI/Development |
| Turing Post | - | AI/Open Source |
| Artificial Ignorance | Charlie Guo | AI/Management |
| The Beautiful Mess | John Cutler | Engineering Management |
| Tidy First? | Kent Beck | Engineering/Design |
| Javarevisited | - | Development |
| [mini]marketing | Gianluca Diegoli | Marketing |
| Paul Krugman | Paul Krugman | Politics/Economics |
| Appunti | Stefano Feltri | Politics (IT) |
| 270 by Youtrend | Youtrend | Politics (IT) |
| Il Mattinale Europeo | David Carretta | EU Politics |
| Il Post | - | News (IT) |
| Semafor | - | News (International) |
| Roberta Villa | Roberta Villa | Health/Science |
| Ellissi | - | Media/Culture |
| Sillabe | Elena Tosato | Literature |

## Processing Workflow

### Step 1: Find Unread Newsletters

```bash
gog gmail search "is:unread (from:substack.com OR from:beehiiv.com OR from:convertkit.com)" --account=maroffo@gmail.com --json --max=20
```

### Step 2: For Each Newsletter

1. **Get full content**:
```bash
gog gmail thread get <threadId> --account=maroffo@gmail.com --json
```

2. **Extract metadata**:
   - Sender/publication name
   - Subject/title
   - Date
   - Body content (HTML → text)

3. **Analyze content** - identify:
   - **Tools/libraries** mentioned → Second Brain - Development/AI
   - **Patterns/techniques** → Second Brain appropriate section
   - **News/opinions** → Reference only (skip or brief note)
   - **Tutorials/guides** → Extract key steps

4. **Categorize destination** (ALL newsletters get processed):
   - AI, LLM, agents, prompts → `Second Brain - AI Agents and Tools.md`
   - Dev tools, libraries, languages → `Second Brain - Development.md`
   - DevOps, cloud, infrastructure → `Second Brain - DevOps and Cloud.md`
   - Leadership, productivity, team practices → `Second Brain - Engineering Management.md`
   - Politics, economics, geopolitics → `Second Brain - Politics and Economics.md`
   - Marketing, business strategy → `Second Brain - Marketing.md`
   - Media, culture, literature → `Second Brain - Media and Culture.md`
   - Health, science, medicine → `Second Brain - Health and Science.md`

### Step 3: Extract & Integrate

For actionable content, add to Second Brain:

```markdown
### [Tool/Topic Name]

Brief description from newsletter.

| Aspect | Detail |
|--------|--------|
| **What** | Core functionality |
| **Why** | Key benefit |

- Source: [Newsletter Name](gmail-url) - YYYY-MM-DD
```

For links in newsletter that need deeper dive:
```bash
# Fetch linked page for more context
# Use WebFetch tool
```

### Step 4: Update Timeline

Add entry to `Second Brain - Timeline.md`:

```markdown
- **YYYY-MM-DD** | [Topic] | Source: [Newsletter Name] | → Second Brain - [File].md
```

### Step 5: Archive Email

```bash
# Remove from inbox (archive)
gog gmail thread modify <threadId> --account=maroffo@gmail.com --remove=INBOX,UNREAD
```

## Output Format

After processing batch:

```
## Newsletter Digest - YYYY-MM-DD

### Processed (X newsletters)

1. **[Pragmatic Engineer]** - "Platform Teams Done Right"
   - Extracted: Platform team anti-patterns
   - → Second Brain - Engineering Management.md
   - ✓ Archived

2. **[ByteByteGo]** - "Rate Limiting Deep Dive"
   - Extracted: Token bucket algorithm summary
   - → Second Brain - Development.md
   - ✓ Archived

3. **[The Batch]** - "AI News Weekly"
   - Skipped: News only, no actionable content
   - ✓ Archived

### Summary
- Newsletters processed: X
- Second Brain entries added: Y
- Archived: X
```

## Content Extraction Guidelines

**Include in Second Brain:**
- Tool/library announcements with clear use case
- Architecture patterns with examples
- Techniques you can apply
- Commands/configs worth remembering
- **Important news** from news-focused newsletters (Il Post, Semafor, Appunti, Il Mattinale Europeo):
  - Geopolitical events with lasting impact
  - Policy changes (EU, IT, international)
  - Economic developments (trade, sanctions, markets)
  - Major political events (elections, government changes)
  - → Add to `Second Brain - Politics and Economics.md`

**Skip (archive only):**
- Tech industry news/opinions (funding, hype cycles)
- Funding announcements
- Job postings
- Content you've already captured
- Ephemeral news (daily weather, minor events)

**Ask user if unclear:**
- Mixed content (some actionable, some not)
- Topics outside usual categories

## Quick Commands

```bash
# Count unread newsletters
gog gmail search "is:unread (from:substack.com OR from:beehiiv.com)" --account=maroffo@gmail.com --json | jq '.resultSizeEstimate'

# Get specific newsletter content (body is base64 encoded)
gog gmail thread get <threadId> --account=maroffo@gmail.com --json | jq -r '.thread.messages[0].payload.parts[0].body.data' | base64 -d

# Archive thread
gog gmail thread modify <threadId> --account=maroffo@gmail.com --remove=INBOX,UNREAD

# Open in browser to read full
gog gmail url <threadId>
```

## Rules

1. **Quality over quantity** - only actionable content goes to Second Brain
2. **Be concise** - distill to key insights, not full summaries
3. **Always archive** - processed = archived, no exceptions
4. **Preserve sources** - include newsletter name and date
5. **Update Timeline** - every Second Brain addition gets logged
6. **Batch process** - handle multiple newsletters in one session
7. **Ask if ambiguous** - unclear categorization → ask user
