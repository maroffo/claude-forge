# ABOUTME: CLI entry point for deterministic Farley Index calculations (JSON in, JSON out)
# ABOUTME: Invoked via Bash to ensure reproducible scoring without LLM variance

#!/usr/bin/env python3
"""CLI entry point for Farley Index calculations.

All output is JSON to stdout. Errors go to stderr.
Invoked by the test-design-reviewer agent via Bash.

Usage:
    python cli_calculator.py normalize-property '{"prop":"U","neg_count":2,"pos_count":8,"total_methods":20}'
    python cli_calculator.py compute-farley '{"U":9,"M":9,"R":9,"A":9,"N":9,"G":9,"F":9,"T":9}'
    python cli_calculator.py full-pipeline '{"properties":{"U":{"neg_count":2,"pos_count":8,"total_methods":20},...}}'
"""

import json
import sys
import warnings

# Suppress all warnings to prevent stdout contamination
warnings.filterwarnings("ignore")

from pathlib import Path  # noqa: E402

_lib_dir = str(Path(__file__).resolve().parent)
if _lib_dir not in sys.path:
    sys.path.insert(0, _lib_dir)

from scoring import (  # noqa: E402
    aggregate_file,
    aggregate_suite,
    blend_scores,
    compute_farley_index,
    full_pipeline,
    get_rating,
    normalize_property,
)


def _ok(result):
    return {"ok": True, "result": result}


def _err(message):
    return {"ok": False, "error": message}


def cmd_normalize_property(data):
    score = normalize_property(
        data["prop"],
        data["neg_count"],
        data["pos_count"],
        data["total_methods"],
        data.get("params"),
    )
    return _ok({"score": round(score, 4)})


def cmd_blend_scores(data):
    score = blend_scores(
        data["static_score"],
        data["llm_score"],
        data.get("static_weight", 0.6),
    )
    return _ok({"score": round(score, 4)})


def cmd_compute_farley(data):
    index = compute_farley_index(data)
    rating = get_rating(index)
    return _ok({"farley_index": round(index, 2), "rating": rating})


def cmd_get_rating(data):
    return _ok({"rating": get_rating(data["farley_index"])})


def cmd_aggregate_file(data):
    result = aggregate_file(data["method_scores"])
    return _ok(result)


def cmd_aggregate_suite(data):
    result = aggregate_suite(data["file_scores"], data["file_locs"])
    return _ok(result)


def cmd_full_pipeline(data):
    result = full_pipeline(data)
    return _ok(result)


COMMANDS = {
    "normalize-property": cmd_normalize_property,
    "blend-scores": cmd_blend_scores,
    "compute-farley": cmd_compute_farley,
    "get-rating": cmd_get_rating,
    "aggregate-file": cmd_aggregate_file,
    "aggregate-suite": cmd_aggregate_suite,
    "full-pipeline": cmd_full_pipeline,
}


def main():
    if len(sys.argv) < 3:
        print(
            json.dumps(_err(f"Usage: {sys.argv[0]} <command> '<json_data>'")),
            file=sys.stdout,
        )
        sys.exit(1)

    command = sys.argv[1]
    json_str = sys.argv[2]

    if command not in COMMANDS:
        print(
            json.dumps(_err(f"Unknown command: {command}. Available: {', '.join(sorted(COMMANDS))}")),
            file=sys.stdout,
        )
        sys.exit(1)

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(json.dumps(_err(f"Invalid JSON: {e}")), file=sys.stdout)
        sys.exit(1)

    try:
        result = COMMANDS[command](data)
        print(json.dumps(result), file=sys.stdout)
    except KeyError as e:
        print(json.dumps(_err(f"Missing required field: {e}")), file=sys.stdout)
        sys.exit(1)
    except Exception as e:
        print(json.dumps(_err(f"Calculation error: {e}")), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
