# ABOUTME: Load prompt.md, split into system/user sections, render template variables
# ABOUTME: Supports {{from}}, {{subject}}, {{content}} placeholders via str.replace

from __future__ import annotations

from pathlib import Path

PROMPT_PATH = Path(__file__).resolve().parent.parent.parent / "prompt.md"


def load_prompt(path: Path | None = None) -> str:
    """Load the raw prompt.md content."""
    p = path or PROMPT_PATH
    return p.read_text(encoding="utf-8")


def split_sections(raw: str) -> tuple[str, str]:
    """Split prompt into system and user sections at ## System / ## User headers.

    Returns (system_text, user_template).
    """
    lines = raw.split("\n")
    system_lines: list[str] = []
    user_lines: list[str] = []
    current: list[str] | None = None

    for line in lines:
        stripped = line.strip().lower()
        if stripped == "## system":
            current = system_lines
            continue
        elif stripped == "## user":
            current = user_lines
            continue
        if current is not None:
            current.append(line)

    system = "\n".join(system_lines).strip()
    user = "\n".join(user_lines).strip()

    if not system:
        raise ValueError("prompt.md missing '## System' section")
    if not user:
        raise ValueError("prompt.md missing '## User' section")

    return system, user


def render_user(template: str, from_sender: str, subject: str, content: str) -> str:
    """Replace {{from}}, {{subject}}, {{content}} placeholders in user template."""
    result = template
    result = result.replace("{{from}}", from_sender)
    result = result.replace("{{subject}}", subject)
    result = result.replace("{{content}}", content)
    return result


def load_and_render(
    from_sender: str,
    subject: str,
    content: str,
    prompt_path: Path | None = None,
) -> tuple[str, str]:
    """Load prompt.md, split, and render. Returns (system_message, user_message)."""
    raw = load_prompt(prompt_path)
    system, user_template = split_sections(raw)
    user = render_user(user_template, from_sender, subject, content)
    return system, user
