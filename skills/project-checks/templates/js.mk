# JavaScript/TypeScript checks
ESLINT ?= npx eslint
TSC ?= npx tsc

.PHONY: check lint typecheck vuln test

check: lint typecheck vuln test

lint:
	$(ESLINT) .

typecheck:
	$(TSC) --noEmit

vuln:
	npm audit --audit-level=moderate

test:
	npm test
