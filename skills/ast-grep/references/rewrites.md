# ast-grep Rewrite Reference

Use this reference when modifying code with ast-grep rewrites. Rewrites are powerful and broad by default: scope tightly, dry-run first, and format after applying.

## Basic Rewrite Flow

1. Write the narrowest pattern that matches only the intended code shape.
2. Use named metavariables for any captured text reused in the rewrite.
3. Run without `--update-all` and inspect the diff preview.
4. Apply with `--update-all` only after the preview is correct.
5. Run the language formatter.
6. Run tests or a focused verification command.

```bash
ast-grep run --pattern '...' --rewrite '...' --lang rust /path/to/project
ast-grep run --pattern '...' --rewrite '...' --lang rust --update-all /path/to/project
cargo fmt --all
```

## Named Metavariables Are Required for Reuse

Anonymous metavariables cannot be safely back-referenced in rewrites. Use names like `$NAME`, `$$$ARGS`, `$$$BEFORE`, and `$$$AFTER`.

```bash
# Broken: anonymous $$$ may be emitted literally or fail to preserve captured args
ast-grep run --pattern 'TodoOrDie($$$, by: "old")' \
  --rewrite 'TodoOrDie($$$, by: "new")' --lang ruby --update-all .

# Correct: named $$$ARGS can be reused
ast-grep run --pattern 'TodoOrDie($$$ARGS, by: "old")' \
  --rewrite 'TodoOrDie($$$ARGS, by: "new")' --lang ruby --update-all .
```

Same rule for single metavariables: use `$NAME`, not bare `$`.

## Common Rewrite Patterns

### Remove a field from a specific struct shape

```bash
ast-grep run \
  --pattern 'User { $$$BEFORE, state_type: $VAL, $$$AFTER }' \
  --rewrite 'User { $$$BEFORE, $$$AFTER }' \
  --lang rust /path/to/project
```

This matches `User { ... }` specifically rather than every object or struct containing `state_type`.

### Add fields before an existing field

```bash
ast-grep run \
  --pattern 'Issue { $$$BEFORE, comments: $VAL }' \
  --rewrite 'Issue { $$$BEFORE, parent: None, children: None, comments: $VAL }' \
  --lang rust /path/to/project
```

### Rewrite function or method arguments

```bash
ast-grep run \
  --pattern 'fetchUser($ID)' \
  --rewrite 'fetchUser({ id: $ID })' \
  --lang typescript /path/to/project
```

For variable arity, capture the rest explicitly:

```bash
ast-grep run \
  --pattern 'logger.warn($$$ARGS)' \
  --rewrite 'logger.warning($$$ARGS)' \
  --lang javascript /path/to/project
```

## Scope Rewrites Tightly

Rewrites apply to every match. If only some matches are safe, narrow the rule with surrounding context or use interactive confirmation.

```yaml
rule:
  pattern: console.log($$$ARGS)
  inside:
    kind: method_definition
    stopBy: end
```

Useful scoping tools:

- `inside` / `has` with `stopBy: end`
- specific outer shapes like `User { ... }` rather than field-only patterns
- `files` / `ignores` for path-level constraints
- `--interactive` when matches need human confirmation

## `fix` Applies to All Matches

A YAML rule's `fix` rewrites every match. A single rule cannot conditionally apply a fix to some matches but not others.

If a pattern has both safe and unsafe cases, split it:

- one fixable rule scoped to the safe shape
- one lint-only/search rule for the remaining cases

## Why Use ast-grep Instead of Regex for Bulk Rewrites

- It can match syntax shape instead of raw text.
- It distinguishes surrounding constructs such as specific calls, structs, classes, or methods.
- It handles multi-line code without `perl -0pe`-style hacks.
- It preserves unmatched code instead of reconstructing nearby text.
- Dry-run previews make large edits easier to audit before applying.

## Formatting and Verification

ast-grep rewrites may preserve awkward spacing or produce formatting that is syntactically valid but ugly. Always format after applying.

```bash
cargo fmt --all
prettier --write .
ruff format .
gofmt -w .
```

Then run a focused verification command: tests, typecheck, linter, or compiler depending on the project.
