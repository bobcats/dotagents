# dotagents

Skills and Pi extensions for AI coding agents.

## Quick Start

```bash
make install
```

First install bootstraps managed install state automatically when the install destinations are empty. Use `FORCE=1` only when bootstrapping over existing files or intentionally overriding local conflicts; it skips conflict checks without deleting unmanaged files.

This builds and installs:
- skills for Claude Code, OpenCode, Pi, and Codex
- Pi subagents
- Pi extensions

## Install Paths

| Agent | Resource | Path |
|-------|----------|------|
| Claude Code | Skills | `~/.claude/skills/` |
| OpenCode, Pi, Codex | Skills | `~/.agents/skills/` |
| Pi | Extensions | `~/.pi/agent/extensions/` |
| Pi | Agents | `~/.pi/agent/agents/` |

## Super Power Skills

These methodology skills improve AI agent effectiveness:

| Skill | Description |
|-------|-------------|
| `brainstorming` | Explore ideas before implementation through collaborative dialogue |
| `writing-plans` | Create detailed implementation plans with bite-sized tasks |
| `executing-plans` | Execute plans task-by-task with verification |
| `test-driven-development` | Write tests first, watch them fail, implement minimally |
| `systematic-debugging` | Find root cause before attempting fixes |
| `verification-before-completion` | Evidence before claims, always |
| `dispatching-parallel-agents` | Run multiple independent investigations concurrently |
| `receiving-code-review` | Technical rigor when implementing feedback |
| `requesting-code-review` | Verify work meets requirements before merging |
| `semantic-commit` | Conventional commits for clear history |
| `ast-grep` | Structural code search and AST-based rule authoring |
| `fetch-ci-build` | Fetch CI build results and diagnose failures across CI providers |

## Commands

| Command | Description |
|---------|-------------|
| `make install` | Build and safely update skills, agents, and Pi extensions |
| `make install FORCE=1` | Bootstrap over non-empty destinations or skip local conflict checks |
| `make build` | Build skills, agents, and Pi extensions to `build/` |
| `make typecheck` | Type-check Pi extensions |
| `make install-skills` | Install skills only |
| `make install-extensions` | Install Pi extensions only |
| `make clean` | Remove all installed artifacts |
| `make help` | Show all available commands |

## Pi Extensions

This repo now ships these first-class Pi extensions:
- `pi-extensions/handoff/`
- `pi-extensions/openai-fast/`
- `pi-extensions/session-query/`

`openai-fast` adds `/fast` for OpenAI priority service-tier requests on configured models.

Install path:
- `~/.pi/agent/extensions/`

## Adding Skills

1. Create `skills/<skill-name>/SKILL.md` with YAML frontmatter
2. Add supporting files to the same directory
3. Run `make install`

## Adding Pi Extensions

1. Create `pi-extensions/<extension-name>/index.ts`
2. Add any supporting files under that directory
3. Run `make install-extensions`
4. Run `pnpm typecheck`
5. Run `pnpm test:ts` when the extension has non-trivial behavior, as `openai-fast` does

See [Agent Skills specification](https://agentskills.io/specification.md) for skill format details.

## Requirements

- Python 3.11+
