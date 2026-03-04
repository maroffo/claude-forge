# ABOUTME: Detailed Python patterns for Docker, CI/CD, async, and testing
# ABOUTME: Reference companion to python SKILL.md with full code examples

# Python Patterns Reference

## Async Patterns

```python
async def fetch_all(ids: list[str]) -> list[User]:
    return await asyncio.gather(*[fetch_user(uid) for uid in ids])

# Rate limiting
async def fetch_limited(urls: list[str], max_concurrent: int = 10):
    sem = asyncio.Semaphore(max_concurrent)
    async def fetch(url):
        async with sem:
            async with httpx.AsyncClient() as c: return await c.get(url)
    return await asyncio.gather(*[fetch(u) for u in urls])
```

---

## Docker

```dockerfile
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache --no-dev

FROM python:3.13-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
RUN useradd --create-home --uid 1000 app
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY --chown=app:app src/ ./src/
USER app
ENV PATH="/app/.venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
CMD ["python", "-m", "myapp"]
```

---

## CI/CD (GitHub Actions)

```yaml
name: CI
on: [push, pull_request]
jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
        with: { enable-cache: true }
      - run: uv python install 3.13
      - run: uv sync --locked
      - run: uv run ruff format --check . && uv run ruff check . && uvx ty check && uv run pytest --cov
```

---

## Detailed Testing

```python
@pytest.fixture
def user_service(mock_repo): return UserService(repo=mock_repo)

def test_find_user(user_service, mock_repo):
    mock_repo.find.return_value = User(id="1", name="Max")
    assert user_service.find("1").name == "Max"

@pytest.mark.parametrize("email,expected", [("test@x.com", True), ("bad", False)])
def test_email(email, expected): assert validate_email(email) == expected
```
