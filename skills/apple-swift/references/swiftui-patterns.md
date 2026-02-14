# SwiftUI Detailed Patterns

## @Observable (iOS 17+, Preferred)

```swift
// ❌ OLD: class VM: ObservableObject { @Published var user: User? }
// ✅ NEW:
@Observable final class UserVM { var user: User?; var isLoading = false }

// @State for view-owned @Observable
struct ContentView: View {
    @State private var vm = UserVM()
    var body: some View { UserView(viewModel: vm) }
}

// @Bindable for two-way bindings
struct ProfileEditor: View {
    @Bindable var vm: ProfileVM
    var body: some View { TextField("Name", text: $vm.name) }
}
```

## NavigationStack (iOS 16+)

```swift
enum AppRoute: Hashable { case profile(String); case settings; case detail(Item) }

struct ContentView: View {
    @State private var path = NavigationPath()
    var body: some View {
        NavigationStack(path: $path) {
            HomeView()
                .navigationDestination(for: AppRoute.self) { route in
                    switch route {
                    case .profile(let id): UserProfileView(userId: id)
                    case .settings: SettingsView()
                    case .detail(let item): ItemDetailView(item: item)
                    }
                }
        }
    }
}
```

### Programmatic Navigation

```swift
struct HomeView: View {
    @State private var path = NavigationPath()

    var body: some View {
        NavigationStack(path: $path) {
            List {
                Button("Go to Profile") {
                    path.append(AppRoute.profile("user123"))
                }
                Button("Go to Settings") {
                    path.append(AppRoute.settings)
                }
            }
            .navigationDestination(for: AppRoute.self) { route in
                destinationView(for: route)
            }
        }
    }

    @ViewBuilder
    func destinationView(for route: AppRoute) -> some View {
        switch route {
        case .profile(let id): ProfileView(userId: id)
        case .settings: SettingsView()
        case .detail(let item): DetailView(item: item)
        }
    }
}
```

## SwiftData (iOS 17+)

### Model Definition

```swift
@Model final class Task {
    var title: String; var notes: String?; var isCompleted: Bool; var dueDate: Date?; var createdAt: Date
    @Relationship(deleteRule: .cascade) var subtasks: [Subtask] = []
    init(title: String, notes: String? = nil) {
        self.title = title; self.notes = notes; self.isCompleted = false; self.createdAt = .now
    }
}

@Model final class Subtask {
    var title: String
    var isCompleted: Bool
    var parent: Task?

    init(title: String) {
        self.title = title
        self.isCompleted = false
    }
}
```

### Querying Data

```swift
struct TaskListView: View {
    @Query(sort: \Task.createdAt, order: .reverse) private var tasks: [Task]
    @Environment(\.modelContext) private var ctx

    var body: some View {
        List(tasks) { task in
            TaskRow(task: task)
        }
        .toolbar {
            Button("Add") { addTask() }
        }
    }

    func addTask() {
        let task = Task(title: "New Task")
        ctx.insert(task)
    }
}
```

### Filtered Queries

```swift
// Predicate-based filtering
@Query(filter: #Predicate<Task> { task in
    !task.isCompleted
}, sort: \Task.dueDate) private var activeTasks: [Task]

// Dynamic filtering
struct FilteredTasksView: View {
    let isCompleted: Bool

    var body: some View {
        TaskList(isCompleted: isCompleted)
    }
}

struct TaskList: View {
    @Query private var tasks: [Task]

    init(isCompleted: Bool) {
        let pred = #Predicate<Task> { task in
            task.isCompleted == isCompleted
        }
        _tasks = Query(filter: pred, sort: \Task.createdAt)
    }

    var body: some View {
        List(tasks) { TaskRow(task: $0) }
    }
}
```

## MVVM with @Observable

```swift
@Observable @MainActor final class UserListVM {
    private(set) var users: [User] = []; private(set) var isLoading = false; private(set) var error: Error?
    private let svc: UserServiceProtocol
    init(svc: UserServiceProtocol = UserService()) { self.svc = svc }
    func load() async { isLoading = true; error = nil; defer { isLoading = false }; do { users = try await svc.fetchUsers() } catch { self.error = error } }
}

struct UserListView: View {
    @State private var vm = UserListVM()
    var body: some View {
        Group {
            if vm.isLoading { ProgressView() }
            else if let e = vm.error { ErrorView(error: e, retry: { Task { await vm.load() } }) }
            else { List(vm.users) { UserRow(user: $0) } }
        }.task { await vm.load() }
    }
}
```

## Dependency Injection

```swift
protocol UserServiceProtocol { func fetchUsers() async throws -> [User] }

// Environment DI
private struct UserServiceKey: EnvironmentKey { static let defaultValue: UserServiceProtocol = UserService() }
extension EnvironmentValues { var userService: UserServiceProtocol { get { self[UserServiceKey.self] } set { self[UserServiceKey.self] = newValue } } }

// Usage
struct ContentView: View {
    @Environment(\.userService) private var userService

    var body: some View {
        UserListView()
            .environment(\.userService, MockUserService())
    }
}
```

## View Decomposition

### Single View (<100 lines)

```swift
struct SimpleView: View {
    @State private var text = ""
    @State private var isEnabled = false

    var body: some View {
        VStack {
            TextField("Enter text", text: $text)
            Toggle("Enabled", isOn: $isEnabled)
            Button("Submit") { submit() }
        }
    }

    private func submit() {
        // Handle submission
    }
}
```

### Multiple Private Subviews (100-200 lines)

```swift
struct MediumView: View {
    @State private var vm = ViewModel()

    var body: some View {
        ScrollView {
            VStack {
                HeaderSection(title: vm.title)
                ContentSection(items: vm.items)
                FooterSection(action: vm.performAction)
            }
        }
    }
}

private struct HeaderSection: View {
    let title: String
    var body: some View { Text(title).font(.title) }
}

private struct ContentSection: View {
    let items: [Item]
    var body: some View { ForEach(items) { ItemRow(item: $0) } }
}

private struct FooterSection: View {
    let action: () -> Void
    var body: some View { Button("Action", action: action) }
}
```

### Multiple Files (>200 lines)

```swift
// ComplexView.swift
struct ComplexView: View {
    @State private var vm = ComplexViewModel()

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack {
                    HeaderView(viewModel: vm.headerVM)
                    ContentView(viewModel: vm.contentVM)
                    FooterView(viewModel: vm.footerVM)
                }
            }
        }
    }
}

// HeaderView.swift
struct HeaderView: View {
    @Bindable var viewModel: HeaderViewModel
    var body: some View { /* ... */ }
}

// ContentView.swift
struct ContentView: View {
    let viewModel: ContentViewModel
    var body: some View { /* ... */ }
}

// FooterView.swift
struct FooterView: View {
    let viewModel: FooterViewModel
    var body: some View { /* ... */ }
}
```
