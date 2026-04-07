---
name: sentry-issue
description: "Fetch and analyze Sentry issues, events, transactions, and logs. Use when given a Sentry issue URL, investigating errors by time window, searching logs, or listing unresolved issues."
origin: https://github.com/mitsuhiko/agent-stuff/blob/main/skills/sentry/SKILL.md
disable-model-invocation: true
metadata:
  category: tools
---

# Sentry Issue Investigation

Fetch and debug Sentry exceptions with a repeatable CLI workflow. Supports URL-based issue investigation, time-window event search, log search, and issue listing.

**Auth:** Uses token from `~/.sentryclirc`. Run `sentry-cli login` if missing.

**Execution path:** Commands are relative to this skill's directory. Run from `{baseDir}` or prefix commands with `{baseDir}/`.

## Quick Reference

| Task | Command |
|------|---------|
| Get issue from URL | Parse URL, then `./scripts/fetch-issue.js <issue-id-or-url> --latest` |
| Find errors on a date | `./scripts/search-events.js --org X --start 2025-12-23T15:00:00 --level error` |
| List open issues | `./scripts/list-issues.js --org X --status unresolved` |
| Get event details | `./scripts/fetch-event.js <event-id> --org X --project Y` |
| Search logs | `./scripts/search-logs.js --org X --project Y "level:error"` |

---

## Workflow 1: Investigate a Sentry Issue URL

### URL Parsing

Given:
`https://buildrtech.sentry.io/issues/7261708580/?environment=demo&project=4510025524707328`

Extract:
- org slug: `buildrtech`
- issue id: `7261708580`
- project id: `4510025524707328`
- environment: `demo` (if present)

### Steps

1. **Verify auth:**
   ```bash
   sentry-cli info
   ```

2. **Fetch issue with latest event:**
   ```bash
   ./scripts/fetch-issue.js <issue-id-or-url> --latest
   # Also accepts: https://sentry.io/organizations/myorg/issues/123/
   # Also accepts: MYPROJ-123 --org myorg
   ```

3. **Drill into specific events if needed:**
   ```bash
   ./scripts/fetch-event.js <event-id> --org <org> --project <project> --breadcrumbs
   ```

### What to Extract

Always report:
- Issue title/type/message
- Culprit (controller/service/method)
- First/last seen, count, status
- Top in-app stack frames (file + line)
- Request/job context (route, params, identifiers)
- Environment, release, user info, tags
- Recurrence pattern

### Root Cause Analysis

Before proposing fixes:
1. Confirm exact throw site from in-app frame
2. Trace caller chain in local code
3. Match stacktrace behavior to request parameters
4. Identify whether failure is expected business condition vs true system fault
5. Propose fix at the boundary where error should be handled

---

## Workflow 2: What went wrong at this time?

Find events around a specific timestamp:

```bash
# Find all events in a 2-hour window
./scripts/search-events.js --org myorg --project backend \
  --start 2025-12-23T15:00:00 --end 2025-12-23T17:00:00

# Filter to just errors
./scripts/search-events.js --org myorg --start 2025-12-23T15:00:00 \
  --level error

# Find a specific transaction type
./scripts/search-events.js --org myorg --start 2025-12-23T15:00:00 \
  --transaction process-incoming-email

# Find by tag
./scripts/search-events.js --org myorg --tag thread_id:th_abc123
```

**Time Range Options:**
- `--period, -t <period>` — Relative time (24h, 7d, 14d)
- `--start <datetime>` — ISO 8601 start time
- `--end <datetime>` — ISO 8601 end time

**Filter Options:**
- `--org, -o <org>` — Organization slug (required)
- `--project, -p <project>` — Project slug or ID
- `--query, -q <query>` — Discover search query
- `--transaction <name>` — Transaction name filter
- `--tag <key:value>` — Tag filter (repeatable)
- `--level <level>` — Level filter (error, warning, info)
- `--limit, -n <n>` — Max results (default: 25, max: 100)

---

## Workflow 3: What errors have occurred recently?

```bash
# List unresolved errors from last 24 hours
./scripts/list-issues.js --org myorg --status unresolved --level error --period 24h

# Find high-frequency issues
./scripts/list-issues.js --org myorg --query "times_seen:>50" --sort freq

# Issues affecting users
./scripts/list-issues.js --org myorg --query "is:unresolved has:user" --sort user
```

**Options:**
- `--org, -o <org>` — Organization slug (required)
- `--project, -p <project>` — Project slug (repeatable)
- `--query, -q <query>` — Issue search query
- `--status <status>` — unresolved, resolved, ignored
- `--level <level>` — error, warning, info, fatal
- `--period, -t <period>` — Time period (default: 14d)
- `--sort <sort>` — date, new, priority, freq, user

---

## Workflow 4: Search Logs

```bash
./scripts/search-logs.js --org myorg --project backend "level:error"

# Also accepts Sentry URLs directly
./scripts/search-logs.js "https://myorg.sentry.io/explore/logs/?project=123&statsPeriod=7d"
```

**Query Syntax:**
```
level:error              Filter by level
message:*timeout*        Search message text with wildcards
trace:abc123             Filter by trace ID
```

---

## Debugging Tips

1. **Start broad, then narrow:** Use `search-events.js` with a time range first, then drill into specific events
2. **Use breadcrumbs:** `fetch-event.js --breadcrumbs` shows the full history before an error
3. **Look for patterns:** `list-issues.js --sort freq` finds frequently occurring problems
4. **Correlate with tags:** Custom tags like `thread_id`, `user_id`, `request_id` help connect events
5. **Check related events:** If you find one event, look for others with the same transaction or trace ID

## Fallback: curl with token

If the scripts fail, extract the token and use curl directly:

```bash
TOKEN=$(rg '^token=' ~/.sentryclirc | head -n1 | cut -d'=' -f2-)

# Issue metadata
curl -sS -H "Authorization: Bearer $TOKEN" \
  "https://sentry.io/api/0/issues/<issue_id>/"

# Latest event
curl -sS -H "Authorization: Bearer $TOKEN" \
  "https://sentry.io/api/0/issues/<issue_id>/events/latest/"
```
