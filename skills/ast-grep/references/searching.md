# ast-grep Search Reference

Use this reference when the core skill is not enough for command syntax, debugging, or search examples.

## Command Selection

### Simple patterns: `run --pattern`

Use for simple, single-node matches and quick searches.

```bash
ast-grep run --pattern 'console.log($ARG)' --lang javascript .
ast-grep run --pattern 'class $NAME' --lang python /path/to/project
ast-grep run --pattern 'function $NAME($$$)' --lang javascript --json .
```

### YAML rules: `scan --rule`

Use for relational rules (`inside`, `has`, `precedes`, `follows`) and composite logic (`all`, `any`, `not`).

```bash
ast-grep scan --rule my_rule.yml /path/to/project
ast-grep scan --rule my_rule.yml --json /path/to/project
```

### One-off complex rules: `scan --inline-rules`

```bash
ast-grep scan --inline-rules "id: find-async
language: javascript
rule:
  kind: function_declaration
  has:
    pattern: await \$EXPR
    stopBy: end" /path/to/project
```

When using inline rules in shell commands, escape metavariables (`\$VAR`) or wrap the rule in single quotes.

```bash
ast-grep scan --inline-rules "rule: {pattern: 'console.log(\$ARG)'}" .
ast-grep scan --inline-rules 'rule: {pattern: "console.log($ARG)"}' .
```

## Test Rules with stdin

Test against a small snippet before scanning the codebase.

```bash
echo "const x = await fetch();" | ast-grep scan --inline-rules "id: test
language: javascript
rule:
  pattern: await \$EXPR" --stdin
```

Add `--json` when you need structured output:

```bash
echo "const x = await fetch();" | ast-grep scan --inline-rules "..." --stdin --json
```

## Debug Code Structure

Use `--debug-query` when a pattern or rule does not match.

```bash
ast-grep run --pattern 'async function example() { await fetch(); }' \
  --lang javascript \
  --debug-query=cst
```

Formats:

- `cst`: concrete syntax tree, including punctuation
- `ast`: abstract syntax tree, named nodes only
- `pattern`: how ast-grep interprets your pattern

Examples:

```bash
ast-grep run --pattern 'class User { constructor() {} }' \
  --lang javascript \
  --debug-query=cst

ast-grep run --pattern 'class $NAME { $$$BODY }' \
  --lang javascript \
  --debug-query=pattern
```

## Rule Writing Tips

- Start with `pattern`; move to `kind` only when shape matching needs more precision.
- Use `has`/`inside` for relational constraints.
- Use `all`, `any`, and `not` for composite logic.
- Add `stopBy: end` to relational rules unless you intentionally want early stopping.
- Prefer AST-shape matching over argument-count or positional text patterns.

```yaml
has:
  pattern: await $EXPR
  stopBy: end
```

## Common Searches

### Find functions with specific content

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

### Find code inside a specific context

```bash
ast-grep scan --inline-rules "id: console-in-class
language: javascript
rule:
  pattern: console.log(\$\$\$)
  inside:
    kind: method_definition
    stopBy: end" /path/to/project
```

### Find code missing an expected pattern

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

## Search Gotchas

- If an `sgconfig.yml` exists at the project root, `ast-grep scan` auto-loads rules from configured `ruleDirs`.
- Suppress individual matches with `// ast-grep-ignore` or the language's equivalent comment syntax on the previous line.
- Put narrow branches before broad branches in `any`; ast-grep returns the first successful branch.
- Scope rules with `files` and `ignores` when only some paths apply.

```yaml
files:
  - "app/**/*.rb"
ignores:
  - "test/**"
```
