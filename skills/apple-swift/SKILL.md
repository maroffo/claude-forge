---
name: apple-swift
description: "Apple platform development with Swift 6, SwiftUI, async/await, and performance. Use when working with .swift files, Package.swift, Xcode projects, or building for iOS/macOS/watchOS/visionOS."
allowed-tools: [mcp__acp__Read, mcp__acp__Edit, mcp__acp__Write, mcp__acp__Bash]
---

# ABOUTME: Apple platform guide - Swift 6, SwiftUI, concurrency, testing, performance
# ABOUTME: Modern Swift (2025-2026): @Observable, SwiftData, NavigationStack, strict concurrency

# Apple Platform Development

## Quick Reference

```bash
# Build
xcodebuild -scheme MyApp -sdk iphoneos build
xcodebuild -scheme MyApp -sdk macosx build

# Tests
xcodebuild test -scheme MyApp -destination 'platform=iOS Simulator,name=iPhone 16'

# SwiftLint
swiftlint lint [--fix]

# SPM
swift build && swift test && swift package resolve

# ast-grep patterns
sg --pattern '@Observable final class $NAME { $$$ }' --lang swift
sg --pattern 'func $NAME() async throws -> $RET { $$$ }' --lang swift
sg --pattern '@MainActor' --lang swift
```

**Nav:** [Swift 6](#swift-6) | [SwiftUI](#swiftui) | [Concurrency](#concurrency) | [Architecture](#architecture) | [Testing](#testing) | [Review](#review)

**See also:** `_AST_GREP.md`, `_PATTERNS.md`, `source-control`, `references/`

---

## Swift 6

### Key Features

- **Strict concurrency** - Data-race safety enforced at compile time
- **@Observable** - Modern state management replacing ObservableObject
- **@MainActor** - Automatic UI thread isolation
- **Sendable** - Safe cross-actor value types
- **Macros** - @Observable, @Model, #Preview

### Migration Checklist

- [ ] Enable strict concurrency: `swiftLanguageModes: [.v6]`
- [ ] Replace `ObservableObject` with `@Observable`
- [ ] Add `@MainActor` to UI classes
- [ ] Add `Sendable` to value types
- [ ] Use actors for shared mutable state
- [ ] Replace callbacks with `async throws`

**Detailed patterns:** See `references/swift6-patterns.md`

---

## SwiftUI

### Property Wrappers

| Wrapper | Use | Observable? |
|---------|-----|-------------|
| `@State` | View-owned values, @Observable | Yes |
| `@Binding` | Two-way to parent | Yes |
| `@Bindable` | Two-way to @Observable props | Yes |
| `@Environment` | System/app values | Yes |
| `@StateObject` | View-owned ObservableObject (legacy) | Yes |
| `@ObservedObject` | Passed-in ObservableObject (legacy) | Yes |

### View Property Ordering

1. `@Environment` values
2. `let` (immutable dependencies)
3. `@State` / `@Binding` (mutable state)
4. Computed properties
5. `init` (if needed)
6. `body`
7. Methods (private)

### View Size Decision Tree

| Condition | Action |
|-----------|--------|
| <100 lines, simple state | Single view with @State |
| 100-200 lines | Extract private subviews |
| >200 lines | Multiple files, shared state |
| Business logic needed | @Observable ViewModel |
| Network/DB access | Repository pattern |

### Modern Patterns (iOS 17+)

```swift
// @Observable instead of ObservableObject
@Observable final class UserVM { var user: User?; var isLoading = false }

// NavigationStack instead of NavigationView
enum AppRoute: Hashable { case profile(String); case settings }

// SwiftData for persistence
@Model final class Task { var title: String; var isCompleted: Bool }
```

**Detailed patterns:** See `references/swiftui-patterns.md`

---

## Concurrency

### Common Fixes

| Error | Fix | Example |
|-------|-----|---------|
| Main actor isolation | Add `@MainActor` to class/func | `@MainActor class ViewModel` |
| Non-isolated access | Mark `nonisolated` | `nonisolated func helper()` |
| Sendable violation | Add `@unchecked Sendable` or fix | `class VM: @unchecked Sendable` |
| Protocol async | Require `async` in protocol | `protocol P { func load() async }` |
| Closure capture | Use `@Sendable` closure | `Task { @Sendable in ... }` |

### MainActor Pattern

```swift
@MainActor final class HomeVM {
    var items: [Item] = []; var isLoading = false
    func load() async {
        isLoading = true; defer { isLoading = false }
        items = (try? await itemService.fetchItems()) ?? []
    }
}
```

### Parallel Execution

```swift
// Fixed parallelism
async let user = fetchUser()
async let posts = fetchPosts()
return try await Dashboard(user: user, posts: posts)

// Dynamic parallelism
try await withThrowingTaskGroup(of: User.self) { group in
    for id in ids { group.addTask { try await fetchUser(id: id) } }
    return try await group.reduce(into: []) { $0.append($1) }
}
```

### Combine vs async/await

| Use Case | Choice |
|----------|--------|
| One-shot network | async/await |
| Parallel fetches | async let / TaskGroup |
| Real-time streams | Combine / AsyncStream |
| UI events, debounce | Combine |

**Detailed patterns:** See `references/concurrency-patterns.md`

---

## Architecture

### MVVM with @Observable

```swift
@Observable @MainActor final class UserListVM {
    private(set) var users: [User] = []
    private(set) var isLoading = false
    private(set) var error: Error?
    private let svc: UserServiceProtocol

    init(svc: UserServiceProtocol = UserService()) { self.svc = svc }

    func load() async {
        isLoading = true; error = nil; defer { isLoading = false }
        do { users = try await svc.fetchUsers() }
        catch { self.error = error }
    }
}
```

### Dependency Injection

```swift
protocol UserServiceProtocol { func fetchUsers() async throws -> [User] }

// Environment DI
private struct UserServiceKey: EnvironmentKey {
    static let defaultValue: UserServiceProtocol = UserService()
}
extension EnvironmentValues {
    var userService: UserServiceProtocol {
        get { self[UserServiceKey.self] }
        set { self[UserServiceKey.self] = newValue }
    }
}
```

---

## Testing

### Swift Testing (iOS 18+, Preferred)

```swift
import Testing

@Suite("UserService") struct UserServiceTests {
    let svc: UserService; let mock: MockNetworkClient
    init() { mock = MockNetworkClient(); svc = UserService(network: mock) }

    @Test("fetch success") func fetch() async throws {
        mock.mockResponse = [User(id: "1", name: "John")]
        let users = try await svc.fetchUsers()
        #expect(users.count == 1); #expect(users[0].name == "John")
    }

    @Test("by id", arguments: ["1", "2", "3"]) func byId(_ id: String) async throws {
        mock.mockResponse = User(id: id, name: "Test")
        #expect((try await svc.fetchUser(id: id)).id == id)
    }
}
```

---

## Review Checklists

### Concurrency
- [ ] MainActor for UI
- [ ] Sendable for cross-actor data
- [ ] Task cancellation handled
- [ ] No data races (Swift 6)

### SwiftUI
- [ ] @Observable not ObservableObject (iOS 17+)
- [ ] NavigationStack not NavigationView
- [ ] .task not .onAppear + Task
- [ ] LazyVStack for long lists

### Red Flags

**CRITICAL:** Force unwrap without safety, UI updates off MainActor, data races, retain cycles

**HIGH:** ObservableObject when @Observable available, NavigationView instead of NavigationStack

---

## Detailed References

For exhaustive patterns and examples, consult:

- `references/swift6-patterns.md` - Swift 6 migration, Sendable, actors, macros
- `references/swiftui-patterns.md` - NavigationStack, SwiftData, MVVM, dependency injection
- `references/concurrency-patterns.md` - async/await, TaskGroup, MainActor, actors, AsyncStream
- `references/performance.md` - Optimization, Instruments profiling, memory management

---

## Resources

**Official:** [Swift](https://developer.apple.com/swift/) | [SwiftUI](https://developer.apple.com/documentation/swiftui/) | [SwiftData](https://developer.apple.com/documentation/swiftdata/) | [Swift 6 Migration](https://developer.apple.com/documentation/swift/adoptingswift6)

**Libraries:** [TCA](https://github.com/pointfreeco/swift-composable-architecture) | [Snapshot Testing](https://github.com/pointfreeco/swift-snapshot-testing) | [Kingfisher](https://github.com/onevcat/Kingfisher) | [SwiftLint](https://github.com/realm/SwiftLint)
