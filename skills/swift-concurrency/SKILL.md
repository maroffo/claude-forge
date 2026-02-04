# ABOUTME: Swift 6.2+ concurrency safety fixes and actor isolation patterns
# Swift Concurrency

## When to Invoke
- Swift 6 strict concurrency errors
- Actor isolation violations
- Sendable conformance failures
- @MainActor warnings
- Protocol + async/await issues

## Capabilities
- Fix actor isolation bugs
- Add Sendable conformance
- Resolve @MainActor conflicts
- Protocol concurrency patterns
- Approachable concurrency mode guidance

## Common Fixes

| Error | Fix | Example |
|-------|-----|---------|
| Main actor isolation | Add `@MainActor` to class/func | `@MainActor class ViewModel` |
| Non-isolated access | Mark `nonisolated` | `nonisolated func helper()` |
| Sendable violation | Add `@unchecked Sendable` or fix | `class VM: @unchecked Sendable` |
| Protocol async | Require `async` in protocol | `protocol P { func load() async }` |
| Closure capture | Use `@Sendable` closure | `Task { @Sendable in ... }` |

## Swift 6 Patterns

```swift
// Actor with nonisolated helpers
@MainActor
class ViewModel: ObservableObject {
    @Published var data: [Item] = []

    nonisolated func formatDate(_ date: Date) -> String {
        DateFormatter().string(from: date)
    }
}

// Sendable conformance
struct Config: Sendable {
    let apiKey: String
    let timeout: Duration
}

// Protocol with async requirement
protocol DataLoader: Sendable {
    func fetch() async throws -> Data
}
```

## Approachable Concurrency Mode
When migrating legacy code, use `SWIFT_UPCOMING_FEATURE_CONCURRENCY_CHECKING = minimal` in build settings. Incrementally fix warnings before enabling complete checking.

## Decision Tree
- UI updates → `@MainActor`
- Background work → `Task { ... }`
- Shared state → `actor` or `@MainActor`
- Value types → `Sendable` conformance
- Reference types → Evaluate thread safety, use `@unchecked Sendable` if proven safe

## Resources
- [Swift Evolution SE-0413](https://github.com/apple/swift-evolution/blob/main/proposals/0413-typed-throws.md)
- [Actor isolation docs](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/concurrency/)
