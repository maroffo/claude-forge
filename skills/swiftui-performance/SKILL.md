# ABOUTME: SwiftUI performance audit patterns and common optimization fixes
# SwiftUI Performance

## When to Invoke
- Laggy scrolling
- Slow animations
- View updates too frequent
- High CPU in SwiftUI code
- List rendering issues

## Capabilities
- Audit view invalidation
- Fix identity issues
- Optimize body computation
- Reduce layout passes
- Prevent unnecessary renders

## Common Performance Killers

| Issue | Symptom | Fix |
|-------|---------|-----|
| Unstable identity | List jumps/flickers | Use `.id()` or stable Identifiable |
| Heavy body | UI lag, dropped frames | Extract to computed properties |
| Observing everything | Over-invalidation | Use `@Observable` macro sparingly |
| Deep nesting | Slow layout | Split into child views |
| Closures in body | Re-creation every render | Extract to methods |

## View Invalidation Audit

```swift
// BAD: Creates new closure every render
struct BadView: View {
    var body: some View {
        Button("Tap") { print("Tapped") }  // New closure each time
    }
}

// GOOD: Stable closure
struct GoodView: View {
    var body: some View {
        Button("Tap", action: handleTap)
    }

    func handleTap() { print("Tapped") }
}
```

## List Identity Issues

```swift
// BAD: Unstable identity
ForEach(items) { item in
    Text(item.name)
        .id(UUID())  // New ID every render!
}

// GOOD: Stable identity
ForEach(items) { item in
    Text(item.name)
        .id(item.id)  // Stable across renders
}
```

## Heavy Body Computation

```swift
// BAD: Heavy work in body
var body: some View {
    let processed = items.map { expensiveTransform($0) }
    List(processed, id: \.id) { item in
        ItemRow(item: item)
    }
}

// GOOD: Cached computation
var processed: [Item] {
    items.map { expensiveTransform($0) }
}

var body: some View {
    List(processed, id: \.id) { item in
        ItemRow(item: item)
    }
}
```

## Layout Thrash

```swift
// BAD: Multiple geometry reads
var body: some View {
    GeometryReader { geo in
        VStack {
            Text("Width: \(geo.size.width)")
            Text("Height: \(geo.size.height)")
        }
    }
}

// GOOD: Single geometry read
var body: some View {
    GeometryReader { geo in
        content(for: geo.size)
    }
}

func content(for size: CGSize) -> some View {
    VStack {
        Text("Width: \(size.width)")
        Text("Height: \(size.height)")
    }
}
```

## Debug Tools

```swift
// Print when view body recomputes
let _ = Self._printChanges()

// Detect identity changes
List(items) { item in
    Text(item.name)
        .id(item.id)
        .background(Color.red.opacity(0.001))  // Force unique identity
}
```
