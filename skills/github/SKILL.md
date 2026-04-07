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

## Creating PRs

Before creating a PR, ensure planning/design docs are removed from the branch unless explicitly requested in the PR scope.

**Never use `--body` with inline strings.** Backticks and shell metacharacters in the body get executed by the shell before `gh` sees them. Always write the body to a temp file and use `--body-file`:

```bash
cat > /tmp/pr-body.md << 'EOF'
Description with `backticks` and $variables that won't be interpreted.
EOF
gh pr create --title "feat: add feature" --body-file /tmp/pr-body.md
```

## API for Advanced Queries

The `gh api` command is useful for accessing data not available through other subcommands.

Get PR with specific fields:
```bash
gh api repos/owner/repo/pulls/55 --jq '.title, .state, .user.login'
```

## JSON Output

Most commands support `--json` for structured output.  You can use `--jq` to filter:

```bash
gh issue list --repo owner/repo --json number,title --jq '.[] | "\(.number): \(.title)"'
```
