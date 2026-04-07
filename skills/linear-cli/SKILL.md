---
name: linear-cli
description: Manage Linear issues, projects, teams, and cycles using the linear-cli tool. Use when the user mentions Linear, linear-cli, or references Linear issue identifiers like ENG-123.
allowed-tools: Bash(linear-cli:*)
metadata:
  category: tools
---

# Linear CLI

Interact with Linear via `linear-cli` — a fast, LLM-friendly Rust CLI. JSON output by default when piped, no interactive prompts, all operations work with flags alone.

## Authentication

```bash
# Interactive login (prompts for token)
linear-cli auth login

# Non-interactive (reads from stdin)
echo "lin_api_xxxxx" | linear-cli auth login --with-token

# Check status
linear-cli auth status

# Print raw token (for scripting)
linear-cli auth token

# Logout
linear-cli auth logout
```

**Token precedence**: `LINEAR_TOKEN` env var → `LINEAR_API_TOKEN` env var → system keyring.

Headless environments (Docker, CI, SSH) may not have keyring access — use environment variables instead.

## Issues

### View and list

```bash
linear-cli issue view ENG-123
linear-cli issue list --assignee @me --limit 10
linear-cli issue list --project "Project Name" --limit 50
linear-cli issue list --project PROJECT-UUID --limit 50
```

### Create

```bash
linear-cli issue create --team ENG --title "Fix login bug"
linear-cli issue create --team ENG --title "Add caching" \
  --description "Implement Redis caching layer" \
  --assignee @me --priority 2 --project my-project --state "In Progress"
```

Flags: `--team` (required), `--title` (required), `--description`, `--assignee` (@me, email, or ID), `--project` (slug or ID), `--state` (name or ID), `--priority` (0=None, 1=Urgent, 2=High, 3=Medium, 4=Low).

### Update

```bash
linear-cli issue update ENG-123 --state "In Progress" --priority 2
linear-cli issue update ENG-123 --assignee @me --title "Updated title"
linear-cli issue update ENG-123 --assignee null  # clear assignee
linear-cli issue update ENG-123 --project null   # clear project
```

### Comments

```bash
linear-cli issue comment add ENG-123 --body "Started investigation"
linear-cli issue comments ENG-123 --limit 20
```

### Delete

```bash
linear-cli issue delete ENG-123
linear-cli issue delete ENG-123 --permanently  # skip 30-day grace period (admin only)
```

### Search issues

```bash
linear-cli issue search "login bug"
linear-cli issue search "caching" --team ENG --include-comments --limit 10
```

Flags: `--team` (boost results from a specific team), `--include-comments`, `--limit` (default 50).

### Lifecycle

```bash
linear-cli issue lifecycle archive ENG-123
linear-cli issue lifecycle unarchive ENG-123
```

### Relations

```bash
linear-cli issue relation link ENG-123 ENG-456
linear-cli issue relation block ENG-123 ENG-456
linear-cli issue relation duplicate ENG-123 ENG-456
```

## Teams

```bash
linear-cli team list
linear-cli team list --limit 25
linear-cli team view TEAM-ID
```

## Projects

```bash
linear-cli project list
linear-cli project list --limit 25
linear-cli project view PROJECT-ID
```

## Cycles

```bash
linear-cli cycle list
linear-cli cycle list --limit 25
linear-cli cycle view CYCLE-ID
linear-cli cycle current              # exit code 2 if no active cycle — not a failure
```

## Search

Semantic search across issues, projects, documents, and initiatives.

```bash
linear-cli search "authentication flow"
linear-cli search "onboarding" --type issue,document --limit 10
```

Flags: `--type` (comma-separated: issue, project, document, initiative), `--limit` (default 50).

This is different from `issue search` — it searches across all entity types, not just issues.

## Workflow States

```bash
linear-cli state list
linear-cli state list --team ENG
```

Use this to discover valid state names before creating or updating issues.

## Labels

```bash
linear-cli label list
linear-cli label list --team ENG
```

## Users

```bash
linear-cli user list
linear-cli user list --limit 100
```

## Output Formats

All commands support: `--json`, `--csv`, `--markdown`, `--table`.

Auto-detects format: JSON when piped (default for agents), table when interactive TTY.

### When to use which format

| Format | Use when |
|--------|----------|
| `--json` | You need to extract or process specific fields. Pipe to `jq`. This is the default when piped — you rarely need the flag explicitly. |
| `--markdown` | You're presenting results directly to the user. Readable, structured, good for chat output. **Use this when showing the user what you found.** |
| `--csv` | Exporting bulk data to a file. |
| `--table` | Never — this is for human terminal use, not agents. |

### Examples

```bash
# Extract data programmatically (auto-JSON when piped)
linear-cli issue list --assignee @me | jq '.[].title'

# Show the user an issue (readable output)
linear-cli issue view ENG-123 --markdown

# Show the user a list of their issues
linear-cli issue list --assignee @me --markdown

# Export to file
linear-cli project list --csv > projects.csv
```

## Creating Issues for the User

**Do not ask for extra details.** Use what the user provided and fill in sensible defaults:

- `--team` — required, always ask or infer from context
- `--description` — write one yourself from context the user provided
- `--priority` — default to `3` (Medium) unless user indicates urgency
- `--assignee`, `--state`, `--project` — only include if user explicitly provides them

## Common Mistakes

- **update uses identifier, not UUID**: `linear-cli issue update ENG-123` takes the human-readable identifier directly — no need to fetch a UUID first.
- **@me shorthand**: Use `--assignee @me` for the current authenticated user. Works in both `list`, `create`, and `update`.
- **Clearing fields**: Pass `null` as the value to clear assignee or project (e.g., `--assignee null`).
- **No interactive prompts**: Every operation is completable with flags alone. Never expect stdin interaction except `auth login` without `--with-token`.
- **`--project` accepts names or UUIDs**: You can use `--project "My Project"` — no need to look up the UUID first. Same applies for `--team` (key or ID) and `--state` (name or ID).
