# ABOUTME: Detailed Go patterns for performance, profiling, concurrency, and code review
# ABOUTME: Reference companion to golang SKILL.md with benchmarks and optimization techniques

# Go Patterns Reference

## Performance

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
// Contiguous, cache-friendly, always initialized
type Conn struct {
    state  State
    buffer [512]byte
    config Config
}
```

---

## Profiling

**fgprof:** On-CPU AND Off-CPU (I/O waits). `http.DefaultServeMux.Handle("/debug/fgprof", fgprof.Handler())`. Analyze: `go tool pprof --http=:6061 http://localhost:6060/debug/fgprof?seconds=30`.

**PGO (2-7% free):** Capture profile, then `go build -pgo=cpu.pprof`.

**Benchmarks:** `go test -bench=. -benchmem ./...`. Use `b.ResetTimer()` after setup.

---

## Detailed Concurrency Patterns

**errgroup (preferred over WaitGroup):**
```go
g, ctx := errgroup.WithContext(ctx)
g.Go(func() error { return loadUsers(ctx) })
g.Go(func() error { return loadMedia(ctx) })
if err := g.Wait(); err != nil { return err }
```

**Bounded pools:** Never unbounded goroutines under load. Fixed workers + buffered channel.

**Channel rules:** Sender closes. Generator returns `<-chan T`, closes on ctx.Done().

**Pitfall:** `time.After` in loops leaks timers, use `time.NewTicker` + `defer Stop()`.

---

## Code Review

**Errors:** All handled, wrapped `%w`, has context, no panic in libs, not logging AND returning.

**Concurrency:** Goroutines exit cleanly, context propagated, sender closes channels, errgroup > WaitGroup, `defer mu.Unlock()`, `-race` passes, bounded pools, libs are synchronous.

**Performance:** Pre-alloc, sync.Pool hot paths, batch queries, L1 cache, easyjson, PGO, stack-friendly loops, structs by value.

**Red flags:** CRITICAL: errors ignored `_`, panic in lib, global mutable state, goroutines w/o exit, data races. HIGH: goroutine leaks, unbounded spawning, resource leaks, no error context, no pre-alloc.
