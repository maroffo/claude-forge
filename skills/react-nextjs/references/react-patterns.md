# ABOUTME: Detailed React/Next.js patterns for forms, state management, performance, testing
# ABOUTME: Reference companion to react-nextjs SKILL.md with full code examples

# React/Next.js Patterns Reference

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

## Performance

```tsx
<Image src={src} alt={alt} width={w} height={h} priority={isAboveFold} />
const Heavy = dynamic(() => import('@/components/heavy'), { loading: () => <Skeleton /> })
experimental: { reactCompiler: true }  // Auto-memoization
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
