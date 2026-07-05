#!/usr/bin/env python3
# ABOUTME: Tests for codemap/generate.py — fixture repos through the real extractors
# ABOUTME: Run with: uv run --no-project python3 codemap/tests/test_generate.py (requires sg on PATH)

import importlib.util
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures")


def load_generator():
    path = os.path.join(HERE, "..", "generate.py")
    spec = importlib.util.spec_from_file_location("codemap_generate", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fx(name):
    return os.path.join(FIXTURES, name)


def main():
    if not shutil.which("sg"):
        sys.exit("FAIL  codemap-generate: ast-grep (sg) not on PATH; install it (brew install ast-grep)")
    g = load_generator()

    # --- Go: chi + net/http, chained receivers, variable paths, tests excluded
    eps = g.extract_route_matches(fx("gochi"), "go")
    paths = {e["path"] for e in eps}
    assert '"/health"' in paths, f"chi Get missing: {paths}"
    assert "configPath" in paths, f"variable path missing: {paths}"
    assert 'configPath+"/test"' in paths, f"expression path missing: {paths}"
    assert '"/v1"' in paths and '"/admin"' in paths, f"Mount/Route missing: {paths}"
    assert '"/metrics"' in paths, f"net/http HandleFunc missing: {paths}"
    assert '"/should-not-appear"' not in paths, "route from _test.go leaked into the map"
    methods = {e["method"] for e in eps}
    assert {"Get", "Post", "Mount", "Route", "HandleFunc"} <= methods, methods
    assert all("\n" not in e["handler"] and len(e["handler"]) <= 60 for e in eps), \
        "closure handlers must be collapsed to one capped line"
    long_h = [e["handler"] for e in eps if e["path"] == '"/long"']
    assert long_h and long_h[0].endswith("..."), f"long handler must be truncated with ...: {long_h}"

    # --- FastAPI: app + router decorators
    eps = g.extract_route_matches(fx("fastapi"), "python")
    got = {(e["method"], e["path"]) for e in eps}
    assert ("get", '"/health"') in got, got
    assert ("post", '"/"') in got, got

    # --- Hono + NestJS (both TypeScript)
    eps = g.extract_route_matches(fx("hono"), "ts")
    got = {(e["method"], e["path"]) for e in eps}
    assert ("get", '"/health"') in got, got
    assert ("post", '"/webhooks/stripe"') in got, got
    assert ("route", '"/api/v1"') in got, got

    eps = g.extract_route_matches(fx("nestjs"), "ts-nest")
    got = {(e["method"], e["path"]) for e in eps}
    assert ("Controller", '"users"') in got, got
    assert ("Post", '"invite"') in got, got
    assert ("Get", "") in got, got  # @Get() with no path

    # --- Next.js file-based routes: parentheses groups stripped, app/ and src/app/
    routes = g.extract_next_routes(fx("nextapp"))
    assert "/api/health [route]" in routes, routes
    assert "/users [page]" in routes, routes
    assert not any("(dashboard)" in r for r in routes), routes
    assert "next" in g.detect_stacks(fx("nextapp"))
    src_routes = g.extract_next_routes(fx("nextsrc"))
    assert "/dashboard [page]" in src_routes, f"src/app not detected: {src_routes}"
    assert "next" in g.detect_stacks(fx("nextsrc"))

    # --- proto services
    svcs = g.extract_proto(fx("proto"))
    assert ("Telemetry", "Ingest") in svcs and ("Telemetry", "Stream") in svcs, svcs

    # --- pnpm workspaces
    ws = g.extract_workspaces(fx("workspace"))
    assert ("services/api", "@acme/api") in ws, ws
    assert ("lib/shared", "@acme/shared") in ws, ws

    # --- stack detection: membership and absence (kills a detect-everything tautology)
    assert "go" in g.detect_stacks(fx("gochi"))
    assert "python" in g.detect_stacks(fx("fastapi"))
    assert "workspace" in g.detect_stacks(fx("workspace"))
    assert "proto" in g.detect_stacks(fx("proto"))
    assert "next" not in g.detect_stacks(fx("gochi")), "Go fixture must not detect as Next"
    assert "workspace" not in g.detect_stacks(fx("fastapi")), "no pnpm-workspace.yaml, no workspace stack"

    # --- workspace ranks above endpoints (monorepo orientation first)
    ws_repo_md = g.generate(fx("workspace"))
    # fixture has no endpoints; assert the section renders and precedes any Endpoints/Layout
    assert "## Workspaces (pnpm)" in ws_repo_md
    assert ws_repo_md.index("## Workspaces") < (ws_repo_md.find("## Layout") if "## Layout" in ws_repo_md else len(ws_repo_md))

    # --- full render: stamp header, determinism, token cap
    md1 = g.generate(fx("gochi"))
    md2 = g.generate(fx("gochi"))
    assert md1 == md2, "generator is not deterministic"
    assert re.match(r"<!-- codemap: [0-9a-f]{7,40}|<!-- codemap: unversioned", md1), md1.splitlines()[0]
    assert "/health" in md1

    tiny = g.generate(fx("gochi"), token_cap=40)
    assert len(tiny) <= 40 * 4 + 2, f"cap not enforced: {len(tiny)} chars > {40*4}"
    assert "truncated" in tiny, "truncation must be visible, not silent"

    print("PASS  codemap-generate (8 groups)")


if __name__ == "__main__":
    main()
