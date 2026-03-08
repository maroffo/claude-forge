#!/usr/bin/env python3
# ABOUTME: CLI entry point for Cognitive Load Index calculations
# ABOUTME: JSON in/out via Bash, deterministic scoring for all 8 dimensions + aggregation

"""CLI entry point for Cognitive Load Index calculations.

All output is JSON to stdout. Errors go to stderr.

Usage:
    python3 cli_calculator.py normalize-d1 '{"complexity_scores": [5, 10, 15]}'
    python3 cli_calculator.py aggregate '{"D1": 0.45, "D2": 0.32, ...}'
    python3 cli_calculator.py sample-files '{"file_paths": [...], "file_locs": {...}}'
"""

import json
import sys
import warnings

warnings.filterwarnings("ignore")

from pathlib import Path

_lib_dir = str(Path(__file__).resolve().parent)
if _lib_dir not in sys.path:
    sys.path.insert(0, _lib_dir)

from aggregation import aggregate_polyglot, compute_cli_score, get_rating  # noqa: E402
from dimensions import (  # noqa: E402
    normalize_d1,
    normalize_d2,
    normalize_d3,
    normalize_d4_fallback,
    normalize_d4_static,
    normalize_d4_with_llm,
    normalize_d5,
    normalize_d6_class,
    normalize_d6_module,
    normalize_d7,
    normalize_d8,
)
from sampling import select_files, select_identifiers_for_file  # noqa: E402


def _ok(result):
    return {"ok": True, "result": result}


def _err(message):
    return {"ok": False, "error": message}


COMMANDS = {
    "normalize-d1": lambda d: _ok(normalize_d1(d["complexity_scores"])),
    "normalize-d2": lambda d: _ok(normalize_d2(d["nesting_depths"])),
    "normalize-d3": lambda d: _ok(normalize_d3(d["func_locs"], d["file_locs"], d["param_counts"], d["methods_per_class"])),
    "normalize-d4-static": lambda d: _ok(normalize_d4_static(d["short_name_proportion"], d["abbreviation_density"], d["single_char_per_100loc"], d["consistency_ratio"])),
    "normalize-d4-llm": lambda d: _ok(normalize_d4_with_llm(d["d4_static"], d["llm_score"])),
    "normalize-d4-fallback": lambda d: _ok(normalize_d4_fallback(d["short_name_proportion"], d["abbreviation_density"], d["single_char_per_100loc"], d["consistency_ratio"], d["dictionary_coverage"])),
    "normalize-d5": lambda d: _ok(normalize_d5(d["efferent_couplings"], d["imports_per_file"], d["afferent_couplings"])),
    "normalize-d6-class": lambda d: _ok(normalize_d6_class(d["lcom_values"])),
    "normalize-d6-module": lambda d: _ok(normalize_d6_module(d["avg_exports_used_together"], d["total_exports"])),
    "normalize-d7": lambda d: _ok(normalize_d7(d["duplication_pct"])),
    "normalize-d8": lambda d: _ok(normalize_d8(d["max_directory_depth"], d["files_per_directory"], d["file_sizes"])),
    "aggregate": lambda d: _ok((lambda r: {"cli_score": r.cli_score, "rating": r.rating, "cli_raw": r.cli_raw, "interaction_penalty": r.interaction_penalty, "weighted_components": r.weighted_components})(compute_cli_score(d))),
    "aggregate-polyglot": lambda d: _ok(aggregate_polyglot(d["language_scores"])),
    "sample-files": lambda d: _ok({"selected_files": (s := select_files(d["file_paths"], d.get("sample_pct", 30), d.get("min_loc", 200), d.get("file_locs"))), "count": len(s)}),
    "sample-identifiers": lambda d: _ok({"selected_identifiers": (s := select_identifiers_for_file(d["file_path"], d["identifiers"], d.get("count", 20))), "count": len(s)}),
    "rating": lambda d: _ok({"rating": get_rating(d["score"])}),
}


def main():
    if len(sys.argv) < 3:
        print(json.dumps(_err(f"Usage: {sys.argv[0]} <command> '<json_data>'")))
        sys.exit(1)

    command = sys.argv[1]
    if command not in COMMANDS:
        print(json.dumps(_err(f"Unknown command: {command}. Available: {', '.join(sorted(COMMANDS))}")))
        sys.exit(1)

    try:
        data = json.loads(sys.argv[2])
    except json.JSONDecodeError as e:
        print(json.dumps(_err(f"Invalid JSON: {e}")))
        sys.exit(1)

    try:
        print(json.dumps(COMMANDS[command](data)))
    except KeyError as e:
        print(json.dumps(_err(f"Missing required field: {e}")))
        sys.exit(1)
    except Exception as e:
        print(json.dumps(_err(f"Calculation error: {e}")), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
