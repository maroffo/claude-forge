#!/usr/bin/env python3
# ABOUTME: Tests for forge-drift-check.sh, the SessionStart scan of ~/.claude against the checkout
# ABOUTME: Run with: uv run --no-project python3 hooks/tests/test_forge_drift_check.py

"""Plan matrix rows 10-16 (2026-07-27_gstack-borrowings).

Every case builds a throwaway checkout plus a fake $HOME. The hook derives the
forge root from its own resolved location, so the copy living inside the fake
checkout is the one invoked: that is what makes the forge-origin test (and the
non-forge hooks it must ignore) testable at all.
"""

import json
import os
import shutil
import subprocess
import tempfile

HOOK_SRC = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "forge-drift-check.sh"))

# Registers two of the three fake hooks: _helper.sh is sourced, never registered,
# and must therefore never be reported as unregistered.
SETTINGS_EXAMPLE = json.dumps({
    "hooks": {
        "SessionStart": [{
            "matcher": "startup|resume",
            "hooks": [
                {"type": "command", "command": "{{HOOKS_DIR}}/forge-drift-check.sh", "timeout": 10},
                {"type": "command", "command": "{{HOOKS_DIR}}/sample-hook.sh", "timeout": 10},
            ],
        }]
    }
}, indent=2)

TEMP_ROOTS = []


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(content)


def make_checkout():
    """A fake forge checkout plus an empty fake ~/.claude. Nothing installed yet."""
    root = os.path.realpath(tempfile.mkdtemp(prefix="forge-drift-"))
    TEMP_ROOTS.append(root)
    forge = os.path.join(root, "forge")
    home = os.path.join(root, "home")

    os.makedirs(os.path.join(forge, "hooks"))
    shutil.copy(HOOK_SRC, os.path.join(forge, "hooks", "forge-drift-check.sh"))
    write(os.path.join(forge, "hooks", "sample-hook.sh"), "#!/usr/bin/env bash\nexit 0\n")
    write(os.path.join(forge, "hooks", "_helper.sh"), "#!/usr/bin/env bash\n: helper\n")
    write(os.path.join(forge, "hooks", "settings.example.json"), SETTINGS_EXAMPLE)
    write(os.path.join(forge, "agents", "agent-a", "AGENT.md"), "a\n")
    write(os.path.join(forge, "agents", "agent-b", "AGENT.md"), "b\n")
    write(os.path.join(forge, "rules", "sample-rule.md"), "rule\n")
    write(os.path.join(forge, "skills", "sample-skill", "SKILL.md"), "skill\n")

    for sub in ("hooks", "agents"):
        os.makedirs(os.path.join(home, ".claude", sub), exist_ok=True)
    return forge, home


def install_clean():
    """Everything installed the way install.sh (developer mode) leaves it."""
    forge, home = make_checkout()
    claude = os.path.join(home, ".claude")
    for name in ("forge-drift-check.sh", "sample-hook.sh", "_helper.sh"):
        os.symlink(os.path.join(forge, "hooks", name), os.path.join(claude, "hooks", name))
    for name in ("agent-a", "agent-b"):
        os.symlink(os.path.join(forge, "agents", name), os.path.join(claude, "agents", name))
    os.symlink(os.path.join(forge, "rules"), os.path.join(claude, "rules"))
    os.symlink(os.path.join(forge, "skills"), os.path.join(claude, "skills"))
    write_settings(home, ["forge-drift-check.sh", "sample-hook.sh"])
    return forge, home


def write_settings(home, hook_names):
    claude = os.path.join(home, ".claude")
    entries = [
        {"type": "command", "command": os.path.join(claude, "hooks", n), "timeout": 10}
        for n in hook_names
    ]
    write(os.path.join(claude, "settings.json"),
          json.dumps({"hooks": {"SessionStart": [{"matcher": "startup|resume", "hooks": entries}]}}))


def run(forge, home, source="startup"):
    env = dict(os.environ, HOME=home)
    proc = subprocess.run(
        ["bash", os.path.join(forge, "hooks", "forge-drift-check.sh")],
        input=json.dumps({"hook_event_name": "SessionStart", "source": source}),
        capture_output=True, text=True, timeout=30, env=env,
    )
    assert proc.returncode == 0, f"hook must always exit 0, got {proc.returncode}: {proc.stderr}"
    out = [ln for ln in proc.stdout.splitlines() if ln.strip()]
    for line in out:
        assert line.startswith("[forge-drift] "), f"unprefixed output line: {line!r}"
    assert len(out) <= 3, f"output budget is 3 lines, got {len(out)}: {out}"
    return out


def one(out, label):
    assert len(out) == 1, f"{label}: expected exactly one finding, got {out}"
    return out[0]


def test_clean_is_silent():
    """Row 16: nothing to say, on both session sources. The noise budget IS the feature."""
    forge, home = install_clean()
    assert run(forge, home, "startup") == [], "clean startup must be silent"
    assert run(forge, home, "resume") == [], "clean resume must be silent"


def test_dangling_symlink():
    """Row 10: a forge-pointing link whose target is gone."""
    forge, home = install_clean()
    entry = os.path.join(home, ".claude", "hooks", "gone.sh")
    os.symlink(os.path.join(forge, "hooks", "gone.sh"), entry)
    line = one(run(forge, home), "dangling")
    assert "dangling symlink" in line and entry in line, line
    assert f"ln -sfn {os.path.join(forge, 'hooks', 'gone.sh')} {entry}" in line, line


def test_missing_entry_flagged_when_category_managed():
    """Row 11: repo file with no ~/.claude entry, in a category forge symlinks manage."""
    forge, home = install_clean()
    os.remove(os.path.join(home, ".claude", "hooks", "sample-hook.sh"))
    line = one(run(forge, home), "missing-hook")
    expected = "ln -s {} {}".format(
        os.path.join(forge, "hooks", "sample-hook.sh"),
        os.path.join(home, ".claude", "hooks", "sample-hook.sh"),
    )
    assert expected in line, line

    # Same for a category whose entries are directories.
    forge, home = install_clean()
    os.remove(os.path.join(home, ".claude", "agents", "agent-b"))
    line = one(run(forge, home), "missing-agent")
    assert "agents/agent-b" in line and "ln -s" in line, line


def test_missing_entry_silent_when_category_unmanaged():
    """Row 11 negative: zero forge symlinks means the category is not installed here.

    The foreign entries are a plain file AND a symlink, because only the symlink
    proves the origin test is what withholds the "managed" verdict.
    """
    forge, home = make_checkout()
    hooks = os.path.join(home, ".claude", "hooks")
    outside = os.path.join(os.path.dirname(forge), "outside")
    write(os.path.join(outside, "external.sh"), "#!/bin/sh\nexit 0\n")
    write(os.path.join(hooks, "notify.sh"), "#!/bin/sh\nexit 0\n")
    os.symlink(os.path.join(outside, "external.sh"), os.path.join(hooks, "external.sh"))
    write_settings(home, ["notify.sh", "external.sh"])
    assert run(forge, home) == [], "a category with no forge symlink must stay silent"


def test_installed_but_unregistered():
    """Row 12: symlinked hook the user's settings.json never mentions."""
    forge, home = install_clean()
    write_settings(home, ["forge-drift-check.sh"])
    line = one(run(forge, home), "unregistered")
    assert "sample-hook.sh" in line and "settings.json" in line, line
    assert "_helper.sh" not in line, "sourced helpers are not registered hooks"


def test_non_forge_hooks_ignored():
    """Row 13: notify.sh and friends, registered or not, linked or dangling."""
    forge, home = install_clean()
    hooks = os.path.join(home, ".claude", "hooks")
    outside = os.path.join(os.path.dirname(forge), "outside")
    write(os.path.join(outside, "external.sh"), "#!/bin/sh\nexit 0\n")

    write(os.path.join(hooks, "notify.sh"), "#!/bin/sh\nexit 0\n")
    write(os.path.join(hooks, "herdr-agent-state.sh"), "#!/bin/sh\nexit 0\n")
    os.symlink(os.path.join(outside, "external.sh"), os.path.join(hooks, "external.sh"))
    os.symlink(os.path.join(outside, "vanished.sh"), os.path.join(hooks, "vanished.sh"))

    # A foreign hook squatting a forge filename, deliberately unregistered: the
    # origin test is the only thing standing between this and a false positive.
    os.remove(os.path.join(hooks, "sample-hook.sh"))
    write(os.path.join(outside, "sample-hook.sh"), "#!/bin/sh\nexit 0\n")
    os.symlink(os.path.join(outside, "sample-hook.sh"), os.path.join(hooks, "sample-hook.sh"))
    write_settings(home, ["forge-drift-check.sh", "notify.sh"])

    assert run(forge, home) == [], "non-forge hooks must never be flagged"


def test_stale_copy():
    """Row 14: the incident class a dangling/missing check walks straight past."""
    forge, home = install_clean()
    entry = os.path.join(home, ".claude", "hooks", "sample-hook.sh")
    os.remove(entry)
    write(entry, "#!/usr/bin/env bash\n# frozen at last year's revision\nexit 0\n")
    line = one(run(forge, home), "stale-copy")
    assert "stale copy" in line and entry in line, line
    assert f"ln -sfn {os.path.join(forge, 'hooks', 'sample-hook.sh')} {entry}" in line, line

    # Identical content is an install choice, not drift.
    forge, home = install_clean()
    entry = os.path.join(home, ".claude", "hooks", "sample-hook.sh")
    os.remove(entry)
    shutil.copy(os.path.join(forge, "hooks", "sample-hook.sh"), entry)
    assert run(forge, home) == [], "a byte-identical copy is not drift"


def test_forge_omit_suppresses():
    """Row 15: partial installs on secondary machines."""
    forge, home = install_clean()
    os.remove(os.path.join(home, ".claude", "hooks", "sample-hook.sh"))
    os.symlink(os.path.join(forge, "hooks", "gone.sh"),
               os.path.join(home, ".claude", "hooks", "gone.sh"))
    assert len(run(forge, home)) == 2, "precondition: two findings before omitting"

    write(os.path.join(home, ".claude", ".forge-omit"),
          "# intentionally absent on this machine\nsample-hook.sh\n  gone.sh  \n\n")
    assert run(forge, home) == [], "omitted names are suppressed everywhere"


def test_whole_directory_symlinks():
    """rules/ and skills/ install as one link: dangling loses every entry at once."""
    forge, home = install_clean()
    shutil.rmtree(os.path.join(forge, "rules"))
    line = one(run(forge, home), "dangling-rules-dir")
    assert "dangling symlink" in line and "ln -sfn" in line, line

    # skills/ as a real directory of copies is install.sh's default, not drift,
    # even when a copy has drifted from the checkout.
    forge, home = install_clean()
    os.remove(os.path.join(home, ".claude", "skills"))
    write(os.path.join(home, ".claude", "skills", "sample-skill", "SKILL.md"), "diverged\n")
    assert run(forge, home) == [], "copied skills/ is not scanned per entry"


def test_output_budget_truncates():
    """More findings than lines allowed: two plus a countable tail."""
    forge, home = install_clean()
    hooks = os.path.join(home, ".claude", "hooks")
    os.remove(os.path.join(hooks, "sample-hook.sh"))
    os.remove(os.path.join(hooks, "_helper.sh"))
    os.remove(os.path.join(home, ".claude", "agents", "agent-a"))
    for name in ("gone-a.sh", "gone-b.sh"):
        os.symlink(os.path.join(forge, "hooks", name), os.path.join(hooks, name))

    out = run(forge, home)
    assert len(out) == 3, out
    assert out[2].startswith("[forge-drift] +") and "more drift findings" in out[2], out[2]
    assert "ln -s" in out[2], "the tail line still carries a remedy"


def main():
    tests = [
        test_clean_is_silent,
        test_dangling_symlink,
        test_missing_entry_flagged_when_category_managed,
        test_missing_entry_silent_when_category_unmanaged,
        test_installed_but_unregistered,
        test_non_forge_hooks_ignored,
        test_stale_copy,
        test_forge_omit_suppresses,
        test_whole_directory_symlinks,
        test_output_budget_truncates,
    ]
    try:
        for test in tests:
            test()
    finally:
        for root in TEMP_ROOTS:
            shutil.rmtree(root, ignore_errors=True)
    print(f"PASS  forge-drift-check ({len(tests)} cases)")


if __name__ == "__main__":
    main()
