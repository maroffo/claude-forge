---
name: react-nextjs
description: "React 19 + Next.js 16 App Router development. Use for React components, Server Components, data fetching, state management, forms, and testing."
allowed-tools: [mcp__acp__Read, mcp__acp__Edit, mcp__acp__Write, mcp__acp__Bash]
---

# ABOUTME: React 19 + Next.js 16 development with App Router, Server Components, TypeScript
# ABOUTME: Modern patterns for data fetching, state management, forms, testing, and styling

# React 19 + Next.js 16

## What's New (2025-2026)

| React 19.2 | Next.js 16 | Tailwind v4 |
|------------|------------|-------------|
| useActionState | `use cache` directive | CSS-first config |
| useFormStatus | proxy.ts | Oxide engine (100x faster) |
| useOptimistic | Turbopack default | Container queries |
| React Compiler | DevTools MCP | |

## Commands

```bash
npm run dev && npm run build && npm run test && npm run typecheck
```

## Core Patterns

```tsx
// Server Component (default)
async function Page() {
  const data = await fetchData()
  return <Component data={data} />
}

// Client Component
'use client'
function Interactive() {
  const [state, setState] = useState()
  return <button onClick={() => setState(x => x + 1)} />
}

// Server Action
async function submit(formData: FormData) {
  'use server'
  await db.insert(formData)
}
```

---

## Project Structure

```
src/
├── app/                    # App Router
├── components/ui/          # Primitives
├── features/*/             # Feature modules
├── lib/                    # Utils
├── stores/                 # Zustand
└── types/
```

---

## Server vs Client Components

**Default to Server. Client only when needed.**

| Server | Client |
|--------|--------|
| Fetch data, DB access | onClick, onChange |
| Sensitive data | useState, useEffect |
| Large deps, SEO | Browser APIs |

---

## Data Fetching

```tsx
// Server
async function getPosts() {
  const res = await fetch('https://api.example.com/posts', { next: { revalidate: 60 } })
  return res.json()
}

// Next.js 16 Caching
async function getData() {
  'use cache'
  cacheLife('minutes')
  return fetchData()
}

// Client: TanStack Query
'use client'
export function usePosts() {
  return useQuery({ queryKey: ['posts'], queryFn: api.posts.list })
}
```

---

## State Management

| Library | Use Case |
|---------|----------|
| TanStack Query | Server state |
| Zustand | Global client |
| nuqs | URL state |

```tsx
// Zustand
export const useAuthStore = create<AuthState>()(
  persist((set) => ({
    user: null,
    login: (user) => set({ user }),
    logout: () => set({ user: null }),
  }), { name: 'auth-storage' })
)
```

---

## Forms & Validation

```tsx
// Server Action + useActionState
'use server'
const schema = z.object({ email: z.string().email(), password: z.string().min(8) })

export async function login(prev: State, formData: FormData): Promise<State> {
  const result = schema.safeParse(Object.fromEntries(formData))
  if (!result.success) return { errors: result.error.flatten().fieldErrors }
  await authenticate(result.data)
  redirect('/dashboard')
}

// Component
'use client'
const [state, action, isPending] = useActionState(login, { errors: {} })
return <form action={action}>...</form>
```

---

## Testing

| Type | Tool |
|------|------|
| Unit | Vitest + RTL |
| E2E | Playwright |

```tsx
describe('Button', () => {
  it('calls onClick', () => {
    const onClick = vi.fn()
    render(<Button onClick={onClick}>Click</Button>)
    fireEvent.click(screen.getByRole('button'))
    expect(onClick).toHaveBeenCalled()
  })
})
```

---

## Performance

```tsx
<Image src={src} alt={alt} width={w} height={h} priority={isAboveFold} />
const Heavy = dynamic(() => import('@/components/heavy'), { loading: () => <Skeleton /> })
experimental: { reactCompiler: true }  // Auto-memoization
```

---

## Checklist

- [ ] No `any`, no unnecessary `'use client'`
- [ ] Server/Client correctly separated
- [ ] Forms: useActionState + useFormStatus
- [ ] useOptimistic for mutations
- [ ] Images: next/image + priority

**Libraries:** TanStack Query, Zustand, nuqs, Zod, Vitest + Playwright
