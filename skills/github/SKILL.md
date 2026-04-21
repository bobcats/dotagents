---
name: github
description: "Interact with GitHub using the `gh` CLI. Use `gh issue`, `gh pr`, `gh run`, and `gh api` for issues, PRs, CI runs, and advanced queries."
origin: https://github.com/mitsuhiko/agent-stuff/blob/main/skills/github/SKILL.md
metadata:
  category: tools
---

# GitHub Skill

Use the `gh` CLI to interact with GitHub. Always specify `--repo owner/repo` when not in a git directory, or use URLs directly.

## Pull Requests

Check CI status on a PR:
```bash
gh pr checks 55 --repo owner/repo
```

List recent workflow runs:
```bash
gh run list --repo owner/repo --limit 10
```

View a run and see which steps failed:
```bash
gh run view <run-id> --repo owner/repo
```

View logs for failed steps only:
```bash
gh run view <run-id> --repo owner/repo --log-failed
```

## Creating PRs (lightweight mechanics)

For polished PR authoring workflow (preflight verification, reviewer-context body structure, and post-create validation), use the `creating-pr` skill.

Before creating a PR, ensure planning/design docs are removed from the branch unless explicitly requested in the PR scope.

**Never use `--body` with inline strings.** Backticks and shell metacharacters in the body get executed by the shell before `gh` sees them. Always write the body to a temp file and use `--body-file`:

```bash
cat > /tmp/pr-body.md << 'EOF'
Description with `backticks` and $variables that won't be interpreted.
EOF
gh pr create --title "feat: add feature" --body-file /tmp/pr-body.md
```

## Stacked PRs (`gh stack`)

Use Stacked PRs when:
- a large change should be reviewed in small, dependent layers
- you already have dependent PRs and need to link them into a stack
- the user explicitly asks for stacked PRs / stacked diffs / `gh stack`

### Verify support first

Before stack operations:

```bash
gh stack --help
```

If `gh stack` is missing, install the extension:

```bash
gh extension install github/gh-stack
```

Even with the extension installed, GitHub Stacked PRs must be enabled for the target repository/account preview. If stack commands fail due to feature availability, stop and report that preview access is required.

### Core commands

Create a new stack:

```bash
gh stack init
```

Adopt existing local branches into a stack:

```bash
gh stack init --adopt branch-1 branch-2 branch-3
```

Add a new layer on top:

```bash
gh stack add feature-next-layer
```

Push and create/update PRs for the stack:

```bash
gh stack submit
```

Link existing PRs/branches into a GitHub stack (bottom -> top):

```bash
gh stack link 101 102 103
# or
gh stack link branch-1 branch-2 branch-3
```

Sync/rebase workflow:

```bash
gh stack rebase
gh stack sync
```

Checkout a stack from an existing PR:

```bash
gh stack checkout 101
```

### Constraints and gotchas

- Stacks are same-repository only (no cross-fork stacks).
- Merges are bottom-up only.
- Linear history is required for merging.
- Reordering/inserting in the middle requires unstack + rebuild.
- `gh stack` does **not** automatically split one giant PR into smaller logical changes.

### Common operational guidance

Existing PRs that should become a stack:
- use `gh stack link <bottom> <...> <top>` in stack order.

Existing branches that should become a stack:
- use `gh stack init --adopt ...` then `gh stack submit`.

One giant PR:
- first split work into smaller logical branch layers, then create/adopt a stack.

## API for Advanced Queries

The `gh api` command is useful for accessing data not available through other subcommands.

Get PR with specific fields:
```bash
gh api repos/owner/repo/pulls/55 --jq '.title, .state, .user.login'
```

## JSON Output

Most commands support `--json` for structured output. You can use `--jq` to filter:

```bash
gh issue list --repo owner/repo --json number,title --jq '.[] | "\(.number): \(.title)"'
```
