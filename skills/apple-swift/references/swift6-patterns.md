# Swift 6 Detailed Patterns

## 6.0 - Strict Concurrency

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

## 6.2 - Approachable Concurrency (2025)

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

## Macros

```swift
@Observable final class UserStore { var users: [User] = []; var isLoading = false }

@Model final class Task { var title: String; var isCompleted: Bool; var createdAt: Date }

#Preview { ContentView() }
#Preview("Dark") { ContentView().preferredColorScheme(.dark) }
```

## Migration Guide

### From Swift 5 to Swift 6

1. **Enable strict concurrency checking:**
   ```swift
   // Package.swift
   swiftSettings: [.enableExperimentalFeature("StrictConcurrency")]
   ```

2. **Fix data-race warnings:**
   - Add `@MainActor` to UI classes
   - Add `Sendable` conformance to value types
   - Use actors for shared mutable state
   - Add `nonisolated` for non-isolated functions

3. **Enable Swift 6 mode:**
   ```swift
   // Package.swift
   swiftLanguageModes: [.v6]
   ```

### Common Migration Patterns

| Swift 5 | Swift 6 |
|---------|---------|
| `class ViewModel: ObservableObject` | `@Observable @MainActor final class ViewModel` |
| `@Published var items: [Item]` | `var items: [Item]` (with @Observable) |
| Global mutable state | `actor` or `@MainActor` isolation |
| Callback closures | `async throws` functions |
