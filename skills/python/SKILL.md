---
name: python
description: "Python development with uv, type checking, linting, testing, and Docker deployment. Use when working with .py files, pyproject.toml, or user asks about pytest, mypy, ruff, FastAPI, Django."
compatibility: "Requires uv. Optional: ruff, ty."
allowed-tools: [mcp__acp__Read, mcp__acp__Edit, mcp__acp__Write, mcp__acp__Bash]
---

# ABOUTME: Complete Python development with uv package manager, quality tools, and Docker
# ABOUTME: Modern workflow with uv, ruff, ty, pytest, Pydantic, and containerization

# Python Development

## Quick Reference

```bash
uv init myproject && cd myproject
uv add requests pydantic httpx
uv add --dev pytest ruff
uv sync --locked
uv run python main.py
uv run ruff check . && uv run ruff format --check . && uvx ty check && uv run pytest
```

**See also:** `_AST_GREP.md`, `_PATTERNS.md`, `source-control`

---

## Version (determine, don't assume)

Never assume a Python version from prior knowledge: it rots fast and you miss CVE fixes. Fetch the truth:

```bash
python3 --version                                                      # local interpreter
cat .python-version 2>/dev/null                                        # pin file (if present)
grep -E '^python' pyproject.toml 2>/dev/null                           # project manifest
curl -s https://endoflife.date/api/python.json | jq -r '.[0].latest'   # latest upstream stable
```

For a new project, pin to the latest stable. For an existing one, read `pyproject.toml` / `.python-version` and prefer idioms gated to that version or lower.

---

## Pre-Commit Verification (MANDATORY)

Before every commit, both of these MUST pass:

```bash
make check       # project-wide gate (lint, types, tests, security)
make test-e2e    # end-to-end tests (or the project's e2e target)
```

If `make check` is missing, scaffold it with the `project-checks` skill. If there is no e2e target, do NOT silently skip: flag it to the user and ask whether to proceed or add one.

Full raw toolchain (what `make check` should expand to):

```bash
uv run ruff check .
uv run ruff format --check .
uvx ty check
uv run pytest --cov=myproject
```

---

## Package Management (uv)

**UV is the ONLY way. Do NOT use pip/poetry/pipenv.** Universal lockfile, fast resolver.

### pyproject.toml
```toml
[project]
name = "myproject"
requires-python = ">=3.13"
dependencies = ["httpx>=0.27.0", "pydantic>=2.10.0"]

[dependency-groups]
dev = ["pytest>=8.0.0", "ruff>=0.8.0"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

---

## Code Quality

**Ruff config:**

```toml
[tool.ruff]
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM", "TCH", "RUF", "PERF"]
```

**Testing:** pytest with fixtures, AAA pattern, parametrize. Coverage via `--cov`.

---

## Pydantic v2

Use Pydantic for all external data boundaries (API I/O, config, queue payloads). Prefer `model_validate_json` over parse-then-validate. `Field(...)` for constraints, `@field_validator` for custom rules.

---

## Code Review Checklist

- [ ] Public functions have type hints, no unjustified `Any`
- [ ] Pydantic for external data, `X | None` not `Optional[X]`
- [ ] Ruff/type checker pass, no bare `except:`
- [ ] Context managers, `asyncio.gather()` for concurrency
- [ ] **Async is not concurrent**: no single stateful client (e.g. SQLAlchemy `AsyncSession`) shared across `gather()` tasks; one session per task via a factory. A shared session corrupts under concurrent use.
- [ ] **No CPU-bound work inside `async def`** without `asyncio.to_thread` (parsing, hashing, rendering): it blocks the event loop and serializes every concurrent task. Rule of thumb: a function that `await`s nothing probably needs `to_thread`.
- [ ] AAA tests, parametrized

For Docker, CI/CD, async patterns, and detailed testing examples, see `references/python-patterns.md`.

---

## Resources

**Astral**: [uv](https://docs.astral.sh/uv/), [Ruff](https://docs.astral.sh/ruff/), [ty](https://docs.astral.sh/ty/)
**Python**: [pytest](https://docs.pytest.org/), [Pydantic](https://docs.pydantic.dev/)
