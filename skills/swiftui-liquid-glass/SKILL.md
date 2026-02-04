# ABOUTME: iOS 26+ Liquid Glass API for glassmorphism effects and interactive UI
# SwiftUI Liquid Glass

## When to Invoke
- iOS 26+ glassmorphism effects
- Frosted glass backgrounds
- Translucent interactive UI
- Material design alternatives
- Modern iOS 26 aesthetic

## Capabilities
- Apply glass effects to views
- Interactive glass for tappable elements
- Fallback to materials on older iOS
- Customize glass intensity/blur
- Layer glass containers

## Basic API

```swift
import SwiftUI

@available(iOS 26, *)
struct GlassCard: View {
    var body: some View {
        VStack {
            Text("Liquid Glass")
            Text("iOS 26+")
        }
        .padding()
        .glassEffect()  // Basic glass effect
    }
}
```

## With Fallbacks

```swift
struct AdaptiveGlassView: View {
    var body: some View {
        if #available(iOS 26, *) {
            content
                .glassEffect(intensity: 0.7)
        } else {
            content
                .background(.ultraThinMaterial)
        }
    }

    var content: some View {
        Text("Works on all iOS versions")
            .padding()
    }
}
```

## Glass Effect Parameters

| Parameter | Type | Purpose |
|-----------|------|---------|
| `intensity` | `Double` | Glass blur strength (0.0-1.0) |
| `tint` | `Color` | Glass tint color |
| `style` | `GlassEffectStyle` | `.light`, `.dark`, `.adaptive` |

## Interactive Glass

```swift
@available(iOS 26, *)
struct InteractiveGlassButton: View {
    var body: some View {
        Button("Tap Me") {
            print("Tapped")
        }
        .padding()
        .glassEffect(intensity: 0.8, interactive: true)  // Responds to touch
    }
}
```

## GlassEffectContainer

```swift
@available(iOS 26, *)
struct LayeredGlass: View {
    var body: some View {
        GlassEffectContainer {
            ZStack {
                // Background content
                Image("background")
                    .resizable()
                    .scaledToFill()

                // Foreground glass UI
                VStack {
                    Text("Title")
                        .font(.largeTitle)
                    Text("Subtitle")
                }
                .padding()
                .glassEffect()
            }
        }
    }
}
```

## Common Patterns

```swift
// Card with glass background
@available(iOS 26, *)
struct GlassCard: View {
    var body: some View {
        VStack(alignment: .leading) {
            Text("Card Title")
                .font(.headline)
            Text("Card content")
        }
        .padding()
        .glassEffect(intensity: 0.75, tint: .blue.opacity(0.1))
        .cornerRadius(16)
    }
}

// Toolbar with glass
@available(iOS 26, *)
struct GlassToolbar: View {
    var body: some View {
        HStack {
            Button(action: {}) { Image(systemName: "plus") }
            Spacer()
            Button(action: {}) { Image(systemName: "gear") }
        }
        .padding()
        .glassEffect(style: .adaptive)
    }
}
```

## Migration from Material

```swift
// Before (iOS 15+)
.background(.ultraThinMaterial)

// After (iOS 26+)
if #available(iOS 26, *) {
    .glassEffect()
} else {
    .background(.ultraThinMaterial)
}
```
