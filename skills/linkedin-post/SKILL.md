---
name: linkedin-post
description: "Publish LinkedIn posts from blog articles or free text via the REST API. Drafts the post, confirms with the user, publishes with an article link card. Use when user says linkedin post, post on linkedin, publish to linkedin, or share on linkedin."
---

# ABOUTME: Publish LinkedIn posts from blog articles or free text via REST API
# ABOUTME: Drafts post text, confirms with user, publishes with article link card

# LinkedIn Post

Publish posts to Max's LinkedIn profile from blog articles or free text.

## Credentials

```
~/.config/linkedin/credentials.json
```

Contains `access_token` (60-day expiry, regenerate at https://www.linkedin.com/developers/tools/oauth/token-generator with scopes `openid` + `w_member_social`) and `person_urn`.

## Entry points

### Mode 1: From blog post

User provides a blog post file or has just published one. Read the post, draft a LinkedIn-appropriate summary.

### Mode 2: Free text

User provides text directly. Format it for LinkedIn.

## Workflow

### Step 1: Draft the post

Write LinkedIn post text following these rules:

**Format:**
- Max 3000 characters (LinkedIn limit)
- First line is the hook (shows before "see more")
- Short paragraphs (1-2 sentences each)
- Line breaks between paragraphs (LinkedIn collapses whitespace otherwise)
- End with the article link on its own line
- 3-5 relevant hashtags on the last line

**Tone: sober and understated.**
- First person, matter-of-fact, no performative energy
- State the facts, let the reader draw conclusions
- No dramatic one-liners or punchlines designed for virality
- Short paragraphs, plain language, conversational but restrained
- "I've been thinking about X" is better than "X will change everything"
- End with a simple pointer to the article, not a call to action

**Anti-patterns (never do):**
- "I'm thrilled/excited/proud to..."
- Emoji bullets or decorative emojis
- "Agree? Disagree? Let me know in the comments!"
- Clickbait hooks ("You won't believe...")
- Listicle format without context
- Dramatic reveals ("The paradox has a name.")
- Staccato one-liner paragraphs for effect ("Power determines what happens.")
- Overly punchy closers ("20 sources, zero comfort.")

### Step 2: Humanize (mandatory)

Run `/humanizer` on the draft text. LinkedIn posts are public-facing content; AI patterns are even more visible in short-form text. Fix all findings before showing the draft.

### Step 3: Second opinion (mandatory)

Run `/second-opinion` on the draft. Ask Gemini to review for: tone (corporate fluff vs Max's voice), hook strength, missing angles, AI writing artifacts. Apply feedback.

### Step 4: Confirm with user

Show the final draft. Wait for approval or edits. Do NOT publish without explicit confirmation.

### Step 5: Publish

```bash
TOKEN=$(cat ~/.config/linkedin/credentials.json | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
PERSON_URN=$(cat ~/.config/linkedin/credentials.json | python3 -c "import sys,json; print(json.load(sys.stdin)['person_urn'])")

curl -s -w "\nHTTP_CODE:%{http_code}" 'https://api.linkedin.com/rest/posts' \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Restli-Protocol-Version: 2.0.0" \
  -H "LinkedIn-Version: 202602" \
  -H "Content-Type: application/json" \
  -d "{
  \"author\": \"$PERSON_URN\",
  \"commentary\": \"$(echo "$POST_TEXT" | sed 's/"/\\"/g')\",
  \"visibility\": \"PUBLIC\",
  \"distribution\": {\"feedDistribution\": \"MAIN_FEED\",\"targetEntities\": [],\"thirdPartyDistributionChannels\": []},
  \"lifecycleState\": \"PUBLISHED\",
  \"isReshareDisabledByAuthor\": false
}"
```

For posts with article link cards, use the `content.article` format:

```bash
curl -s -w "\nHTTP_CODE:%{http_code}" 'https://api.linkedin.com/rest/posts' \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Restli-Protocol-Version: 2.0.0" \
  -H "LinkedIn-Version: 202602" \
  -H "Content-Type: application/json" \
  -d "{
  \"author\": \"$PERSON_URN\",
  \"commentary\": \"$(echo "$POST_TEXT" | sed 's/"/\\"/g')\",
  \"visibility\": \"PUBLIC\",
  \"distribution\": {\"feedDistribution\": \"MAIN_FEED\",\"targetEntities\": [],\"thirdPartyDistributionChannels\": []},
  \"content\": {
    \"article\": {
      \"source\": \"$ARTICLE_URL\",
      \"title\": \"$ARTICLE_TITLE\",
      \"description\": \"$ARTICLE_SUMMARY\"
    }
  },
  \"lifecycleState\": \"PUBLISHED\",
  \"isReshareDisabledByAuthor\": false
}"
```

A `201` response means success.

### Step 6: Report

```
LinkedIn post published.
  Visibility: PUBLIC
  Characters: XXX/3000
  Link: article URL (if included)
```

## Token expiry

If API returns `401`, the token has expired. Tell Max to regenerate at:
https://www.linkedin.com/developers/tools/oauth/token-generator

Select scopes: `openid` + `w_member_social`. Update `~/.config/linkedin/credentials.json`.

## Rules

- **NEVER publish without user confirmation.** Always show draft first.
- **No test posts to PUBLIC.** Use `CONNECTIONS` visibility for testing.
- Keep posts under 2000 characters when possible (engagement drops after that).
- Blog URL format: `https://maroffo.github.io/blog/posts/{slug}/`
