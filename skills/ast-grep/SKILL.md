---
name: ast-grep
description: "Structural code search and rewriting using AST patterns. Use when you need to find or change code based on syntax/shape rather than plain text, especially across multiple files or when surrounding context matters."
metadata:
  category: tools
---

# ast-grep Code Search & Rewrite

## Overview

ast-grep matches parsed syntax trees, so use it when code structure matters more than exact text.

## When to Use This Skill

Use this skill when:
- You need to find code by syntactic shape, not just matching text.
- You need to change repeated code patterns across one or more files.
- The surrounding context determines whether a match is valid, e.g. only matching one struct/call/component shape.
- You need more precision than grep/regex can comfortably provide.

## General Workflow

1. **Clarify the target shape** — language, code shape, include/exclude cases, and whether this is search-only or rewrite.
2. **Create a tiny fixture** — write representative matching and non-matching examples before scanning the real codebase.
3. **Start with the simplest pattern** — use `ast-grep run --pattern` first; move to YAML rules only when you need `has`, `inside`, `all`, `any`, or `not`.
4. **Test before broad search** — verify the fixture matches exactly what you expect.
5. **Search the codebase** — run the rule on the smallest relevant path, then widen.
6. **For rewrites, follow the rewrite workflow below** — dry-run first, inspect the diff, apply, then format.

## Rewriting Workflow

Use rewrites when you need to modify repeated code shapes.

1. **Capture context with named metavariables** — use names like `$$$BEFORE`, `$$$AFTER`, or `$$$ARGS`; anonymous `$$$` cannot be reused safely in rewrites.
2. **Dry-run first** — omit `--update-all` and inspect the diff.
3. **Apply only after the preview is correct** — add `--update-all`.
4. **Format after applying** — ast-grep may preserve awkward spacing.

```bash
ast-grep run \
  --pattern 'User { $$$BEFORE, state_type: $VAL, $$$AFTER }' \
  --rewrite 'User { $$$BEFORE, $$$AFTER }' \
  --lang rust /path/to/project

ast-grep run --pattern '...' --rewrite '...' --lang rust --update-all /path/to/project
cargo fmt --all
```

Load `references/rewrites.md` for rewrite patterns and safety gotchas.

## Search Commands

- `ast-grep run --pattern ... --lang <lang> <path>` for simple structural patterns.
- `ast-grep scan --rule rule.yml <path>` for YAML rules with relational or composite logic.
- `ast-grep scan --inline-rules "..." <path>` for one-off complex rules.
- `--debug-query=cst|ast|pattern` when a rule does not match.

Load `references/searching.md` for command recipes, search examples, and rule debugging.
Load `references/rule_reference.md` for detailed rule syntax.

## Key Gotchas

- Add `stopBy: end` to relational rules (`inside`, `has`) unless you intentionally want early stopping.
- In shell inline rules, escape metavariables (`\$VAR`) or use single quotes.
- In rewrites, use named metavariables like `$$$ARGS`; anonymous `$$$` cannot be back-referenced safely.
- Rewrites apply to every match. Scope tightly, dry-run first, and inspect the diff before `--update-all`.

## References

Do not load reference files by default; open them only when command syntax, examples, or rule details are needed.

- `references/searching.md` — command recipes, search examples, and debugging.
- `references/rewrites.md` — rewrite patterns and safety gotchas.
- `references/rule_reference.md` — detailed rule syntax.
