---
name: swiftui-liquid-glass
description: "iOS 26+ Liquid Glass API for glassmorphism effects. Use when user wants glass effects, frosted backgrounds, translucent UI, or .glassEffect() modifier guidance."
compatibility: "Requires Xcode with iOS 26+ SDK."
---

# ABOUTME: iOS 26+ Liquid Glass API for glassmorphism effects and interactive UI
# ABOUTME: .glassEffect() modifier, Glass variants, tint, interactive glass, containers, fallbacks

# SwiftUI Liquid Glass

API verified against Apple's SwiftUI documentation (2026-07). If a parameter is not listed here, do not guess it: fetch the current docs for `View.glassEffect(_:in:)` and `Glass`.

## When to Invoke
- iOS 26+ glassmorphism effects
- Frosted glass backgrounds
- Translucent interactive UI
- Modern iOS 26 aesthetic

## The Real API

```swift
nonisolated func glassEffect(
    _ glass: Glass = .regular,
    in shape: some Shape = DefaultGlassEffectShape()  // capsule by default
) -> some View
```

`Glass` is a configuration struct, NOT an enum of styles:

| Member | Declaration | Purpose |
|--------|-------------|---------|
| `.regular` | `static var regular: Glass` | Standard Liquid Glass material |
| `.clear` | `static var clear: Glass` | Clear variant |
| `.identity` | `static var identity: Glass` | No-op variant (content unaffected) |
| `.tint(_:)` | `func tint(Color?) -> Glass` | Returns a tinted copy |
| `.interactive(_:)` | `func interactive(Bool) -> Glass` | Returns an interactive copy (responds to touch) |

There is NO `intensity:` parameter, NO `GlassEffectStyle`, NO `interactive:` label on `glassEffect` itself. Configuration composes on the `Glass` value.

## Basic Usage

```swift
@available(iOS 26, *)
struct GlassCard: View {
    var body: some View {
        VStack {
            Text("Liquid Glass")
            Text("iOS 26+")
        }
        .padding()
        .glassEffect()  // .regular, in a capsule
    }
}
```

Custom shape and composed configuration:

```swift
content
    .glassEffect(.regular.tint(.blue.opacity(0.2)), in: .rect(cornerRadius: 16))

Button("Tap Me") { ... }
    .padding()
    .glassEffect(.regular.interactive(true))
```

## With Fallbacks

```swift
struct AdaptiveGlassView: View {
    var body: some View {
        if #available(iOS 26, *) {
            content.glassEffect()
        } else {
            content.background(.ultraThinMaterial)
        }
    }

    var content: some View {
        Text("Works on all iOS versions").padding()
    }
}
```

## GlassEffectContainer

`GlassEffectContainer` combines multiple Liquid Glass shapes into a single shape and can morph individual shapes into one another. Use it when several glass elements sit close together or animate between layouts; give elements a `glassEffectID(_:in:)` within a shared `@Namespace` for morphing transitions.
