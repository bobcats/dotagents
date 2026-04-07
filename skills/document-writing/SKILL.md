---
name: document-writing
description: Write README files, API docs, architecture docs, and user guides. Verification-driven - all code examples must be tested.
metadata:
  category: workflow
---

This skill guides the creation of accurate, comprehensive, and genuinely useful documentation. Documentation must obsess over clarity, structure, and completeness while ensuring technical correctness.

## Activation

Invoke this skill when:
- User requests README, API docs, architecture docs, or user guides
- User asks to "document" a feature, API, or codebase
- Creating getting-started guides or tutorials
- Writing CHANGELOG or CONTRIBUTING files
- User says "write docs for..."

## DOCUMENTATION TYPES

| Type | Structure | Focus |
|------|-----------|-------|
| README | Title, Description, Installation, Usage, API, Contributing | Getting started quickly |
| API Docs | Endpoint, Method, Parameters, Request/Response, Errors | Every detail for integration |
| Architecture | Overview, Components, Data Flow, Dependencies, Decisions | Why things are built this way |
| User Guides | Introduction, Prerequisites, Tutorials, Troubleshooting | Guiding users to success |

## Output Locations

**Always check existing project structure first.** Respect conventions already in place.

| Doc Type | Default Location | Notes |
|----------|------------------|-------|
| README | `./README.md` | Project root, always |
| API Docs | `./docs/api/` | Or `./api-docs/` if exists |
| Architecture | `./docs/architecture/` | Or `./docs/design/` if exists |
| User Guides | `./docs/guides/` | Or `./docs/` if flat structure |
| Changelog | `./CHANGELOG.md` | Project root |
| Contributing | `./CONTRIBUTING.md` | Project root |

**Before writing:**
1. Run `ls -la` and `ls docs/` to see existing structure
2. Check for existing documentation patterns (e.g., `docs/` vs `doc/`)
3. Follow existing conventions over defaults

## Verification Methods

| Doc Type | Verification Approach |
|----------|----------------------|
| README | Run every installation command. Execute all code examples. Verify output matches. |
| API Docs | `curl` or `httpie` against running server. Compare actual responses to documented responses. |
| Architecture | Cross-reference diagrams with actual code structure using `Glob` and `Read`. Verify component names exist. |
| User Guides | Follow tutorial end-to-end from scratch. Every step must succeed. |
| Changelog | Verify mentioned commits/PRs exist via `git log` or `gh pr view`. |
| Code Examples | Copy-paste into REPL or test file. Must run without modification. |

**Verification is not optional.** If you cannot verify (e.g., no running server for API docs), document what was verified and what requires manual verification.

## VERIFICATION (MANDATORY)

**Documentation without verification is potentially harmful.**

- Verify all code examples actually work
- Test installation/setup instructions
- Check all links (internal and external)
- Verify API request/response examples against actual API
- If verification fails: Fix documentation and re-verify

**The task is INCOMPLETE until documentation is verified. Period.**

## QUALITY CHECKLIST

### Clarity
- [ ] Can a new developer understand this?
- [ ] Are technical terms explained?
- [ ] Is the structure logical and scannable?

### Completeness
- [ ] All features documented?
- [ ] All parameters explained?
- [ ] All error cases covered?

### Accuracy
- [ ] Code examples tested?
- [ ] API responses verified?
- [ ] Version numbers current?

### Consistency
- [ ] Terminology consistent?
- [ ] Formatting consistent?
- [ ] Style matches existing docs?

## STYLE GUIDE

### Tone
- Professional but approachable
- Direct and confident
- Active voice
- No filler words or hedging

For prose quality, apply the `writing-clearly-and-concisely` skill — active voice, positive form, concrete language, omit needless words.

### Formatting
- Headers for scanability
- Code blocks with syntax highlighting
- Tables for structured data
- Mermaid diagrams where helpful

### Code Examples
- Start simple, build complexity
- Include both success and error cases
- Show complete, runnable examples
- Add comments explaining key parts

## Examples

<examples>
<example>
<request>Write a README for a Ruby gem called `retry_block` that provides a simple DSL for retrying operations with exponential backoff.</request>
<response>
# retry_block

A minimal Ruby DSL for retrying operations with exponential backoff.

## Installation

```ruby
gem 'retry_block'
```

## Usage

### Basic Retry

```ruby
require 'retry_block'

RetryBlock.retry(max_attempts: 3) do
  response = HTTParty.get('https://api.example.com/data')
  raise "API error" unless response.success?
  response.parsed_response
end
```

### Exponential Backoff

```ruby
RetryBlock.retry(
  max_attempts: 5,
  base_delay: 1,      # Start with 1 second
  max_delay: 30,      # Cap at 30 seconds
  exponential: true   # 1s, 2s, 4s, 8s, 16s (capped at 30s)
) do
  ExternalService.call
end
```

### Retry Specific Exceptions

```ruby
RetryBlock.retry(
  max_attempts: 3,
  rescue_only: [Net::TimeoutError, Errno::ECONNREFUSED]
) do
  # Only retries on network errors, not on ArgumentError etc.
  api_client.fetch_user(user_id)
end
```

### With Callbacks

```ruby
RetryBlock.retry(
  max_attempts: 3,
  on_retry: ->(attempt, error, delay) {
    Rails.logger.warn "Attempt #{attempt} failed: #{error.message}. Retrying in #{delay}s"
  }
) do
  payment_gateway.charge(amount)
end
```

## API Reference

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `max_attempts` | Integer | 3 | Maximum retry attempts |
| `base_delay` | Float | 1.0 | Initial delay in seconds |
| `max_delay` | Float | nil | Maximum delay cap |
| `exponential` | Boolean | true | Use exponential backoff |
| `jitter` | Boolean | true | Add randomness to delay |
| `rescue_only` | Array | [StandardError] | Exceptions to retry on |
| `on_retry` | Proc | nil | Callback on each retry |

## License

MIT

---

**Verification completed**:
- [x] Code examples tested with mock implementations
- [x] API table matches implementation
</response>
</example>
</examples>
