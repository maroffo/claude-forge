# ABOUTME: Markdown formatter for classification results
# ABOUTME: P1-P3 checkbox format, P4 compact grouped, archive command generation

from __future__ import annotations

import re
from collections import Counter

from .models import ClassificationResult, ClassifiedThread

DEFAULT_ACCOUNT = "maroffo@gmail.com"

_DISPLAY_NAME_RE = re.compile(r'^"?([^"<]+?)"?\s*<[^>]+>$')

_PRIORITY_LABELS = {
    "P1": "Urgent",
    "P2": "Important",
    "P3": "Normal",
    "P4": "Low Priority",
}


def _sender_display(from_field: str) -> str:
    """Extract display name from 'Name <email>' or return email as-is."""
    match = _DISPLAY_NAME_RE.match(from_field.strip())
    if match:
        return match.group(1).strip()
    return from_field.strip()


def _format_thread_line(ct: ClassifiedThread) -> str:
    """Format a single thread as a checkbox line."""
    sender = _sender_display(ct.thread.from_)
    return f"- [ ] **{sender}** - {ct.thread.subject}"


def _format_p4_section(threads: list[ClassifiedThread]) -> list[str]:
    """Format P4 as compact grouped lines by matched_rule."""
    counts: Counter[str] = Counter()
    for ct in threads:
        counts[ct.matched_rule] += 1
    lines: list[str] = []
    for rule, count in counts.most_common():
        lines.append(f"- {rule}: {count}")
    return lines


def format_summary(result: ClassificationResult) -> str:
    """Generate markdown summary from classification result."""
    by_priority = result.by_priority
    parts: list[str] = []

    parts.append(f"## Inbox Triage - {result.date}")
    parts.append("")
    parts.append(f"**Total:** {result.total} threads")

    for pkey in ("P1", "P2", "P3", "P4"):
        threads = by_priority.get(pkey, [])
        if not threads:
            continue

        label = _PRIORITY_LABELS.get(pkey, pkey)
        parts.append("")
        parts.append(f"### {pkey} - {label} ({len(threads)})")

        if pkey == "P4":
            parts.extend(_format_p4_section(threads))
        else:
            for ct in threads:
                parts.append(_format_thread_line(ct))

    # Archive commands footer
    archive_sections: list[str] = []
    for pkey in ("P3", "P4"):
        threads = by_priority.get(pkey, [])
        if threads:
            label = pkey.lower()
            project = "~/.claude/skills/inbox-triage"
            cmd = f"uv run --project {project} -- inbox-triage archive {label} --yes"
            archive_sections.append(f"- Archive {pkey}: `{cmd}` ({len(threads)} threads)")

    if archive_sections:
        parts.append("")
        parts.append("### Actions")
        parts.extend(archive_sections)

    parts.append("")
    return "\n".join(parts)


def format_archive_commands(
    result: ClassificationResult,
    priorities: list[str],
) -> list[tuple[str, str]]:
    """Return (thread_id, gog_command) tuples for archiving threads at given priorities."""
    by_priority = result.by_priority
    commands: list[tuple[str, str]] = []
    for pkey in priorities:
        for ct in by_priority.get(pkey, []):
            tid = ct.thread.id
            cmd = (
                f"gog gmail thread modify {tid} --account={DEFAULT_ACCOUNT} --remove=INBOX,UNREAD"
            )
            commands.append((tid, cmd))
    return commands
