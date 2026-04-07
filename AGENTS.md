# AGENTS.md

This file provides guidance for AI assistants working with this codebase.

## Project Overview

This repository manages reusable skills and Pi extensions for AI coding agents including:
- **Claude Code** (Anthropic)
- **OpenCode**
- **Pi Coding Agent** (badlogic)
- **Codex CLI** (OpenAI)

Skills are specialized instruction sets that guide AI agents through specific tasks.

## Install Paths

| Agent | Resource | Path |
|-------|----------|------|
| Claude Code | Skills | `~/.claude/skills/` |
| OpenCode, Pi, Codex | Skills | `~/.agents/skills/` |
| Pi | Extensions | `~/.pi/agent/extensions/` |
| Pi | Agents | `~/.pi/agent/agents/` |

## Repository Structure

```
dotagents/
├── skills/                   # Custom skills
│   └── <skill-name>/
│       ├── SKILL.md          # Skill definition (YAML frontmatter + markdown)
│       └── <additional files>
├── pi-extensions/            # Custom Pi extensions
│   └── <extension-name>/
│       ├── index.ts          # Extension entrypoint
│       └── <additional files>
├── agents/                   # Pi subagent definitions
├── configs/
│   └── AGENTS.md             # Global AGENTS.md installed to ~/.agents/
├── scripts/
│   └── build.py              # Python build system (requires Python 3.11+)
├── build/                    # Generated during build (gitignored)
├── tests/                    # Repo tests
├── Makefile                  # Build automation
└── README.md                 # User documentation
```

## Key Concepts

### Skills
Skills follow the [Agent Skills specification](https://agentskills.io/specification.md). When creating or modifying skills, fetch the latest specification for current format requirements.

## Development Workflow

### Setup
```bash
make install
```

### Common Commands
| Command | Description |
|---------|-------------|
| `make install` | Build and install skills, agents, and Pi extensions |
| `make build` | Build skills, agents, and Pi extensions to `build/` |
| `make typecheck` | Type-check Pi extensions |
| `make install-skills` | Install skills only |
| `make install-extensions` | Install Pi extensions only |
| `make clean` | Remove all installed artifacts |

## Code Conventions

### Skills (SKILL.md)
- Follow the [Agent Skills specification](https://agentskills.io/specification.md)
- Include workflow diagrams (graphviz dot format) for complex processes
- Document prerequisites, step-by-step processes, and common mistakes

### Pi Extensions (TypeScript)
- Follow the latest Pi extensions documentation
- Put each extension in `pi-extensions/<extension-name>/`
- Use `index.ts` as the entrypoint
- Add focused tests when behavior is non-trivial
- Run `pnpm typecheck` after changes

### Skill Scripts (Python)
Use [uv inline script metadata](https://docs.astral.sh/uv/guides/scripts/) for dependency management.

## Adding New Content

### Adding a Custom Skill
1. Fetch the [Agent Skills specification](https://agentskills.io/specification.md)
2. Create `skills/<skill-name>/SKILL.md` following the specification
3. Add any supporting files to the same directory
4. Run `make install` to build and install

### Adding a Pi Extension
1. Fetch the Pi extensions documentation
2. Create `pi-extensions/<extension-name>/index.ts`
3. Add any supporting files in that directory
4. Run `make install-extensions`
5. Run `pnpm typecheck`
