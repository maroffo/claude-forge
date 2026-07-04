#!/usr/bin/env python3
# ABOUTME: Static checks for claude-forge (config/docs repo)
# ABOUTME: Validates ABOUTME headers, em-dashes, SKILL.md frontmatter, skill schema

import sys
import re
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCOPE_DIRS = ["skills", "rules", "agents"]
EXTRA_FILES = ["README.md", "LEARNING.md", "MEMORY.md", "CLAUDE.md.example"]
# Em-dash rule is enforced on the skills/ surface (where new authoring happens).
# rules/ and agents/ have baseline violations that predate this rule; clean on touch.
EM_DASH_SCOPE_SUBSTRINGS = ("/skills/",)
# Humanizer deliberately contains bad writing as training examples.
EM_DASH_EXEMPT_PATH_SUBSTRINGS = ("skills/humanizer/",)

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
FENCED_CODE_RE = re.compile(r"```.*?```", re.DOTALL)


def collect_md():
    files = []
    for d in SCOPE_DIRS:
        p = ROOT / d
        if p.is_dir():
            files.extend(sorted(p.rglob("*.md")))
    for name in EXTRA_FILES:
        p = ROOT / name
        if p.is_file():
            files.append(p)
    return files


def strip_frontmatter(text):
    m = FRONTMATTER_RE.match(text)
    return text[m.end():] if m else text


def strip_code(text):
    text = FENCED_CODE_RE.sub("", text)
    text = INLINE_CODE_RE.sub("", text)
    return text


def check_aboutme(files):
    """SKILL.md needs 2 `# ABOUTME:` lines, either before or after the frontmatter block."""
    failures = []
    for f in files:
        if f.name != "SKILL.md":
            continue
        text = f.read_text()
        # Candidate 1: ABOUTME before frontmatter
        pre = text.split("---\n", 1)[0] if text.startswith("# ABOUTME:") else ""
        # Candidate 2: ABOUTME after frontmatter
        post = strip_frontmatter(text)
        for candidate in (pre, post):
            head = [l for l in candidate.splitlines()[:10] if l.strip()][:2]
            if len(head) >= 2 and all(l.startswith("# ABOUTME:") for l in head):
                break
        else:
            failures.append(str(f.relative_to(ROOT)))
    return failures


def check_em_dash(files):
    """Flag em-dashes in prose (not in code spans). Scoped to skills/ (excluding humanizer)."""
    failures = []
    for f in files:
        rel = "/" + str(f.relative_to(ROOT))
        if not any(sub in rel for sub in EM_DASH_SCOPE_SUBSTRINGS):
            continue
        if any(sub in rel for sub in EM_DASH_EXEMPT_PATH_SUBSTRINGS):
            continue
        text = f.read_text()
        for i, line in enumerate(text.splitlines(), 1):
            stripped = INLINE_CODE_RE.sub("", line)
            if "\u2014" in stripped:
                failures.append(f"{f.relative_to(ROOT)}:{i}")
    return failures


def _extract_frontmatter(text):
    """Find the YAML frontmatter whether it's at the very top or after an ABOUTME preamble."""
    # Top of file
    m = FRONTMATTER_RE.match(text)
    if m:
        return m.group(1)
    # After ABOUTME lines: find first `---` line and match from there
    lines = text.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if line.strip() == "---":
            rest = "".join(lines[i:])
            m = FRONTMATTER_RE.match(rest)
            if m:
                return m.group(1)
            break
    return None


def check_frontmatter(files):
    """If SKILL.md has frontmatter, it must have name + description. No frontmatter is OK (ABOUTME is fallback)."""
    failures = []
    for f in files:
        if f.name != "SKILL.md":
            continue
        fm = _extract_frontmatter(f.read_text())
        if fm is None:
            continue  # ABOUTME-only skills are allowed
        if not re.search(r"^name:\s*\S", fm, re.M):
            failures.append(f"{f.relative_to(ROOT)}: missing 'name'")
        if not re.search(r"^description:\s*['\"]?\S", fm, re.M):
            failures.append(f"{f.relative_to(ROOT)}: missing 'description'")
    return failures


def check_skill_schema(files):
    """Deeper SKILL.md validation: name matches dir, description length."""
    failures = []
    for f in files:
        if f.name != "SKILL.md":
            continue
        fm = _extract_frontmatter(f.read_text())
        if fm is None:
            continue  # ABOUTME-only skills are allowed
        nm = re.search(r"^name:\s*(.+)$", fm, re.M)
        dm = re.search(r"^description:\s*(.+)$", fm, re.M)
        if nm:
            name = nm.group(1).strip().strip('"\'')
            dir_name = f.parent.name
            if name != dir_name:
                failures.append(f"{f.relative_to(ROOT)}: name '{name}' does not match dir '{dir_name}'")
        else:
            failures.append(f"{f.relative_to(ROOT)}: no name")
        if dm:
            desc = dm.group(1).strip().strip('"\'')
            if len(desc) < 20:
                failures.append(f"{f.relative_to(ROOT)}: description too short ({len(desc)} chars)")
            if len(desc) > 2500:
                failures.append(f"{f.relative_to(ROOT)}: description too long ({len(desc)} chars)")
        else:
            failures.append(f"{f.relative_to(ROOT)}: no description")
    return failures


def check_agent_schema(files):
    """AGENT.md validation, mirroring check_skill_schema: frontmatter must parse
    at the top of the file, name must match the directory, description must be
    present and sane. Unlike skills, agents have no ABOUTME-only fallback: an
    unparseable AGENT.md is an unspawnable agent (2026-07-04: harness-mechanic)."""
    failures = []
    for f in files:
        if f.name != "AGENT.md":
            continue
        m = FRONTMATTER_RE.match(f.read_text())
        if m is None:
            failures.append(f"{f.relative_to(ROOT)}: no frontmatter at top of file (agent will not register)")
            continue
        fm = m.group(1)
        nm = re.search(r"^name:\s*(.+)$", fm, re.M)
        dm = re.search(r"^description:\s*(.+)$", fm, re.M)
        if nm:
            name = nm.group(1).strip().strip('"\'')
            if name != f.parent.name:
                failures.append(f"{f.relative_to(ROOT)}: name '{name}' does not match dir '{f.parent.name}'")
        else:
            failures.append(f"{f.relative_to(ROOT)}: no name")
        if dm:
            desc = dm.group(1).strip().strip('"\'')
            if len(desc) < 20 or len(desc) > 2500:
                failures.append(f"{f.relative_to(ROOT)}: description length out of range ({len(desc)} chars)")
        else:
            failures.append(f"{f.relative_to(ROOT)}: no description")
    return failures


def check_frontmatter_first(files):
    """SKILL.md and AGENT.md must OPEN with the YAML frontmatter. ABOUTME (or
    anything else) above the first `---` makes the registry publish the wrong
    description, or not register the definition at all (2026-07-04 audit: four
    skills shipped this way; the harness-mechanic AGENT was invisible to the
    Agent tool for the same reason)."""
    failures = []
    for f in files:
        if f.name not in ("SKILL.md", "AGENT.md"):
            continue
        for line in f.read_text().splitlines():
            if not line.strip():
                continue
            if line.strip() != "---":
                failures.append(f"{f.relative_to(ROOT)}: first content is not frontmatter (found: {line.strip()[:40]!r})")
            break
    return failures


def report(label, failures, max_show=20):
    if not failures:
        print(f"PASS  {label}")
        return 0
    print(f"FAIL  {label} ({len(failures)} issues)")
    for x in failures[:max_show]:
        print(f"      {x}")
    if len(failures) > max_show:
        print(f"      ... and {len(failures) - max_show} more")
    return 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["check", "test-e2e"])
    args = ap.parse_args()
    files = collect_md()
    print(f"Scanning {len(files)} markdown files under {ROOT}")
    rc = 0
    if args.mode == "check":
        rc |= report("ABOUTME headers (SKILL.md)", check_aboutme(files))
        rc |= report("em-dashes", check_em_dash(files))
        rc |= report("frontmatter basics", check_frontmatter(files))
        rc |= report("frontmatter first (SKILL.md/AGENT.md opens with ---)", check_frontmatter_first(files))
        # Schema also runs here so the pre-commit gate can safely skip
        # test-e2e on docs-only commits without losing SKILL.md validation.
        rc |= report("skill schema (name=dir, description length)", check_skill_schema(files))
        rc |= report("agent schema (frontmatter parses, name=dir, description)", check_agent_schema(files))
    elif args.mode == "test-e2e":
        rc |= report("skill schema (name=dir, description length)", check_skill_schema(files))
    sys.exit(1 if rc else 0)


if __name__ == "__main__":
    main()
