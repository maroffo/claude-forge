# Jetpack Compose Patterns

## Composable Conventions
```kotlin
// State hoisting, single responsibility
@Composable
fun UserCard(user: User, onClick: () -> Unit, modifier: Modifier = Modifier) {
    Card(onClick = onClick, modifier = modifier) { /* content */ }
}

// BAD: fetching in composable
@Composable fun UserCard(userId: String) { val vm: UserViewModel = viewModel() }
```

## State
```kotlin
var count by remember { mutableStateOf(0) }           // Lost on config change
var count by rememberSaveable { mutableStateOf(0) }   // Survives config change

// Derived state (recomputes only when items changes)
val itemCount by remember(items) { derivedStateOf { items.size } }
```

## Side Effects
```kotlin
LaunchedEffect(userId) { viewModel.loadUser(userId) }  // Runs when key changes
LaunchedEffect(Unit) { viewModel.sideEffects.collect { /* handle */ } }

DisposableEffect(lifecycleOwner) {
    val observer = LifecycleEventObserver { _, event -> /* handle */ }
    lifecycleOwner.lifecycle.addObserver(observer)
    onDispose { lifecycleOwner.lifecycle.removeObserver(observer) }
}
```

## Type-Safe Navigation (2.8.0+)
```kotlin
@Serializable object Home
@Serializable data class UserProfile(val userId: String)

NavHost(navController, startDestination = Home) {
    composable<Home> { HomeScreen(onUserClick = { navController.navigate(UserProfile(it)) }) }
    composable<UserProfile> { UserProfileScreen(it.toRoute<UserProfile>().userId) }
}
```

## Image Loading (Coil 3)
```kotlin
AsyncImage(model = url, contentDescription = null, modifier = Modifier.size(48.dp).clip(CircleShape))
```

## Dependency Injection Setup

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
