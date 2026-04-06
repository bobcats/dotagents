#!/usr/bin/env python3
"""
Build and install custom skills and agents for AI coding agents.

Builds skills from ./skills and agents from ./agents, then installs them for:
- Claude Code (~/.claude/skills)
- OpenCode, Pi, Codex (~/.agents/skills)
- Pi Subagents (~/.pi/agent/agents)

Requires Python 3.11+.
"""

import argparse
import shutil
import sys
import tomllib
from pathlib import Path

if sys.version_info < (3, 11):
    sys.exit("Error: Python 3.11+ required")

# Directories
ROOT = Path(__file__).parent.parent
SKILLS_DIR = ROOT / "skills"
AGENTS_DIR = ROOT / "agents"
BUILD_DIR = ROOT / "build"
CONFIGS_DIR = ROOT / "configs"
GLOBAL_AGENTS_MD = CONFIGS_DIR / "AGENTS.md"
SKILL_OVERRIDES_FILE = ROOT / "skill-overrides.toml"

# Installation paths
HOME = Path.home()
INSTALL_PATHS = {
    "claude": HOME / ".claude" / "skills",
    "unified": HOME / ".agents" / "skills",  # opencode, pi, codex
}
PI_AGENTS_PATH = HOME / ".pi" / "agent" / "agents"


def load_skill_overrides() -> dict[str, dict]:
    """Load per-skill frontmatter overrides from skill-overrides.toml."""
    if not SKILL_OVERRIDES_FILE.exists():
        return {}
    with open(SKILL_OVERRIDES_FILE, "rb") as f:
        return tomllib.load(f)


def apply_frontmatter_overrides(content: str, overrides: dict[str, str]) -> str:
    """Add or replace frontmatter fields based on overrides dict."""
    import re

    if not overrides:
        return content

    frontmatter_pattern = r"^---\s*\n(.*?)\n---"
    match = re.match(frontmatter_pattern, content, re.DOTALL)
    if not match:
        return content

    frontmatter = match.group(1)

    for key, value in overrides.items():
        if isinstance(value, bool):
            yaml_value = "true" if value else "false"
        else:
            yaml_value = str(value)

        field_pattern = rf"^{re.escape(key)}:\s*.*$"
        if re.search(field_pattern, frontmatter, re.MULTILINE):
            frontmatter = re.sub(
                field_pattern, f"{key}: {yaml_value}", frontmatter, flags=re.MULTILINE
            )
        else:
            frontmatter += f"\n{key}: {yaml_value}"

    return content[: match.start(1)] + frontmatter + content[match.end(1) :]


def fix_skill_frontmatter_name(content: str, expected_name: str) -> str:
    """Fix SKILL.md frontmatter `name` to match directory name."""
    import re

    frontmatter_pattern = r"^---\s*\n(.*?)\n---"
    match = re.match(frontmatter_pattern, content, re.DOTALL)
    if not match:
        return content

    frontmatter = match.group(1)
    name_pattern = r"^name:\s*(.+)$"
    name_match = re.search(name_pattern, frontmatter, re.MULTILINE)
    if not name_match:
        return content

    current_name = name_match.group(1).strip().strip("\"'")
    if current_name == expected_name:
        return content

    new_frontmatter = re.sub(
        name_pattern, f"name: {expected_name}", frontmatter, flags=re.MULTILINE
    )
    return content[: match.start(1)] + new_frontmatter + content[match.end(1) :]


def build_skill(name: str, source: Path, overrides: dict[str, dict] | None = None) -> bool:
    """Build a single skill from source directory."""
    skill_md = source / "SKILL.md"
    if not skill_md.exists():
        print(f"    Warning: {source} has no SKILL.md, skipping")
        return False

    raw_content = skill_md.read_text()

    dest = BUILD_DIR / "skills" / name
    dest.mkdir(parents=True, exist_ok=True)

    dest_skill_md = dest / "SKILL.md"
    skill_content = fix_skill_frontmatter_name(raw_content, name)

    # Apply per-skill frontmatter overrides
    if overrides and name in overrides:
        skill_content = apply_frontmatter_overrides(skill_content, overrides[name])

    dest_skill_md.write_text(skill_content)

    for item in source.iterdir():
        if item.name == "SKILL.md":
            continue
        dest_item = dest / item.name
        if item.is_dir():
            shutil.copytree(item, dest_item, dirs_exist_ok=True)
        else:
            shutil.copy(item, dest_item)

    return True


def build_skills() -> None:
    """Build all custom skills from ./skills."""
    print("Building skills...")

    skills_build = BUILD_DIR / "skills"
    if skills_build.exists():
        shutil.rmtree(skills_build)
    skills_build.mkdir(parents=True)

    overrides = load_skill_overrides()
    built = 0
    if SKILLS_DIR.exists():
        for skill_dir in sorted(SKILLS_DIR.iterdir()):
            if not skill_dir.is_dir():
                continue
            if build_skill(skill_dir.name, skill_dir, overrides):
                print(f"  {skill_dir.name}")
                built += 1

    print(f"  Built {built} skills")


def install_skills() -> None:
    """Install built skills to configured agent directories."""
    print("Installing skills...")

    source = BUILD_DIR / "skills"
    if not source.exists():
        print("  No skills built, run 'make build' first")
        return

    for name, dest in INSTALL_PATHS.items():
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True, exist_ok=True)

        count = 0
        for skill_dir in sorted(source.iterdir()):
            if not skill_dir.is_dir():
                continue
            shutil.copytree(skill_dir, dest / skill_dir.name)
            count += 1

        print(f"  {name}: {count} skills -> {dest}")


def build_agents() -> None:
    """Build agent definitions from ./agents."""
    print("Building agents...")

    agents_build = BUILD_DIR / "agents"
    if agents_build.exists():
        shutil.rmtree(agents_build)
    agents_build.mkdir(parents=True)

    built = 0
    if AGENTS_DIR.exists():
        for agent_file in sorted(AGENTS_DIR.iterdir()):
            if not agent_file.is_file() or agent_file.suffix != ".md":
                continue
            shutil.copy(agent_file, agents_build / agent_file.name)
            print(f"  {agent_file.stem}")
            built += 1

    print(f"  Built {built} agents")


def install_agents() -> None:
    """Install built agents to pi-subagents user directory."""
    print("Installing agents...")

    source = BUILD_DIR / "agents"
    if not source.exists():
        print("  No agents built, run 'make build' first")
        return

    PI_AGENTS_PATH.mkdir(parents=True, exist_ok=True)

    count = 0
    for agent_file in sorted(source.iterdir()):
        if not agent_file.is_file() or agent_file.suffix != ".md":
            continue
        shutil.copy(agent_file, PI_AGENTS_PATH / agent_file.name)
        count += 1

    print(f"  pi-subagents: {count} agents -> {PI_AGENTS_PATH}")


def install_global_agents_md() -> None:
    """Install global AGENTS.md for unified agents path."""
    print("Installing global AGENTS.md...")

    if not GLOBAL_AGENTS_MD.exists():
        print("  No AGENTS.md found in configs/, skipping")
        return

    dest = HOME / ".agents" / "AGENTS.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(GLOBAL_AGENTS_MD, dest)
    print(f"  Installed to {dest}")


def clean() -> None:
    """Remove all installed artifacts."""
    print("Cleaning installed artifacts...")

    for path in INSTALL_PATHS.values():
        if path.exists():
            shutil.rmtree(path)
            print(f"  Removed {path}")

    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
        print("  Removed build directory")

    # Clean installed agents (only those we manage)
    if PI_AGENTS_PATH.exists() and AGENTS_DIR.exists():
        for agent_file in AGENTS_DIR.iterdir():
            if not agent_file.is_file() or agent_file.suffix != ".md":
                continue
            installed = PI_AGENTS_PATH / agent_file.name
            if installed.exists():
                installed.unlink()
                print(f"  Removed {installed}")

    agents_md_path = HOME / ".agents" / "AGENTS.md"
    if agents_md_path.exists():
        agents_md_path.unlink()
        print(f"  Removed {agents_md_path}")

    print("  Done")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build and install AI agent skills")
    parser.add_argument(
        "command",
        choices=["build", "install", "install-skills", "clean"],
        help="Command to run",
    )
    args = parser.parse_args()

    if args.command == "build":
        build_skills()
        build_agents()
    elif args.command == "install":
        build_skills()
        build_agents()
        install_skills()
        install_agents()
        install_global_agents_md()
        print("\nAll done!")
    elif args.command == "install-skills":
        build_skills()
        install_skills()
    elif args.command == "clean":
        clean()


if __name__ == "__main__":
    main()
