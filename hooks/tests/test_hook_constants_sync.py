#!/usr/bin/env python3
# ABOUTME: Drift guard — asserts the constants duplicated across Stop hooks stay identical
# ABOUTME: Run with: uv run --no-project python3 hooks/tests/test_hook_constants_sync.py

import importlib.util
import os
import re

HOOKS_DIR = os.path.join(os.path.dirname(__file__), "..")
REPO_ROOT = os.path.join(HOOKS_DIR, "..")
SYNCED_CONSTANTS = ("SOURCE_EXTS", "EXEMPT_PATH_SUBSTRINGS", "NON_VERIFY_PREFIXES")

FREEZE_HOOK = os.path.join(HOOKS_DIR, "_freeze_boundary.sh")
FREEZE_SKILL = os.path.join(REPO_ROOT, "skills", "freeze", "SKILL.md")
FREEZE_TOKEN_RE = re.compile(r"\.freeze[-\w]*")


def load(filename):
    path = os.path.join(HOOKS_DIR, filename)
    module_name = filename.replace("-", "_").removesuffix(".py")
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def check_freeze_boundary_basename():
    """The /freeze skill writes the boundary file that freeze-guard.sh reads. gstack,
    where the idea comes from, ships that pair with two independent path sources that
    only accidentally agree; here the basename has one home and the skill quotes it."""
    with open(FREEZE_HOOK) as fh:
        m = re.search(r'^FREEZE_BOUNDARY_BASENAME="([^"]+)"', fh.read(), re.M)
    assert m, "FREEZE_BOUNDARY_BASENAME not found in hooks/_freeze_boundary.sh"
    basename = m.group(1)

    with open(FREEZE_SKILL) as fh:
        skill = fh.read()
    assert basename in skill, (
        f"skills/freeze/SKILL.md never names {basename!r}: the write path and the read path can drift"
    )
    strays = sorted(set(FREEZE_TOKEN_RE.findall(skill)) - {basename})
    assert not strays, (
        f"skills/freeze/SKILL.md names {strays} besides {basename!r}: "
        "the skill would write a boundary file the hook never reads"
    )


def main():
    vbs = load("verify-before-stop.py")
    seg = load("score-evidence-guard.py")

    for name in SYNCED_CONSTANTS:
        a, b = getattr(vbs, name), getattr(seg, name)
        assert a == b, f"{name} drifted between verify-before-stop.py and score-evidence-guard.py"

    assert vbs.VERIFY_RE.pattern == seg.VERIFY_RE.pattern, (
        "VERIFY_RE drifted between verify-before-stop.py and score-evidence-guard.py"
    )

    check_freeze_boundary_basename()

    print("test_hook_constants_sync: all tests passed")


if __name__ == "__main__":
    main()
