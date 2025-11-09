---
name: golang
description: "Complete Go development: code conventions, architecture, concurrency, and code review."
allowed-tools: [mcp__acp__Read, mcp__acp__Edit, mcp__acp__Write, mcp__acp__Bash]
---

# ABOUTME: Complete Go development guide - code, design, concurrency, review
# ABOUTME: Idiomatic Go with formatting, architecture, goroutines, and best practices

# Go Development

## Quick Reference

```bash
# Format & Vet
gofmt -w . && goimports -w . && go vet ./...

# Tests
go test ./...
go test -race ./...
go test -cover ./...

# Build
go build -o bin/app ./cmd/app

# Lint
golangci-lint run

# Common patterns (ast-grep)
sg --pattern 'func $NAME($$$) $$$' --lang go              # Find functions
sg --pattern 'if err != nil { $$$ }' --lang go            # Error handling
sg --pattern 'go $FUNC($$$)' --lang go                    # Goroutines
sg --pattern '$VAR, _ := $EXPR' --lang go                 # Ignored errors
```

**Navigation:**
- [§ Code Conventions](#-code-conventions)
- [§ Architecture & Design](#-architecture--design)
- [§ Concurrency](#-concurrency)
- [§ Code Review](#-code-review)

**See also:**
- Code search: `_AST_GREP.md`
- Patterns: `_PATTERNS.md`
- Git: `source-control`

---

## § Code Conventions

### Formatting - NON-NEGOTIABLE

**ALL Go code MUST be formatted with `gofmt` or `goimports`. Not negotiable. No exceptions.**

```bash
# Format files
gofmt -w *.go
go fmt ./...

# Format + manage imports (recommended)
goimports -w .
```

**Auto-format rules:**
- Tabs for indentation (not spaces)
- Opening brace on same line (REQUIRED)
- Grouped imports: stdlib, blank line, third-party

```go
import (
    // Standard library
    "fmt"
    "os"

    // Third-party
    "github.com/gorilla/mux"
)
```

**Editor setup:**
```json
// VS Code
{
  "go.formatTool": "goimports",
  "editor.formatOnSave": true
}
```

### Naming Conventions

**General principles:**
- mixedCaps (camelCase or PascalCase), NEVER snake_case
- Uppercase first letter = exported
- Lowercase first letter = unexported
- Short names in limited scope
- Longer names for package-level declarations

**Variables:**
```go
// ✅ GOOD - Short in functions
func process(items []Item) {
    for i, item := range items {  // i, not itemIndex
        c := item.Count               // c, not count
        if c > 0 {
            // Use c
        }
    }
}

// ✅ GOOD - Descriptive at package level
var defaultMaxConnectionsPerHost = 10
var ErrNotFound = errors.New("not found")
```

**Receivers:**
```go
// ✅ GOOD - 1-2 letter abbreviation, consistent
type Client struct{}

func (c *Client) Do() {}
func (c *Client) Get() {}

// ❌ BAD - Inconsistent
func (this *Client) Do() {}
func (client *Client) Get() {}
```

**Constants:**
```go
// ✅ GOOD - mixedCaps
const maxLength = 100
const MaxLength = 100  // Exported

// ❌ BAD - SCREAMING_SNAKE_CASE
const MAX_LENGTH = 100
```

**Functions:**
```go
// ✅ GOOD - No "Get" prefix for getters
obj.Owner()
obj.SetOwner(user)

// ✅ GOOD - Boolean functions
func (u *User) IsActive() bool
func (u *User) HasPermission(perm string) bool
```

**Initialisms - Consistency REQUIRED:**
```go
// ✅ GOOD - All caps or all lowercase
ServeHTTP
XMLHTTPRequest
appID
userID

// ❌ BAD - Mixed case
ServeHttp
appId
userId
```

Common: HTTP, HTTPS, URL, URI, XML, JSON, YAML, API, ID, SQL, DB, UUID

**Package names:**
```go
// ✅ GOOD - lowercase, single-word
package user
package http
package postgres

// ❌ BAD
package users          // Use singular
package utils          // Too generic
package user_service   // No underscores
```

### Error Handling

**ALWAYS handle errors. Never ignore.**

```go
// ✅ ALWAYS do this
result, err := doSomething()
if err != nil {
    return err
}

// ❌ NEVER do this
result, _ := doSomething()
```

**Error wrapping (Go 1.13+):**
```go
if err != nil {
    return fmt.Errorf("decompress %v: %w", name, err)
}
```

**Sentinel errors:**
```go
var ErrNotFound = errors.New("not found")

if errors.Is(err, ErrNotFound) {
    // Handle not found
}
```

**Custom error types:**
```go
type QueryError struct {
    Query string
    Err   error
}

func (e *QueryError) Error() string {
    return fmt.Sprintf("query failed %q: %v", e.Query, e.Err)
}

func (e *QueryError) Unwrap() error {
    return e.Err
}

// Check
var qe *QueryError
if errors.As(err, &qe) {
    log.Printf("query %q failed", qe.Query)
}
```

**Error message rules:**
- Lowercase (no capital)
- No punctuation at end
- Add context (operation, parameters)

```go
// ✅ GOOD
fmt.Errorf("failed to connect to database")
fmt.Errorf("user %s not found", userID)

// ❌ BAD
fmt.Errorf("Failed to connect")  // Capital
fmt.Errorf("Error!")              // Punctuation
```

**Indent error flow (guard clauses):**
```go
// ✅ GOOD - Happy path flows down
func process() error {
    if err := step1(); err != nil {
        return err
    }
    if err := step2(); err != nil {
        return err
    }
    // Success path
    return nil
}
```

**Panic vs Error:**
- Return error for expected failures
- Panic only for programmer errors (invariants violated)

```go
// ✅ GOOD - Return error
func fetchData() error {
    return errors.New("service unavailable")
}

// ✅ GOOD - Panic for programmer error
func mustParse(s string) int {
    v, err := strconv.Atoi(s)
    if err != nil {
        panic(fmt.Sprintf("invalid integer: %q", s))
    }
    return v
}
```

### Documentation

- ALL exported names MUST have doc comments
- Comments start with name being described
- Full sentences with proper capitalization
- End with period

```go
// Package user provides user management functionality.
package user

// User represents a system user.
type User struct {
    ID   string
    Name string
}

// Find returns the user with the given ID.
func Find(id string) (*User, error) {
    // Implementation
}
```

### Testing

**Table-driven tests (STANDARD):**
```go
func TestAdd(t *testing.T) {
    tests := []struct {
        name string
        a, b int
        want int
    }{
        {"positive", 2, 3, 5},
        {"negative", -2, 3, 1},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got := Add(tt.a, tt.b)
            if got != tt.want {
                t.Errorf("Add(%d, %d) = %d; want %d", tt.a, tt.b, got, tt.want)
            }
        })
    }
}
```

**Use t.Helper() in test helpers:**
```go
func assertUser(t *testing.T, got, want *User) {
    t.Helper()
    if got.ID != want.ID {
        t.Errorf("got ID %s, want %s", got.ID, want.ID)
    }
}
```

---

## § Architecture & Design

### Project Structure

**Start simple, add structure only when needed.**

**Basic (small projects):**
```
project-root/
├── go.mod
├── main.go
├── user.go
└── user_test.go
```

**Standard (medium/large):**
```
project-root/
├── cmd/                    # Main applications
│   ├── api-server/
│   │   └── main.go
│   └── worker/
│       └── main.go
├── internal/              # Private code
│   ├── domain/           # Business entities
│   ├── service/          # Use case logic
│   └── repository/       # Data access
├── pkg/                   # Public libraries (use with caution)
├── api/                   # API definitions (OpenAPI, proto)
├── configs/              # Configuration files
├── go.mod
└── go.sum
```

**Directory guidelines:**

**`/cmd`** - Main applications
- One directory per executable
- Minimal code, just wiring
- Directory name = executable name

```go
// cmd/api-server/main.go
func main() {
    db := initDB()
    repo := postgres.NewRepository(db)
    service := user.NewService(repo)
    handler := http.NewHandler(service)
    http.ListenAndServe(":8080", handler)
}
```

**`/internal`** - Private code
- Go compiler enforced (cannot be imported by other projects)
- Contains most business logic

**Avoid:**
- ❌ `/src` - Not idiomatic Go
- ❌ `/models` - Organize by feature, not type
- ❌ `/utils`, `/common`, `/helpers` - Non-descriptive

### Package Organization

**Organize by feature/domain, NOT by technical layer.**

**✅ GOOD - By feature:**
```
internal/
├── ordering/          # Domain: Orders
│   ├── order.go
│   ├── service.go
│   ├── repository.go
│   └── handler.go
├── catalog/           # Domain: Products
│   ├── product.go
│   ├── service.go
│   └── repository.go
```

**❌ BAD - By layer:**
```
internal/
├── models/
│   ├── order.go
│   └── product.go
├── controllers/
│   ├── order_controller.go
│   └── product_controller.go
```

**Package naming:**
- Lowercase, single-word, no underscores
- Describe WHAT they provide, not WHAT they contain
- Singular, not plural

```go
package user      // ✅ not users
package auth      // ✅ not authentication
package postgres  // ✅ not postgresdb
```

### Design Patterns

**Functional Options Pattern:**
```go
type Server struct {
    host    string
    port    int
    timeout time.Duration
}

type Option func(*Server)

func WithHost(host string) Option {
    return func(s *Server) {
        s.host = host
    }
}

func WithPort(port int) Option {
    return func(s *Server) {
        s.port = port
    }
}

func NewServer(options ...Option) *Server {
    s := &Server{
        host:    "localhost",
        port:    8080,
        timeout: 30 * time.Second,
    }
    for _, opt := range options {
        opt(s)
    }
    return s
}

// Usage
server := NewServer(
    WithHost("0.0.0.0"),
    WithPort(9090),
)
```

**Constructor Injection:**
```go
type UserService struct {
    repo   UserRepository
    logger Logger
    cache  Cache
}

func NewUserService(repo UserRepository, logger Logger, cache Cache) *UserService {
    if repo == nil {
        panic("repository is required")
    }
    if logger == nil {
        logger = nopLogger{}
    }
    return &UserService{
        repo:   repo,
        logger: logger,
        cache:  cache,
    }
}
```

### Interface Design

**Golden rule: "Accept interfaces, return structs"**

```go
// ✅ GOOD
func NewHandler(repo Repository) *Handler {
    return &Handler{repo: repo}
}

// ❌ BAD
func NewHandler(repo Repository) Handler {
    return &concreteHandler{repo: repo}
}
```

**Small interfaces (1-3 methods):**
```go
// ✅ EXCELLENT
type Stringer interface {
    String() string
}

// ✅ GOOD
type Storage interface {
    Save(data []byte) error
    Load() ([]byte, error)
}
```

**Consumer-side interface definition:**
```go
// Package: service (CONSUMER)
package service

type Storage interface {
    Save(data []byte) error
    Load() ([]byte, error)
}

type UserService struct {
    storage Storage
}

// Package: postgres (PROVIDER)
package postgres

// Implicitly implements Storage
type PostgresStorage struct {
    db *sql.DB
}

func (p *PostgresStorage) Save(data []byte) error {
    // Implementation
    return nil
}

func (p *PostgresStorage) Load() ([]byte, error) {
    return nil, nil
}
```

### Dependency Injection

**Manual DI (recommended) - Wire in main():**
```go
func main() {
    // Infrastructure
    db := initDB()
    cache := redis.NewClient(&redis.Options{
        Addr: "localhost:6379",
    })
    logger := zap.NewProduction()

    // Repositories
    userRepo := postgres.NewUserRepository(db)

    // Services
    userService := user.NewService(userRepo, logger, cache)

    // HTTP Handlers
    userHandler := http.NewUserHandler(userService)

    // Router
    router := chi.NewRouter()
    router.Mount("/users", userHandler.Routes())

    http.ListenAndServe(":8080", router)
}
```

**Best practices:**
- ✅ Inject dependencies via constructors
- ✅ Use interfaces for dependencies
- ✅ Validate required dependencies
- ✅ Wire in main()
- ❌ No global variables for dependencies
- ❌ Limit to 3-5 dependencies per service

---

## § Concurrency

### Golden Rule

**Always know WHEN and HOW a goroutine terminates.**

### Context for Cancellation

**Context ALWAYS as first parameter:**
```go
func ProcessData(ctx context.Context, data []byte) error {
    // Check cancellation
    select {
    case <-ctx.Done():
        return ctx.Err()
    default:
    }
    
    // Process data
    return nil
}
```

**Propagate context down the call stack:**
```go
func Handler(w http.ResponseWriter, r *http.Request) {
    ctx := r.Context()
    result, err := service.Process(ctx, data)
    // Handle result
}

func (s *Service) Process(ctx context.Context, data Data) (Result, error) {
    return s.repo.Save(ctx, data)
}
```

### Goroutine Patterns

**Always provide exit mechanism:**
```go
// ✅ GOOD - Context for cancellation
func worker(ctx context.Context, jobs <-chan Job) {
    for {
        select {
        case job := <-jobs:
            processJob(job)
        case <-ctx.Done():
            return
        }
    }
}

// ❌ BAD - No way to stop
func worker(jobs <-chan Job) {
    for job := range jobs {
        processJob(job)
    }
}
```

### WaitGroup Pattern

**Call wg.Add() BEFORE go statement:**
```go
// ✅ GOOD
var wg sync.WaitGroup
for i := 0; i < 10; i++ {
    wg.Add(1)
    go func(n int) {
        defer wg.Done()
        process(n)
    }(i)
}
wg.Wait()

// ❌ BAD - Race condition
go func() {
    wg.Add(1)  // Too late!
    defer wg.Done()
}()
```

**Pass loop variables as parameters:**
```go
// ✅ GOOD
for _, item := range items {
    wg.Add(1)
    go func(it Item) {
        defer wg.Done()
        process(it)
    }(item)
}

// ❌ BAD - Captures loop variable
for _, item := range items {
    wg.Add(1)
    go func() {
        defer wg.Done()
        process(item)  // All goroutines see same item!
    }()
}
```

### Channel Patterns

**Sender closes channel:**
```go
func producer(ch chan<- int) {
    defer close(ch)
    for i := 0; i < 10; i++ {
        ch <- i
    }
}

func consumer(ch <-chan int) {
    for v := range ch {  // Loop exits when channel closed
        process(v)
    }
}
```

**Buffered channels prevent blocking:**
```go
// ✅ GOOD - Won't block if receiver is slow
ch := make(chan int, 10)

// ❌ DANGEROUS - Can block forever
ch := make(chan int)
go func() {
    ch <- compute()  // Blocks if nobody reads
}()
// Function returns before reading
```

**Generator pattern:**
```go
func generate(ctx context.Context) <-chan int {
    ch := make(chan int)
    go func() {
        defer close(ch)
        for i := 0; ; i++ {
            select {
            case ch <- i:
            case <-ctx.Done():
                return
            }
        }
    }()
    return ch
}
```

**Worker pool:**
```go
func processJobs(ctx context.Context, jobs <-chan Job) {
    const workers = 10
    var wg sync.WaitGroup

    for i := 0; i < workers; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for {
                select {
                case job, ok := <-jobs:
                    if !ok {
                        return
                    }
                    processJob(job)
                case <-ctx.Done():
                    return
                }
            }
        }()
    }

    wg.Wait()
}
```

### Mutex Usage

**Always defer unlock:**
```go
// ✅ GOOD
func (c *Counter) Inc() {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.count++
}

// ❌ BAD - Easy to forget
func (c *Counter) Inc() {
    c.mu.Lock()
    c.count++
    c.mu.Unlock()  // What if panic?
}
```

**Use RWMutex for read-heavy workloads:**
```go
type Cache struct {
    mu   sync.RWMutex
    data map[string]string
}

func (c *Cache) Get(key string) (string, bool) {
    c.mu.RLock()
    defer c.mu.RUnlock()
    val, ok := c.data[key]
    return val, ok
}

func (c *Cache) Set(key, val string) {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.data[key] = val
}
```

**Don't copy mutexes (use pointer receivers):**
```go
// ✅ GOOD
type Counter struct {
    mu    sync.Mutex
    count int
}

func (c *Counter) Inc() {  // Pointer receiver
    c.mu.Lock()
    defer c.mu.Unlock()
    c.count++
}

// ❌ BAD - Copies mutex
func (c Counter) Inc() {  // Value receiver
    c.mu.Lock()  // Copies the mutex!
    defer c.mu.Unlock()
    c.count++
}
```

### Common Pitfalls

**Goroutine leak:**
```go
// ❌ BAD - Goroutine leaks if channel not read
ch := make(chan int)
go func() {
    result := compute()
    ch <- result  // Blocks forever
}()
return  // Function returns, channel never read

// ✅ GOOD - Use buffered channel or context
ch := make(chan int, 1)
go func() {
    ch <- compute()  // Won't block
}()
```

**time.After in loop:**
```go
// ❌ BAD - Leaks timers
for {
    select {
    case <-time.After(1 * time.Second):  // Creates new timer each iteration
    }
}

// ✅ GOOD - Reuse timer
ticker := time.NewTicker(1 * time.Second)
defer ticker.Stop()
for {
    select {
    case <-ticker.C:
    }
}
```

---

## § Code Review

### Automated Checks (MUST run before submitting)

```bash
# Format
gofmt -w .
goimports -w .

# Vet
go vet ./...

# Lint
golangci-lint run

# Tests
go test ./...
go test -race ./...
go test -cover ./...
```

### Error Handling Review

**Checklist:**
- [ ] All errors handled (no `_` discard)
- [ ] Error wrapping with %w when appropriate
- [ ] Error messages have context
- [ ] Panic only for programmer errors
- [ ] Not both logging AND returning same error

**Red flags:**
```go
// 🚩 Ignored error
result, _ := doSomething()

// 🚩 No context
return err

// 🚩 Panic in library
if err != nil {
    panic(err)
}
```

### Concurrency Review

**Checklist:**
- [ ] Goroutines have clear exit mechanism
- [ ] Context propagated correctly
- [ ] Channels closed by sender
- [ ] WaitGroup.Add() before `go`
- [ ] Mutex unlocked with defer
- [ ] No data races (verified with -race)
- [ ] No goroutine leaks
- [ ] Mutexes not copied

**Red flags:**
```go
// 🚩 No exit mechanism
go func() {
    for {
        work()
    }
}()

// 🚩 Channel not closed
go func() {
    for i := 0; i < 10; i++ {
        ch <- i
    }
}()

// 🚩 WaitGroup.Add after go
go func() {
    wg.Add(1)  // Race!
    defer wg.Done()
}()

// 🚩 Value receiver copies mutex
func (c Counter) Inc() {
    c.mu.Lock()
    defer c.mu.Unlock()
}
```

### Naming Review

**Checklist:**
- [ ] mixedCaps (no snake_case)
- [ ] Package names lowercase, singular
- [ ] No "Get" prefix for getters
- [ ] Initialisms consistent case (HTTP not Http)
- [ ] Receiver names consistent (1-2 letters)
- [ ] Exported symbols documented

**Red flags:**
```go
// 🚩 Bad package names
package utils
package user_service

// 🚩 Inconsistent receivers
func (c *Client) Do() {}
func (client *Client) Get() {}

// 🚩 Mixed initialism
ServeHttp()  // Should be: ServeHTTP()
```

### Design Review

**Checklist:**
- [ ] Packages organized by feature
- [ ] Interfaces small (1-3 methods)
- [ ] "Accept interfaces, return structs"
- [ ] No circular dependencies
- [ ] Dependencies injected, not created
- [ ] No global mutable state

### Critical Red Flags 🚩

**STOP and review:**

**Severity: CRITICAL**
- 🚩 Errors ignored with `_`
- 🚩 Panic in library code
- 🚩 Global mutable state
- 🚩 Goroutines without exit mechanism
- 🚩 Data races

**Severity: HIGH**
- 🚩 Goroutine leaks
- 🚩 Resource leaks (files, connections)
- 🚩 Circular dependencies
- 🚩 Missing error context

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "Running pre-commit checks..."

# Format
goimports -w .

# Vet
if ! go vet ./...; then
    echo "go vet failed"
    exit 1
fi

# Tests
if ! go test -race ./...; then
    echo "Tests failed"
    exit 1
fi

echo "Pre-commit checks passed"
```

---

## § Resources

**Official:**
- https://go.dev/doc/effective_go
- https://go.dev/wiki/CodeReviewComments
- https://go.dev/blog/errors-are-values
- https://go.dev/blog/context

**Tools:**
- gofmt, goimports
- go vet
- staticcheck
- golangci-lint

**Related Skills:**
- Code search: `_AST_GREP.md`
- Patterns: `_PATTERNS.md`
- Git: `source-control`

---

**End of SKILL: Go Development**
