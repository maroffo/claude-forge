# ABOUTME: SwiftUI view structure refactoring patterns and MV architecture guidance
# SwiftUI Refactor

## When to Invoke
- Large view files (>200 lines)
- Messy property ordering
- MVVM over-engineering
- View reusability issues
- State management confusion

## Capabilities
- Restructure view properties
- Split large views into subviews
- Apply MV patterns (not MVVM)
- Extract reusable components
- Simplify state management

## Property Ordering

```swift
struct WellOrderedView: View {
    // 1. Environment values
    @Environment(\.dismiss) private var dismiss
    @Environment(\.colorScheme) private var colorScheme

    // 2. Immutable dependencies (let)
    let title: String
    let onSave: () -> Void

    // 3. State (@State, @StateObject, @Binding)
    @State private var text = ""
    @State private var isExpanded = false

    // 4. Computed properties
    var isValid: Bool {
        !text.isEmpty
    }

    // 5. init (if needed)
    init(title: String, onSave: @escaping () -> Void) {
        self.title = title
        self.onSave = onSave
    }

    // 6. body
    var body: some View {
        VStack {
            TextField("Enter text", text: $text)
            Button("Save", action: handleSave)
        }
    }

    // 7. Methods
    private func handleSave() {
        onSave()
        dismiss()
    }
}
```

## MV Not MVVM

```swift
// AVOID: Unnecessary ViewModel
class MyViewModel: ObservableObject {
    @Published var text = ""
    @Published var count = 0
}

struct OverEngineeredView: View {
    @StateObject private var viewModel = MyViewModel()
    var body: some View {
        Text(viewModel.text)
    }
}

// PREFER: Direct state in view
struct SimpleView: View {
    @State private var text = ""
    @State private var count = 0

    var body: some View {
        Text(text)
    }
}

// USE ViewModel ONLY for:
// - Complex business logic
// - Network/persistence layer
// - Shared state across views
```

## Split Large Views

```swift
// BEFORE: 250-line view
struct LargeView: View {
    var body: some View {
        ScrollView {
            VStack {
                // 50 lines of header
                // 100 lines of content
                // 50 lines of footer
            }
        }
    }
}

// AFTER: Composed subviews
struct ComposedView: View {
    var body: some View {
        ScrollView {
            VStack {
                HeaderSection()
                ContentSection()
                FooterSection()
            }
        }
    }
}

private struct HeaderSection: View {
    var body: some View {
        // Header implementation
    }
}

private struct ContentSection: View {
    var body: some View {
        // Content implementation
    }
}

private struct FooterSection: View {
    var body: some View {
        // Footer implementation
    }
}
```

## Extract Reusable Components

```swift
// Reusable modifier
extension View {
    func cardStyle() -> some View {
        self
            .padding()
            .background(Color(.systemBackground))
            .cornerRadius(12)
            .shadow(radius: 2)
    }
}

// Reusable component
struct PrimaryButton: View {
    let title: String
    let action: () -> Void

    var body: some View {
        Button(title, action: action)
            .buttonStyle(.borderedProminent)
            .controlSize(.large)
    }
}
```

## Decision Tree

| Scenario | Pattern |
|----------|---------|
| <100 lines, simple state | Single view, @State |
| 100-200 lines | Extract subviews (private) |
| >200 lines | Multiple files, shared state |
| Business logic | Model layer, not ViewModel |
| Network/DB | Repository pattern |
| Shared state | @Observable or @StateObject |
