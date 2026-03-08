# ABOUTME: Deterministic file and identifier selection for large codebase sampling
# ABOUTME: SHA-256 hashing ensures identical selection across runs

"""Deterministic file and identifier selection for large codebase sampling.

Uses SHA-256 hashing to ensure identical selection across runs.
"""

import hashlib


def sha256_seed(file_path: str) -> int:
    """Compute a deterministic integer seed from a file path."""
    return int(hashlib.sha256(file_path.encode()).hexdigest()[:8], 16)


def select_files(
    paths: list[str],
    sample_pct: int = 30,
    min_loc: int = 200,
    file_locs: dict[str, int] | None = None,
) -> list[str]:
    """Select a deterministic subset of files for analysis.

    Uses SHA-256 hash modulo 100 to select ~sample_pct% of files.
    Additionally includes all files exceeding min_loc lines.
    """
    selected = set()
    sorted_paths = sorted(paths)
    for path in sorted_paths:
        if sha256_seed(path) % 100 < sample_pct:
            selected.add(path)
    if file_locs:
        for path, loc in file_locs.items():
            if loc > min_loc:
                selected.add(path)
    return sorted(selected)


def select_identifiers_for_file(
    file_path: str,
    identifiers: list[str],
    count: int = 20,
) -> list[str]:
    """Deterministically select identifiers from a file for D4 assessment.

    Uses SHA-256 of file path as seed for consistent selection.
    """
    if len(identifiers) <= count:
        return list(identifiers)
    seed = sha256_seed(file_path)
    decorated = [
        (hashlib.sha256(f"{seed}:{ident}".encode()).hexdigest(), ident)
        for ident in identifiers
    ]
    decorated.sort()
    return [ident for _, ident in decorated[:count]]
