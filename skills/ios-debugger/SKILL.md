---
name: ios-debugger
description: "Build, run, and debug iOS apps via CLI without Xcode UI. Use when user wants to build iOS app, run on simulator, capture logs, take screenshots, or automate simulator interactions. Not for Swift code patterns (use apple-swift)."
compatibility: "Requires Xcode and iOS Simulator. Optionally XcodeBuildMCP for enhanced integration."
---

# ABOUTME: XcodeBuildMCP integration for building, running, and debugging iOS apps via CLI
# ABOUTME: Simulator control, UI interaction, log capture, screenshot automation

# iOS Debugger

## When to Invoke
- Build/run iOS apps without Xcode UI
- Automate simulator interactions
- Capture app logs programmatically
- UI testing via CLI
- CI/CD iOS workflows

## Capabilities
- Build and run on booted simulator
- Interact with simulator UI (tap, type, gestures)
- Capture and filter app logs
- Take screenshots
- Install/uninstall apps

## Prerequisites

```bash
# Ensure XcodeBuildMCP is available
# Check if simulator is booted
xcrun simctl list devices | grep Booted

# Boot simulator if needed
xcrun simctl boot "iPhone 16 Pro"
```

## Build and Run

```bash
# Build for simulator
xcodebuild -workspace MyApp.xcworkspace \
    -scheme MyApp \
    -sdk iphonesimulator \
    -destination 'platform=iOS Simulator,name=iPhone 16 Pro' \
    build

# Install app on simulator
xcrun simctl install booted path/to/MyApp.app

# Launch app
xcrun simctl launch booted com.example.myapp
```

## UI Interaction

`simctl io` does NOT do taps/typing/swipes (it only handles `screenshot`, `recordVideo`, `enumerate`, `poll`). For UI automation pick one of:

```bash
# Screenshot / screen recording (simctl's actual io surface)
xcrun simctl io booted screenshot screenshot.png
xcrun simctl io booted recordVideo demo.mov   # stop with Ctrl-C

# Taps/typing/gestures option 1: XCUITest (robust, accessibility-ID based)
xcodebuild test -workspace App.xcworkspace -scheme AppUITests \
    -destination 'platform=iOS Simulator,name=<booted device>'

# Taps/typing/gestures option 2: Meta's idb (brew install idb-companion; pip install fb-idb)
idb ui tap 200 400
idb ui text "Hello World"
idb ui swipe 200 600 200 200 --duration 0.5
```

If a command shape is not listed here, verify with `xcrun simctl help io` before using it (this file once shipped invented `simctl io tap/type/swipe` subcommands).

## Log Capture

```bash
# Stream all logs from booted simulator
xcrun simctl spawn booted log stream --predicate 'processImagePath CONTAINS "MyApp"'

# Filter by subsystem
xcrun simctl spawn booted log stream --predicate 'subsystem == "com.example.myapp"'

# Capture logs to file
xcrun simctl spawn booted log stream \
    --predicate 'processImagePath CONTAINS "MyApp"' \
    > app.log &
```

## Common Workflows

### Reset Simulator
```bash
# Erase all data
xcrun simctl erase "iPhone 16 Pro"

# Shutdown and boot
xcrun simctl shutdown "iPhone 16 Pro"
xcrun simctl boot "iPhone 16 Pro"
```

## Tips
- Always check simulator is booted before commands
- Use `log stream` predicates to filter noise
- Coordinate-based taps are fragile (prefer accessibility IDs in XCTest)
- Capture screenshots for visual regression tests
- Use `xcrun simctl openurl` to test deep links

## Integration with Tests
```bash
# Run XCTests on simulator
xcodebuild test \
    -workspace App.xcworkspace \
    -scheme App \
    -destination 'platform=iOS Simulator,name=iPhone 16 Pro' \
    -resultBundlePath TestResults.xcresult
```
