# ABOUTME: Tests for prompt_loader: section splitting, template rendering
# ABOUTME: Covers split_sections, render_user, load_and_render

from __future__ import annotations

from pathlib import Path

import pytest

from autoresearch_prompt.prompt_loader import (
    load_and_render,
    load_prompt,
    render_user,
    split_sections,
)


class TestSplitSections:
    def test_basic_split(self):
        raw = "## System\n\nYou are a classifier.\n\n## User\n\nClassify this: {{content}}\n"
        system, user = split_sections(raw)
        assert "classifier" in system
        assert "{{content}}" in user

    def test_missing_system_raises(self):
        with pytest.raises(ValueError, match="System"):
            split_sections("## User\n\nHello\n")

    def test_missing_user_raises(self):
        with pytest.raises(ValueError, match="User"):
            split_sections("## System\n\nHello\n")

    def test_case_insensitive_headers(self):
        raw = "## system\n\nSys content\n\n## user\n\nUser content\n"
        system, user = split_sections(raw)
        assert system == "Sys content"
        assert user == "User content"

    def test_multiline_sections(self):
        raw = (
            "## System\n\nLine 1\nLine 2\nLine 3\n\n"
            "## User\n\nFrom: {{from}}\nSubject: {{subject}}\n"
        )
        system, user = split_sections(raw)
        assert "Line 1" in system
        assert "Line 3" in system
        assert "{{from}}" in user


class TestRenderUser:
    def test_all_placeholders(self):
        template = "From: {{from}}\nSubject: {{subject}}\n\n{{content}}"
        fields = {"from": "Alice <a@b.com>", "subject": "Test Subject", "content": "Body text"}
        result = render_user(template, fields)
        assert "Alice <a@b.com>" in result
        assert "Test Subject" in result
        assert "Body text" in result

    def test_no_placeholders(self):
        template = "Static text"
        result = render_user(template, {"from": "from", "subject": "sub", "content": "body"})
        assert result == "Static text"

    def test_multiple_occurrences(self):
        template = "{{from}} said {{from}}"
        result = render_user(template, {"from": "Alice"})
        assert result == "Alice said Alice"

    def test_arbitrary_fields(self):
        template = "Diff: {{diff}}\nContext: {{context}}"
        result = render_user(template, {"diff": "- old\n+ new", "context": "refactor"})
        assert "- old\n+ new" in result
        assert "refactor" in result

    def test_non_string_values_cast_to_str(self):
        template = "Count: {{count}}, Active: {{active}}"
        result = render_user(template, {"count": 5, "active": True})
        assert "Count: 5" in result
        assert "Active: True" in result


class TestLoadPrompt:
    def test_load_from_file(self, sample_prompt_md: Path):
        content = load_prompt(sample_prompt_md)
        assert "## System" in content
        assert "## User" in content


class TestLoadAndRender:
    def test_end_to_end(self, sample_prompt_md: Path):
        fields = {"from": "Test <t@x.com>", "subject": "My Subject", "content": "Body here"}
        system, user = load_and_render(fields, prompt_path=sample_prompt_md)
        assert "classifier" in system
        assert "Test <t@x.com>" in user
        assert "My Subject" in user
        assert "Body here" in user
