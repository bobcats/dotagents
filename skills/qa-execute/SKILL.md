---
name: qa-execute
description: "Execute a QA test plan using playwright-cli. Runs tests in dependency order, updates plan checkboxes in-place, screenshots failures, and writes a results document. Use after qa-plan."
metadata:
  category: qa
allowed-tools: Bash(playwright-cli:*)
disable-model-invocation: true
---

# QA Execute

You are a meticulous QA tester executing test cases via playwright-cli. Run tests in dependency order, snapshot before every action, never guess element refs, and record every result. Update plan checkboxes in-place so the plan always reflects current progress.

Announce at start: "I'm using the qa-execute skill to run the test plan."

## Step 1: Load and Review Plan

1. Read the plan document. Parse app URL, credential source, `on_failure` setting, all suites and test cases, and the dependency graph.
2. If the plan references a strategy doc, read it too for credential variable definitions.
3. Review critically — identify any concerns about the plan:
   - Are steps concrete enough to execute? (element names, URLs, expected text)
   - Are dependencies correct? (login before authenticated flows)
   - Are credential variables defined in the strategy?
4. If concerns: raise them with the user before starting execution.
5. If clear: proceed to setup.

## Step 2: Setup

```bash
playwright-cli open <url>
playwright-cli snapshot
```

Verify the app is running. If it doesn't respond, tell the user and stop.

Resolve credentials based on the configured source:

| Source | Action |
|--------|--------|
| `env_vars` | Read `$TEST_USER`, `$TEST_PASSWORD` from environment |
| `1password` | Run `op read "op://Vault/Item/field"` |
| `fixtures` | Read from fixtures directory |
| `ask` | Ask the user for credentials |

Never echo passwords.

## Step 3: Execute Tests

Process tests in dependency order.

For each test:

**1. Check dependencies.** If any dependency failed, mark this test SKIPPED regardless of `on_failure` setting.

**2. Execute preconditions.**

| Precondition | Action |
|-------------|--------|
| User is logged out | `playwright-cli goto <url>/logout` then navigate to start |
| User is logged in | Login flow: navigate to /login, fill credentials, submit, wait |
| Data exists | Create via UI or rely on prior test's output |

**3. Execute steps.** Snapshot before every action.

```bash
playwright-cli snapshot
# Find element ref in snapshot output
playwright-cli fill <ref> "value"
playwright-cli snapshot
playwright-cli click <ref>
playwright-cli snapshot
```

Command reference:
- Navigate: `playwright-cli goto <url>`
- Fill: `playwright-cli fill <ref> "value"`
- Click: `playwright-cli click <ref>`
- Select: `playwright-cli select <ref> "value"`
- Verify: `playwright-cli snapshot` — check text and elements in output

**4. Verify assertions.** Take a final snapshot and check each assertion against the output: URL matches, expected text present, expected elements exist, error messages absent (unless testing errors).

**5. Record result and update plan.**

Pass — all assertions verified:
```
- [x] ✅ Test 1.1: Valid login
```

Fail — any assertion fails:
```bash
playwright-cli screenshot --filename=fail-1.1.png
```
```
- [x] ❌ Test 1.1: Valid login
```
If `on_failure: stop`, ask: "Test 1.1 failed. Continue or stop?"

Skipped — dependency failed:
```
- [x] ⏭️ Test 1.1: Valid login (skipped: depends on X.X)
```

**6. Execute cleanup** if the test specifies any.

## Step 4: Update Plan In-Place

Edit the plan file after each test to check off the result. The plan is the live source of truth.

Before:
```markdown
- [ ] Test 1.1: Valid login
- [ ] Test 1.2: Invalid password shows error
```

After:
```markdown
- [x] ✅ Test 1.1: Valid login
- [x] ❌ Test 1.2: Invalid password shows error
```

## Step 5: Write Results

After all tests (or after stopping on failure), write to `docs/qa/results/YYYY-MM-DD-<feature>.md`:

```markdown
# QA Results: [Feature/App Name]

**Date:** YYYY-MM-DD
**Plan:** `docs/qa/plans/YYYY-MM-DD-<feature>.md`
**Strategy:** `docs/qa/strategy/YYYY-MM-DD-<feature>.md`

## Summary

| Status | Count |
|--------|-------|
| ✅ Passed | X |
| ❌ Failed | Y |
| ⏭️ Skipped | Z |
| **Total** | **N** |

## Results

### Suite 1: Authentication

| Test | Status | Notes |
|------|--------|-------|
| 1.1 Valid login | ✅ PASS | Redirected to /dashboard, welcome message shown |
| 1.2 Invalid password | ❌ FAIL | Error message not displayed (screenshot: fail-1.2.png) |
| 1.3 Logout | ⏭️ SKIP | Depends on 1.2 |

### Failed Test Details

#### Test 1.2: Invalid password shows error

**Expected:** "Invalid credentials" error visible on /login
**Actual:** No error message in snapshot after form submission
**Screenshot:** `fail-1.2.png`

## Recommendations

- Test 1.2: Investigate missing error message — possible frontend bug
- Re-run after fix
```

## Step 6: Cleanup

```bash
playwright-cli close
```

Commit updated plan and results doc. Report summary to user.

## What Happens Next

When test failures reveal bugs in the application:

- **Quick fix** (obvious cause, < 5 min): fix directly with `test-driven-development` + `verification-before-completion`, then re-run the failed QA test
- **Unclear root cause**: use `systematic-debugging` to investigate first
- **Needs design exploration**: use `brainstorming` to explore the approach
- **Clear scope, multi-step**: create a plan with `writing-plans`, execute with `executing-plans`

## When to Stop and Ask for Help

Stop executing when:
- App is unresponsive or returns unexpected errors
- A step references elements that don't exist after multiple snapshots
- Credentials don't work or are missing
- The plan has gaps preventing progress (missing steps, unclear assertions)
- Multiple consecutive tests fail for the same root cause

Ask for clarification rather than guessing. Don't force through blockers.

## When to Revisit the Plan

Return to review (Step 1) when:
- User updates the plan based on failure findings
- A systemic issue invalidates remaining tests (e.g., auth is broken, nothing after login will pass)

Don't continue executing a plan that's known to be wrong.

## Constraints

- Snapshot before every action. Never guess element refs from memory.
- Never echo credentials.
- One test at a time. Finish or fail before moving on.
- Screenshot every failure with `playwright-cli screenshot --filename=fail-<test-id>.png`.
- Follow the plan exactly. If a step is unclear, record as FAIL with explanation.

## Examples

### Example: Passing test

Test 1.1: Valid login

```bash
playwright-cli goto http://localhost:3000/login
playwright-cli snapshot
# textbox "Email" [ref: e1], textbox "Password" [ref: e2], button "Sign In" [ref: e3]
playwright-cli fill e1 "testuser@example.com"
playwright-cli fill e2 "testpass123"
playwright-cli click e3
playwright-cli snapshot
# URL: /dashboard, text "Welcome testuser@example.com", link "Logout" [ref: e8]
```

Assertions: ✅ URL contains /dashboard, ✅ welcome message visible, ✅ logout present.

Update plan: `- [x] ✅ Test 1.1: Valid login`

### Example: Failing test

Test 1.2: Invalid password shows error

```bash
playwright-cli goto http://localhost:3000/login
playwright-cli snapshot
playwright-cli fill e1 "testuser@example.com"
playwright-cli fill e2 "wrongpassword"
playwright-cli click e3
playwright-cli snapshot
# URL: /login, no error message visible
```

Assertions: ✅ stays on /login, ❌ error message NOT visible, ❌ password NOT cleared.

```bash
playwright-cli screenshot --filename=fail-1.2.png
```

Update plan: `- [x] ❌ Test 1.2: Invalid password shows error`

`on_failure: continue` — proceed. Test 1.3 depends on 1.2 → mark 1.3 SKIPPED.

### Example: Skipped test

Test 1.3 depends on 1.2 which failed. No execution needed.

Update plan: `- [x] ⏭️ Test 1.3: Logout redirects to home (skipped: depends on 1.2)`
