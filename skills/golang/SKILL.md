---
name: golang
description: "Complete Go development: code conventions, architecture, concurrency, performance, and code review."
allowed-tools: [mcp__acp__Read, mcp__acp__Edit, mcp__acp__Write, mcp__acp__Bash]
---

# ABOUTME: Complete Go development guide - code, design, concurrency, performance, review
# ABOUTME: Modern Go (1.22-1.26): stdlib router, Green Tea GC, fgprof, easyjson, pgx batching

# Go Development

## Quick Reference

```bash
gofmt -w . && goimports -w . && go vet ./...     # Format & Vet
go test ./... && go test -race ./... && go test -cover ./...  # Tests
go build -pgo=cpu.pprof -o bin/app ./cmd/app     # Build with PGO
golangci-lint run                                 # Lint

# ast-grep patterns
sg --pattern 'func $NAME($$$) $$$' --lang go              # Functions
sg --pattern 'if err != nil { $$$ }' --lang go            # Error handling
sg --pattern 'go $FUNC($$$)' --lang go                    # Goroutines
sg --pattern '$VAR, _ := $EXPR' --lang go                 # Ignored errors
sg --pattern 'make([]$TYPE)' --lang go                    # Slices w/o capacity
```

**Nav:** [Conventions](#-code-conventions) | [Architecture](#-architecture--design) | [Concurrency](#-concurrency) | [Performance](#-performance) | [Profiling](#-profiling) | [Review](#-code-review)

**See also:** `_AST_GREP.md`, `_PATTERNS.md`, `source-control`

---

## § Modern Go (1.22+)

### 1.22

**Loop variable fix:** Each iteration gets own variable - safe in closures.
```go
for _, item := range items {
    go func() { process(item) }()  // ✅ Safe now
}
```

**Range over integers:** `for i := range 10 { ... }`

**Enhanced stdlib router:**
```go
mux := http.NewServeMux()
mux.HandleFunc("GET /api/v1/feed/{id}", getFeedItem)
// r.PathValue("id") for params - 3x faster than gorilla/mux
```

### 1.23

**iter package:** Lazy sequences via `iter.Seq[T]`. Use sparingly - adds complexity.

### 1.25

- Container-aware GOMAXPROCS (auto-respects cgroup limits)
- Green Tea GC (experimental): `GOEXPERIMENT=greenteagc`
- `sync.WaitGroup.Go()` convenience method

### 1.26

| Feature | Details |
|---------|---------|
| Green Tea GC | Default ON, 10-40% lower overhead, +10% on modern AMD64 |
| `new(expr)` | `new(42)` returns `*int` initialized to 42 |
| Self-referential generics | `type Adder[A Adder[A]] interface` |
| cgo | ~30% faster |
| Small allocations | ~30% faster |
| Goroutine leak detection | `/debug/pprof/goroutineleak` (experimental) |
| crypto/hpke | RFC 9180, post-quantum MLKEM default |

**Platform:** macOS 12 last supported, 32-bit Windows ARM removed

---

## § Code Conventions

### Formatting - NON-NEGOTIABLE

`gofmt` or `goimports` - tabs, opening brace same line, grouped imports (stdlib / third-party).

### Naming

| Type | Rule | Example |
|------|------|---------|
| Variables | Short in functions, descriptive at package level | `i`, `c`, `ErrNotFound` |
| Receivers | 1-2 letter, consistent | `(c *Client)` |
| Initialisms | All caps or all lowercase | `ServeHTTP`, `appID` |
| Packages | Lowercase, singular, no underscores | `user`, `postgres` |

### Error Handling

```go
// ALWAYS handle - never ignore with _
if err != nil {
    return fmt.Errorf("decompress %v: %w", name, err)  // Wrap with context
}
```

**Rules:** Lowercase, no punctuation, add context, guard clauses (happy path flows down).

### Testing

```go
func TestAdd(t *testing.T) {
    tests := []struct{ name string; a, b, want int }{
        {"positive", 2, 3, 5},
        {"negative", -2, 3, 1},
    }
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            if got := Add(tt.a, tt.b); got != tt.want {
                t.Errorf("Add(%d,%d)=%d; want %d", tt.a, tt.b, got, tt.want)
            }
        })
    }
}
```

Use `t.Helper()` in test helpers.

---

## § Architecture & Design

### Project Structure

**Small:** `main.go`, `user.go`, `user_test.go`

**Standard:**
```
cmd/api-server/main.go    # Entry points
internal/domain/          # Business entities
internal/service/         # Use case logic
internal/repository/      # Data access
pkg/                      # Public libraries (use sparingly)
```

**Avoid:** `/src`, `/models`, `/utils`, `/common`, `/helpers`

### Package Organization

Organize by **feature/domain**, NOT technical layer.

```
internal/ordering/   # order.go, service.go, repository.go, handler.go
internal/catalog/    # product.go, service.go, repository.go
```

### Design Patterns

**Functional Options:**
```go
type Option func(*Server)
func WithPort(p int) Option { return func(s *Server) { s.port = p } }
func NewServer(opts ...Option) *Server { /* apply opts */ }
```

**Constructor Injection:** Accept interfaces, return structs. Panic on required nil params.

**Interface Design:** Small (1-3 methods), accept interfaces, return structs.

---

## § Concurrency

**Golden Rule:** Always know WHEN and HOW a goroutine terminates.

### errgroup (RECOMMENDED)

```go
g, ctx := errgroup.WithContext(ctx)
g.Go(func() error { return loadUsers(ctx) })
g.Go(func() error { return loadMedia(ctx) })
if err := g.Wait(); err != nil { return err }
// First error cancels context, stops others
```

### Context

Always first param. Check `ctx.Done()` for cancellation.

### Bounded Worker Pool

**CRITICAL:** Never unbounded goroutines under load.

```go
pool := &WorkerPool{jobs: make(chan Job, queueSize)}
// Fixed workers consuming from channel
// Submit returns false when full (graceful degradation)
```

### Channel Patterns

- Sender closes channel
- Generator: Return `<-chan T`, close on ctx.Done()

### Pitfalls

```go
// ❌ time.After in loop leaks timers
// ✅ Use time.NewTicker with defer Stop()
```

---

## § Performance

**Profile first, optimize second.** JSON often slower than DB queries.

### Go 1.26 Free Gains

Recompile = 10-40% lower GC, 30% faster cgo/allocations.

### Optimizations

| Technique | Result | Example |
|-----------|--------|---------|
| easyjson | ~12x faster JSON | `//go:generate easyjson -all types.go` |
| pgx batch | 2.8x faster, 78% fewer allocs | Batch queries in single round-trip |
| Ristretto L1 | ~10x faster, 0 allocs | Local cache before Redis |
| sync.Pool | 3.2x faster, ~100% alloc reduction | Pool + `clear()` maps before reuse |
| Pre-allocation | 10x (slices), 2.6x (maps) | `make([]T, 0, len(rows))` |
| sqlc | Compile-time SQL validation | Type-safe generated code |

---

## § Profiling

### fgprof (RECOMMENDED)

Captures On-CPU AND Off-CPU (I/O waits) - complete picture.

```go
http.DefaultServeMux.Handle("/debug/fgprof", fgprof.Handler())
// go tool pprof --http=:6061 http://localhost:6060/debug/fgprof?seconds=30
```

### PGO

Free 2-7% improvement:
```bash
curl http://localhost:6060/debug/pprof/profile?seconds=30 > cpu.pprof
go build -pgo=cpu.pprof -o api ./cmd/api
```

### Benchmarking

```go
func BenchmarkX(b *testing.B) {
    data := generateTestData()
    b.ResetTimer()
    for i := 0; i < b.N; i++ { /* ... */ }
}
// go test -bench=. -benchmem ./...
```

---

## § Code Review

### Automated Checks

```bash
gofmt -w . && goimports -w . && go vet ./... && golangci-lint run && nilaway ./...
go test ./... && go test -race ./... && go test -cover ./...
```

### Checklists

**Errors:** All handled, wrapped with %w, has context, no panic in libs, not both logging AND returning.

**Concurrency:** Goroutines exit cleanly, context propagated, channels closed by sender, errgroup over WaitGroup, mutex unlock with defer, -race passes, bounded pools.

**Performance:** Pre-allocation, sync.Pool on hot paths, batch queries, L1 cache, easyjson, PGO.

### Critical Red Flags 🚩

| Severity | Issue |
|----------|-------|
| CRITICAL | Errors ignored `_`, panic in lib, global mutable state, goroutines w/o exit, data races |
| HIGH | Goroutine leaks, unbounded spawning, resource leaks, no error context, no pre-allocation |

---

## § Resources

**Official:** [Effective Go](https://go.dev/doc/effective_go) | [Code Review Comments](https://go.dev/wiki/CodeReviewComments) | [1.22](https://go.dev/doc/go1.22) | [1.23](https://go.dev/doc/go1.23) | [1.25](https://go.dev/doc/go1.25) | [1.26](https://go.dev/doc/go1.26)

**Performance:** [goperf.dev](https://goperf.dev/) | [go-perfbook](https://github.com/dgryski/go-perfbook) | [fgprof](https://github.com/felixge/fgprof) | [Go 1.26 tour](https://antonz.org/go-1-26/)

**Libraries:** [easyjson](https://github.com/mailru/easyjson) | [ristretto](https://github.com/dgraph-io/ristretto) | [pgx](https://github.com/jackc/pgx) | [sqlc](https://sqlc.dev/)

**Tools:** gofmt, goimports, go vet, golangci-lint, nilaway, staticcheck
