---
name: react-nextjs
description: "React + Next.js App Router development. Use when working with .tsx/.jsx files, next.config, or user asks about Server Components, data fetching, state management, forms, or React testing."
compatibility: "Requires Node.js and npm. Optional: Vitest, Playwright."
allowed-tools: [mcp__acp__Read, mcp__acp__Edit, mcp__acp__Write, mcp__acp__Bash]
---

# ABOUTME: React + Next.js App Router development with Server Components, TypeScript
# ABOUTME: Patterns for data fetching, state management, forms, testing, and styling

# React + Next.js

## Quick Reference

```bash
npm run dev && npm run build && npm run test && npm run typecheck
```

**See also:** `_AST_GREP.md`, `_PATTERNS.md`, `source-control`

---

## Version (determine, don't assume)

See `../_LANG_COMMON.md`. Fetch the truth:

```bash
jq -r '.dependencies.react, .dependencies.next' package.json 2>/dev/null   # project React + Next
cat .nvmrc 2>/dev/null                                                     # project Node
node -v                                                                    # local Node
npm view react version && npm view next version                            # latest upstream
```

---

## Pre-Commit Verification (MANDATORY)

`make check && make test-e2e` must pass (enforced by the `pre-commit-gate` hook; see `../_LANG_COMMON.md`). What `make check` expands to for a Next.js app:

```bash
npm run lint         # ESLint
npm run typecheck    # tsc --noEmit
npm run test         # Vitest unit tests
npm run build        # Next.js production build
npm audit --omit=dev # Dependency CVEs
```

---

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

Organize by **feature**, not technical layer.

---

## Server vs Client Components

**Default to Server. Client only when needed.**

| Server | Client |
|--------|--------|
| Fetch data, DB access | onClick, onChange |
| Sensitive data | useState, useEffect |
| Large deps, SEO | Browser APIs |

---

## Key Patterns

**State:** TanStack Query (server state), Zustand (global client), nuqs (URL state).

**Forms:** Server Action + `useActionState` + Zod validation. `useFormStatus` for pending UI.

**Performance:** `next/image` with priority, `dynamic()` for lazy loading, React Compiler for auto-memoization.

**Testing:** Vitest + React Testing Library (unit), Playwright (E2E).

For detailed code examples (forms, Zustand, testing, performance), see `references/react-patterns.md`.

---

## Checklist

- [ ] No `any`, no unnecessary `'use client'`
- [ ] Server/Client correctly separated
- [ ] Forms: useActionState + useFormStatus
- [ ] useOptimistic for mutations
- [ ] Images: next/image + priority

**Libraries:** TanStack Query, Zustand, nuqs, Zod, Vitest + Playwright
