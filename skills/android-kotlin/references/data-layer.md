# Networking & Data

## Retrofit + Kotlin Serialization
```kotlin
interface UserApi {
    @GET("users/{id}") suspend fun getUser(@Path("id") id: String): UserDto
    @POST("users") suspend fun createUser(@Body user: CreateUserRequest): UserDto
}
val retrofit = Retrofit.Builder().baseUrl(URL)
    .addConverterFactory(Json { ignoreUnknownKeys = true }.asConverterFactory("application/json".toMediaType()))
    .build()
```

## Ktor (KMP)
```kotlin
val client = HttpClient(OkHttp) {
    install(ContentNegotiation) { json(Json { ignoreUnknownKeys = true }) }
    defaultRequest { url(BASE_URL); contentType(ContentType.Application.Json) }
}
```

## Room
```kotlin
@Entity(tableName = "users") data class UserEntity(@PrimaryKey val id: String, val name: String)
@Dao interface UserDao {
    @Query("SELECT * FROM users WHERE id = :id") suspend fun getUser(id: String): UserEntity?
    @Query("SELECT * FROM users") fun getAllUsers(): Flow<List<UserEntity>>
    @Insert(onConflict = OnConflictStrategy.REPLACE) suspend fun insertUser(user: UserEntity)
}
```

## DataStore
```kotlin
val Context.dataStore by preferencesDataStore(name = "settings")
val darkModeFlow: Flow<Boolean> = context.dataStore.data.map { it[booleanPreferencesKey("dark_mode")] ?: false }
suspend fun setDarkMode(enabled: Boolean) { context.dataStore.edit { it[booleanPreferencesKey("dark_mode")] = enabled } }
```
