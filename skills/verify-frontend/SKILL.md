---
name: verify-frontend
description: "Verify UI changes end-to-end in a real browser before declaring them done: dev server, direct interaction, console check, before/after screenshots, Lighthouse when perf-relevant. Use after any frontend/UI change, when user says verify UI, check the page, or does it render. Supersedes generic verify flows for rendered UI. Not for backend-only changes (verification-protocol test/lint/build covers those)."
compatibility: "Requires chrome-devtools MCP (or claude-in-chrome) and a runnable dev server."
---

# ABOUTME: End-to-end UI verification; never report a UI change done on a green edit or passing tests alone
# ABOUTME: Browser interaction, zero-new-console-errors, before/after screenshots, Lighthouse gate when perf-relevant

# Verify Frontend

A successful edit and green unit tests do NOT verify a UI change: they can encode the same wrong assumption as the code. Verify the way a human reviewer would, in a real browser, with quantitative checks wherever possible.

## When

- After any change touching rendered UI (components, templates, styles, client-side logic)
- Before reporting a UI subtask complete in the orchestrator loop (feeds VERIFY, step 2)
- Skip only for changes with no runtime surface (type-only, test-only, docs)

## Protocol

Run every step. A failure at any step means: fix, then rerun **from step 1**. Never hand back partially verified work.

If the chrome-devtools MCP tools are deferred, load the needed set in ONE ToolSearch call first (`new_page`, `navigate_page`, `take_screenshot`, `list_console_messages`, `list_network_requests`, `resize_page`, `lighthouse_audit`).

1. **Baseline (before the change, when still possible):** start the dev server, open the affected page, screenshot it, record the console error/warning count. If the change is already applied and touches shared layout or navigation (risky: regressions can land outside the edited page), capture a true baseline: `git stash` → screenshot + console count → `git stash pop`, then continue. Otherwise note that the baseline is post-hoc.
2. **Load:** open the edited page in the browser (`new_page`/`navigate_page`). The page must render without blank screens or error overlays.
3. **Interact:** exercise the change directly. New control (button, input, toggle): click/type into it and confirm the expected state change. Changed layout: resize to mobile and desktop widths (`resize_page`).
4. **Screenshot after:** capture the changed state (`take_screenshot`). Pair it with the baseline for the report.
5. **Console gate (quantitative):** `list_console_messages`: **zero new errors or warnings** versus baseline. A pre-existing error is noted, not fixed silently, and never used to excuse a new one.
6. **Network gate (when the change fetches):** `list_network_requests`: no failed requests introduced by the change.
7. **Performance gate (when perf-relevant: new page, heavy asset, list rendering, hydration change):** run `lighthouse_audit` and report the scores. Regression >5 points on Performance versus baseline is a finding, not a footnote.

## Report format

State results per step, with numbers:

```
UI verification: PASS
- Render: /dashboard loads, no overlay
- Interaction: like button toggles state, count 0 → 1
- Console: 0 new errors (baseline 2 pre-existing warnings, unchanged)
- Screenshots: before/after captured
- Lighthouse: perf 94 (baseline 93); n/a if skipped, say why
```

A FAIL report names the step, the observed value, and what was expected. Partial verification is reported as NOT verified.

## Quality notes

- Prefer quantitative checks (error counts, scores, pixel sizes) over "looks fine": they make self-verification and the two-confirmation gate (score-evidence-guard) possible.
- Browser dialogs (`alert`/`confirm`) block the automation: don't trigger them; use console logging instead.
- This skill composes with `rules/verification-protocol.md`: test/lint/build still run; this adds the runtime surface those can't see.
