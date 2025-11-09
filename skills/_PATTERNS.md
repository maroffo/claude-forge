# ABOUTME: Common architectural patterns across Go, Python, and Rails
# ABOUTME: Quick lookup for dependency injection, error handling, testing, background jobs

# Cross-Language Patterns

## Quick Navigation

- [Dependency Injection](#dependency-injection)
- [Error Handling](#error-handling)
- [Testing Strategies](#testing-strategies)
- [Background Jobs](#background-jobs)
- [Configuration Management](#configuration-management)
- [Logging](#logging)
- [Database Patterns](#database-patterns)

---

## Dependency Injection

### Go: Constructor Injection

```go
type UserService struct {
    repo   UserRepository
    logger Logger
    cache  Cache
}

// Constructor with explicit dependencies
func NewUserService(repo UserRepository, logger Logger, cache Cache) *UserService {
    if repo == nil {
        panic("repository required")
    }
    return &UserService{
        repo:   repo,
        logger: logger,
        cache:  cache,
    }
}
```

**Key points:**
- Dependencies as interfaces
- Validate required deps (panic early)
- Wire in main()

### Python: Constructor Injection + Protocols

```python
from typing import Protocol

class UserRepository(Protocol):
    def find(self, id: str) -> User | None: ...
    def save(self, user: User) -> None: ...

class UserService:
    def __init__(
        self,
        repo: UserRepository,
        logger: Logger,
        cache: Cache
    ):
        self.repo = repo
        self.logger = logger
        self.cache = cache
```

**Key points:**
- Use Protocol for interfaces (Python 3.8+)
- Type hints for clarity
- pytest fixtures for testing

### Rails: Constructor Injection + Services

```ruby
class UserService
  def initialize(repo:, logger:, cache:)
    @repo = repo
    @logger = logger
    @cache = cache
  end

  def call
    # Use @repo, @logger, @cache
  end
end

# Usage
UserService.new(
  repo: UserRepository.new,
  logger: Rails.logger,
  cache: Rails.cache
).call
```

**Key points:**
- Named parameters (keyword args)
- Services use `#call`
- Wire in controllers

---

## Error Handling

### Go: Explicit Errors with Wrapping

```go
func ProcessUser(id string) error {
    user, err := repo.Find(id)
    if err != nil {
        return fmt.Errorf("failed to find user %s: %w", id, err)
    }

    if err := validator.Validate(user); err != nil {
        return fmt.Errorf("validation failed: %w", err)
    }

    return nil
}

// Check errors
if errors.Is(err, ErrNotFound) { }
if errors.As(err, &validationErr) { }
```

**Principles:**
- Return errors, don't panic
- Wrap with %w for context
- Check with errors.Is/As

### Python: Exceptions + Context

```python
class UserNotFoundError(Exception):
    def __init__(self, user_id: str):
        self.user_id = user_id
        super().__init__(f"User {user_id} not found")

def process_user(user_id: str) -> User:
    try:
        user = repo.find(user_id)
    except DatabaseError as e:
        raise UserNotFoundError(user_id) from e
    
    if not validator.validate(user):
        raise ValidationError("User validation failed")
    
    return user

# Handle
try:
    user = process_user(id)
except UserNotFoundError as e:
    logger.error(f"User not found: {e.user_id}")
```

**Principles:**
- Custom exceptions with context
- Chain with `from`
- Log at boundaries

### Rails: Exceptions + Service Results

```ruby
class UserService
  Result = Struct.new(:success, :data, :error, keyword_init: true)

  def call
    user = repo.find(user_id)
    
    unless user
      return Result.new(
        success: false,
        error: "User not found"
      )
    end

    Result.new(success: true, data: user)
  rescue ActiveRecord::RecordInvalid => e
    Result.new(success: false, error: e.message)
  end
end

# Usage
result = UserService.new(user_id: id).call
if result.success
  render json: result.data
else
  render json: { error: result.error }, status: :unprocessable_entity
end
```

**Principles:**
- Return result objects
- Catch at service boundary
- Log in services, not controllers

---

## Testing Strategies

### Go: Table-Driven Tests

```go
func TestAdd(t *testing.T) {
    tests := []struct {
        name string
        a, b int
        want int
    }{
        {"positive", 2, 3, 5},
        {"negative", -2, 3, 1},
        {"zero", 0, 0, 0},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got := Add(tt.a, tt.b)
            if got != tt.want {
                t.Errorf("got %d, want %d", got, tt.want)
            }
        })
    }
}
```

### Python: pytest with fixtures

```python
@pytest.fixture
def user_service(mock_repo, mock_logger):
    return UserService(repo=mock_repo, logger=mock_logger)

def test_find_user_success(user_service, mock_repo):
    mock_repo.find.return_value = User(id="1", name="Max")
    
    user = user_service.find("1")
    
    assert user.name == "Max"
    mock_repo.find.assert_called_once_with("1")

@pytest.mark.parametrize("input,expected", [
    ("test@example.com", True),
    ("invalid", False),
])
def test_email_validation(input, expected):
    assert validate_email(input) == expected
```

### Rails: RSpec with factories

```ruby
RSpec.describe UserService do
  let(:repo) { instance_double(UserRepository) }
  let(:service) { described_class.new(repo: repo) }

  describe '#call' do
    context 'when user exists' do
      let(:user) { create(:user) }

      before do
        allow(repo).to receive(:find).and_return(user)
      end

      it 'returns success result' do
        result = service.call
        expect(result.success).to be true
        expect(result.data).to eq(user)
      end
    end

    context 'when user not found' do
      before do
        allow(repo).to receive(:find).and_return(nil)
      end

      it 'returns error result' do
        result = service.call
        expect(result.success).to be false
      end
    end
  end
end
```

---

## Background Jobs

### Go: Worker Pool Pattern

```go
func ProcessJobs(ctx context.Context, jobs <-chan Job) {
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

### Python: Celery/Dramatiq

```python
from dramatiq import actor

@actor(max_retries=3)
def process_user(user_id: str):
    user = User.objects.get(id=user_id)
    # Process user
    
# Enqueue
process_user.send(user_id="123")

# Delayed
process_user.send_with_options(
    args=(user_id,),
    delay=5000  # 5 seconds
)
```

### Rails: Sidekiq

```ruby
class ProcessUserJob
  include Sidekiq::Job
  
  sidekiq_options retry: 3

  def perform(user_id)
    user = User.find(user_id)
    # Process user
  end
end

# Enqueue
ProcessUserJob.perform_async(user.id)

# Delayed
ProcessUserJob.perform_in(5.minutes, user.id)
```

**Common principles:**
- Jobs should be idempotent
- Pass IDs, not objects
- Handle missing records gracefully
- Use appropriate retry strategies

---

## Configuration Management

### Go: Environment + Struct

```go
type Config struct {
    DatabaseURL string
    Port        int
    LogLevel    string
}

func LoadConfig() (*Config, error) {
    return &Config{
        DatabaseURL: os.Getenv("DATABASE_URL"),
        Port:        getEnvInt("PORT", 8080),
        LogLevel:    getEnv("LOG_LEVEL", "info"),
    }, nil
}
```

### Python: pydantic Settings

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    port: int = 8080
    log_level: str = "info"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### Rails: Environment Variables + Credentials

```ruby
# config/application.rb
config.database_url = ENV.fetch("DATABASE_URL")
config.port = ENV.fetch("PORT", 3000).to_i

# Encrypted credentials
Rails.application.credentials.secret_key_base
```

---

## Logging

### Go: Structured Logging (zap/zerolog)

```go
logger.Info("user created",
    zap.String("user_id", user.ID),
    zap.String("email", user.Email),
)

logger.Error("failed to create user",
    zap.Error(err),
    zap.String("email", email),
)
```

### Python: structlog

```python
logger.info("user created", user_id=user.id, email=user.email)
logger.error("failed to create user", email=email, exc_info=True)
```

### Rails: Tagged Logging

```ruby
Rails.logger.tagged("UserService", user.id) do
  Rails.logger.info "User created"
end
```

**Principles:**
- Structured logging (key-value pairs)
- Log at boundaries (services, jobs)
- Don't log AND return errors (choose one)
- Include context (IDs, operation names)

---

## Database Patterns

### Repository Pattern (All Languages)

**Go:**
```go
type UserRepository interface {
    Find(id string) (*User, error)
    Save(user *User) error
    Delete(id string) error
}
```

**Python:**
```python
class UserRepository(Protocol):
    def find(self, id: str) -> User | None: ...
    def save(self, user: User) -> None: ...
```

**Rails:**
```ruby
# ActiveRecord already provides repository pattern
User.find(id)
User.where(email: email).first
user.save
```

### Transaction Patterns

**Go:**
```go
tx, err := db.Begin()
if err != nil {
    return err
}
defer tx.Rollback()

// Operations...

return tx.Commit()
```

**Python:**
```python
with db.transaction():
    user.save()
    order.save()
```

**Rails:**
```ruby
ActiveRecord::Base.transaction do
  user.save!
  order.save!
end
```

---

## Common Anti-Patterns to Avoid

### All Languages

❌ **Global mutable state**
```
# Don't use global variables for application state
```

❌ **God objects**
```
# Keep classes/services focused (single responsibility)
```

❌ **Mixing concerns**
```
# Don't put business logic in controllers/handlers
# Don't put HTTP logic in services
```

❌ **Not handling errors**
```
# Always handle errors explicitly
```

❌ **Premature optimization**
```
# Make it work, make it right, make it fast (in that order)
```

---

## When to Use Each Pattern

| Pattern              | Use When                                      |
|----------------------|-----------------------------------------------|
| Dependency Injection | Building testable, decoupled systems          |
| Repository           | Abstracting data access                       |
| Service Objects      | Encapsulating business logic                  |
| Background Jobs      | Long-running or async operations              |
| Result Objects       | Need structured success/failure (Rails/Python)|
| Error Wrapping       | Need error context and tracing (Go)           |

---

**For implementation details, see language-specific skills:**
- Go: `golang/SKILL.md`
- Python: `python/SKILL.md`
- Rails: `rails/SKILL.md`
