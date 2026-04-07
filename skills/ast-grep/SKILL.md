---
name: ast-grep
description: "Structural code search AND rewriting using AST patterns. Use when: (1) finding code by structure rather than text, (2) bulk code transformations across many files — adding/removing/renaming fields in struct literals, function arguments, imports, etc. Prefer over sed/perl/regex for any multi-file code modification where the change depends on surrounding structure (e.g., 'remove field X from struct Foo but not struct Bar')."
metadata:
  category: tools
---

# ast-grep Code Search & Rewrite

## Overview

This skill helps write ast-grep rules for structural code search **and bulk code transformation**. ast-grep uses Abstract Syntax Tree (AST) patterns to match code based on its structure rather than just text, enabling powerful and precise code search and rewriting across large codebases.

## When to Use This Skill

Use this skill when:
- **Bulk code transformation** — adding, removing, or modifying fields/arguments/imports across many files where the change depends on structural context (e.g., "add `parent: None` to all `Issue { ... }` literals but not `User { ... }` literals")
- **You're about to reach for `sed`, `perl -pe`, or a Python script for multi-file code changes** — ast-grep is almost always safer because it distinguishes struct types, function names, and nesting
- Searching for code patterns using structural matching (e.g., "find all async functions that don't have error handling")
- Locating specific language constructs (e.g., "find all function calls with specific parameters")
- Performing complex code queries that traditional text search cannot handle

## General Workflow

Follow this process to help users write effective ast-grep rules:

### Step 1: Understand the Query

Clearly understand what the user wants to find. Ask clarifying questions if needed:
- What specific code pattern or structure are they looking for?
- Which programming language?
- Are there specific edge cases or variations to consider?
- What should be included or excluded from matches?

### Step 2: Create Example Code

Write a simple code snippet that represents what the user wants to match. Save this to a temporary file for testing.

**Example:**
If searching for "async functions that use await", create a test file:

```javascript
// test_example.js
async function example() {
  const result = await fetchData();
  return result;
}
```

### Step 3: Write the ast-grep Rule

Translate the pattern into an ast-grep rule. Start simple and add complexity as needed.

**Key principles:**
- Always use `stopBy: end` for relational rules (`inside`, `has`) to ensure search goes to the end of the direction
- Use `pattern` for simple structures
- Use `kind` with `has`/`inside` for complex structures
- Break complex queries into smaller sub-rules using `all`, `any`, or `not`

**Example rule file (test_rule.yml):**
```yaml
id: async-with-await
language: javascript
rule:
  kind: function_declaration
  has:
    pattern: await $EXPR
    stopBy: end
```

See `references/rule_reference.md` for comprehensive rule documentation.

### Step 4: Test the Rule

Use ast-grep CLI to verify the rule matches the example code. There are two main approaches:

**Option A: Test with inline rules (for quick iterations)**
```bash
echo "async function test() { await fetch(); }" | ast-grep scan --inline-rules "id: test
language: javascript
rule:
  kind: function_declaration
  has:
    pattern: await \$EXPR
    stopBy: end" --stdin
```

**Option B: Test with rule files (recommended for complex rules)**
```bash
ast-grep scan --rule test_rule.yml test_example.js
```

**Debugging if no matches:**
1. Simplify the rule (remove sub-rules)
2. Add `stopBy: end` to relational rules if not present
3. Use `--debug-query` to understand the AST structure (see below)
4. Check if `kind` values are correct for the language

### Step 5: Search the Codebase

Once the rule matches the example code correctly, search the actual codebase:

**For simple pattern searches:**
```bash
ast-grep run --pattern 'console.log($ARG)' --lang javascript /path/to/project
```

**For complex rule-based searches:**
```bash
ast-grep scan --rule my_rule.yml /path/to/project
```

**For inline rules (without creating files):**
```bash
ast-grep scan --inline-rules "id: my-rule
language: javascript
rule:
  pattern: \$PATTERN" /path/to/project
```

## Rewriting Workflow (Bulk Code Transformation)

When the task is **modifying** code across many files (not just finding it), use `--rewrite` + `--update-all`:

### Step 1: Write the pattern and rewrite

Use named multi-metavariables (`$$$BEFORE`, `$$$AFTER`) to capture surrounding context:

```bash
# Remove a field from a specific struct type (leaves other structs untouched)
ast-grep run \
  --pattern 'User { $$$BEFORE, state_type: $VAL, $$$AFTER }' \
  --rewrite 'User { $$$BEFORE, $$$AFTER }' \
  --lang rust /path/to/project
```

```bash
# Add a field before an existing field
ast-grep run \
  --pattern 'Issue { $$$BEFORE, comments: $VAL }' \
  --rewrite 'Issue { $$$BEFORE, parent: None, children: None, comments: $VAL }' \
  --lang rust /path/to/project
```

### Step 2: Dry-run first (no `--update-all`)

Without `--update-all`, ast-grep shows a diff preview. Verify the changes look correct.

### Step 3: Apply and format

```bash
ast-grep run --pattern '...' --rewrite '...' --lang rust --update-all /path/to/project
# ast-grep rewriting may mangle formatting — always run the language formatter after
cargo fmt --all    # Rust
prettier --write . # JS/TS
```

**Why ast-grep over sed/perl/regex for bulk code changes:**
- Struct-type-aware: `User { ... }` won't match `IssueState { ... }` even if they share field names
- Handles multi-line patterns naturally (no `perl -0pe` hacks)
- Preserves unmatched code exactly (no accidental edits to nearby lines)
- `--update-all` is idempotent — safe to re-run

## ast-grep CLI Commands

### Inspect Code Structure (--debug-query)

Dump the AST structure to understand how code is parsed:

```bash
ast-grep run --pattern 'async function example() { await fetch(); }' \
  --lang javascript \
  --debug-query=cst
```

**Available formats:**
- `cst`: Concrete Syntax Tree (shows all nodes including punctuation)
- `ast`: Abstract Syntax Tree (shows only named nodes)
- `pattern`: Shows how ast-grep interprets your pattern

**Use this to:**
- Find the correct `kind` values for nodes
- Understand the structure of code you want to match
- Debug why patterns aren't matching

**Example:**
```bash
# See the structure of your target code
ast-grep run --pattern 'class User { constructor() {} }' \
  --lang javascript \
  --debug-query=cst

# See how ast-grep interprets your pattern
ast-grep run --pattern 'class $NAME { $$$BODY }' \
  --lang javascript \
  --debug-query=pattern
```

### Test Rules (scan with --stdin)

Test a rule against code snippet without creating files:

```bash
echo "const x = await fetch();" | ast-grep scan --inline-rules "id: test
language: javascript
rule:
  pattern: await \$EXPR" --stdin
```

**Add --json for structured output:**
```bash
echo "const x = await fetch();" | ast-grep scan --inline-rules "..." --stdin --json
```

### Search with Patterns (run)

Simple pattern-based search for single AST node matches:

```bash
# Basic pattern search
ast-grep run --pattern 'console.log($ARG)' --lang javascript .

# Search specific files
ast-grep run --pattern 'class $NAME' --lang python /path/to/project

# JSON output for programmatic use
ast-grep run --pattern 'function $NAME($$$)' --lang javascript --json .
```

**When to use:**
- Simple, single-node matches
- Quick searches without complex logic
- When you don't need relational rules (inside/has)

### Search with Rules (scan)

YAML rule-based search for complex structural queries:

```bash
# With rule file
ast-grep scan --rule my_rule.yml /path/to/project

# With inline rules
ast-grep scan --inline-rules "id: find-async
language: javascript
rule:
  kind: function_declaration
  has:
    pattern: await \$EXPR
    stopBy: end" /path/to/project

# JSON output
ast-grep scan --rule my_rule.yml --json /path/to/project
```

**When to use:**
- Complex structural searches
- Relational rules (inside, has, precedes, follows)
- Composite logic (all, any, not)
- When you need the power of full YAML rules

**Tip:** For relational rules (inside/has), always add `stopBy: end` to ensure complete traversal.

## Tips for Writing Effective Rules

### Always Use stopBy: end

For relational rules, always use `stopBy: end` unless there's a specific reason not to:

```yaml
has:
  pattern: await $EXPR
  stopBy: end
```

This ensures the search traverses the entire subtree rather than stopping at the first non-matching node.

### Start Simple, Then Add Complexity

Begin with the simplest rule that could work:
1. Try a `pattern` first
2. If that doesn't work, try `kind` to match the node type
3. Add relational rules (`has`, `inside`) as needed
4. Combine with composite rules (`all`, `any`, `not`) for complex logic

### Use the Right Rule Type

- **Pattern**: For simple, direct code matching (e.g., `console.log($ARG)`)
- **Kind + Relational**: For complex structures (e.g., "function containing await")
- **Composite**: For logical combinations (e.g., "function with await but not in try-catch")

### Debug with AST Inspection

When rules don't match:
1. Use `--debug-query=cst` to see the actual AST structure
2. Check if metavariables are being detected correctly
3. Verify the node `kind` matches what you expect
4. Ensure relational rules are searching in the right direction

### Escaping in Inline Rules

When using `--inline-rules`, escape metavariables in shell commands:
- Use `\$VAR` instead of `$VAR` (shell interprets `$` as variable)
- Or use single quotes: `'$VAR'` works in most shells

**Example:**
```bash
# Correct: escaped $
ast-grep scan --inline-rules "rule: {pattern: 'console.log(\$ARG)'}" .

# Or use single quotes
ast-grep scan --inline-rules 'rule: {pattern: "console.log($ARG)"}' .
```

### Name Multi-Metavariables in Rewrites

Anonymous `$$$` cannot be back-referenced in `--rewrite` — it emits the literal string `$$$`, corrupting code. Always use a **named** multi-metavariable like `$$$ARGS`.

```bash
# BROKEN: anonymous $$$ emits literally
ast-grep run --pattern 'TodoOrDie($$$, by: "old")' \
  --rewrite 'TodoOrDie($$$, by: "new")' --lang ruby --update-all .

# CORRECT: named $$$ARGS substitutes properly
ast-grep run --pattern 'TodoOrDie($$$ARGS, by: "old")' \
  --rewrite 'TodoOrDie($$$ARGS, by: "new")' --lang ruby --update-all .
```

Same applies to single metavariables — `$` won't back-reference, but `$NAME` will.

## Common Use Cases

### Find Functions with Specific Content

Find async functions that use await:
```bash
ast-grep scan --inline-rules "id: async-await
language: javascript
rule:
  all:
    - kind: function_declaration
    - has:
        pattern: await \$EXPR
        stopBy: end" /path/to/project
```

### Find Code Inside Specific Contexts

Find console.log inside class methods:
```bash
ast-grep scan --inline-rules "id: console-in-class
language: javascript
rule:
  pattern: console.log(\$\$\$)
  inside:
    kind: method_definition
    stopBy: end" /path/to/project
```

### Find Code Missing Expected Patterns

Find async functions without try-catch:
```bash
ast-grep scan --inline-rules "id: async-no-trycatch
language: javascript
rule:
  all:
    - kind: function_declaration
    - has:
        pattern: await \$EXPR
        stopBy: end
    - not:
        has:
          pattern: try { \$\$\$ } catch (\$E) { \$\$\$ }
          stopBy: end" /path/to/project
```

## Gotchas

### `fix` applies to ALL matches

A rule's `fix` field rewrites every match, not just the first. If you intend a targeted fix, scope the rule tightly with `inside`/`has` constraints or use `--interactive` to confirm each change.

### `sgconfig.yml` auto-discovers from project root

If an `sgconfig.yml` exists at the project root, `ast-grep scan` automatically loads rules from its configured `ruleDirs`. You don't need to pass `--rule` explicitly for project rules — just run `ast-grep scan <paths>`.

### Native suppression comments

ast-grep supports inline suppression: `// ast-grep-ignore` (or the language's comment syntax) on the line before a match suppresses that specific instance. No config file changes needed.

### Prefer AST-shape matching over arity patterns

Match the structural shape of code (node `kind` + `has`/`inside`) rather than trying to match by argument count or positional patterns. AST-shape rules are more robust to formatting and whitespace changes.

### Split fixable and unfixable shapes into separate rules

A single rule can't conditionally apply a `fix` to some matches but not others. If a pattern has both auto-fixable and unfixable shapes, write two rules: one with `fix` for the safe cases, one lint-only for the rest.

### Order specific branches before broad in `any`

ast-grep evaluates `any` branches in order and matches the first that succeeds. Put narrow/specific patterns before catch-all patterns, or the broad branch will swallow matches the specific one should have caught.

### `files`/`ignores` for per-rule scoping

Individual rules can specify which files they apply to directly in the YAML — no wrapper script needed:

```yaml
files:
  - "app/**/*.rb"
ignores:
  - "test/**"
```

## Resources

### references/
Contains detailed documentation for ast-grep rule syntax:
- `rule_reference.md`: Comprehensive ast-grep rule documentation covering atomic rules, relational rules, composite rules, and metavariables

Load these references when detailed rule syntax information is needed.
