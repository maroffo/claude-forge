---
name: refine-requirements
description: "Structured requirements gathering before planning. Use when request has ambiguities, multiple valid approaches, or implicit decisions."
---

# ABOUTME: Structured requirements refinement using AskUserQuestion before planning
# ABOUTME: Identifies gray areas, clarifies with concrete options, captures decisions for the plan

# Requirements Refinement

Invoke explicitly or triggered automatically by plan-first-workflow for 🟡/🔴 tasks.

## Process

0. **Pick the scope mode** before any other question. Classify the task, then:

   | Task class | Modes offered | Applied |
   |------------|---------------|---------|
   | bugfix, refactor | none, no question asked | Hold Scope, silently |
   | feature | Hold Scope (recommended) / Selective Expansion / Reduction | user's answer |
   | greenfield | Hold Scope (recommended) / Selective Expansion / Reduction / Expansion | user's answer |
   | unsure which class | none, no question asked | Hold Scope, silently |

   One `AskUserQuestion` for the mode where modes are offered; Hold Scope is the recommended option. Never ask on a bugfix or refactor, and never ask when the class is unclear: Hold is the escape from misclassifying.

   - **Hold Scope**: clarify HOW to build what was requested, never WHETHER to add more (steps 1-4 below as written)
   - **Selective Expansion**: adjacent additions may be proposed, one at a time
   - **Expansion**: same, with a wider radius (greenfield only)
   - **Reduction**: propose cuts to what was requested, one at a time

   In Selective Expansion and Expansion: each proposed addition is its own AskUserQuestion; never bundle. Reduction works the same way for cuts: one question per cut, nothing dropped silently. Declined proposals become deferred ideas, exactly as in Hold Scope.

1. **Identify gray areas** by domain:
   - Visual → layout, density, interactions, empty states
   - API/CLI → response format, error handling, auth flow
   - Infrastructure → scaling, redundancy, monitoring
   - Integration → protocol, auth method, error recovery

2. **For each gray area**, use `AskUserQuestion`:
   - Concrete options ("JWT" not "Option A"), 2-4 choices
   - Include "You decide" when Claude's discretion is fine
   - Follow threads: each answer may reveal the next question

3. **Scope guard**: in Hold Scope (and outside the opted-in mode's radius), if user suggests new scope, capture as deferred idea, redirect back

4. **Output**: list of decisions to include as `## Decisions` in the plan file

## Anti-patterns

- Generic questions ("What are your requirements?") → ask about specific decisions
- Checklist walking → follow the thread the user cares about
- Expanding scope in Hold Scope → clarify HOW to implement what's requested, not WHETHER to add more
- Asking the mode question on a bugfix, a refactor, or an unclear task → Hold applies, silently
- Bundling several additions into one "expansion accepted" → one question per addition, always
