# ABOUTME: Go patterns for performance, profiling, concurrency, modern stdlib, and code review
# ABOUTME: Reference companion to golang SKILL.md with benchmarks, modern API prefs, optimization

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

**Benchmarks:** `go test -bench=. -benchmem ./...`. Use `b.ResetTimer()` after setup. **1.24+:** prefer `b.Loop()` over `for range b.N` (prevents compiler from optimizing away loop body).

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

**Pitfall (pre-1.23):** `time.After` in loops leaks timers, use `time.NewTicker` + `defer Stop()`. **1.23+:** `time.Tick` is GC-safe; tickers are reclaimed when unreferenced (requires `go 1.23` in go.mod).

---

## Modern Stdlib Preferences

Prefer modern APIs over manual equivalents:

| Instead of | Use | Since |
|------------|-----|-------|
| `sync.Once` + separate var | `sync.OnceValue(func() T)` / `sync.OnceFunc` | 1.21 |
| Manual default chain (`if x == "" { x = fallback }`) | `cmp.Or(x, fallback, "default")` | 1.22 |
| `strings.Index` + slice | `strings.Cut(s, sep)` | 1.18 |
| `strings.HasPrefix` + slice | `strings.CutPrefix(s, prefix)` | 1.20 |
| Multiple `if err != nil` to collect | `errors.Join(err1, err2)` | 1.20 |
| `atomic.StoreInt32` / `LoadInt32` | `atomic.Bool`, `atomic.Pointer[T]` | 1.19 |
| `context.Background()` + cancel in tests | `t.Context()` | 1.24 |
| `for range b.N` in benchmarks | `for b.Loop()` | 1.24 |
| `omitempty` for Duration/structs | `omitzero` JSON tag | 1.24 |
| `strings.Split` in for-range | `strings.SplitSeq` (avoids slice alloc) | 1.24 |
| `wg.Add(1); go func(){ defer wg.Done() }` | `wg.Go(func() { ... })` | 1.25 |
| `errors.As(err, &target)` | `errors.AsType[*T](err)` (returns val, ok) | 1.26 |
| `x := val; &x` (pointer to value) | `new(val)` | 1.26 |
| `context.WithCancel` (no cause) | `context.WithCancelCause` + `context.Cause` | 1.20 |
| `[]byte(fmt.Sprintf(...))` | `fmt.Appendf(buf, ...)` | 1.19 |

---

## Code Review

**Errors:** All handled, wrapped `%w`, has context, no panic in libs, not logging AND returning. Domain sentinels at service layer, log only at boundaries. Never wrap `io.EOF`.

**Concurrency:** Goroutines exit cleanly, context propagated, sender closes channels, errgroup > WaitGroup, `defer mu.Unlock()`, `-race` passes, bounded pools, libs are synchronous.

**Performance:** Pre-alloc, sync.Pool hot paths, batch queries, L1 cache, easyjson, PGO, stack-friendly loops, structs by value.

**Red flags:** CRITICAL: errors ignored `_`, panic in lib, global mutable state, goroutines w/o exit, data races. HIGH: goroutine leaks, unbounded spawning, resource leaks, no error context, no pre-alloc.
