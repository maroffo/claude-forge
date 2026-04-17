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

Never assume a React/Next.js/Node version from prior knowledge: it rots fast and you miss CVE fixes. Fetch the truth:

```bash
jq -r '.dependencies.react, .dependencies.next' package.json 2>/dev/null   # project React + Next
cat .nvmrc 2>/dev/null                                                     # project Node
node -v                                                                    # local Node
npm view react version && npm view next version                            # latest upstream
```

For a new project, pin to the latest stable. For an existing one, read `package.json` and prefer idioms gated to that version or lower.

---

## Pre-Commit Verification (MANDATORY)

Before every commit, both of these MUST pass:

```bash
make check       # project-wide gate (lint, types, tests, security)
make test-e2e    # end-to-end tests (or the project's e2e target)
```

If `make check` is missing, scaffold it with the `project-checks` skill. If there is no e2e target, do NOT silently skip: flag it to the user and ask whether to proceed or add one.

Full raw toolchain (what `make check` should expand to):

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
