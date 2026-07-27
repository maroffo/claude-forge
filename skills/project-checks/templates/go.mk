# Go checks
GOLANGCI_LINT ?= golangci-lint
GOVULNCHECK ?= govulncheck
CRAP4GO ?= crap4go
GREMLINS ?= gremlins
PKG ?= ./...
GOTOOLS_BIN ?= $(or $(shell go env GOBIN),$(shell go env GOPATH)/bin)

.PHONY: check lint vet fmt-check vuln test crap mutation

check: lint vet fmt-check vuln test

lint:
	$(GOLANGCI_LINT) run ./...

vet:
	go vet ./...

fmt-check:
	@test -z "$$(gofmt -l .)" || (echo "gofmt: files need formatting:" && gofmt -l . && exit 1)

vuln:
	$(GOVULNCHECK) ./...

test:
	go test -race -count=1 ./...

# Advisory, outside check. crap4go runs the suite with a coverage profile and
# reports CC, coverage and CRAP per function. The output is evidence for a
# review finding, never a gate: there is no CRAP threshold, because CRAP >= CC
# always and any fixed threshold is a cyclomatic-complexity gate in disguise.
crap:
	@PATH="$$PATH:$(GOTOOLS_BIN)"; command -v $(CRAP4GO) >/dev/null 2>&1 || go install github.com/unclebob/crap4go/cmd/crap4go@latest; $(CRAP4GO)

# Advisory, outside check, and never in the inner loop: gremlins recompiles and
# reruns the whole suite once per mutant. Invoke it on suspicion, scoped to one
# package: make mutation PKG=./internal/foo
mutation:
	@PATH="$$PATH:$(GOTOOLS_BIN)"; command -v $(GREMLINS) >/dev/null 2>&1 || go install github.com/go-gremlins/gremlins/cmd/gremlins@latest; $(GREMLINS) unleash $(PKG)
