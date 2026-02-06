---
name: android-kotlin
description: "Modern Android development with Kotlin 2.x, Jetpack Compose, Clean Architecture, and performance optimization."
allowed-tools: [mcp__acp__Read, mcp__acp__Edit, mcp__acp__Write, mcp__acp__Bash]
---

# ABOUTME: Android/Kotlin - Compose, architecture, testing, performance
# ABOUTME: Kotlin 2.x, Compose 1.7+, type-safe navigation, Baseline Profiles

# Android/Kotlin

## Commands
```bash
./gradlew assembleDebug|assembleRelease|test|connectedAndroidTest|lint|ktlintFormat
./gradlew :feature:home:build                    # Module-specific
```

**See:** `_AST_GREP.md` (sg patterns) | `_PATTERNS.md` | `source-control`

---

## Kotlin 2.x

### K2 Compiler (2.0)
2x faster, improved smart casts, better type inference, unified platform support.

### Guard Conditions (2.1)
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

### Context Parameters (2.2 Preview)
```kotlin
context(logger: Logger, metrics: Metrics)
fun processOrder(order: Order) { logger.info("..."); metrics.increment("...") }
```

### Kotlin 2.3
- Compose stack traces (readable in minified builds)
- `kotlin.uuid.Uuid`: `Uuid.random()`, `Uuid.parse("...")`

---

## Jetpack Compose

### Composable Conventions
```kotlin
// State hoisting, single responsibility
@Composable
fun UserCard(user: User, onClick: () -> Unit, modifier: Modifier = Modifier) {
    Card(onClick = onClick, modifier = modifier) { /* content */ }
}

// BAD: fetching in composable
@Composable fun UserCard(userId: String) { val vm: UserViewModel = viewModel() }
```

### State
```kotlin
var count by remember { mutableStateOf(0) }           // Lost on config change
var count by rememberSaveable { mutableStateOf(0) }   // Survives config change

// Derived state (recomputes only when items changes)
val itemCount by remember(items) { derivedStateOf { items.size } }
```

### Side Effects
```kotlin
LaunchedEffect(userId) { viewModel.loadUser(userId) }  // Runs when key changes
LaunchedEffect(Unit) { viewModel.sideEffects.collect { /* handle */ } }

DisposableEffect(lifecycleOwner) {
    val observer = LifecycleEventObserver { _, event -> /* handle */ }
    lifecycleOwner.lifecycle.addObserver(observer)
    onDispose { lifecycleOwner.lifecycle.removeObserver(observer) }
}
```

### Type-Safe Navigation (2.8.0+)
```kotlin
@Serializable object Home
@Serializable data class UserProfile(val userId: String)

NavHost(navController, startDestination = Home) {
    composable<Home> { HomeScreen(onUserClick = { navController.navigate(UserProfile(it)) }) }
    composable<UserProfile> { UserProfileScreen(it.toRoute<UserProfile>().userId) }
}
```

### Image Loading (Coil 3)
```kotlin
AsyncImage(model = url, contentDescription = null, modifier = Modifier.size(48.dp).clip(CircleShape))
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

### Use Cases
```kotlin
// Single responsibility, orchestration here (NOT in ViewModel)
class SignInUseCase(private val auth: AuthRepository, private val user: UserRepository) {
    suspend operator fun invoke(email: String, password: String): Result<User> {
        val result = auth.signIn(email, password).getOrElse { return Result.failure(it) }
        user.saveUserLocally(result)
        return Result.success(result)
    }
}
```

### ViewModel
```kotlin
class FeedViewModel(private val getFeed: GetFeedUseCase) : ViewModel() {
    private val _uiState = MutableStateFlow<FeedUiState>(FeedUiState.Loading)
    val uiState = _uiState.asStateFlow()

    private val _sideEffects = Channel<FeedSideEffect>(Channel.BUFFERED)
    val sideEffects = _sideEffects.receiveAsFlow()

    fun loadFeed() = viewModelScope.launch {
        _uiState.value = FeedUiState.Loading
        getFeed().onSuccess { _uiState.value = FeedUiState.Success(it) }
                 .onFailure { _uiState.value = FeedUiState.Error(it.message) }
    }
}

sealed interface FeedUiState { data object Loading; data class Success(val items: List<FeedItem>); data class Error(val msg: String?) }
sealed interface FeedSideEffect { data class NavigateToDetail(val id: String); data class ShowSnackbar(val msg: String) }
```

---

## Dependency Injection

| Aspect | Hilt | Koin |
|--------|------|------|
| Type | Compile-time | Runtime |
| Build time | Slower | Faster |
| Error detection | Compile | Runtime |
| KMP support | No | Yes |
| Best for | Large/enterprise | Small-medium/KMP |

### Hilt
```kotlin
@HiltAndroidApp class MyApp : Application()
@AndroidEntryPoint class MainActivity : ComponentActivity()
@HiltViewModel class FeedViewModel @Inject constructor(private val getFeed: GetFeedUseCase) : ViewModel()

@Module @InstallIn(SingletonComponent::class)
object NetworkModule {
    @Provides @Singleton fun provideRetrofit(): Retrofit = Retrofit.Builder().baseUrl(URL).build()
}
```

### Koin
```kotlin
val appModule = module {
    single<FeedRepository> { FeedRepositoryImpl(get(), get()) }
    factory { GetFeedUseCase(get()) }
    viewModelOf(::FeedViewModel)
}
startKoin { androidContext(this@MyApp); modules(appModule) }

@Composable fun FeedScreen(viewModel: FeedViewModel = koinViewModel()) { }
```

---

## Networking & Data

### Retrofit + Kotlin Serialization
```kotlin
interface UserApi {
    @GET("users/{id}") suspend fun getUser(@Path("id") id: String): UserDto
    @POST("users") suspend fun createUser(@Body user: CreateUserRequest): UserDto
}
val retrofit = Retrofit.Builder().baseUrl(URL)
    .addConverterFactory(Json { ignoreUnknownKeys = true }.asConverterFactory("application/json".toMediaType()))
    .build()
```

### Ktor (KMP)
```kotlin
val client = HttpClient(OkHttp) {
    install(ContentNegotiation) { json(Json { ignoreUnknownKeys = true }) }
    defaultRequest { url(BASE_URL); contentType(ContentType.Application.Json) }
}
```

### Room
```kotlin
@Entity(tableName = "users") data class UserEntity(@PrimaryKey val id: String, val name: String)
@Dao interface UserDao {
    @Query("SELECT * FROM users WHERE id = :id") suspend fun getUser(id: String): UserEntity?
    @Query("SELECT * FROM users") fun getAllUsers(): Flow<List<UserEntity>>
    @Insert(onConflict = OnConflictStrategy.REPLACE) suspend fun insertUser(user: UserEntity)
}
```

### DataStore
```kotlin
val Context.dataStore by preferencesDataStore(name = "settings")
val darkModeFlow: Flow<Boolean> = context.dataStore.data.map { it[booleanPreferencesKey("dark_mode")] ?: false }
suspend fun setDarkMode(enabled: Boolean) { context.dataStore.edit { it[booleanPreferencesKey("dark_mode")] = enabled } }
```

---

## Testing

### Compose UI
```kotlin
@get:Rule val composeTestRule = createComposeRule()

@Test fun feedScreen_displaysItems() {
    composeTestRule.setContent { FeedScreen(uiState = FeedUiState.Success(items), onItemClick = {}) }
    composeTestRule.onNodeWithText("Title 1").assertIsDisplayed()
}
```

### ViewModel
```kotlin
@get:Rule val mainDispatcherRule = MainDispatcherRule()

@Test fun `loadFeed updates state`() = runTest {
    coEvery { getFeedUseCase() } returns Result.success(items)
    viewModel.loadFeed()
    viewModel.uiState.test {
        assertThat(awaitItem()).isEqualTo(FeedUiState.Loading)
        assertThat(awaitItem()).isEqualTo(FeedUiState.Success(items))
    }
}

class MainDispatcherRule(private val dispatcher: TestDispatcher = UnconfinedTestDispatcher()) : TestWatcher() {
    override fun starting(d: Description) { Dispatchers.setMain(dispatcher) }
    override fun finished(d: Description) { Dispatchers.resetMain() }
}
```

### Snapshot (Paparazzi)
```kotlin
@get:Rule val paparazzi = Paparazzi(deviceConfig = DeviceConfig.PIXEL_5)
@Test fun userCard_default() { paparazzi.snapshot { MaterialTheme { UserCard(user, {}) } } }
```

---

## Performance

### R8 (MUST ENABLE)
```kotlin
release {
    isMinifyEnabled = true; isShrinkResources = true
    proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
}
```

### Baseline Profiles
30-50% faster cold start. Generate via `BaselineProfileRule` for critical user journeys.

### Compose Performance
```kotlin
@Immutable data class UserUiModel(val id: String, val name: String)  // Stable
data class FeedUiModel(val items: List<Item>)  // List not MutableList

// Defer reads to layout phase
Box(modifier = Modifier.offset { IntOffset(0, scrollState.value) })  // Not: val offset = scrollState.value

// Stable keys
LazyColumn { items(users, key = { it.id }) { UserRow(it) } }
```

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
| Missing error handling | collectAsState vs collectAsStateWithLifecycle |
| R8 disabled in release | |

---

## Resources

**Official:** [android.com/kotlin](https://developer.android.com/kotlin) | [compose](https://developer.android.com/develop/ui/compose) | [architecture](https://developer.android.com/topic/architecture) | [type-safe nav](https://developer.android.com/guide/navigation/design/type-safety) | [baseline profiles](https://developer.android.com/topic/performance/baselineprofiles)

**Kotlin:** [2.2](https://kotlinlang.org/docs/whatsnew22.html) | [2.1.20](https://kotlinlang.org/docs/whatsnew2120.html) | [2.3](https://blog.jetbrains.com/kotlin/2025/12/kotlin-2-3-0-released/)

**Libraries:** [Coil](https://coil-kt.github.io/coil/) | [Koin](https://insert-koin.io/) | [Hilt](https://dagger.dev/hilt/) | [Retrofit](https://square.github.io/retrofit/) | [Ktor](https://ktor.io/docs/client.html) | [Room](https://developer.android.com/training/data-storage/room)

**Testing:** [Compose testing](https://developer.android.com/develop/ui/compose/testing) | [Paparazzi](https://github.com/cashapp/paparazzi) | [Turbine](https://github.com/cashapp/turbine)
