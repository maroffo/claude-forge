---
name: golang
description: "Go development: conventions, architecture, concurrency, performance, and code review. Use when working with .go files, go.mod, or user asks about goroutines, channels, error handling, interfaces."
allowed-tools: [mcp__acp__Read, mcp__acp__Edit, mcp__acp__Write, mcp__acp__Bash]
---

# ABOUTME: Complete Go development guide - code, design, concurrency, performance, review
# ABOUTME: Modern Go (1.22-1.26): stdlib router, Green Tea GC, fgprof, easyjson, pgx batching

# Go Development

## Quick Reference

```bash
gofmt -w . && goimports -w . && go vet ./...
go test ./... && go test -race ./... && go test -cover ./...
go build -pgo=cpu.pprof -o bin/app ./cmd/app
golangci-lint run
```

**See also:** `_AST_GREP.md`, `_PATTERNS.md`, `source-control`

---

## § Modern Go (1.22+)

**1.22:** Loop var fix (each iteration owns its variable). Range over int: `for i := range 10`. Stdlib router: `mux.HandleFunc("GET /api/v1/feed/{id}", h)` + `r.PathValue("id")`.

**1.23:** `iter.Seq[T]` lazy sequences. Use sparingly.

**1.25:** Container-aware GOMAXPROCS, Green Tea GC (experimental `GOEXPERIMENT=greenteagc`), `sync.WaitGroup.Go()`.

**1.26:** Green Tea GC default ON (10-40% lower overhead), `new(42)` → `*int`, self-referential generics, ~30% faster cgo + small allocs, goroutine leak detection (`/debug/pprof/goroutineleak`).

---

## § Code Conventions

**Formatting:** `gofmt`/`goimports` — NON-NEGOTIABLE.

**Naming:** Short vars in funcs (`i`, `c`), descriptive at pkg level (`ErrNotFound`). Receivers 1-2 letter (`c *Client`). Initialisms all-caps or all-lower (`ServeHTTP`, `appID`). Packages lowercase singular (`user`, `postgres`).

**Errors:** Always handle (never `_`). Wrap: `fmt.Errorf("decompress %v: %w", name, err)`. Lowercase, no punctuation, guard clauses.

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

**Build tags for simulation:** Swap implementations at compile time — `//go:build simulation` in `driver_sim.go`, `//go:build !simulation` in `driver_real.go`. Same type, different impl. `go test -tags simulation ./...`. Use for hardware, external APIs, infra deps.

---

## § Architecture & Design

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

**Constructor Injection:** Accept interfaces, return structs. **No global mutable state** — pass deps explicitly.
```go
// ❌ var db *sql.DB + func GetUser(id int)
// ✅ type UserStore struct{ db *sql.DB } + method with ctx
```

**Interfaces:** Small (1-3 methods), accept interfaces, return structs.

**Useful Zero Values:** Uninitialized struct = safe to use or obviously invalid. `0`/`""` as valid default OR use `Invalid`/`Unknown` iota to force init. Stdlib examples: `sync.Mutex`, `bytes.Buffer`.
```go
func (c Config) PortOrDefault() int {
    if c.Port == 0 { return 8080 }
    return c.Port
}

type State int
const (
    StateInvalid State = iota  // 0 = must initialize
    StateReady
)
```

---

## § Concurrency

**Golden Rules:**
- Always know WHEN and HOW a goroutine terminates
- **Libraries are synchronous** — never launch goroutines from lib code unless concurrency IS the feature. Let `main`/caller orchestrate.

```go
// ❌ func (c *Client) Fetch(url string) { go func() { ... }() }
// ✅ func (c *Client) Fetch(ctx context.Context, url string) ([]byte, error)
// Caller uses errgroup to parallelize
```

**errgroup (preferred over WaitGroup):**
```go
g, ctx := errgroup.WithContext(ctx)
g.Go(func() error { return loadUsers(ctx) })
g.Go(func() error { return loadMedia(ctx) })
if err := g.Wait(); err != nil { return err }
```

**Context:** Always first param. Check `ctx.Done()`.

**Bounded pools:** Never unbounded goroutines under load. Fixed workers + buffered channel.

**Channel rules:** Sender closes. Generator returns `<-chan T`, closes on ctx.Done().

**Pitfall:** `time.After` in loops leaks timers → use `time.NewTicker` + `defer Stop()`.

---

## § Performance

**Profile first, optimize second.** JSON often slower than DB queries.

**1.26 free gains:** Recompile = 10-40% lower GC, 30% faster cgo/allocs.

| Technique | Result |
|-----------|--------|
| easyjson | ~12x faster JSON (`//go:generate easyjson -all types.go`) |
| pgx batch | 2.8x faster, 78% fewer allocs |
| Ristretto L1 | ~10x faster, 0 allocs (local cache before Redis) |
| sync.Pool | 3.2x faster, ~100% alloc reduction |
| Pre-allocation | 10x slices, 2.6x maps (`make([]T, 0, len(rows))`) |
| sqlc | Compile-time SQL validation, type-safe codegen |

**Stack-friendly hot paths:** `var s MyStruct` over `&MyStruct{}` in loops. Pass pre-allocated buffers IN, don't return new slices. Verify: `go build -gcflags='-m'`.

**Struct composition by value:** Embed structs by value (not pointer) for data locality + nil safety. Fixed arrays over slices when size is known.
```go
// ✅ Contiguous, cache-friendly, always initialized
type Conn struct {
    state  State
    buffer [512]byte
    config Config
}
```

---

## § Profiling

**fgprof:** On-CPU AND Off-CPU (I/O waits). `http.DefaultServeMux.Handle("/debug/fgprof", fgprof.Handler())`. Analyze: `go tool pprof --http=:6061 http://localhost:6060/debug/fgprof?seconds=30`.

**PGO (2-7% free):** Capture profile → `go build -pgo=cpu.pprof`.

**Benchmarks:** `go test -bench=. -benchmem ./...`. Use `b.ResetTimer()` after setup.

---

## § Code Review

**Errors:** All handled, wrapped `%w`, has context, no panic in libs, not logging AND returning.

**Concurrency:** Goroutines exit cleanly, context propagated, sender closes channels, errgroup > WaitGroup, `defer mu.Unlock()`, `-race` passes, bounded pools, libs are synchronous.

**Performance:** Pre-alloc, sync.Pool hot paths, batch queries, L1 cache, easyjson, PGO, stack-friendly loops, structs by value.

**Red flags:** CRITICAL — errors ignored `_`, panic in lib, global mutable state, goroutines w/o exit, data races. HIGH — goroutine leaks, unbounded spawning, resource leaks, no error context, no pre-alloc.

---

## § Resources

[Effective Go](https://go.dev/doc/effective_go) | [Code Review Comments](https://go.dev/wiki/CodeReviewComments) | [Release Notes](https://go.dev/doc/) | [goperf.dev](https://goperf.dev/) | [fgprof](https://github.com/felixge/fgprof)
