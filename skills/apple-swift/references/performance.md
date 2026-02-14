# Performance Detailed Guide

## Common Performance Killers

| Issue | Impact | Fix |
|-------|--------|-----|
| Unstable identity | List jumps/flickers | Use `.id()` or stable Identifiable |
| Observing everything | Over-invalidation | Fine-grained `@Observable` tracking |
| Deep nesting | Slow layout | Split into child views |
| VStack for long lists | Memory usage, slow scrolling | Use LazyVStack |
| Force unwrapping in loops | Crashes | Use optional chaining or guard |
| Synchronous I/O | UI freezes | Use async/await |
| Unnecessary recomputation | Wasted CPU | Cache computed values |

## SwiftUI Optimization

### LazyVStack/LazyHStack

```swift
// ❌ Loads all items at once
ScrollView {
    VStack {
        ForEach(items) { ItemRow(item: $0) }
    }
}

// ✅ Loads items on demand
ScrollView {
    LazyVStack {
        ForEach(items) { ItemRow(item: $0) }
    }
}
```

### Stable Identity

```swift
// ❌ Unstable - recreates UUID each time
struct Item: Identifiable {
    var id: UUID { UUID() }
    let title: String
}

// ✅ Stable - consistent identity
struct Item: Identifiable {
    let id: UUID = UUID()
    let title: String
}
```

### Fine-grained @Observable

```swift
// @Observable only tracks accessed properties
@Observable final class ViewModel {
    var items: [Item] = []
    var searchText: String = ""
    var isLoading: Bool = false
}

// View only re-renders when items changes
struct ItemsList: View {
    let vm: ViewModel

    var body: some View {
        List(vm.items) { item in  // Only tracks `items`
            ItemRow(item: item)
        }
    }
}
```

### View decomposition for performance

```swift
// Extract subviews to limit invalidation scope
struct ParentView: View {
    @State private var vm = ViewModel()

    var body: some View {
        VStack {
            HeaderView(title: vm.title)  // Only re-renders when title changes
            ItemsList(items: vm.items)   // Only re-renders when items changes
        }
    }
}

private struct HeaderView: View {
    let title: String
    var body: some View { Text(title).font(.title) }
}

private struct ItemsList: View {
    let items: [Item]
    var body: some View { List(items) { ItemRow(item: $0) } }
}
```

## Debug: View Invalidation

```swift
struct MyView: View {
    @State private var vm = ViewModel()

    var body: some View {
        let _ = Self._printChanges()  // Prints what caused re-render
        VStack {
            Text(vm.title)
            List(vm.items) { ItemRow(item: $0) }
        }
    }
}
```

**Output example:**
```
MyView: @self, @identity, _vm changed.
```

## Instruments Profiling

### Time Profiler (CPU hotspots)

```bash
# Start profiling attached to running app
xctrace record --template "Time Profiler" --attach "MyApp" --output ~/profile.trace --time-limit 30s

# Launch app and profile
xctrace record --template "Time Profiler" --launch com.example.myapp --output ~/profile.trace --time-limit 60s

# Profile on device
xctrace record --template "Time Profiler" --device "iPhone 16 Pro" --attach "MyApp" --output ~/profile.trace
```

**Analysis:** Look for hot paths with high self time (excluding child calls).

### Allocations (memory usage)

```bash
xctrace record --template "Allocations" --attach "MyApp" --output ~/allocations.trace --time-limit 30s
```

**Analysis:** Look for growing heap, large allocations, or allocation spikes.

### System Trace (I/O, system calls)

```bash
xctrace record --template "System Trace" --attach "MyApp" --output ~/system.trace --time-limit 30s
```

**Analysis:** Look for disk I/O, network delays, thread contention.

### Leaks (memory leaks)

```bash
xctrace record --template "Leaks" --attach "MyApp" --output ~/leaks.trace --time-limit 60s
```

**Analysis:** Leaks reported as objects with no references.

### Export and symbolicate

```bash
# Export to XML for analysis
xctrace export --input profile.trace --output profile.xml

# Symbolicate (replace addresses with function names)
xctrace symbolicate --input profile.trace --output symbolicated.trace
```

### List available templates

```bash
xctrace list templates
```

## Best Practices

1. **Always profile Release builds** - Debug builds have optimizations disabled
2. **Warm up the app** - First run is always slower (JIT, caching)
3. **Use `--time-limit`** - Auto-stop profiling after set duration
4. **Profile on real devices** - Simulators are faster than actual hardware
5. **Measure before and after** - Confirm optimizations actually help

## Memory Management

### Weak references to avoid retain cycles

```swift
// ❌ Retain cycle - closure captures self strongly
class ViewModel {
    var onUpdate: (() -> Void)?

    func setup() {
        onUpdate = {
            self.refresh()  // Strong reference
        }
    }
}

// ✅ Weak reference breaks cycle
class ViewModel {
    var onUpdate: (() -> Void)?

    func setup() {
        onUpdate = { [weak self] in
            self?.refresh()
        }
    }
}
```

### Unowned for guaranteed non-nil

```swift
// Use unowned when reference is guaranteed to exist
class Parent {
    var child: Child?

    func setup() {
        child = Child(parent: self)
    }
}

class Child {
    unowned let parent: Parent  // Parent always exists while Child exists

    init(parent: Parent) {
        self.parent = parent
    }
}
```

## Caching Computed Values

```swift
@Observable final class ViewModel {
    var items: [Item] = []

    // ❌ Recomputes every access
    var filteredItems: [Item] {
        items.filter { $0.isActive }
    }

    // ✅ Cached until items changes
    private var _filteredItemsCache: [Item]?
    var filteredItems: [Item] {
        if let cached = _filteredItemsCache { return cached }
        let filtered = items.filter { $0.isActive }
        _filteredItemsCache = filtered
        return filtered
    }

    func updateItems(_ newItems: [Item]) {
        items = newItems
        _filteredItemsCache = nil  // Invalidate cache
    }
}
```

## Asynchronous Loading

### Lazy image loading

```swift
import Kingfisher  // Popular image loading library

struct ItemRow: View {
    let item: Item

    var body: some View {
        HStack {
            KFImage(URL(string: item.imageURL))
                .placeholder { ProgressView() }
                .resizable()
                .frame(width: 50, height: 50)

            Text(item.title)
        }
    }
}
```

### Prefetch on scroll

```swift
struct ItemList: View {
    @State private var vm = ViewModel()

    var body: some View {
        List(vm.items) { item in
            ItemRow(item: item)
                .onAppear {
                    if vm.shouldLoadMore(item: item) {
                        Task { await vm.loadMore() }
                    }
                }
        }
    }
}

@Observable final class ViewModel {
    var items: [Item] = []
    private var isLoading = false

    func shouldLoadMore(item: Item) -> Bool {
        guard let lastItem = items.last else { return false }
        return item.id == lastItem.id && !isLoading
    }

    func loadMore() async {
        guard !isLoading else { return }
        isLoading = true
        defer { isLoading = false }

        let newItems = await fetchMoreItems()
        items.append(contentsOf: newItems)
    }
}
```

## Compilation Performance

### Reduce type inference complexity

```swift
// ❌ Complex type inference - slow compile
let result = items
    .filter { $0.isActive }
    .map { $0.title }
    .compactMap { $0.uppercased() }
    .reduce("") { $0 + $1 }

// ✅ Explicit types - faster compile
let activeItems: [Item] = items.filter { $0.isActive }
let titles: [String] = activeItems.map { $0.title }
let uppercased: [String] = titles.compactMap { $0.uppercased() }
let result: String = uppercased.reduce("") { $0 + $1 }
```

### Avoid massive view builders

```swift
// ❌ Huge body - slow compile
struct MyView: View {
    var body: some View {
        VStack {
            // 50+ lines of nested views
        }
    }
}

// ✅ Extract subviews
struct MyView: View {
    var body: some View {
        VStack {
            HeaderSection()
            ContentSection()
            FooterSection()
        }
    }
}
```
