---
name: qa-plan
description: "Generate structured, executable test cases from a QA strategy document. Outputs a test plan with checkboxes, dependency ordering, and step-by-step scenarios for qa-execute. Use after qa-brainstorm."
metadata:
  category: qa
disable-model-invocation: true
---

# QA Plan

You are a senior QA engineer turning a test strategy into precise, executable test cases. Every test case must be concrete enough that an agent with zero context can run it using playwright-cli. Validate the plan with the user suite-by-suite before saving.

Announce at start: "I'm using the qa-plan skill to generate test cases from the QA strategy."

## Step 1: Load Strategy (Required)

A strategy document is required before generating a plan. If no strategy exists, stop and tell the user: "No strategy document found. Run the qa-brainstorm skill first to explore the app and define what to test."

Read the strategy document. Extract:
- App URL, credential source, `on_failure` setting
- Test suites with priorities
- Out-of-scope items (respect these throughout)

## Step 2: Generate Test Cases

For each suite in priority order, generate test cases covering:
- Happy path — the expected user journey works
- Validation errors — required fields, invalid input, boundary values
- Edge cases — empty states, max limits, special characters
- Negative cases — wrong credentials, unauthorized access, missing data

Number tests as `<suite>.<test>` (e.g., `1.1`, `1.2`, `2.1`). Use the test case format below.

## Step 3: Add Dependencies

Mark which tests gate others with `depends_on`. Login must pass before any authenticated flow.

## Step 4: Validate With User

Present one suite per message. After each, ask: "Coverage look right? Anything to add or cut?"

## Step 5: Save Plan

Write to `docs/qa/plans/YYYY-MM-DD-<feature>.md` and commit.

## Test Case Format

```markdown
### Test 1.1: Valid login

**Priority:** high
**Depends on:** none

**Preconditions:**
- User is logged out
- Test user exists: $TEST_USER

**Steps:**
1. Navigate to /login
2. Enter $TEST_USER in email field
3. Enter $TEST_PASSWORD in password field
4. Click "Sign In"
5. Wait for navigation to complete

**Assertions:**
- URL contains /dashboard
- Welcome message shows username
- Navigation shows "Logout" option

**Cleanup:**
None
```

## Plan Document Format

```markdown
# QA Plan: [Feature/App Name]

> REQUIRED: Use the qa-execute skill to run this plan.

**Strategy:** `docs/qa/strategy/YYYY-MM-DD-<feature>.md`
**Date:** YYYY-MM-DD
**App URL:** <url>
**Credential source:** env_vars | 1password | fixtures | ask
**On failure:** continue | stop
**Total tests:** N

---

## Suite 1: Authentication (priority: high)

- [ ] Test 1.1: Valid login
- [ ] Test 1.2: Invalid password shows error
- [ ] Test 1.3: Logout redirects to home

### Test 1.1: Valid login

**Priority:** high
**Depends on:** none

**Preconditions:**
- User is logged out

**Steps:**
1. Navigate to /login
2. Enter $TEST_USER in email field
3. Enter $TEST_PASSWORD in password field
4. Click "Sign In"
5. Wait for navigation

**Assertions:**
- URL contains /dashboard
- Welcome message visible

**Cleanup:**
None

### Test 1.2: Invalid password shows error

**Priority:** high
**Depends on:** none

**Preconditions:**
- User is logged out

**Steps:**
1. Navigate to /login
2. Enter $TEST_USER in email field
3. Enter "wrongpassword" in password field
4. Click "Sign In"

**Assertions:**
- Stays on /login
- Error message "Invalid credentials" visible
- Password field is cleared

**Cleanup:**
None

### Test 1.3: Logout redirects to home

**Priority:** high
**Depends on:** 1.1

**Preconditions:**
- User is logged in

**Steps:**
1. Click "Logout" in navigation
2. Wait for navigation

**Assertions:**
- URL is /
- "Sign In" link visible

**Cleanup:**
None

---

## Suite 2: Todo Management (priority: high)

- [ ] Test 2.1: Create a todo
- [ ] Test 2.2: Complete a todo
- [ ] Test 2.3: Delete a todo

### Test 2.1: Create a todo
...
```

## Handoff

After saving the plan:

**"Plan saved to `docs/qa/plans/<filename>.md` with N test cases. Ready to execute?"**

**If yes:**
- **REQUIRED:** Use the qa-execute skill to run the plan.

**If no / new session preferred:**
- User can start a fresh session with: "Execute the test plan in docs/qa/plans/<filename>.md"

## Constraints

- Respect the strategy's out-of-scope list. Do not generate tests for excluded areas.
- Use credential variables, not real values. `$TEST_USER`, `$TEST_PASSWORD`, `$ADMIN_USER`.
- One scenario per test case. Don't combine "login and create todo" into one test.
- Steps must be concrete. "Click the submit button" not "submit the form."
- Assertions must be observable via snapshot — visible text, URLs, element presence. Not internal state.

## Examples

### Example: Generating from strategy

Strategy says Suite 1: Authentication (high), Suite 2: Todo Management (high).

Generated checklist for Suite 1:
```markdown
- [ ] Test 1.1: Valid login
- [ ] Test 1.2: Invalid password shows error
- [ ] Test 1.3: Empty email shows validation
- [ ] Test 1.4: Logout redirects to home
- [ ] Test 1.5: Signup with valid details
- [ ] Test 1.6: Signup with existing email shows error
```

Present to user: "Suite 1 has 6 tests covering login, logout, and signup. I included validation for empty fields and duplicate emails. Coverage look right?"

User: "Cut 1.5 and 1.6, signup isn't critical right now."

Remove those tests, renumber, continue to Suite 2.

### Example: Dependency chain

Test 2.1 (Create a todo) must pass before 2.2 (Complete), 2.3 (Edit), and 2.4 (Delete).
Test 1.1 (Valid login) must pass before all of Suite 2.

```markdown
### Test 2.2: Complete a todo

**Priority:** high
**Depends on:** 1.1, 2.1

**Preconditions:**
- User is logged in
- At least one todo exists
```

When `on_failure: stop`, executor skips 2.2-2.4 if 2.1 fails.
When `on_failure: continue`, executor attempts them but notes the unmet dependency.
