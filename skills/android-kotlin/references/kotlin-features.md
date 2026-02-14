# Kotlin 2.x Features

## K2 Compiler (2.0)
2x faster, improved smart casts, better type inference, unified platform support.

## Guard Conditions (2.1)
```kotlin
fun handleResult(result: Result<String>) = when (result) {
    is Success if result.data.isNotEmpty() -> "Data: ${result.data}"
    is Success -> "Empty"
    is Error if result.code == 404 -> "Not found"
    is Error -> "Error ${result.code}"
}

// Non-local break/continue in inline lambdas
items.forEach { if (it.skip) continue; if (it.terminal) break; process(it) }
```

## Context Parameters (2.2 Preview)
```kotlin
context(logger: Logger, metrics: Metrics)
fun processOrder(order: Order) { logger.info("..."); metrics.increment("...") }
```

## Kotlin 2.3
- Compose stack traces (readable in minified builds)
- `kotlin.uuid.Uuid`: `Uuid.random()`, `Uuid.parse("...")`
