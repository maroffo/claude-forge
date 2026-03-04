---
name: python
description: "Python development with uv, type checking, linting, testing, and Docker deployment. Use when working with .py files, pyproject.toml, or user asks about pytest, mypy, ruff, FastAPI, Django."
compatibility: "Requires uv. Optional: ruff, ty."
allowed-tools: [mcp__acp__Read, mcp__acp__Edit, mcp__acp__Write, mcp__acp__Bash]
---

# ABOUTME: Complete Python development with uv package manager, quality tools, and Docker
# ABOUTME: Modern workflow with uv, ruff, ty, pytest, Pydantic, and containerization

# Python Development

## What's New (2025-2026)

### Python 3.14 (Oct 2025)
- **Template strings (PEP 750)**: `t"Hello {name}"` - safe SQL/HTML interpolation
- **Incremental GC**: 10ms pauses (was 100ms)
- **uuid7**: Time-ordered UUIDs (better for DBs)
- **Remote pdb**: `python -p PID`

### Tooling
| Tool | Notes |
|------|-------|
| ty | Astral's type checker, 10-60x faster than mypy |
| Ruff 0.8+ | Type-aware linting, 800+ rules |
| uv 0.5+ | Stable, production-ready |

## Quick Reference

```bash
uv init myproject && cd myproject              # New project
uv add requests pydantic httpx                 # Add deps
uv add --dev pytest ruff                       # Dev deps
uv sync --locked                               # CI-safe sync
uv run python main.py                          # Run code
uv run ruff check . && uv run ruff format --check . && uvx ty check && uv run pytest  # Quality
```

**Target: Python 3.13** | **See also:** `_AST_GREP.md`, `_PATTERNS.md`, `source-control`

---

## Package Management (uv)

**UV is the ONLY way. Do NOT use pip/poetry/pipenv.** 10-100x faster, universal lockfile.

### pyproject.toml
```toml
[project]
name = "myproject"
version = "0.1.0"
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

**Type checking:** `uvx ty check`

**Linting (Ruff):** `uv run ruff check . && uv run ruff format --check .`

```toml
[tool.ruff]
line-length = 100
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM", "TCH", "RUF", "PERF"]
```

**Testing:** `uv run pytest --cov=myproject --cov-report=html`. Fixtures, AAA pattern, parametrize.

---

## Pydantic v2

```python
from pydantic import BaseModel, Field, field_validator

class User(BaseModel):
    id: int
    name: str = Field(min_length=1, max_length=100)
    email: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v): return v.lower() if "@" in v else raise ValueError("Invalid")

# Performance
user = User.model_validate_json('{"id":1,"name":"Max","email":"m@x.com"}')  # Fast JSON
```

---

## Code Review Checklist

- [ ] Public functions have type hints, no unjustified `Any`
- [ ] Pydantic for external data, `X | None` not `Optional[X]`
- [ ] Ruff/type checker pass, no bare `except:`
- [ ] Context managers, `asyncio.gather()` for concurrency
- [ ] AAA tests, parametrized

For Docker, CI/CD, async patterns, and detailed testing examples, see `references/python-patterns.md`.

---

## Resources

**Astral**: [uv](https://docs.astral.sh/uv/), [Ruff](https://docs.astral.sh/ruff/), [ty](https://docs.astral.sh/ty/)
**Python**: [pytest](https://docs.pytest.org/), [Pydantic](https://docs.pydantic.dev/)
