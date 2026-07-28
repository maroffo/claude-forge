#!/usr/bin/env python3
# ABOUTME: Executes the Auto rows of a plan's DoD table and writes dod-results.json into the evidence bundle
# ABOUTME: The script does the work, the model supplies only paths; exit 0 iff every Auto row passes

"""Usage: dod_run.py --plan <plan.md> --evidence-dir <dir> [--repo <path>] [--timeout <s>]

Parses the `## DoD` markdown table (columns: # | Criterion | Command | Expected | Auto)
from the plan file, runs each `Auto: yes` row's Command with `bash -c` in the repo
directory, and writes `dod-results.json` into the evidence dir. Manual rows are
recorded with passed=null, never executed.

Exit codes: 0 all auto rows passed; 1 at least one auto row failed (results are
still written: partial failure is recorded, never hidden); 2 usage/parse error
before any command ran.
"""

import argparse
import json
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

ROW_RE = re.compile(r"^\s*\|(.+)\|\s*$")
SEPARATOR_RE = re.compile(r"^[\s|:-]+$")
EXPECTED_HEADER = ["#", "criterion", "command", "expected", "auto"]
CELL_SPLIT_RE = re.compile(r"(?<!\\)\|")  # cells may carry shell pipes as `\|`

# Command cells reach `bash -c`. Plans can be seeded from GitHub issue text
# (plan-forge <- gh issue view), which anyone can write, and dod_run executes
# OUTSIDE Claude Code's Bash permission layer — so commands are constrained to
# a conservative prefix allowlist. Callers extend it per repo with --allow;
# a non-allowlisted command is recorded as a failed row, never executed.
DEFAULT_ALLOWED_PREFIXES = (
    "make ", "make", "./scripts/", "bash scripts/", "sh scripts/",
    "go test", "go vet", "go build", "uv run ", "pytest",
)


def allowed(command, extra_prefixes):
    return any(command.startswith(p) for p in (*DEFAULT_ALLOWED_PREFIXES, *extra_prefixes))


def die(msg):
    print(f"dod_run: {msg}", file=sys.stderr)
    sys.exit(2)


def parse_dod_table(plan_text):
    """Return the list of row dicts from the ## DoD section's first table."""
    lines = plan_text.splitlines()
    try:
        start = next(i for i, l in enumerate(lines) if l.strip().lower().startswith("## dod"))
    except StopIteration:
        die("no '## DoD' section in the plan")
    rows, header_seen = [], False
    for line in lines[start + 1:]:
        if line.startswith("## "):  # next section
            break
        m = ROW_RE.match(line)
        if not m:
            continue
        cells = [c.strip().replace("\\|", "|") for c in CELL_SPLIT_RE.split(m.group(1))]
        if not header_seen:
            if [c.lower() for c in cells] != EXPECTED_HEADER:
                die(f"DoD table header must be {EXPECTED_HEADER}, got {cells}")
            header_seen = True
            continue
        if SEPARATOR_RE.match(m.group(1).replace("|", "")):
            continue
        if len(cells) != len(EXPECTED_HEADER):
            die(f"DoD row has {len(cells)} cells, expected {len(EXPECTED_HEADER)}: {line!r}")
        rows.append(dict(zip(("id", "criterion", "command", "expected", "auto"), cells)))
    if not header_seen or not rows:
        die("no parseable DoD table found under '## DoD'")
    return rows


def clean_command(cell):
    """Strip markdown code formatting; `—`/`-`/empty means no command."""
    cmd = cell.strip().strip("`").strip()
    return "" if cmd in ("", "-", "—") else cmd


def execute(command, repo, timeout):
    """Run command in its own process group so a timeout kills grandchildren too
    (a backgrounded daemon holding stdout would otherwise hang the read forever)."""
    proc = subprocess.Popen(
        ["bash", "-c", command], cwd=str(repo),
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        start_new_session=True,
    )
    try:
        out, _ = proc.communicate(timeout=timeout)
        return proc.returncode, (out or "")[-2000:]
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
        proc.wait()
        return -1, f"timeout after {timeout}s (process group killed)"


def run_rows(rows, repo, timeout, extra_prefixes):
    results, overall_pass = [], True
    for row in rows:
        auto = row["auto"].strip().lower() == "yes"
        entry = {
            "id": row["id"],
            "criterion": row["criterion"],
            "auto": auto,
            "command": clean_command(row["command"]) if auto else "",
            "expected": row["expected"],
            "exit_code": None,
            "passed": None,
            "duration_s": None,
            "output_tail": None,
        }
        if auto:
            if not entry["command"]:
                # An Auto row without a runnable command is a plan defect, not a pass.
                entry["passed"] = False
                entry["exit_code"] = -1
                entry["output_tail"] = "auto row without a runnable command"
                overall_pass = False
            elif not allowed(entry["command"], extra_prefixes):
                entry["passed"] = False
                entry["exit_code"] = -1
                entry["output_tail"] = (
                    "command not on the allowlist, not executed "
                    "(extend with --allow '<prefix>' if legitimate)"
                )
                overall_pass = False
            else:
                start = time.monotonic()
                entry["exit_code"], entry["output_tail"] = execute(
                    entry["command"], repo, timeout
                )
                entry["passed"] = entry["exit_code"] == 0
                entry["duration_s"] = round(time.monotonic() - start, 1)
                overall_pass = overall_pass and entry["passed"]
        results.append(entry)
    return results, overall_pass


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--plan", required=True)
    ap.add_argument("--evidence-dir", required=True)
    ap.add_argument("--repo", default=".")
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--allow", action="append", default=[],
                    help="additional allowed command prefix (repeatable)")
    args = ap.parse_args()

    plan = Path(args.plan)
    if not plan.is_file():
        die(f"plan file not found: {plan}")
    repo = Path(args.repo)
    if not repo.is_dir():
        die(f"repo dir not found: {repo}")
    evidence_dir = Path(args.evidence_dir)
    if not evidence_dir.is_dir():
        die(f"evidence dir not found (run the bundle first): {evidence_dir}")

    rows = parse_dod_table(plan.read_text(encoding="utf-8"))
    results, overall_pass = run_rows(rows, repo, args.timeout, tuple(args.allow))

    out = {
        "schema_version": 1,
        "plan": str(plan),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "overall_pass": overall_pass,
        "auto_rows": sum(1 for r in results if r["auto"]),
        "manual_rows": sum(1 for r in results if not r["auto"]),
        "rows": results,
    }
    (evidence_dir / "dod-results.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    for r in results:
        state = "PASS" if r["passed"] else ("FAIL" if r["passed"] is False else "manual")
        print(f"  [{state}] {r['id']} {r['criterion'][:70]}")
    print(f"dod_run: {'PASS' if overall_pass else 'FAIL'} "
          f"({out['auto_rows']} auto, {out['manual_rows']} manual) -> {evidence_dir / 'dod-results.json'}")
    sys.exit(0 if overall_pass else 1)


if __name__ == "__main__":
    main()
