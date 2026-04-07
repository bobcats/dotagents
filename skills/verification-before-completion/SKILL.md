---
name: verification-before-completion
description: Use when about to claim work is complete, fixed, or passing, before committing or creating PRs - requires running verification commands and confirming output before making any success claims; evidence before assertions always
metadata:
  category: superpowers
---

# Verification Before Completion

## Overview

Claiming work is complete without verification is dishonesty, not efficiency.

**Core principle:** Evidence before claims, always.

**Violating the letter of this rule is violating the spirit of this rule.**

## The Iron Law

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

If you haven't run the verification command in this message, you cannot claim it passes.

## The Gate Function

```
BEFORE claiming any status or expressing satisfaction:

1. IDENTIFY: What command proves this claim?
2. RUN: Execute the FULL command (fresh, complete)
3. READ: Full output, check exit code, count failures
4. VERIFY: Does output confirm the claim?
   - If NO: State actual status with evidence
   - If YES: State claim WITH evidence
5. ONLY THEN: Make the claim

Skip any step = lying, not verifying
```

## Practical Verification Checklist

Run the checks that match your change. Verification is contextual, but never optional.

### Automated Tests

Run relevant automated tests first (unit/integration/e2e as applicable).

Examples:
- `npm test`
- `pytest`
- `go test ./...`

Report concrete evidence:
- command executed
- pass/fail counts
- exit code

### Linters and Type Checks

Run static checks separately from tests.

Examples:
- `npm run lint`
- `npm run typecheck`
- `ruff check .`
- `mypy .`

Linters passing does **not** prove compilation/runtime correctness. Type checks passing does **not** prove behavior.

### Manual UI Testing (when required)

Use this decision split:

- **UI changes (web/mobile/desktop):** run automated checks **and** verify manually in browser/app flows affected.
  - Prefer the `playwright-cli` skill for browser validation.
  - Do **not** rely on MCP server-based browsing as your default verification path.
- **CLI/library/backend-only changes with no UI impact:** automated tests may be sufficient if they fully cover changed behavior.

For manual checks, state exactly what you exercised (pages, inputs, expected outcomes).
Never skip verification because it feels complicated or expensive; reduce scope, but still run real checks.
If the human requested headed browser verification, run it headed and report concrete evidence (steps + observed result).

### Non-Deterministic Verification

If verification results are non-deterministic (flaky tests, timing-dependent assertions), fix the harness before trusting results. A passing test that sometimes fails is not evidence of correctness. See `make-verification-deterministic` principle.

### Clean State Checklist

Before claiming completion or committing:

- [ ] Remove debug statements (`console.log`, `print`, ad-hoc tracing)
- [ ] Resolve or intentionally track TODO/FIXME/HACK comments
- [ ] Remove commented-out dead code
- [ ] Remove half-implemented branches and placeholder paths
- [ ] Ensure no skipped/disabled tests were introduced to force green

Optional hygiene pass: run the `remove-slop` skill before final completion claims.

### Verification-Proof Claim Examples

Good claim:
- "Ran `npm test` (128 passed, 0 failed), `npm run lint` (0 issues), and manual checkout flow in Chrome; all checks passed."

Bad claim:
- "Looks good now, should be fixed."

## Common Failures

| Claim | Requires | Not Sufficient |
|-------|----------|----------------|
| Tests pass | Test command output: 0 failures | Previous run, "should pass" |
| Linter clean | Linter output: 0 errors | Partial check, extrapolation |
| Build succeeds | Build command: exit 0 | Linter passing, logs look good |
| Bug fixed | Test original symptom: passes | Code changed, assumed fixed |
| Regression test works | Red-green cycle verified | Test passes once |
| Agent completed | VCS diff shows changes | Agent reports "success" |
| Requirements met | Line-by-line checklist | Tests passing |

## Red Flags - STOP

- Using "should", "probably", "seems to"
- Expressing satisfaction before verification ("Great!", "Perfect!", "Done!", etc.)
- About to commit/push/PR without verification
- Trusting agent success reports
- Relying on partial verification
- Thinking "just this once"
- Tired and wanting work over
- **ANY wording implying success without having run verification**

## Rationalization Prevention

| Excuse | Reality |
|--------|---------|
| "Should work now" | RUN the verification |
| "I'm confident" | Confidence ≠ evidence |
| "Just this once" | No exceptions |
| "Linter passed" | Linter ≠ compiler |
| "Agent said success" | Verify independently |
| "I'm tired" | Exhaustion ≠ excuse |
| "Partial check is enough" | Partial proves nothing |
| "Different words so rule doesn't apply" | Spirit over letter |

## Key Patterns

**Tests:**
```
✅ [Run test command] [See: 34/34 pass] "All tests pass"
❌ "Should pass now" / "Looks correct"
```

**Regression tests (TDD Red-Green):**
```
✅ Write → Run (pass) → Revert fix → Run (MUST FAIL) → Restore → Run (pass)
❌ "I've written a regression test" (without red-green verification)
```

**Build:**
```
✅ [Run build] [See: exit 0] "Build passes"
❌ "Linter passed" (linter doesn't check compilation)
```

**Requirements:**
```
✅ Re-read plan → Create checklist → Verify each → Report gaps or completion
❌ "Tests pass, phase complete"
```

**Agent delegation:**
```
✅ Agent reports success → Check VCS diff → Verify changes → Report actual state
❌ Trust agent report
```

## Why This Matters

From 24 failure memories:
- your human partner said "I don't believe you" - trust broken
- Undefined functions shipped - would crash
- Missing requirements shipped - incomplete features
- Time wasted on false completion → redirect → rework
- Violates: "Honesty is a core value. If you lie, you'll be replaced."

## When To Apply

**ALWAYS before:**
- ANY variation of success/completion claims
- ANY expression of satisfaction
- ANY positive statement about work state
- Committing, PR creation, task completion
- Moving to next task
- Delegating to agents

**Rule applies to:**
- Exact phrases
- Paraphrases and synonyms
- Implications of success
- ANY communication suggesting completion/correctness

## The Bottom Line

**No shortcuts for verification.**

Run the command. Read the output. THEN claim the result.

This is non-negotiable.
