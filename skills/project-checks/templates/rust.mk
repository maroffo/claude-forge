# Rust checks
CARGO_AUDIT ?= cargo audit

.PHONY: check lint fmt-check vuln test

check: lint fmt-check vuln test

lint:
	cargo clippy -- -D warnings

fmt-check:
	cargo fmt -- --check

vuln:
	$(CARGO_AUDIT)

test:
	cargo test
