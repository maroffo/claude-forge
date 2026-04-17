---
name: apple-swift
description: "Apple platform development with Swift, SwiftUI, async/await, and performance. Use when working with .swift files, Package.swift, Xcode projects, or building for iOS/macOS/watchOS/visionOS."
compatibility: "Requires Xcode and platform SDKs. Optional: SwiftLint."
allowed-tools: [mcp__acp__Read, mcp__acp__Edit, mcp__acp__Write, mcp__acp__Bash]
---

# ABOUTME: Apple platform guide, Swift, SwiftUI, concurrency, testing, performance
# ABOUTME: Conventions, strict concurrency rules, MVVM + DI patterns, review checklists

# Apple Platform Development

## Quick Reference

```bash
# Build
xcodebuild -scheme MyApp -sdk iphoneos build
xcodebuild -scheme MyApp -sdk macosx build

# Tests
xcodebuild test -scheme MyApp -destination 'platform=iOS Simulator,name=iPhone 16'

# SwiftLint / SPM
swiftlint lint [--fix]
swift build && swift test && swift package resolve

# ast-grep
sg --pattern '@Observable final class $NAME { $$$ }' --lang swift
sg --pattern '@MainActor' --lang swift
```

**See also:** `_AST_GREP.md`, `_PATTERNS.md`, `source-control`, `references/`

---

## Version (determine, don't assume)

Never assume a Swift/Xcode version from prior knowledge: it rots fast and you miss CVE fixes. Fetch the truth:

```bash
swift --version                                 # local toolchain
xcodebuild -version                             # Xcode version
cat .swift-version 2>/dev/null                  # pinned toolchain (if present)
grep -E 'swift-tools-version' Package.swift     # SPM minimum
curl -s https://api.github.com/repos/swiftlang/swift/releases/latest | jq -r .tag_name  # latest upstream
```

For a new project, pin to the latest stable. For an existing one, read `Package.swift` (plus `.xcode-version` / `.tool-versions` if present) and prefer idioms gated to that version or lower.

---

## Pre-Commit Verification (MANDATORY)

Before every commit, both of these MUST pass:

```bash
make check       # project-wide gate (lint, types, tests, security)
make test-e2e    # end-to-end tests (UI tests, integration target, or project's e2e scheme)
```

If `make check` is missing, scaffold it with the `project-checks` skill. If there is no e2e target, do NOT silently skip: flag it to the user and ask whether to proceed or add one.

Full raw toolchain (what `make check` should expand to):

```bash
swift build                                     # compilation check
swift test                                      # unit tests
swiftlint lint --strict                         # lint (fail on warnings)
swift-format lint --recursive Sources Tests     # formatting check
xcodebuild -scheme MyApp test \
  -destination 'platform=iOS Simulator,name=iPhone 16'   # platform tests
```

---

## SwiftUI

### Property Wrappers

| Wrapper | Use |
|---------|-----|
| `@State` | View-owned values, @Observable |
| `@Binding` | Two-way to parent |
| `@Bindable` | Two-way to @Observable props |
| `@Environment` | System/app values |
| `@StateObject` | View-owned ObservableObject (legacy) |

**View property order:** @Environment, let, @State/@Binding, computed, init, body, private methods

**View sizing:** <100 lines = single view; 100-200 = extract subviews; >200 = multiple files; business logic = @Observable VM; network/DB = repository pattern

For NavigationStack, SwiftData, MVVM, and DI patterns, see `references/swiftui-patterns.md`.

---

## Concurrency

### Common Fixes

| Error | Fix |
|-------|-----|
| Main actor isolation | Add `@MainActor` to class/func |
| Non-isolated access | Mark `nonisolated` |
| Sendable violation | Add `@unchecked Sendable` or fix |
| Protocol async | Require `async` in protocol |
| Closure capture | Use `@Sendable` closure |

### When to use what

| Use Case | Choice |
|----------|--------|
| One-shot network | async/await |
| Parallel fetches | async let / TaskGroup |
| Real-time streams | Combine / AsyncStream |
| UI events, debounce | Combine |

**NON-NEGOTIABLE:** UI updates always on `@MainActor`. Cross-actor value types must be `Sendable`. Respect task cancellation: check `Task.isCancelled` in long-running work.

For MainActor, parallel execution, and actor patterns, see `references/concurrency-patterns.md`.

---

## Architecture

**MVVM with @Observable:** `@Observable @MainActor final class VM` with `private(set)` properties, injected service protocols, `async` load methods with `defer { isLoading = false }`.

**DI:** Protocol-based with `EnvironmentKey` for SwiftUI injection.

**Coordinator pattern:** For flow-heavy apps, lift navigation state out of views into a Coordinator type owning a `NavigationPath` (or route enum) and exposing intents.

**Testing (Swift Testing):** `@Suite`, `@Test`, `#expect`. Parameterized with `arguments:`. Mock via protocol injection. XCTest still valid where needed (UI tests, legacy targets).

For full code examples, see `references/swiftui-patterns.md` and `references/swift6-patterns.md`.

---

## Review Checklists

**Concurrency:** MainActor for UI, Sendable for cross-actor data, task cancellation handled, no data races

**SwiftUI:** @Observable over ObservableObject where available, NavigationStack over NavigationView, `.task` over `.onAppear + Task`, LazyVStack for long lists

**CRITICAL:** Force unwrap without safety, UI updates off MainActor, data races, retain cycles

**HIGH:** Legacy ObservableObject when @Observable fits, NavigationView in new code

---

## Detailed References

- `references/swift6-patterns.md` - Strict concurrency migration, Sendable, actors, macros
- `references/swiftui-patterns.md` - NavigationStack, SwiftData, MVVM, dependency injection
- `references/concurrency-patterns.md` - async/await, TaskGroup, MainActor, actors, AsyncStream
- `references/performance.md` - Optimization, Instruments profiling, memory management

**Official:** [Swift](https://developer.apple.com/swift/) | [SwiftUI](https://developer.apple.com/documentation/swiftui/) | [SwiftData](https://developer.apple.com/documentation/swiftdata/)

**Libraries:** [TCA](https://github.com/pointfreeco/swift-composable-architecture) | [Snapshot Testing](https://github.com/pointfreeco/swift-snapshot-testing) | [SwiftLint](https://github.com/realm/SwiftLint)
