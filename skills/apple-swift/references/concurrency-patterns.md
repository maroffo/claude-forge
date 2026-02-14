# Concurrency Detailed Patterns

## async/await Fundamentals

### Basic async function

```swift
func fetchUser(id: String) async throws -> User {
    let (data, _) = try await URLSession.shared.data(from: URL(string: "https://api.example.com/users/\(id)")!)
    return try JSONDecoder().decode(User.self, from: data)
}
```

### Calling async functions

```swift
// From async context
let user = try await fetchUser(id: "123")

// From sync context - use Task
Task {
    let user = try await fetchUser(id: "123")
    print(user.name)
}
```

## Parallel Execution

### async let (fixed concurrency)

```swift
func loadDashboard() async throws -> Dashboard {
    async let user = fetchUser()
    async let posts = fetchPosts()
    async let notifs = fetchNotifications()
    return try await Dashboard(user: user, posts: posts, notifications: notifs)
}
```

**When to use:** Fixed number of concurrent operations known at compile time.

### TaskGroup (dynamic concurrency)

```swift
func fetchAll(ids: [String]) async throws -> [User] {
    try await withThrowingTaskGroup(of: User.self) { group in
        for id in ids { group.addTask { try await fetchUser(id: id) } }
        return try await group.reduce(into: []) { $0.append($1) }
    }
}
```

**When to use:** Dynamic number of concurrent operations (e.g., from array).

### TaskGroup with cancellation

```swift
func fetchWithTimeout(ids: [String], timeout: TimeInterval) async throws -> [User] {
    try await withThrowingTaskGroup(of: User.self) { group in
        // Timeout task
        group.addTask {
            try await Task.sleep(for: .seconds(timeout))
            throw TimeoutError()
        }

        // Fetch tasks
        for id in ids {
            group.addTask { try await fetchUser(id: id) }
        }

        var users: [User] = []
        for try await user in group {
            users.append(user)
        }
        return users
    }
}
```

## MainActor

### MainActor isolation

```swift
@MainActor final class HomeVM {
    var items: [Item] = []
    var isLoading = false

    func load() async {
        isLoading = true
        defer { isLoading = false }
        items = (try? await itemService.fetchItems()) ?? []
    }
}
```

### Explicit MainActor calls

```swift
func updateUI() {
    Task { @MainActor in
        self.label.text = "Updated"
    }
}

// Or
await MainActor.run {
    self.label.text = "Updated"
}
```

### nonisolated functions

```swift
@MainActor final class ViewModel {
    var items: [Item] = []

    // This can be called from any context
    nonisolated func formatItem(_ item: Item) -> String {
        return item.title.uppercased()
    }

    // This requires MainActor context
    func updateItems(_ newItems: [Item]) {
        self.items = newItems
    }
}
```

## Actors

### Basic actor

```swift
actor UserCache {
    private var cache: [String: User] = [:]

    func get(_ id: String) -> User? {
        cache[id]
    }

    func set(_ user: User) {
        cache[user.id] = user
    }

    func clear() {
        cache.removeAll()
    }
}
```

### Actor usage

```swift
let cache = UserCache()

// All calls are async
let user = await cache.get("123")
await cache.set(newUser)
```

### nonisolated actor methods

```swift
actor DataProcessor {
    private var data: [String] = []

    func add(_ item: String) {
        data.append(item)
    }

    nonisolated func format(_ text: String) -> String {
        return text.uppercased()
    }
}
```

## Task Management

### Task with priority

```swift
Task(priority: .high) {
    await performCriticalOperation()
}

Task(priority: .background) {
    await performBackgroundSync()
}
```

### Task cancellation

```swift
let task = Task {
    for i in 0..<100 {
        try Task.checkCancellation()
        await processItem(i)
    }
}

// Cancel later
task.cancel()
```

### Detached tasks

```swift
// Detached from current context - doesn't inherit priority/actor
Task.detached {
    await performIndependentWork()
}
```

## Combine vs async/await

### Publisher to async

```swift
// Convert Publisher to async sequence
let values = publisher.values
for await value in values {
    print(value)
}

// Single value
let value = try await publisher.singleValue
```

### async to Publisher

```swift
import Combine

extension Publisher {
    static func asyncValue(_ operation: @escaping () async throws -> Output) -> AnyPublisher<Output, Error> where Failure == Error {
        Future { promise in
            Task {
                do {
                    let value = try await operation()
                    promise(.success(value))
                } catch {
                    promise(.failure(error))
                }
            }
        }.eraseToAnyPublisher()
    }
}
```

## AsyncStream

### Creating AsyncStream

```swift
func notifications() -> AsyncStream<Notification> {
    AsyncStream { continuation in
        let observer = NotificationCenter.default.addObserver(
            forName: .someNotification,
            object: nil,
            queue: nil
        ) { notification in
            continuation.yield(notification)
        }

        continuation.onTermination = { _ in
            NotificationCenter.default.removeObserver(observer)
        }
    }
}
```

### Consuming AsyncStream

```swift
for await notification in notifications() {
    print("Received: \(notification)")
}
```

## Common Patterns

### Retry with exponential backoff

```swift
func fetchWithRetry<T>(
    maxRetries: Int = 3,
    operation: @escaping () async throws -> T
) async throws -> T {
    var lastError: Error?

    for attempt in 0..<maxRetries {
        do {
            return try await operation()
        } catch {
            lastError = error
            let delay = pow(2.0, Double(attempt))
            try await Task.sleep(for: .seconds(delay))
        }
    }

    throw lastError ?? RetryError.exhausted
}
```

### Debounce

```swift
actor Debouncer {
    private var task: Task<Void, Never>?

    func debounce(for duration: Duration, operation: @escaping () async -> Void) {
        task?.cancel()
        task = Task {
            try? await Task.sleep(for: duration)
            if !Task.isCancelled {
                await operation()
            }
        }
    }
}
```

### Race (first to complete wins)

```swift
func race<T>(_ operations: [() async throws -> T]) async throws -> T {
    try await withThrowingTaskGroup(of: T.self) { group in
        for operation in operations {
            group.addTask { try await operation() }
        }

        guard let first = try await group.next() else {
            throw RaceError.noResults
        }

        group.cancelAll()
        return first
    }
}
```
