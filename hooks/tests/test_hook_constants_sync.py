#!/usr/bin/env python3
# ABOUTME: Drift guard — asserts the constants duplicated across Stop hooks stay identical
# ABOUTME: Run with: uv run --no-project python3 hooks/tests/test_hook_constants_sync.py

import importlib.util
import os

HOOKS_DIR = os.path.join(os.path.dirname(__file__), "..")
SYNCED_CONSTANTS = ("SOURCE_EXTS", "EXEMPT_PATH_SUBSTRINGS", "NON_VERIFY_PREFIXES")


def load(filename):
    path = os.path.join(HOOKS_DIR, filename)
    module_name = filename.replace("-", "_").removesuffix(".py")
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    vbs = load("verify-before-stop.py")
    seg = load("score-evidence-guard.py")

    for name in SYNCED_CONSTANTS:
        a, b = getattr(vbs, name), getattr(seg, name)
        assert a == b, f"{name} drifted between verify-before-stop.py and score-evidence-guard.py"

    assert vbs.VERIFY_RE.pattern == seg.VERIFY_RE.pattern, (
        "VERIFY_RE drifted between verify-before-stop.py and score-evidence-guard.py"
    )

    print("test_hook_constants_sync: all tests passed")


if __name__ == "__main__":
    main()
