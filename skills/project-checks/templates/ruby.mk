# Ruby checks
RUBOCOP ?= bundle exec rubocop
BUNDLER_AUDIT ?= bundle exec bundler-audit

.PHONY: check lint vuln test

check: lint vuln test

lint:
	$(RUBOCOP)

vuln:
	$(BUNDLER_AUDIT) check --update

test:
	bundle exec rspec
