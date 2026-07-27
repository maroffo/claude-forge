# ABOUTME: Static checks and skill schema smoke test for claude-forge
# ABOUTME: `make check` + `make test-e2e` are the pre-commit gate

.PHONY: help check test-e2e lint-shell lint-dockerfile learning-corpus doc-garden

help:
	@echo "Targets:"
	@echo "  check            static lints (ABOUTME, em-dashes, frontmatter) + shellcheck/hadolint if installed"
	@echo "  test-e2e         skill schema smoke test (name=dir, description length)"
	@echo "  learning-corpus  build the cross-repo atomic-learning corpus (phase 1 of the learning-loop skill)"
	@echo "  doc-garden       stale cross-reference scan of governance docs (phase 1 of doc-gardening)"

# Deterministic phase 1 of the doc-gardening pass (learning-loop skill).
doc-garden:
	@uv run --no-project python3 scripts/doc_gardening.py --root .

# Deterministic phase 1 of the learning-loop skill. ROOT defaults to ~/Development.
# Output is gitignored (contains private war stories). Recurrence detection is the agent pass.
learning-corpus:
	@uv run --no-project python3 scripts/learning_corpus.py \
		--root $(or $(ROOT),$(HOME)/Development) \
		--out quality_reports/learning_corpus/corpus.jsonl

check:
	@uv run --no-project python3 scripts/check_repo.py check
	@$(MAKE) --no-print-directory lint-shell
	@$(MAKE) --no-print-directory lint-dockerfile

test-e2e:
	@uv run --no-project python3 scripts/check_repo.py test-e2e
	@for t in hooks/tests/test_*.py codemap/tests/test_*.py scripts/tests/test_*.py; do \
		[ -f "$$t" ] || continue; \
		uv run --no-project python3 "$$t" || exit 1; \
	done

lint-shell:
	@if command -v shellcheck >/dev/null 2>&1; then \
		shellcheck install.sh get.sh scripts/pi-exec scripts/score-log.sh && echo "PASS  shellcheck"; \
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
