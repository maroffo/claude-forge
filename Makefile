# ABOUTME: Static checks and skill schema smoke test for claude-forge
# ABOUTME: `make check` + `make test-e2e` are the pre-commit gate

.PHONY: help check test-e2e lint-shell lint-dockerfile

help:
	@echo "Targets:"
	@echo "  check       static lints (ABOUTME, em-dashes, frontmatter) + shellcheck/hadolint if installed"
	@echo "  test-e2e    skill schema smoke test (name=dir, description length)"

check:
	@uv run --no-project python3 scripts/check_repo.py check
	@$(MAKE) --no-print-directory lint-shell
	@$(MAKE) --no-print-directory lint-dockerfile

test-e2e:
	@uv run --no-project python3 scripts/check_repo.py test-e2e

lint-shell:
	@if command -v shellcheck >/dev/null 2>&1; then \
		shellcheck install.sh get.sh && echo "PASS  shellcheck"; \
	else \
		echo "SKIP  shellcheck (install with: brew install shellcheck)"; \
	fi

lint-dockerfile:
	@if command -v hadolint >/dev/null 2>&1; then \
		fail=0; \
		for f in docker/*/Dockerfile; do \
			[ -f "$$f" ] && { hadolint "$$f" || fail=1; }; \
		done; \
		[ "$$fail" = "0" ] && echo "PASS  hadolint" || { echo "FAIL  hadolint"; exit 1; }; \
	else \
		echo "SKIP  hadolint (install with: brew install hadolint)"; \
	fi
