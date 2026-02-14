# Performance

## R8 (MUST ENABLE)
```kotlin
release {
    isMinifyEnabled = true; isShrinkResources = true
    proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
}
```

## Baseline Profiles
30-50% faster cold start. Generate via `BaselineProfileRule` for critical user journeys.

## Compose Performance
```kotlin
@Immutable data class UserUiModel(val id: String, val name: String)  // Stable
data class FeedUiModel(val items: List<Item>)  // List not MutableList

// Defer reads to layout phase
Box(modifier = Modifier.offset { IntOffset(0, scrollState.value) })  // Not: val offset = scrollState.value

// Stable keys
LazyColumn { items(users, key = { it.id }) { UserRow(it) } }
```
