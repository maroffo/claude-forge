#!/usr/bin/env python3
# ABOUTME: Guards hooks/settings.example.json against duplicate keys and dangling hook references
# ABOUTME: Run with: uv run --no-project python3 hooks/tests/test_settings_example.py

import json
import os

HOOKS_DIR = os.path.join(os.path.dirname(__file__), "..")
TEMPLATE = os.path.join(HOOKS_DIR, "settings.example.json")


def _no_duplicate_keys(pairs):
    seen = {}
    for key, value in pairs:
        if key in seen:
            raise AssertionError(f"duplicate key {key!r} in settings.example.json (JSON keeps only the last, silently dropping the earlier block)")
        seen[key] = value
    return seen


def test_valid_json_without_duplicate_keys():
    with open(TEMPLATE) as fh:
        data = json.load(fh, object_pairs_hook=_no_duplicate_keys)
    assert "hooks" in data, "template is missing the 'hooks' key"
    return data


def test_referenced_hooks_exist(data):
    for event, blocks in data["hooks"].items():
        for block in blocks:
            for entry in block["hooks"]:
                cmd = entry["command"]
                assert cmd.startswith("{{HOOKS_DIR}}/"), f"{event}: command should be templated with {{{{HOOKS_DIR}}}}, got {cmd!r}"
                script = cmd.removeprefix("{{HOOKS_DIR}}/")
                path = os.path.join(HOOKS_DIR, script)
                assert os.path.exists(path), f"{event}: registered hook {script!r} does not exist in hooks/"


def main():
    data = test_valid_json_without_duplicate_keys()
    test_referenced_hooks_exist(data)
    print("test_settings_example: all tests passed")


if __name__ == "__main__":
    main()
