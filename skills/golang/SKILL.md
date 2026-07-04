---
name: golang
description: "Go development: conventions, architecture, concurrency, performance, and code review. Use when working with .go files, go.mod, or user asks about goroutines, channels, error handling, interfaces."
compatibility: "Requires Go compiler. Optional: golangci-lint."
allowed-tools: [mcp__acp__Read, mcp__acp__Edit, mcp__acp__Write, mcp__acp__Bash]
---

# ABOUTME: Complete Go development guide - code, design, concurrency, performance, review
# ABOUTME: Conventions, error layering, concurrency rules, modern stdlib preferences

# Go Development

## Quick Reference

```bash
gofmt -w . && goimports -w . && go fix ./... && go vet ./...
go test ./... && go test -race ./... && go test -cover ./...
govulncheck ./...
go build -pgo=cpu.pprof -o bin/app ./cmd/app
golangci-lint run
```

**See also:** `_AST_GREP.md`, `_PATTERNS.md`, `source-control`

---

## Version (determine, don't assume)

See `../_LANG_COMMON.md`. Fetch the truth:

```bash
go version                                      # project toolchain (for existing repos: also check go.mod)
curl -s https://go.dev/VERSION?m=text | head -1 # latest upstream stable (for new projects)
```

---

## Pre-Commit Verification (MANDATORY)

`make check && make test-e2e` must pass (enforced by the `pre-commit-gate` hook; see `../_LANG_COMMON.md`). What `make check` expands to for Go:

```bash
gofmt -w .                    # Fix formatting FIRST (sqlc/codegen can misalign)
go fix ./... && go fix ./...  # Run twice for synergistic fixes
go vet ./...                  # Static analysis
go build ./...                # Compilation check
go test -race -count=1 ./...  # Tests with race detector
govulncheck ./...             # Reachable vulnerability scan
golangci-lint run             # Lint
```

**Why gofmt before build:** Code generators (sqlc, protoc) may produce code `gofmt` disagrees with. Always run `gofmt -w` after regeneration and before commit.

**`go fix` modernizers** are version-gated by `go.mod`. Preview with `go fix -diff ./...`. List with `go tool fix help`.

---

## Code Conventions

**Formatting:** `gofmt`/`goimports`: NON-NEGOTIABLE.

**Naming:** Short vars in funcs (`i`, `c`), descriptive at pkg level (`ErrNotFound`). Receivers 1-2 letter (`c *Client`). Initialisms all-caps or all-lower (`ServeHTTP`, `appID`). Packages lowercase singular.

**Errors:** Always handle (never `_`). Wrap: `fmt.Errorf("decompress %v: %w", name, err)`. Lowercase, no punctuation, guard clauses. Never wrap `io.EOF` (callers use `==`).

**Error layering:** Repo wraps infra errors with context. Service translates to domain sentinels (`ErrUserNotFound`, `ErrInsufficientFunds`). Handler maps sentinels to HTTP/gRPC codes. Log errors **only at system boundaries** (handlers, consumers, workers), not at every layer.
```go
// Domain sentinels
var ErrUserNotFound = errors.New("user not found")

// Service: translate infra → domain
if errors.Is(err, sql.ErrNoRows) { return nil, ErrUserNotFound }

// Handler: map domain → HTTP
if errors.Is(err, ErrUserNotFound) { http.Error(w, "not found", 404); return }
```

**Structured errors (APIs only):** For HTTP/gRPC APIs needing machine-readable error codes in responses, define an `AppError` type with `Code`/`Message`/wrapped cause. Not needed for CLIs, workers, or internal packages: use sentinels + `%w` wrapping.

**Testing:** Table-driven with `t.Run()`, `t.Helper()` in helpers, `t.Context()` for cancellation.

**Function literals:** Extract complex callbacks into named vars. Nested literals around `slices`/`maps`/iterators hurt readability fast.

**Build tags for simulation:** `//go:build simulation` in `driver_sim.go`, `//go:build !simulation` in `driver_real.go`. Same type, different impl. Use for hardware, external APIs, infra deps.

---

## Architecture & Design

**Project structure:**
```
cmd/api-server/main.go    # Entry points
internal/domain/          # Business entities
internal/service/         # Use cases
internal/repository/      # Data access
```
Organize by **feature/domain**, not technical layer. Avoid `/src`, `/utils`, `/common`, `/helpers`.

**Functional Options:** preferred for optional configuration (`WithX(...) Option` + `NewServer(opts ...Option)`).

**Constructor Injection:** Accept interfaces, return structs. **No global mutable state**: pass deps explicitly.

**Interfaces:** Small (1-3 methods), accept interfaces, return structs.

**Useful Zero Values:** Uninitialized struct = safe to use or obviously invalid. Stdlib examples: `sync.Mutex`, `bytes.Buffer`.

---

## Concurrency

**Golden Rules:**
- Always know WHEN and HOW a goroutine terminates
- **Libraries are synchronous**: never launch goroutines from lib code unless concurrency IS the feature

**errgroup** (preferred over WaitGroup), **context** always first param, **bounded pools** for load, **sender closes** channels.

**Cancellation traps (review these explicitly, they pass tests and hang/panic in prod):**
- `for x := range ch` over an externally-produced channel (network stream, LLM provider) has no `ctx.Done()` injection point. If the producer hangs, the consumer hangs forever. Use `select { case x, ok := <-ch: ...; case <-ctx.Done(): return }`. Bare `range` is fine only when you own the channel's lifecycle and it is guaranteed to close.
- `nil` passed as a `context.Context` argument: `<-nil` in a select never fires, so cancellation silently does nothing (and `ParseSSE(nil, ...)`-style calls panic on first cancel in prod). Grep for `nil` context args.
- Unbuffered hub/notify channels that block forever if the receiving goroutine has already exited (shutdown deadlock). Pair every blocking send with a `select` on `ctx.Done()`.
- A goroutine writing a shared buffer (`bytes.Buffer`) that another path reads: data race in tests, corruption in prod.

For detailed concurrency patterns, performance optimization, profiling, and code review checklists, see `references/golang-patterns.md`.

---

## Resources

[Effective Go](https://go.dev/doc/effective_go) | [Code Review Comments](https://go.dev/wiki/CodeReviewComments) | [Release Notes](https://go.dev/doc/) | [goperf.dev](https://goperf.dev/) | [fgprof](https://github.com/felixge/fgprof)
