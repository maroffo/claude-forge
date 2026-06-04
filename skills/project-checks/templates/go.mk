# Go checks
GOLANGCI_LINT ?= golangci-lint
GOVULNCHECK ?= govulncheck

.PHONY: check lint vet fmt-check vuln test

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
