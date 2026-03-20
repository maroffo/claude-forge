---
name: golang
description: "Go development: conventions, architecture, concurrency, performance, and code review. Use when working with .go files, go.mod, or user asks about goroutines, channels, error handling, interfaces."
compatibility: "Requires Go compiler. Optional: golangci-lint."
allowed-tools: [mcp__acp__Read, mcp__acp__Edit, mcp__acp__Write, mcp__acp__Bash]
---

# ABOUTME: Complete Go development guide - code, design, concurrency, performance, review
# ABOUTME: Modern Go (1.22-1.26): error layering, stdlib router, Green Tea GC, modern stdlib prefs

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

## Pre-Commit Verification (MANDATORY)

```bash
gofmt -w .                    # Fix formatting FIRST (sqlc/codegen can misalign)
go fix ./... && go fix ./...  # 1.26+: 25 modernizers (run twice for synergistic fixes)
go vet ./...                  # Static analysis
go build ./...                # Compilation check
go test -race -count=1 ./...  # Tests with race detector
govulncheck ./...             # Reachable vulnerability scan
golangci-lint run             # Lint
```

**Why gofmt before build:** Code generators (sqlc, protoc) may produce code `gofmt` disagrees with. Always run `gofmt -w` after regeneration and before commit.

**`go fix` in 1.26+:** Completely rewritten with 25 modernizers on the `go/analysis` framework. Auto-rewrites: `interface{}`→`any`, `sort.Slice`→`slices.Sort`, `wg.Add+go`→`wg.Go`, `errors.As`→`errors.AsType[T]`, `omitempty`→`omitzero`, C-style loops→`range int`, and more. Version-gated by `go.mod` directive. Run twice (synergistic fixes). Preview with `go fix -diff ./...`. List fixers: `go tool fix help`.

---

## Modern Go (1.22+)

**1.22:** Loop var fix (each iteration owns its variable). Range over int: `for i := range 10`. Stdlib router: `mux.HandleFunc("GET /api/v1/feed/{id}", h)` + `r.PathValue("id")`.

**1.23:** `iter.Seq[T]` lazy sequences (use sparingly). `time.Tick` now GC-safe (no more leak). `maps.Keys`, `slices.Collect`, `slices.Sorted`.

**1.24:** `t.Context()` auto-cancelled test context. `omitzero` JSON tag (fixes `omitempty` for Duration/structs). `b.Loop()` for benchmarks. `strings.SplitSeq` lazy iteration (avoids slice alloc).

**1.25:** Container-aware GOMAXPROCS, Green Tea GC (experimental), `sync.WaitGroup.Go()`.

**1.26:** Green Tea GC default ON (10-40% lower overhead), `new(42)`, `errors.AsType[T]`, self-referential generics, ~30% faster cgo, `go fix` rewritten (25 modernizers). Goroutine leak detection (`/debug/pprof/goroutineleak`) requires `GOEXPERIMENT=goroutineleakprofile`.

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

**Structured errors (APIs only):** For HTTP/gRPC APIs needing error codes in responses:
```go
type AppError struct {
    Code    string // "USER_NOT_FOUND", machine-readable
    Message string // Human-readable
    Err     error  // Wrapped cause
}
func (e *AppError) Error() string { return fmt.Sprintf("%s: %s", e.Code, e.Message) }
func (e *AppError) Unwrap() error { return e.Err }
```
Not needed for CLIs, workers, or internal packages: use sentinels + `%w` wrapping.

**Testing:** Table-driven with `t.Run()`, use `t.Helper()` in helpers.
```go
tests := []struct{ name string; a, b, want int }{
    {"positive", 2, 3, 5},
}
for _, tt := range tests {
    t.Run(tt.name, func(t *testing.T) {
        if got := Add(tt.a, tt.b); got != tt.want {
            t.Errorf("Add(%d,%d)=%d; want %d", tt.a, tt.b, got, tt.want)
        }
    })
}
```

**Function literals:** Extract complex callbacks into named vars. Especially with iterators and functional stdlib (`slices`, `maps`), nested literals hurt readability fast.
```go
// bad: nested, hard to scan
for k, v := range slices.Sorted(func(yield func(string, int) bool) {
    for k, v := range m { yield(k, v) }
}) { fmt.Println(k, v) }

// good: named, intent is clear
byKey := func(yield func(string, int) bool) {
    for k, v := range m { yield(k, v) }
}
for k, v := range slices.Sorted(byKey) { fmt.Println(k, v) }
```

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

**Functional Options:**
```go
type Option func(*Server)
func WithPort(p int) Option { return func(s *Server) { s.port = p } }
func NewServer(opts ...Option) *Server { /* apply opts */ }
```

**Constructor Injection:** Accept interfaces, return structs. **No global mutable state**: pass deps explicitly.

**Interfaces:** Small (1-3 methods), accept interfaces, return structs.

**Useful Zero Values:** Uninitialized struct = safe to use or obviously invalid. Stdlib examples: `sync.Mutex`, `bytes.Buffer`.

---

## Concurrency

**Golden Rules:**
- Always know WHEN and HOW a goroutine terminates
- **Libraries are synchronous**: never launch goroutines from lib code unless concurrency IS the feature

**errgroup** (preferred over WaitGroup), **context** always first param, **bounded pools** for load, **sender closes** channels. Pre-1.23: `time.After` in loops leaks timers, use `time.NewTicker`. **1.23+:** `time.Tick` is GC-safe (requires `go 1.23` in go.mod).

For detailed concurrency patterns, performance optimization, profiling, and code review checklists, see `references/golang-patterns.md`.

---

## Resources

[Effective Go](https://go.dev/doc/effective_go) | [Code Review Comments](https://go.dev/wiki/CodeReviewComments) | [Release Notes](https://go.dev/doc/) | [goperf.dev](https://goperf.dev/) | [fgprof](https://github.com/felixge/fgprof)
