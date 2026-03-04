# ABOUTME: Common architectural patterns across Go, Python, and Rails
# ABOUTME: Quick lookup for dependency injection, error handling, testing, background jobs

# Cross-Language Patterns

## Dependency Injection

### Go: Constructor Injection
```go
type UserService struct {
    repo   UserRepository  // interface
    logger Logger
}

func NewUserService(repo UserRepository, logger Logger) *UserService {
    if repo == nil { panic("repository required") }
    return &UserService{repo: repo, logger: logger}
}
```

### Python: Protocol + Constructor
```python
class UserRepository(Protocol):
    def find(self, id: str) -> User | None: ...

class UserService:
    def __init__(self, repo: UserRepository, logger: Logger):
        self.repo, self.logger = repo, logger
```

### Rails: Keyword Args
```ruby
class UserService
  def initialize(repo:, logger:)
    @repo, @logger = repo, logger
  end
  def call = # use @repo, @logger
end
```

---

## Error Handling

### Go: Wrap with %w
```go
if err != nil {
    return fmt.Errorf("failed to find user %s: %w", id, err)
}
// Check: errors.Is(err, ErrNotFound), errors.As(err, &validErr)
```

### Python: Chain with `from`
```python
class UserNotFoundError(Exception):
    def __init__(self, user_id: str):
        self.user_id = user_id
        super().__init__(f"User {user_id} not found")

try:
    user = repo.find(id)
except DatabaseError as e:
    raise UserNotFoundError(id) from e
```

### Rails: Result Objects
```ruby
Result = Struct.new(:success, :data, :error, keyword_init: true)

def call
  user = repo.find(id)
  return Result.new(success: false, error: "Not found") unless user
  Result.new(success: true, data: user)
rescue ActiveRecord::RecordInvalid => e
  Result.new(success: false, error: e.message)
end
```

---

## Testing

### Go: Table-Driven
```go
tests := []struct{ name string; a, b, want int }{
    {"positive", 2, 3, 5},
    {"zero", 0, 0, 0},
}
for _, tt := range tests {
    t.Run(tt.name, func(t *testing.T) {
        if got := Add(tt.a, tt.b); got != tt.want {
            t.Errorf("got %d, want %d", got, tt.want)
        }
    })
}
```

### Python: pytest + parametrize
```python
@pytest.fixture
def user_service(mock_repo):
    return UserService(repo=mock_repo)

@pytest.mark.parametrize("email,valid", [("test@x.com", True), ("bad", False)])
def test_email(email, valid):
    assert validate_email(email) == valid
```

### Rails: RSpec + factories
```ruby
RSpec.describe UserService do
  let(:repo) { instance_double(UserRepository) }
  let(:service) { described_class.new(repo: repo) }

  it 'returns success' do
    allow(repo).to receive(:find).and_return(create(:user))
    expect(service.call.success).to be true
  end
end
```

---

## Background Jobs

### Go: Worker Pool
```go
func ProcessJobs(ctx context.Context, jobs <-chan Job) {
    var wg sync.WaitGroup
    for i := 0; i < 10; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for {
                select {
                case job, ok := <-jobs:
                    if !ok { return }
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

### Python: Dramatiq/Celery
```python
@actor(max_retries=3)
def process_user(user_id: str):
    user = User.objects.get(id=user_id)
    # process

process_user.send(user_id="123")
```

### Rails: Sidekiq
```ruby
class ProcessUserJob
  include Sidekiq::Job
  sidekiq_options retry: 3

  def perform(user_id)
    User.find(user_id).then { ProcessService.new(user: _1).call }
  end
end

ProcessUserJob.perform_async(user.id)
```

**Rules:** Idempotent, pass IDs not objects, handle missing records

---

## Configuration

| Language | Pattern |
|----------|---------|
| Go | Struct + env vars |
| Python | pydantic-settings |
| Rails | ENV.fetch + credentials |

---

## Logging

| Language | Pattern |
|----------|---------|
| Go | `logger.Info("msg", zap.String("key", val))` |
| Python | `logger.info("msg", key=val)` |
| Rails | `Rails.logger.tagged("Service") { info "msg" }` |

**Rules:** Structured (key-value), log at boundaries, include context (IDs)

---

## Database

### Repository Pattern
```go
type UserRepository interface {
    Find(id string) (*User, error)
    Save(user *User) error
}
```

### Transactions
```go
tx, _ := db.Begin()
defer tx.Rollback()
// ops...
tx.Commit()
```

```python
with db.transaction():
    user.save()
```

```ruby
ActiveRecord::Base.transaction { user.save! }
```

---

## Anti-Patterns

| Avoid | Why |
|-------|-----|
| Global mutable state | Testing nightmare |
| God objects | Single responsibility |
| Logic in controllers | Separation of concerns |
| Swallowing errors | Debug nightmare |
| Premature optimization | YAGNI |

---

---

## Hotspot Analysis

Identify where to focus refactoring effort. A hotspot is a file that is both complex and frequently changed.

```
hotspot_score = complexity x change_frequency
```

**Collect data:**
```bash
# Change frequency (last 6 months)
git log --since="6 months ago" --format=format: --name-only | sort | uniq -c | sort -rn | head -20

# Approximate complexity (lines of code, proxy)
wc -l $(git ls-files '*.go' '*.py' '*.rb' '*.ts') | sort -rn | head -20
```

**Interpret:** Files appearing in both top-20 lists are hotspots. Prioritize these for refactoring, test coverage, and code review. Files that are complex but rarely change are low priority.

---

## Cognitive Load Dimensions

8 dimensions for assessing codebase complexity (adapted from cognitive-load-analyzer). Useful for "should we refactor?" decisions.

| Dimension | What to measure | High-load signal |
|-----------|----------------|------------------|
| Structural complexity | Cyclomatic complexity, branching depth | Functions with CC > 15 |
| Nesting depth | Max indentation levels | > 4 levels deep |
| Volume | File length, function length | Files > 500 lines, functions > 50 |
| Naming quality | Semantic clarity, abbreviation density | Single-letter vars, ambiguous names |
| Coupling | Import fan-in/fan-out, dependency depth | Module importing > 10 others |
| Cohesion | Semantic relatedness within module | "Utils" classes, mixed responsibilities |
| Duplication | Clone detection, near-miss patterns | Copy-paste with minor variations |
| Navigability | Directory depth, file discoverability | > 5 levels deep, unclear organization |

**Key insight:** Use P90 (90th percentile) rather than averages. Averages hide complexity: a codebase with 95% clean files and 5% nightmares looks "fine" by average but painful to work in.

---

**Details:** See `golang/SKILL.md`, `python/SKILL.md`, `rails/SKILL.md`
