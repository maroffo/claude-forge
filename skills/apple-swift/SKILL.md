---
name: apple-swift
description: "Modern Apple platform development with Swift 6, SwiftUI, async/await, and performance optimization for iOS, iPadOS, macOS, watchOS, and visionOS."
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

**Nav:** [Swift 6](#swift-6) | [SwiftUI](#swiftui) | [Concurrency](#concurrency) | [Architecture](#architecture) | [Networking](#networking) | [Testing](#testing) | [Performance](#performance) | [Review](#review)

**See also:** `_AST_GREP.md`, `_PATTERNS.md`, `source-control`

---

## Swift 6

### 6.0 - Strict Concurrency
Data-race safety enforced at compile time.

```swift
// Enable: swiftLanguageModes: [.v6] in Package.swift
// Or: Build Settings → Swift Language Mode → Swift 6

// ✅ Sendable struct
struct UserData: Sendable { let id: String; let name: String }

// ✅ Actor for mutable shared state
actor UserCache {
    private var cache: [String: User] = [:]
    func get(_ id: String) -> User? { cache[id] }
    func set(_ user: User) { cache[user.id] = user }
}

// ❌ Compile error - mutable class not Sendable
class UserManager { var users: [User] = [] }

// Migration: -strict-concurrency=complete → fix warnings → enable Swift 6
```

### 6.2 - Approachable Concurrency (2025)

```swift
// Main-actor by default: SWIFT_STRICT_CONCURRENCY=default_isolation
// No @MainActor needed for UI code

// @concurrent for explicit parallelism
@concurrent func processInBackground() async { /* off main thread */ }

// Async stays in caller's context - no unexpected thread hops
@MainActor class ViewModel {
    func loadData() async {
        let data = await fetchData()  // Returns to main actor
        self.items = data             // Safe
    }
}

// Isolated conformances - MainActor types can conform to protocols
@MainActor final class UserVM: Equatable {
    var name = ""
    static func == (lhs: UserVM, rhs: UserVM) -> Bool { lhs.name == rhs.name }
}
```

### Macros

```swift
@Observable final class UserStore { var users: [User] = []; var isLoading = false }

@Model final class Task { var title: String; var isCompleted: Bool; var createdAt: Date }

#Preview { ContentView() }
#Preview("Dark") { ContentView().preferredColorScheme(.dark) }
```

---

## SwiftUI

### @Observable (iOS 17+, Preferred)

```swift
// ❌ OLD: class VM: ObservableObject { @Published var user: User? }
// ✅ NEW:
@Observable final class UserVM { var user: User?; var isLoading = false }

// @State for view-owned @Observable
struct ContentView: View {
    @State private var vm = UserVM()
    var body: some View { UserView(viewModel: vm) }
}

// @Bindable for two-way bindings
struct ProfileEditor: View {
    @Bindable var vm: ProfileVM
    var body: some View { TextField("Name", text: $vm.name) }
}
```

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

### NavigationStack (iOS 16+)

```swift
enum AppRoute: Hashable { case profile(String); case settings; case detail(Item) }

struct ContentView: View {
    @State private var path = NavigationPath()
    var body: some View {
        NavigationStack(path: $path) {
            HomeView()
                .navigationDestination(for: AppRoute.self) { route in
                    switch route {
                    case .profile(let id): UserProfileView(userId: id)
                    case .settings: SettingsView()
                    case .detail(let item): ItemDetailView(item: item)
                    }
                }
        }
    }
}
```

### SwiftData (iOS 17+)

```swift
@Model final class Task {
    var title: String; var notes: String?; var isCompleted: Bool; var dueDate: Date?; var createdAt: Date
    @Relationship(deleteRule: .cascade) var subtasks: [Subtask] = []
    init(title: String, notes: String? = nil) {
        self.title = title; self.notes = notes; self.isCompleted = false; self.createdAt = .now
    }
}

struct TaskListView: View {
    @Query(sort: \Task.createdAt, order: .reverse) private var tasks: [Task]
    @Environment(\.modelContext) private var ctx
    var body: some View { List(tasks) { TaskRow(task: $0) } }
    func add(_ title: String) { ctx.insert(Task(title: title)) }
}
```

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

### async/await

```swift
func fetchUser(id: String) async throws -> User {
    let (data, _) = try await URLSession.shared.data(from: URL(string: "https://api.example.com/users/\(id)")!)
    return try JSONDecoder().decode(User.self, from: data)
}

// Parallel with async let
func loadDashboard() async throws -> Dashboard {
    async let user = fetchUser()
    async let posts = fetchPosts()
    async let notifs = fetchNotifications()
    return try await Dashboard(user: user, posts: posts, notifications: notifs)
}

// TaskGroup for dynamic parallelism
func fetchAll(ids: [String]) async throws -> [User] {
    try await withThrowingTaskGroup(of: User.self) { group in
        for id in ids { group.addTask { try await fetchUser(id: id) } }
        return try await group.reduce(into: []) { $0.append($1) }
    }
}
```

### MainActor

```swift
@MainActor final class HomeVM {
    var items: [Item] = []; var isLoading = false
    func load() async {
        isLoading = true; defer { isLoading = false }
        items = (try? await itemService.fetchItems()) ?? []
    }
}
```

### Combine vs async/await

| Use Case | Choice |
|----------|--------|
| One-shot network | async/await |
| Parallel fetches | async let / TaskGroup |
| Real-time streams | Combine / AsyncStream |
| UI events, debounce | Combine |

---

## Architecture

### MVVM with @Observable

```swift
@Observable @MainActor final class UserListVM {
    private(set) var users: [User] = []; private(set) var isLoading = false; private(set) var error: Error?
    private let svc: UserServiceProtocol
    init(svc: UserServiceProtocol = UserService()) { self.svc = svc }
    func load() async { isLoading = true; error = nil; defer { isLoading = false }; do { users = try await svc.fetchUsers() } catch { self.error = error } }
}

struct UserListView: View {
    @State private var vm = UserListVM()
    var body: some View {
        Group {
            if vm.isLoading { ProgressView() }
            else if let e = vm.error { ErrorView(error: e, retry: { Task { await vm.load() } }) }
            else { List(vm.users) { UserRow(user: $0) } }
        }.task { await vm.load() }
    }
}
```

### Dependency Injection

```swift
protocol UserServiceProtocol { func fetchUsers() async throws -> [User] }

// Environment DI
private struct UserServiceKey: EnvironmentKey { static let defaultValue: UserServiceProtocol = UserService() }
extension EnvironmentValues { var userService: UserServiceProtocol { get { self[UserServiceKey.self] } set { self[UserServiceKey.self] = newValue } } }
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

## Performance

### Common Performance Killers

| Issue | Impact | Fix |
|-------|--------|-----|
| Unstable identity | List jumps/flickers | Use `.id()` or stable Identifiable |
| Observing everything | Over-invalidation | Fine-grained `@Observable` tracking |
| Deep nesting | Slow layout | Split into child views |

### Debug: `let _ = Self._printChanges()` in body to trace recomputations.

### SwiftUI Optimization

```swift
// @Observable tracks accessed properties only
// LazyVStack for long lists (not VStack)
ScrollView { LazyVStack { ForEach(items) { ItemRow(item: $0) } } }
```

### Instruments (CLI via xctrace)

| Template | Use Case |
|----------|----------|
| Time Profiler | CPU hotspots, slow functions |
| Allocations | Memory usage, leaks |
| System Trace | I/O, system calls |
| Leaks | Memory leak detection |

```bash
xctrace list templates
xctrace record --template "Time Profiler" --attach "MyApp" --output ~/profile.trace --time-limit 30s
xctrace record --template "Time Profiler" --device "iPhone 16 Pro" --attach "MyApp" --output ~/profile.trace
xctrace record --template "Time Profiler" --launch com.example.myapp --output ~/profile.trace --time-limit 60s
xctrace export --input profile.trace --output profile.xml
xctrace symbolicate --input profile.trace --output symbolicated.trace
```

**Tips:** Profile Release builds. Use `--time-limit` to auto-stop. Warm up app first.

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

## Resources

**Official:** [Swift](https://developer.apple.com/swift/) | [SwiftUI](https://developer.apple.com/documentation/swiftui/) | [SwiftData](https://developer.apple.com/documentation/swiftdata/) | [Swift 6 Migration](https://developer.apple.com/documentation/swift/adoptingswift6)

**Libraries:** [TCA](https://github.com/pointfreeco/swift-composable-architecture) | [Snapshot Testing](https://github.com/pointfreeco/swift-snapshot-testing) | [Kingfisher](https://github.com/onevcat/Kingfisher) | [SwiftLint](https://github.com/realm/SwiftLint)
