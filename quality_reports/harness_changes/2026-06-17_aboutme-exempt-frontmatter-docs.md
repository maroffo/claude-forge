# ABOUTME: Change contract for exempting YAML-front-matter markdown from the ABOUTME enforcer
# ABOUTME: Failure mode = Hugo/Jekyll content posts blocked, and the local exemption did not survive install.sh

# Harness Change Contract: aboutme-enforcer front-matter exemption

Authored before landing. Linked from the commit body. Append-only after merge.

## Component

`hooks/aboutme-enforcer.py`: new `is_frontmatter_doc(path, content)` check, called in the PreToolUse Write branch before the ABOUTME assertion.

## Failure mode targeted

The ABOUTME enforcer blocks writing markdown that uses YAML front matter as its header convention (Hugo/Jekyll posts, content pages). Blog content markdown correctly has no `# ABOUTME:` lines (documented convention), so every blog post Write was denied. A local-only exemption existed in the installed `~/.claude/hooks/aboutme-enforcer.py`, but it lived only there and `install.sh` overwrites the file from the repo version, so re-running the installer silently removed it (observed 2026-06-17, blocked a blog draft; the recurrence was already flagged in a memory note). This is the same "regenerated away" class: a fix that does not live in the source does not survive.

## Predicted improvement

Front-matter markdown is exempt at the source, so the fix survives `install.sh`. Writing a Hugo post no longer requires the temp workaround. Verifiable now: a 5-case suite passes (Hugo post exempt; `SKILL.md`, `AGENT.md`, a `.go` file, and a front-matter-less `.md` all still required to carry ABOUTME).

## Invariants preserved

- `SKILL.md` and `AGENT.md` carry front matter AND still require ABOUTME (explicit exclusion set); the hook's coverage of the authoring surface is unchanged.
- A markdown file with NO front matter still requires ABOUTME (a new prose doc is not silently exempted).
- Non-markdown source (`.go`, `.py`, `.sh`, etc.) is unaffected.
- The exemption is content-based (first non-empty line opens a `---` block with a closing `---`), so a `.md` that merely mentions `---` is not exempted.
- Edit-time ABOUTME-removal advisory (PostToolUse) is unchanged.

## Falsification

If a real source file that should carry ABOUTME starts being silently exempted because it happens to open with a `---` fence (e.g. someone puts a horizontal rule first), the heuristic is too loose: tighten to require `key: value` lines inside the fence, or revert. If `SKILL.md`/`AGENT.md` ever stop being enforced, the exclusion set broke: revert.

## Rollback

`git revert <commit>` then re-copy `hooks/aboutme-enforcer.py` to `~/.claude/hooks/` (or re-run `install.sh`). Affects: `hooks/aboutme-enforcer.py` only.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
