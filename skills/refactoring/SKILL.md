---
name: refactoring
description: Audit codebase for refactoring opportunities - dead code, type improvements, test gaps, code smells, elegance, performance
metadata:
  category: superpowers
---

# Refactoring Audit

Systematically analyze the codebase for refactoring opportunities. Output feeds directly into issue planning and creation workflows.

## Activation

- User invokes `/refactoring`
- User asks to audit code quality, find tech debt, or plan refactoring work

## Process

### Step 1: Detect Languages and Load Skills

```bash
# Count files by extension to determine project languages
fd -t f -e rb -e ts -e tsx -e js -e py -e go -e rs | wc -l
fd -t f -e rb | head -1  # Ruby
fd -t f -e ts -e tsx | head -1  # TypeScript
fd -t f -e py | head -1  # Python
fd -t f -e go | head -1  # Go
fd -t f -e rs | head -1  # Rust
```

Check for framework indicators:
```bash
test -f Gemfile && rg "rails" Gemfile  # Rails
test -f Gemfile && rg "sorbet" Gemfile  # Sorbet
```

Based on detected languages, load the corresponding language skills:

| Detected | Load Skills |
|----------|-------------|
| `*.rb` | `ruby` |
| `*.rb` + Gemfile has rails | `ruby` + `rails` |
| `*.rb` + Gemfile has sorbet | `ruby` + `sorbet` |
| `*.ts`, `*.tsx` | `typescript` |
| `*.py` | `python` |
| `*.go` | `go` |
| `*.rs` | `rust` |
| `*.sql` or migrations | `sql` |
| PostgreSQL (check database.yml or schema) | `postgres` |

Each language skill contains detection patterns and idiomatic examples for that language.

### Step 2: Run Category Analysis

For each category, apply the language-specific detection patterns from the loaded skills.

## Categories

### 1. Dead Code

Find code that can be removed entirely.

**What to flag:**
- Methods/functions with zero callers
- Files not imported/required anywhere
- Feature flag branches that are always true/false
- Commented-out code blocks
- Unused constants/variables
- Dead exception handlers (exceptions never raised)

### 2. Type Improvements

Find weak types that should be strengthened.

**What to flag:**
- Escape hatches (`T.untyped`, `any`, `unknown`) → specific types
- Weak container types (`T::Hash[String, T.untyped]`, `Record<string, any>`) → structured types
- Boolean parameters → enums/union types (boolean blindness)
- Optional types that are never nil in practice
- Functions without return type annotations
- Repeated hash/object shapes → extract struct/interface/type

### 3. Test Gaps & Improvements

Find testing opportunities.

**What to flag:**
- Public methods with no test coverage
- Skipped/pending tests (fix or delete)
- Tests with no assertions
- Happy-path-only tests (missing error cases)
- Duplicated test setup
- Flaky tests

### 4. Code Smells

Find concrete violations of good design principles.

**What to flag:**
- Agent noun classes (`*Validator`, `*Processor`, `*Handler`, `*Manager`) → module functions
- Deep inheritance hierarchies (> 2 levels) → composition
- Raw data passing (hash/dict params through multiple functions) → parse into structs at boundary
- Metaprogramming in application code (`define_method`, `method_missing`, decorators that obscure) → explicit code
- God classes (classes doing too many things)
- Feature envy (methods that use another object's data more than their own)

### 5. Elegance

Find code that could be more elegant. Use judgment - look for opportunities to make code clearer, simpler, more readable, or more idiomatic.

### 6. Performance Improvements

Find performance issues.

**What to flag:**
- N+1 queries
- Missing database indexes on foreign keys
- Unbounded queries (missing limits)
- Repeated database queries in loops
- Synchronous operations that could be async/background
- Large object allocations in hot paths
- Chained collection operations that could be combined

## Output Format

### Step 3: Prioritize Findings

Group findings by impact:

| Priority | Criteria |
|----------|----------|
| P0 | Bugs, security issues, broken tests |
| P1 | Significant tech debt blocking features |
| P2 | Code quality improvements |
| P3 | Nice-to-have cleanups |

### Step 4: Present Summary

```markdown
## Dead Code (X items)

### P1
- [ ] Remove `UserLegacyController` - replaced by `UsersController` 2 years ago
- [ ] Delete `lib/old_auth.rb` - feature flag `use_new_auth` is always true

### P2
- [ ] Remove unused `format_legacy_date` helper

## Type Improvements (X items)

### P1
- [ ] Replace `T.untyped` in `PaymentProcessor#process` return type
- [ ] Convert `options` hash in `EmailSender` to T::Struct

## Test Improvements (X items)

### P1
- [ ] Add tests for `RefundProcessor` - 0% coverage on critical path

## Code Smells (X items)

### P2
- [ ] `UserValidator` class → `Users.validate` module function
- [ ] `OrderProcessor` class → `Orders.process` module function
- [ ] `ReportGenerator` inherits 4 levels deep → flatten with composition

## Performance Improvements (X items)

### P1
- [ ] Add index on `orders.user_id`
- [ ] Fix N+1 in `OrdersController#index`
```

### Step 5: What Happens Next

Present findings to the user. For findings they choose to act on:

- **Quick fix** (obvious, < 5 min): apply directly with `test-driven-development` + `verification-before-completion`
- **Needs design exploration**: use `brainstorming` to explore the approach
- **Clear scope, multi-step**: create a plan with `writing-plans`, then execute with `executing-plans`

## Notes

- This is **read-only analysis**. Don't modify any code.
- False positives happen. Use judgment.
- Context matters - a 100-line method in a test helper differs from core business logic.
- Not everything needs to be fixed. Flag it, prioritize it, let the user decide.
