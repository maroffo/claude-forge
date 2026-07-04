#!/usr/bin/env python3
# ABOUTME: PostToolUse hook — counts edits per file per session and nudges "stop, re-plan" at thresholds
# ABOUTME: Advisory only (additionalContext), never blocks; state in ~/.claude/tmp keyed by session id

import glob
import json
import os
import re
import sys
import time

NUDGE_AT = 5  # first nudge on the 5th edit to the same file
NUDGE_EVERY = 3  # then every 3rd edit after that (8, 11, ...)
MAX_TRACKED_PATHS = 200
STALE_STATE_SECONDS = 7 * 24 * 3600

# Only tools registered in settings.example.json; failed tool calls never reach PostToolUse,
# so a loop of erroring edits is invisible to this counter (documented in the contract).
EDIT_TOOLS = ("Edit", "Write", "MultiEdit")


def state_dir():
    # User-owned dir, same convention as routing-advisor (shared /tmp is symlink-attackable)
    d = os.path.join(os.path.expanduser("~"), ".claude", "tmp")
    os.makedirs(d, exist_ok=True)
    return d


def state_path(session_id):
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", session_id or "unknown")[:64]
    return os.path.join(state_dir(), "claude-doom-loop-{}.json".format(safe))


def load_counts(path):
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            return {}
        return {k: v for k, v in data.items() if isinstance(k, str) and isinstance(v, int) and v > 0}
    except (OSError, json.JSONDecodeError, ValueError):
        return {}


def save_counts(path, counts, current_path):
    if len(counts) > MAX_TRACKED_PATHS:
        # keep the hottest paths, but never drop the one just incremented
        current = counts.get(current_path)
        counts = dict(sorted(counts.items(), key=lambda kv: -kv[1])[:MAX_TRACKED_PATHS])
        if current is not None:
            counts[current_path] = current
    try:
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(counts, fh)
        os.replace(tmp, path)
    except OSError:
        pass


def sweep_stale(current_state_path):
    # Best-effort GC of state files from old sessions
    cutoff = time.time() - STALE_STATE_SECONDS
    pattern = os.path.join(state_dir(), "claude-doom-loop-*.json")
    for p in glob.glob(pattern):
        if p == current_state_path:
            continue
        try:
            if os.path.getmtime(p) < cutoff:
                os.unlink(p)
        except OSError:
            continue


def main():
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        sys.exit(0)

    if payload.get("tool_name", "") not in EDIT_TOOLS:
        sys.exit(0)
    tool_input = payload.get("tool_input", {}) or {}
    file_path = tool_input.get("file_path") or ""
    if not file_path:
        sys.exit(0)

    try:
        spath = state_path(payload.get("session_id", ""))
        counts = load_counts(spath)
        counts[file_path] = counts.get(file_path, 0) + 1
        n = counts[file_path]
        save_counts(spath, counts, file_path)
        sweep_stale(spath)
    except OSError:
        sys.exit(0)

    if n < NUDGE_AT or (n - NUDGE_AT) % NUDGE_EVERY != 0:
        sys.exit(0)

    base = "".join(ch for ch in os.path.basename(file_path)[:80] if ch.isprintable())
    msg = (
        "Doom-loop check: this is edit #{} to {} this session. If you are "
        "iterating on a failing approach, stop and re-plan instead of pushing "
        "harder: classify the error (syntax / logic / design / environment) "
        "and adjust strategy (Problem-Solving rule). After 2+ failed "
        "root-cause attempts, invoke /second-opinion. If this is legitimate "
        "incremental work on one file, carry on.".format(n, base)
    )
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": msg,
        }
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
