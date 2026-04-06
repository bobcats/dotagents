---
name: code-review
description: Thorough code review surfacing all findings. Deep analysis across safety, security, performance, operations, testing, and code organization.
metadata:
  category: superpowers
---

# Code Review

Staff Engineer-level review for production systems. Assumes code ships to millions of users tomorrow.

Surface all findings with evidence. The reader decides what to act on.

## Activation

- User invokes `/code-review`
- User asks to review code, PR, or changes
- Self-review before merge or PR creation (see "Self-Review" below)

## Review Philosophy

Thorough fact-finding over selective filtering. Report everything found with evidence.

**Prioritize issues that:**
- Could cause data loss or corruption
- Create security vulnerabilities
- Fail silently in production
- Scale poorly under real load
- Make future debugging painful

**Also examine:**
- Test coverage and verification gaps
- Code organization and clarity
- API design and interface contracts

**For each finding:**
- Cite specific code locations
- Explain what you observed and why it matters
- Provide concrete fix when applicable

## Severity Labels

Use these labels to organize findings. Report ALL findings regardless of severity:

| Severity | Criteria |
|----------|----------|
| **P0 - Blocker** | Data loss, security breach, or hard failure - cannot deploy as-is |
| **P1 - Critical** | Degraded experience, race conditions, missing validation |
| **P2 - Important** | Technical debt, suboptimal patterns, missing observability |
| **P3 - Minor** | Code clarity, documentation, style consistency |
| **P4 - Observation** | Patterns noticed, questions raised, things to consider |

## Review Process

Analyze the code systematically across six domains. Examine each area and note ALL findings with severity and specific code references.

### 1. Safety & Correctness
- **Data Integrity**: Risk of corruption, loss, or inconsistency
- **Concurrency**: Race conditions, deadlocks, lock contention
- **Edge Cases**: Boundary conditions, null handling, error states
- **Business Logic**: Financial calculations, state transitions, validation

### 2. Security Assessment
- **Input Validation**: Injection attacks (SQL, XSS, command), sanitization
- **Auth/Authz**: Session management, access controls, privilege escalation
- **Data Protection**: PII handling, encryption, secure transmission
- **Dependencies**: Known vulnerabilities, supply chain risks

### 3. Performance & Scale
- **Query Efficiency**: N+1 queries, missing indexes, full scans
- **Resource Usage**: Memory leaks, connection pools, CPU-bound operations
- **Scale Cliffs**: Operations that break at 10x/100x current load
- **Caching**: Missing opportunities, invalidation bugs

### 4. Operational Readiness
- **Observability**: Logging, metrics, tracing, alerting coverage
- **Failure Modes**: Graceful degradation, retry logic, circuit breakers
- **Deployment**: Migration safety, rollback plans, feature flags
- **Debugging**: Error context, reproduction paths, diagnostic tools

### 5. Testing & Verification
- **Coverage Gaps**: Untested paths, missing edge cases
- **Test Quality**: Assertions, isolation, determinism
- **Testability**: Hard-to-test patterns, dependency injection
- **Integration Points**: External system mocking, contract testing

### 6. Code Organization & Clarity
- **Structure**: Module boundaries, cohesion, coupling
- **Naming**: Clarity, consistency, domain alignment
- **Abstractions**: Appropriate level, premature generalization, missing abstractions
- **Patterns**: Consistency with codebase conventions, anti-patterns

## Working With Tools

**Diff scope**: Always diff against the merge-base, not straight `main`. A straight diff includes changes that landed on main after the branch was created, producing false positives.
```bash
git diff $(git merge-base origin/main HEAD)..HEAD
```

**Code analysis (always start here)**:
- Use `Read`, `Grep`, `Glob` to understand the full context
- Trace data flow through the code path
- Identify all callers and dependencies

**Security verification (when vulnerabilities suspected)**:
- Use `WebSearch` to check CVE databases for dependencies
- Use `WebFetch` on OWASP or security documentation for best practices
- Verify cryptographic implementations against current standards

**Performance validation (when bottlenecks identified)**:
- Use `Bash` to check database indexes, query plans
- Look for existing benchmarks or monitoring data

Exhaust local code context before reaching for external resources.

## Output Format

Structure the review in this format:

**Summary**
- Blockers: [count]
- Critical: [count]
- Important: [count]
- Minor: [count]
- Observations: [count]

**P0 - Blockers** (if any)
For each issue:
- Location: `file:line` or function name
- Issue: What's wrong and why it matters
- Impact: Specific failure scenario
- Fix: Concrete recommendation with code example
- Effort: Quick(<1h) / Short(1-4h) / Medium(1-2d) / Large(3d+)

**P1 - Critical** (if any)
For each issue:
- Location and description
- Impact on users/operations
- Suggested approach
- Effort: Quick(<1h) / Short(1-4h) / Medium(1-2d) / Large(3d+)

**P2 - Important** (if any)
- Design improvements
- Technical debt
- Pattern recommendations

**P3 - Minor** (if any)
- Code clarity
- Documentation gaps
- Minor optimizations

**P4 - Observations** (if any)
- Patterns noticed
- Questions raised
- Things to consider

**Trade-off Analysis** (when significant choices exist)
- Why current approach was likely chosen
- Alternative approaches with pros/cons

## Self-Review

Use this workflow to review your own changes before merge or PR creation.

**When:**
- After completing a major feature
- Before merge to main
- When stuck (fresh perspective)
- Before refactoring (baseline check)

**How:**

1. Get the diff:
```bash
BASE_SHA=$(git merge-base HEAD origin/main)
git diff $BASE_SHA HEAD
```

2. Apply the six-domain review above to your own changes, flagging issues by severity (P0–P4).

3. Fix Critical and Important issues before proceeding. Note Minor issues for later.

**Cadence during plan execution:**
- Review after every 3 tasks or at natural checkpoints
- Review before merge, always
- Review when stuck — a self-review often surfaces the issue

## Constraints

**Never do**:
- Flag hypothetical issues without evidence in the code
- Omit findings because they seem minor
- Make shipping recommendations (that's the reader's call)

**Always do**:
- Quote specific code when citing issues
- Provide actionable fixes, not just problems
- Report all findings, organized by severity
- Consider multiple valid approaches when they exist

## Examples

<examples>
<example>
<request>Review this payment processing endpoint for production readiness.</request>
<response>
**Summary**
- Blockers: 1
- Critical: 2
- Important: 2
- Minor: 2

**P0 - Blockers**

**Missing idempotency on payment creation**
- Location: `app/services/payment_processor.rb:45`
- Issue: `create_payment` can process duplicate charges if client retries
- Impact: Customer charged multiple times for same order
- Fix: Add idempotency key check before processing
```ruby
def create_payment(order, idempotency_key:)
  return existing if (existing = Payment.find_by(idempotency_key: idempotency_key))
  # ... proceed with creation
end
```
- Effort: Short (1-4h)

**P1 - Critical**

**Race condition in balance check**
- Location: `app/services/payment_processor.rb:62-68`
- Issue: Balance checked then debited without lock; concurrent requests can overdraw
- Impact: Negative balances, financial loss
- Suggested approach: Use `with_lock` or SELECT FOR UPDATE
- Effort: Short (1-4h)

**No timeout on payment gateway call**
- Location: `app/clients/stripe_client.rb:23`
- Issue: HTTP call has no timeout; gateway hang blocks worker indefinitely
- Impact: Worker pool exhaustion under gateway degradation
- Suggested approach: Add 30s timeout, circuit breaker for repeated failures
- Effort: Quick (<1h)

**P2 - Important**

- Consider extracting payment state machine to make transitions explicit
- Add structured logging with payment_id, order_id on all operations for debugging

**P3 - Minor**

- Add `# frozen_string_literal: true` to all files
- Document the retry policy in README
</response>
</example>

<example>
<request>Review these API changes for the new search feature.</request>
<response>
**Summary**
- Blockers: 0
- Critical: 1
- Important: 3
- Minor: 4

**P1 - Critical**

**Unbounded result set**
- Location: `app/controllers/api/v1/search_controller.rb:18`
- Issue: `Search.query(params[:q])` returns all matches; no limit
- Impact: Memory exhaustion on broad queries, slow responses, potential OOM
- Suggested approach: Add `limit` param with max 100, default 25
```ruby
def index
  limit = [params.fetch(:limit, 25).to_i, 100].min
  @results = Search.query(params[:q]).limit(limit)
end
```
- Effort: Quick (<1h)

**P2 - Important**

- Consider adding cursor-based pagination for deep result sets
- Search index should be async; current sync approach will slow writes at scale
- Add request_id to all search logs for debugging slow queries

**P3 - Minor**

- Add OpenAPI spec for the new endpoint
- Include `total_count` in response for UI pagination
- Add index on `searchable_content` if not present (check with `\d+ table_name`)
- Lowercase search terms for case-insensitive matching

**Trade-off Analysis**

The synchronous indexing is fine for current scale (<10k records). When you hit 100k+, consider:
- Background job for indexing (Sidekiq)
- Dedicated search service (Elasticsearch/Meilisearch)
</response>
</example>
</examples>

## Critical Note

Surface everything. The reader decides what matters for their context.

Make it actionable: clear findings with evidence that can be acted on.

## What Happens Next

Present findings to the user. For findings they choose to act on:

- **Quick fix** (obvious, < 5 min): apply directly with `test-driven-development` + `verification-before-completion`
- **Needs design exploration**: use `brainstorming` to explore the approach
- **Clear scope, multi-step**: create a plan with `writing-plans`, execute with `executing-plans`

For refactoring-focused reviews, also apply the `refactoring` skill.
