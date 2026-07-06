#!/usr/bin/env python3
# ABOUTME: CODEMAP.md generator — deterministic repo orientation map from ast-grep rules + globs
# ABOUTME: Commit-stamped, token-capped; run with: uv run --no-project python3 codemap/generate.py --repo <path>

"""Generate a token-cheap orientation map (endpoints, RPC services, routes,
workspaces, layout) for a repo. Deterministic: same tree in, same map out.
No LLM, no network. The stamp carries the generating commit so staleness is
detectable by hooks and humans (see 2026-07-05_codemap-toolkit contract)."""

import argparse
import json
import os
import re
import subprocess
import sys

RULES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rules")
GENERATOR_VERSION = "v1"
DEFAULT_TOKEN_CAP = 1200
SKIP_DIRS = {".git", "node_modules", "vendor", "dist", "build", ".venv", "__pycache__", ".next", "target"}

# stack key -> (rule file, extra sg globs)
STACK_RULES = {
    "go": ("go-routes.yml", ["--globs", "!**/*_test.go"]),
    "python": ("fastapi-routes.yml", ["--globs", "!**/test_*.py", "--globs", "!**/*_test.py"]),
    "ts": ("hono-routes.yml", ["--globs", "!**/*.spec.ts", "--globs", "!**/*.test.ts"]),
    "ts-nest": ("nestjs-routes.yml", ["--globs", "!**/*.spec.ts", "--globs", "!**/*.test.ts"]),
}


def _walk_files(repo, exts, limit=20000):
    """Yield repo-relative paths with one of exts, skipping vendored dirs."""
    count = 0
    for root, dirs, files in os.walk(repo):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith("."))
        for f in sorted(files):
            if os.path.splitext(f)[1] in exts:
                yield os.path.relpath(os.path.join(root, f), repo)
                count += 1
                if count >= limit:
                    return


def detect_stacks(repo):
    """Which extractors apply. Extension/manifest based, cheap."""
    stacks = set()
    if os.path.exists(os.path.join(repo, "go.mod")) or next(_walk_files(repo, {".go"}, 1), None):
        stacks.add("go")
    if os.path.exists(os.path.join(repo, "pyproject.toml")) or next(_walk_files(repo, {".py"}, 1), None):
        stacks.add("python")
    pkg = os.path.join(repo, "package.json")
    pkg_text = ""
    if os.path.exists(pkg):
        try:
            pkg_text = open(pkg, encoding="utf-8", errors="ignore").read()
        except OSError:
            pass
    if "hono" in pkg_text:
        stacks.add("ts")
    if "@nestjs" in pkg_text:
        stacks.add("ts-nest")
    if extract_next_routes(repo):
        stacks.add("next")
    if next(_walk_files(repo, {".proto"}, 1), None):
        stacks.add("proto")
    if os.path.exists(os.path.join(repo, "pnpm-workspace.yaml")):
        stacks.add("workspace")
    return stacks


def _sg_scan(rule_file, repo, globs):
    cmd = ["sg", "scan", "--rule", os.path.join(RULES_DIR, rule_file), "--json=compact", *globs, "."]
    try:
        out = subprocess.run(cmd, cwd=repo, capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired) as e:
        print(f"codemap: sg scan failed for {rule_file}: {e}", file=sys.stderr)
        return []
    if out.returncode != 0:
        print(f"codemap: sg scan exit {out.returncode} for {rule_file}: {out.stderr[:200]}", file=sys.stderr)
        return []
    try:
        return json.loads(out.stdout or "[]")
    except json.JSONDecodeError:
        return []


def extract_route_matches(repo, stack):
    """[{method, path, handler, file, line}] for one stack key, deduped by file:line."""
    rule_file, globs = STACK_RULES[stack]
    seen, routes = set(), []
    for m in _sg_scan(rule_file, repo, globs):
        single = (m.get("metaVariables") or {}).get("single") or {}
        multi = (m.get("metaVariables") or {}).get("multi") or {}
        method = (single.get("METHOD") or single.get("DEC") or {}).get("text", "")
        path = (single.get("PATH") or {}).get("text", "")
        if not path:
            args = multi.get("ARGS") or []
            path = args[0].get("text", "") if args else ""
            if path and not re.match(r"""^["'`]""", path):
                path = ""  # decorator kwarg-only or non-literal first arg
        handler = (single.get("H") or {}).get("text", "")
        # Inline closures drag whole function bodies into the map: keep one line, capped.
        handler = handler.splitlines()[0].strip() if handler else ""
        if len(handler) > 60:
            handler = handler[:57] + "..."
        file = m.get("file", "")
        line = (m.get("range") or {}).get("start", {}).get("line", 0)
        key = (file, line)
        if method and key not in seen:
            seen.add(key)
            routes.append({"method": method, "path": path, "handler": handler, "file": file, "line": line})
    routes.sort(key=lambda r: (r["file"], r["line"]))
    return routes


def _next_app_prefix(parts):
    """Return the app-dir depth if parts live under app/ or src/app/, else None."""
    if parts[:1] == ["app"]:
        return 1
    if parts[:2] == ["src", "app"]:
        return 2
    return None


def extract_next_routes(repo):
    """File-based Next.js routes from app/ or src/app/; (group) segments stripped."""
    routes = []
    for p in _walk_files(repo, {".ts", ".tsx", ".js", ".jsx"}):
        parts = p.split(os.sep)
        depth = _next_app_prefix(parts)
        if depth is None:
            continue
        kind = os.path.basename(p).split(".")[0]
        if kind not in ("page", "route"):
            continue
        segs = [s for s in parts[depth:-1] if not (s.startswith("(") and s.endswith(")"))]
        routes.append("/" + "/".join(segs) + f" [{kind}]")
    return sorted(set(routes))


def extract_proto(repo):
    """[(service, rpc)] from .proto files."""
    out = []
    for p in _walk_files(repo, {".proto"}):
        try:
            text = open(os.path.join(repo, p), encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        for svc_m in re.finditer(r"service\s+(\w+)\s*\{(.*?)\n\}", text, re.S):
            svc, body = svc_m.group(1), svc_m.group(2)
            for rpc_m in re.finditer(r"\brpc\s+(\w+)", body):
                out.append((svc, rpc_m.group(1)))
    return sorted(out)


def extract_workspaces(repo):
    """[(dir, package-name)] from pnpm-workspace.yaml patterns."""
    ws_file = os.path.join(repo, "pnpm-workspace.yaml")
    if not os.path.exists(ws_file):
        return []
    patterns = re.findall(r"^\s*-\s*['\"]?([^'\"\n#]+?)['\"]?\s*$", open(ws_file, encoding="utf-8").read(), re.M)
    found = []
    import glob as globmod

    for pat in patterns:
        for d in sorted(globmod.glob(os.path.join(repo, pat))):
            pj = os.path.join(d, "package.json")
            if os.path.isdir(d) and os.path.exists(pj):
                try:
                    name = json.loads(open(pj, encoding="utf-8").read()).get("name", "")
                except (OSError, json.JSONDecodeError):
                    name = ""
                found.append((os.path.relpath(d, repo), name))
    return sorted(set(found))


def structural_summary(repo):
    """Cheap orientation facts for the SessionStart nudge: detected stacks and
    (if a monorepo) the workspace count. Manifest/glob only, NEVER an ast-grep
    scan, so it is safe to run on every session start."""
    stacks = detect_stacks(repo)
    if not (stacks & (set(STACK_RULES) | {"proto", "next", "workspace"})):
        return None
    parts = []
    if "workspace" in stacks:
        n = len(extract_workspaces(repo))
        if n:
            parts.append(f"{n} pnpm workspaces")
    label = {"go": "Go", "python": "Python", "ts": "Hono", "ts-nest": "NestJS",
             "next": "Next.js", "proto": "gRPC/proto"}
    langs = sorted({label.get(s, s) for s in stacks if s in label})
    if langs:
        parts.append(", ".join(langs))
    return {"stacks": stacks, "summary": "; ".join(parts) if parts else "HTTP/RPC surfaces"}


def _layout(repo):
    """Top-level directories with source-file counts."""
    rows = []
    for entry in sorted(os.listdir(repo)):
        full = os.path.join(repo, entry)
        if not os.path.isdir(full) or entry in SKIP_DIRS or entry.startswith("."):
            continue
        n = sum(1 for _ in _walk_files(full, {".go", ".py", ".ts", ".tsx", ".rb", ".js", ".swift", ".kt"}, 2000))
        rows.append((entry, n))
    return rows


def _stamp(repo):
    def _git(*args):
        try:
            r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, timeout=10)
            return r.stdout.strip() if r.returncode == 0 else ""
        except OSError:
            return ""

    sha = _git("rev-parse", "--short", "HEAD")
    ts = _git("show", "-s", "--format=%cI", "HEAD")
    if not sha:
        return f"<!-- codemap: unversioned {GENERATOR_VERSION} -->"
    return f"<!-- codemap: {sha} {ts} {GENERATOR_VERSION} -->"


def generate(repo, token_cap=DEFAULT_TOKEN_CAP):
    repo = os.path.abspath(repo)
    stacks = detect_stacks(repo)
    lines = [_stamp(repo), f"# Code Map — {os.path.basename(repo)}", ""]

    # Workspaces rank above endpoints: in a monorepo the package list is the
    # top-level orientation, and endpoints (often hundreds) are per-package detail.
    if "workspace" in stacks:
        ws = extract_workspaces(repo)
        if ws:
            lines += ["## Workspaces (pnpm)", *[f"- `{d}` — {n or '(unnamed)'}" for d, n in ws], ""]

    endpoint_rows = []
    for stack in sorted(stacks & STACK_RULES.keys()):
        for r in extract_route_matches(repo, stack):
            endpoint_rows.append(f"- `{r['method']} {r['path']}` → {r['handler'] or '-'} ({r['file']}:{r['line']})")
    if endpoint_rows:
        lines += ["## Endpoints", *endpoint_rows, ""]

    if "proto" in stacks:
        svcs = extract_proto(repo)
        if svcs:
            lines += ["## RPC services", *[f"- `{s}.{r}`" for s, r in svcs], ""]

    if "next" in stacks:
        routes = extract_next_routes(repo)
        if routes:
            lines += ["## Next.js routes", *[f"- `{r}`" for r in routes], ""]

    layout = _layout(repo)
    if layout:
        lines += ["## Layout", *[f"- `{d}/` ({n} source files)" for d, n in layout], ""]

    # Hard token cap: drop from the end (lowest-rank sections last in doc order).
    # Accepted tradeoff: truncation drops trailing lines, so on a repo with more
    # endpoints than fit, the tail of the Endpoints section is cut (sorted by
    # file:line, so roughly the last files alphabetically). Workspaces rank first,
    # so a monorepo's package list always survives; the depth that gets cut is
    # covered by the LSP layer on demand. We do NOT rank by reference centrality
    # (aider-style PageRank): that needs a resolved symbol graph, which is exactly
    # what the LSP already provides. The visible marker keeps the cut honest.
    marker = "\n*(truncated to fit token cap)*\n"
    budget = token_cap * 4 - len(marker)
    text = "\n".join(lines)
    if len(text) > token_cap * 4:
        while lines and len("\n".join(lines)) > budget:
            lines.pop()
        text = "\n".join(lines) + marker
    return text if text.endswith("\n") else text + "\n"


def main():
    ap = argparse.ArgumentParser(description="Generate CODEMAP.md for a repo")
    ap.add_argument("--repo", required=True)
    ap.add_argument("--output", default=None, help="default: <repo>/CODEMAP.md")
    ap.add_argument("--token-cap", type=int, default=DEFAULT_TOKEN_CAP)
    ap.add_argument("--print", action="store_true", dest="print_only")
    args = ap.parse_args()

    md = generate(args.repo, token_cap=args.token_cap)
    if args.print_only:
        print(md, end="")
        return
    out = args.output or os.path.join(args.repo, "CODEMAP.md")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(md)
    print(f"codemap: wrote {out} ({len(md) // 4} tokens approx)")


if __name__ == "__main__":
    main()
