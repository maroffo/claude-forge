---
name: android-kotlin
description: "Android development with Kotlin, Jetpack Compose, Clean Architecture, and performance. Use when working with .kt files, build.gradle.kts, AndroidManifest.xml, or Compose UI."
compatibility: "Requires Android SDK, Gradle. Optional: ktlint."
allowed-tools: [mcp__acp__Read, mcp__acp__Edit, mcp__acp__Write, mcp__acp__Bash]
---

# ABOUTME: Android/Kotlin, Compose, Clean Architecture, testing, performance
# ABOUTME: MVVM + DI conventions, state/side-effect patterns, review checklists

# Android/Kotlin

## Commands
```bash
./gradlew assembleDebug|assembleRelease|test|connectedAndroidTest|lint|ktlintFormat
./gradlew :feature:home:build                    # Module-specific
```

**See:** `_AST_GREP.md` (sg patterns) | `_PATTERNS.md` | `source-control`

---

## Version (determine, don't assume)

See `../_LANG_COMMON.md`. Fetch the truth:

```bash
./gradlew --version                                         # Gradle + JVM
grep -E 'kotlin|agp|compose' gradle/libs.versions.toml      # version catalog (preferred)
grep -E 'kotlin|android' build.gradle.kts                   # fallback
cat gradle.properties                                       # AGP / Kotlin flags
curl -s https://api.github.com/repos/JetBrains/kotlin/releases/latest | jq -r .tag_name   # latest Kotlin
curl -s https://api.github.com/repos/gradle/gradle/releases/latest | jq -r .tag_name      # latest Gradle
```

---

## Pre-Commit Verification (MANDATORY)

`make check && make test-e2e` must pass (enforced by the `pre-commit-gate` hook; see `../_LANG_COMMON.md`). What `make check` expands to for Android:

```bash
./gradlew ktlintCheck                           # formatting
./gradlew detekt                                # static analysis
./gradlew lint                                  # Android lint
./gradlew test                                  # unit tests (all variants)
./gradlew connectedAndroidTest                  # instrumented / e2e (device/emulator)
```

---

## Architecture

### Clean Architecture Structure
```
feature/
├── data/repository/, datasource/local/, datasource/remote/
├── domain/model/, repository/ (interface), usecase/
└── presentation/screen/, viewmodel/
```

### Use Cases and ViewModels
Use cases: single responsibility, orchestration here (NOT in ViewModel). ViewModels expose immutable `StateFlow` UI state and one-time events via `Channel`/`SharedFlow` (never StateFlow). For the full `SignInUseCase` + `FeedViewModel` + `UiState`/`SideEffect` code, see `references/compose-patterns.md`.

---

## Dependency Injection

| Aspect | Hilt | Koin |
|--------|------|------|
| Type | Compile-time | Runtime |
| Build time | Slower | Faster |
| Error detection | Compile | Runtime |
| KMP support | No | Yes |
| Best for | Large/enterprise | Small-medium/KMP |

**Hilt:** `@HiltAndroidApp`, `@AndroidEntryPoint`, `@HiltViewModel`, `@Inject constructor`
**Koin:** `module { }`, `single`, `factory`, `viewModelOf`, `koinViewModel()`

See `references/compose-patterns.md` for setup examples.

---

## Compose Essentials

**State hoisting:** lift state to the caller, pass callbacks down.

**State APIs:**
- `remember { mutableStateOf() }`, lost on config change
- `rememberSaveable { mutableStateOf() }`, survives config change
- `derivedStateOf`, computed state

**Side effects:** `LaunchedEffect(key)`, `DisposableEffect`. Collect flows with `collectAsStateWithLifecycle()` (not `collectAsState`).

**Type-safe navigation:** `@Serializable` routes.

See `references/compose-patterns.md` for detailed examples.

---

## Code Review Checklists

### Architecture
- [ ] VMs don't chain use cases (orchestration in domain)
- [ ] VMs don't call repositories directly
- [ ] Use cases have single responsibility
- [ ] State immutable (use `copy()`)
- [ ] Side effects use Channel/SharedFlow (not StateFlow)

### Compose
- [ ] State hoisted appropriately
- [ ] `remember` vs `rememberSaveable` correct
- [ ] Side effects use correct APIs
- [ ] Stable types for parameters
- [ ] `key` used in LazyColumn/LazyRow

### Red Flags
| Critical | High |
|----------|------|
| Network/DB on main thread | Use case chaining in VM |
| StateFlow for one-time events | Mutable state exposed from VM |
| Hardcoded strings in UI | Missing `key` in LazyColumn |
| Missing error handling | `collectAsState` vs `collectAsStateWithLifecycle` |
| R8 disabled in release | |

---

## Detailed References

- `references/kotlin-features.md` - Kotlin language features and idioms
- `references/compose-patterns.md` - State, side effects, navigation, image loading
- `references/data-layer.md` - Retrofit, Ktor, Room, DataStore
- `references/testing-patterns.md` - Compose UI tests, ViewModel tests, snapshot tests (Paparazzi), Turbine
- `references/performance.md` - R8, Baseline Profiles, Compose optimization

---

## Resources

**Official:** [android.com/kotlin](https://developer.android.com/kotlin) | [compose](https://developer.android.com/develop/ui/compose) | [architecture](https://developer.android.com/topic/architecture) | [type-safe nav](https://developer.android.com/guide/navigation/design/type-safety) | [baseline profiles](https://developer.android.com/topic/performance/baselineprofiles)

**Libraries:** [Coil](https://coil-kt.github.io/coil/) | [Koin](https://insert-koin.io/) | [Hilt](https://dagger.dev/hilt/) | [Retrofit](https://square.github.io/retrofit/) | [Ktor](https://ktor.io/docs/client.html) | [Room](https://developer.android.com/training/data-storage/room)

**Testing:** [Compose testing](https://developer.android.com/develop/ui/compose/testing) | [Paparazzi](https://github.com/cashapp/paparazzi) | [Turbine](https://github.com/cashapp/turbine)
