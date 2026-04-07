---
name: remove-slop
description: Remove AI-generated code slop from the current branch - extra comments, defensive checks, type casts, and style inconsistencies.
allowed-tools: Bash(*), Read(**), Edit(*), Glob(*), Grep(*)
metadata:
  category: workflow
---

# Remove AI Code Slop

## Activation

This skill activates when:
- Before committing code (called by the `semantic-commit` skill)
- User requests code cleanup
- Reviewing AI-generated changes
- User says "remove slop" or "clean up"
- Preparing a PR or code review

## Dependencies

**Invoked by:** `semantic-commit`, `verification-before-completion`

Check the diff against main, and remove all AI generated slop introduced in this branch.

This includes:
- Extra comments that a human wouldn't add or is inconsistent with the rest of the file
- Extra defensive checks or try/catch blocks that are abnormal for that area of the codebase (especially if called by trusted / validated codepaths)
- Casts to any to get around type issues
- Any other style that is inconsistent with the file

Report at the end with only a 1-3 sentence summary of what you changed.

## Detection Patterns

### AI-Style Comments

```bash
# Comments starting with explanatory preambles
rg "// (Note:|TODO:|This |The |We |Here )" --glob "*.{ts,tsx,js,jsx}"

# Obvious narration comments
rg "// (Create|Initialize|Set up|Handle|Process|Check if)" --glob "*.{ts,tsx,js,jsx}"

# Ruby comment variants
rg "# (Note:|TODO:|This |The |We |Here )" --type ruby
```

### Type Safety Violations

```bash
# Direct any casts
rg "as any" --glob "*.{ts,tsx}"

# Double-cast escape hatch
rg "as unknown as" --glob "*.{ts,tsx}"

# Suppression directives
rg "@ts-ignore|@ts-expect-error" --glob "*.{ts,tsx}"
```

### Unnecessary Error Handling

```bash
# Empty catch blocks
ast-grep -p 'catch ($_) { }' -l typescript

# Catch that just rethrows
ast-grep -p 'catch ($ERR) { throw $ERR; }' -l typescript
```

### Defensive Null Checks

```bash
# Excessive optional chaining (3+ in one expression)
rg "\?\.\w+\?\.\w+\?\." --glob "*.{ts,tsx}"

# Fallback to empty object/array
rg "\|\| \{\}|\|\| \[\]" --glob "*.{ts,tsx}"
```

## What NOT to Remove

### Legitimate Error Handling
- Try/catch at public API boundaries (HTTP handlers, CLI entry points)
- Error recovery that does something useful (cleanup, fallback, logging + recovery)

### Justified Comments
- Comments explaining non-obvious business logic
- Comments referencing tickets, specs, or external docs
- TODO comments with ticket numbers

### Necessary Type Assertions
- Type assertions with a comment explaining why
- Third-party library type mismatches (known issues)

### Appropriate Defensive Checks
- Validation at system boundaries (user input, API responses)
- Guards that match surrounding code style
