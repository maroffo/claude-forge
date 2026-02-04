# ABOUTME: CLI-based Instruments profiling with xctrace for performance analysis
# Native App Performance

## When to Invoke
- App performance issues
- CPU/memory profiling needed
- No Instruments.app access
- CI/CD performance testing
- Automated profiling workflows

## Capabilities
- Profile running apps via CLI
- Capture Time Profiler data
- Extract flamegraphs
- Analyze allocation patterns
- Export traces for analysis

## xctrace Workflow

### 1. List Available Templates
```bash
xctrace list templates
# Use: "Time Profiler", "Allocations", "Leaks"
```

### 2. Attach to Running App
```bash
# Attach to process by name
xctrace record --template "Time Profiler" \
    --attach "MyApp" \
    --output ~/profile.trace \
    --time-limit 30s

# Attach to simulator
xctrace record --template "Time Profiler" \
    --device "iPhone 16 Pro" \
    --attach "MyApp" \
    --output ~/profile.trace
```

### 3. Launch and Profile
```bash
# Launch app and profile
xctrace record --template "Time Profiler" \
    --launch com.example.myapp \
    --output ~/profile.trace \
    --time-limit 60s
```

## Common Templates

| Template | Use Case |
|----------|----------|
| Time Profiler | CPU hotspots, slow functions |
| Allocations | Memory usage, leaks |
| System Trace | I/O, system calls |
| Leaks | Memory leak detection |

## Analysis

```bash
# Export trace data
xctrace export --input profile.trace --output profile.xml

# List instruments in trace
xctrace symbolicate --input profile.trace --output symbolicated.trace
```

## Integration with Tests
```swift
// XCTest performance measurement
measure(metrics: [XCTCPUMetric(), XCTMemoryMetric()]) {
    // Code to profile
}
```

## CI/CD Pattern
```bash
#!/bin/bash
xctrace record --template "Time Profiler" \
    --device "iPhone 16 Pro" \
    --launch com.example.app \
    --output build/profile.trace \
    --time-limit 30s

# Parse and fail if CPU > threshold
# Extract metrics from XML export
```

## Tips
- Profile Release builds, not Debug
- Use `--time-limit` to auto-stop
- Warm up app before profiling critical paths
- Run multiple samples, compare medians
