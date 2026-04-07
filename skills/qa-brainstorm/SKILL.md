---
name: qa-brainstorm
description: "Discover what to test in a web application through hybrid interactive + autonomous exploration with playwright-cli. Ask essentials, explore the live app, then collaboratively define a QA strategy. Use before qa-plan."
metadata:
  category: qa
allowed-tools: Bash(playwright-cli:*)
disable-model-invocation: true
---

# QA Brainstorm

You are a senior QA engineer exploring a web application to build a test strategy. Ask just enough to get started, explore the live app yourself, then come back with findings for collaborative refinement.

Announce at start: "I'm using the qa-brainstorm skill to explore the app and build a QA strategy."

## Phase 1: Ask Essentials

Ask these one at a time. Move to exploration after 3 questions max.

1. **App URL and startup** — What's the URL? Does anything need running first?
2. **Credential source** (pick one) — a) Environment variables (`$TEST_USER`, `$TEST_PASSWORD`) b) 1Password CLI c) Test fixtures d) Ask each time
3. **Scope** (pick one) — a) Full application b) Specific feature c) Regression after a change

## Phase 2: Autonomous Exploration

Open the app and discover what's testable. Snapshot before every action.

```bash
playwright-cli open <url>
playwright-cli snapshot
```

Explore systematically:
1. Landing page — what's visible without auth?
2. Navigation — follow every nav link, record each route
3. Forms — identify inputs, buttons, validation
4. Auth flows — login, signup, logout, password reset
5. Key workflows — follow main user journeys end to end
6. Error states — 404, empty states, validation messages

For each page:
```bash
playwright-cli goto <route>
playwright-cli snapshot
```

Close when done:
```bash
playwright-cli close
```

## Phase 3: Present Findings

Present in sections of 200-300 words. Confirm after each.

1. Discovered routes — table of pages found
2. Proposed test suites — grouped by user journey, prioritized high/medium/low
3. Configuration — failure mode, credential setup, exclusions

## Phase 4: Save Strategy

Write to `docs/qa/strategy/YYYY-MM-DD-<feature>.md` and commit.

## Strategy Document Format

Every strategy MUST start with this header:

```markdown
# QA Strategy: [Feature/App Name]

> REQUIRED: Use the qa-plan skill to generate test cases from this strategy.

**Date:** YYYY-MM-DD
**App URL:** <url>
**Scope:** full | feature:<name> | regression:<description>

## Configuration

**Credential source:** env_vars | 1password | fixtures | ask
**On failure:** continue | stop
**Credential variables:**
- `$TEST_USER` — what this resolves to
- `$TEST_PASSWORD` — what this resolves to

## Discovered Routes

| Route | Description | Auth Required |
|-------|-------------|---------------|
| `/` | Landing page | No |
| `/login` | Login form | No |
| `/dashboard` | Main dashboard | Yes |

## Test Suites

### Suite 1: [Journey Name] (priority: high)

**Description:** What this validates from the user's perspective.

**Covers:**
- Scenario A
- Scenario B

## Out of Scope

- What's excluded and why
```

## Handoff

After saving the strategy:

**"Strategy saved to `docs/qa/strategy/<filename>.md`. Ready to create a test plan?"**

**If yes:**
- **REQUIRED:** Use the qa-plan skill to generate test cases from the strategy.

**If no / new session preferred:**
- User can start a fresh session with: "Create a test plan from docs/qa/strategy/<filename>.md"

## Constraints

- Do not write test cases. That's qa-plan's job.
- Do not guess credentials. Record the source method only.
- Do not test third-party widgets (analytics, chat, OAuth provider UIs).
- Skip timing-dependent scenarios that would be flaky as E2E tests.

## Examples

### Example: Full app exploration

User says: "Test my todo app at localhost:3000"

Phase 1 — ask credential source and scope, then explore.

Phase 2 — exploration:
```bash
playwright-cli open http://localhost:3000
playwright-cli snapshot
# Landing page: header, "Sign In" link, "Sign Up" link
playwright-cli goto http://localhost:3000/login
playwright-cli snapshot
# Login form: email, password, "Sign In" button
playwright-cli goto http://localhost:3000/todos
playwright-cli snapshot
# Todo list: input field, todo items with checkboxes, filter buttons
```

Phase 3 — present: "I found 6 routes. The app has auth and a todo CRUD interface with filtering. I'd propose 3 suites: 1) Authentication (high) 2) Todo Management (high) 3) Filtering (medium)."

Phase 4 — save strategy doc.

### Example: Feature-scoped

User says: "We just added settings, test that. staging.example.com, creds in env vars."

Phase 1 — URL and creds already provided, ask only about scope.

Phase 2 — explore just settings:
```bash
playwright-cli open https://staging.example.com
# ...login...
playwright-cli goto https://staging.example.com/settings
playwright-cli snapshot
# Profile form, password change, notification prefs, delete account
```

Phase 3 — present: "Settings has 3 sub-sections. I'd propose 2 suites: 1) Profile Management (high) 2) Notification Preferences (medium). Out of scope: delete account (destructive, needs dedicated test user)."
