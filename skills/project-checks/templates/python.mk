# Python checks (via uv)
UV ?= uv

.PHONY: check lint typecheck vuln test

check: lint vuln test

lint:
	$(UV) run ruff check .

vuln:
	$(UV) run pip-audit

test:
	$(UV) run pytest
