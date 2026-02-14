# Testing Patterns

## Compose UI
```kotlin
@get:Rule val composeTestRule = createComposeRule()

@Test fun feedScreen_displaysItems() {
    composeTestRule.setContent { FeedScreen(uiState = FeedUiState.Success(items), onItemClick = {}) }
    composeTestRule.onNodeWithText("Title 1").assertIsDisplayed()
}
```

## ViewModel
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

## Snapshot (Paparazzi)
```kotlin
@get:Rule val paparazzi = Paparazzi(deviceConfig = DeviceConfig.PIXEL_5)
@Test fun userCard_default() { paparazzi.snapshot { MaterialTheme { UserCard(user, {}) } } }
```
