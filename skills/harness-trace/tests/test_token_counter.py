# ABOUTME: Tests for token counter and baseline generation
# ABOUTME: Validates tiktoken counting, directory scanning, TSV output

from __future__ import annotations

from pathlib import Path

from harness_trace.token_counter import (
    FileTokenCount,
    count_file_tokens,
    count_tokens,
    generate_baseline_tsv,
    scan_directory,
)


class TestCountTokens:
    def test_empty_string(self):
        assert count_tokens("") == 0

    def test_simple_text(self):
        tokens = count_tokens("hello world")
        assert tokens > 0
        assert tokens <= 3  # "hello", " world" typically 2 tokens

    def test_markdown_table(self):
        table = "| col1 | col2 |\n|------|------|\n| a | b |"
        tokens = count_tokens(table)
        assert tokens > 0

    def test_deterministic(self):
        text = "The quick brown fox jumps over the lazy dog."
        assert count_tokens(text) == count_tokens(text)


class TestCountFileTokens:
    def test_count_file(self, tmp_path: Path):
        f = tmp_path / "test.md"
        f.write_text("# Hello\n\nThis is a test file with some content.\n")
        tokens = count_file_tokens(f)
        assert tokens > 0


class TestScanDirectory:
    def test_scan_rules(self, tmp_path: Path):
        rules_dir = tmp_path / "rules"
        rules_dir.mkdir()
        (rules_dir / "test-rule.md").write_text("# Rule\nDo things.\n")

        results = scan_directory(rules_dir, base_dir=tmp_path)
        assert len(results) == 1
        assert results[0].tier == "rule"
        assert results[0].loaded == "always"

    def test_scan_skills(self, tmp_path: Path):
        skill_dir = tmp_path / "skills" / "test-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Skill\nDo skill things.\n")

        results = scan_directory(tmp_path / "skills", base_dir=tmp_path)
        assert len(results) == 1
        assert results[0].tier == "skill"
        assert results[0].loaded == "on-demand"

    def test_scan_agents(self, tmp_path: Path):
        agent_dir = tmp_path / "agents" / "test-agent"
        agent_dir.mkdir(parents=True)
        (agent_dir / "AGENT.md").write_text("# Agent\nReview things.\n")

        results = scan_directory(tmp_path / "agents", base_dir=tmp_path)
        assert len(results) == 1
        assert results[0].tier == "agent"
        assert results[0].loaded == "on-demand"

    def test_scan_reference_files(self, tmp_path: Path):
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        (skills_dir / "_PATTERNS.md").write_text("# Patterns\nCross-language.\n")

        results = scan_directory(skills_dir, base_dir=tmp_path)
        assert len(results) == 1
        assert results[0].tier == "skill-ref"

    def test_scan_skill_references_subdir(self, tmp_path: Path):
        ref_dir = tmp_path / "skills" / "golang" / "references"
        ref_dir.mkdir(parents=True)
        (ref_dir / "patterns.md").write_text("# Go patterns\n")

        results = scan_directory(tmp_path / "skills", base_dir=tmp_path)
        assert len(results) == 1
        assert results[0].tier == "skill-ref"

    def test_skips_hidden_files(self, tmp_path: Path):
        rules_dir = tmp_path / "rules"
        rules_dir.mkdir()
        (rules_dir / ".hidden.md").write_text("hidden")
        (rules_dir / "visible.md").write_text("visible")

        results = scan_directory(rules_dir, base_dir=tmp_path)
        assert len(results) == 1
        assert "visible" in results[0].file

    def test_empty_directory(self, tmp_path: Path):
        empty = tmp_path / "empty"
        empty.mkdir()
        results = scan_directory(empty)
        assert results == []


class TestGenerateBaselineTsv:
    def test_generates_header(self):
        results = [
            FileTokenCount("rules/test.md", 100, 50, 10, "rule", "always"),
        ]
        tsv = generate_baseline_tsv(results)
        assert tsv.startswith("file\ttokens\twords\tlines\ttier\tloaded\n")

    def test_includes_data_row(self):
        results = [
            FileTokenCount("rules/test.md", 100, 50, 10, "rule", "always"),
        ]
        tsv = generate_baseline_tsv(results)
        assert "rules/test.md\t100\t50\t10\trule\talways" in tsv

    def test_includes_summary(self):
        results = [
            FileTokenCount("rules/a.md", 100, 50, 10, "rule", "always"),
            FileTokenCount("skills/b/SKILL.md", 200, 80, 20, "skill", "on-demand"),
        ]
        tsv = generate_baseline_tsv(results)
        assert "# Always-on: 100 tokens" in tsv
        assert "# On-demand: 200 tokens" in tsv
        assert "# Total: 300 tokens" in tsv

    def test_sorted_by_tokens_desc(self):
        results = [
            FileTokenCount("rules/small.md", 50, 20, 5, "rule", "always"),
            FileTokenCount("rules/big.md", 500, 200, 50, "rule", "always"),
        ]
        tsv = generate_baseline_tsv(results)
        lines = [
            row for row in tsv.split("\n")
            if row and not row.startswith("#") and not row.startswith("file")
        ]
        assert lines[0].startswith("rules/big.md")
