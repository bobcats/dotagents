#!/usr/bin/env python3
"""
Build and install custom skills, agents, and Pi extensions.

Builds assets from:
- ./skills -> build/skills -> agent skill install paths
- ./agents -> build/agents -> ~/.pi/agent/agents
- ./pi-extensions -> build/extensions -> ~/.pi/agent/extensions

Requires Python 3.11+.
"""

import argparse
from collections.abc import Iterable
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass
import fcntl
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Literal

if sys.version_info < (3, 11):
    sys.exit("Error: Python 3.11+ required")

ROOT = Path(__file__).parent.parent
SKILLS_DIR = ROOT / "skills"
AGENTS_DIR = ROOT / "agents"
PI_EXTENSIONS_DIR = ROOT / "pi-extensions"
BUILD_DIR = ROOT / "build"
CONFIGS_DIR = ROOT / "configs"
GLOBAL_AGENTS_MD = CONFIGS_DIR / "AGENTS.md"

HOME = Path.home()
INSTALL_PATHS = {
    "claude": HOME / ".claude" / "skills",
    "unified": HOME / ".agents" / "skills",
}
PI_AGENTS_PATH = HOME / ".pi" / "agent" / "agents"
PI_EXTENSIONS_PATH = HOME / ".pi" / "agent" / "extensions"
STATE_DIR = Path(os.environ.get("XDG_STATE_HOME") or HOME / ".local" / "state") / "dotagents"
MANIFEST_PATH = STATE_DIR / "install-manifest.json"
LOCK_PATH = STATE_DIR / "install.lock"
MANIFEST_VERSION = 1

# Legacy per-root manifests are only used as a clean() fallback for installs made
# before the unified manifest existed.
SKILLS_MANIFEST = ".dotagents-managed-skills"
PI_EXTENSIONS_MANIFEST = ".dotagents-managed-extensions"


class InstallConflict(RuntimeError):
    pass


@dataclass(frozen=True)
class InstallTarget:
    name: str
    source: Path
    destination: Path
    kind: Literal["tree", "file"]


@dataclass(frozen=True)
class InstallResult:
    files_written: int
    files_removed: int


@dataclass(frozen=True)
class StagedTarget:
    target: InstallTarget
    stage_path: Path
    previous_files: dict[str, str]
    next_files: dict[str, str]


@dataclass(frozen=True)
class SwappedTarget:
    target: InstallTarget
    backup_path: Path | None


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_install_manifest(manifest_path: Path | None = None) -> dict | None:
    if manifest_path is None:
        manifest_path = MANIFEST_PATH
    if not manifest_path.exists():
        return None
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("version") != MANIFEST_VERSION:
        raise InstallConflict(
            f"Unsupported dotagents install manifest version at {manifest_path}. "
            "Run `make install FORCE=1` to reinitialize it."
        )
    return manifest


def empty_manifest() -> dict:
    return {"version": MANIFEST_VERSION, "targets": {}}


def iter_source_files(target: InstallTarget) -> dict[str, Path]:
    if target.kind == "file":
        if not target.source.is_file():
            return {}
        return {target.destination.name: target.source}

    files: dict[str, Path] = {}
    if not target.source.exists():
        return files

    for source_file in sorted(
        path for path in target.source.rglob("*") if path.is_file() and not path.is_symlink()
    ):
        files[source_file.relative_to(target.source).as_posix()] = source_file
    return files


def destination_file(target: InstallTarget, relative_path: str) -> Path:
    if target.kind == "file":
        return target.destination
    return target.destination / relative_path


def stage_file_path(target: InstallTarget, stage_path: Path, relative_path: str) -> Path:
    if target.kind == "file":
        return stage_path
    return stage_path / relative_path


def target_files_from_manifest(manifest: dict, target: InstallTarget) -> dict[str, str]:
    target_data = manifest.get("targets", {}).get(target.name, {})
    return dict(target_data.get("files", {}))


def desired_hashes(target: InstallTarget) -> dict[str, str]:
    return {
        relative_path: hash_file(source_file)
        for relative_path, source_file in iter_source_files(target).items()
    }


def prune_empty_parents(path: Path, stop_at: Path) -> None:
    current = path.parent
    stop_at = stop_at.resolve()
    while current.exists() and current.resolve() != stop_at:
        try:
            current.rmdir()
        except OSError:
            return
        current = current.parent


def remove_path(path: Path) -> None:
    if not path.exists() and not path.is_symlink():
        return
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()


def resolved_path(path: Path) -> Path:
    return path.resolve(strict=False)


def path_has_unsafe_existing_ancestor(path: Path, *, include_self: bool = False) -> bool:
    end = path if include_self else path.parent
    try:
        relative = end.relative_to(HOME)
    except ValueError:
        candidates = [end, end.parent] if include_self else [end]
    else:
        current = HOME
        candidates = []
        for part in relative.parts:
            current = current / part
            candidates.append(current)

    return any(
        (candidate.exists() or candidate.is_symlink())
        and (candidate.is_symlink() or not candidate.is_dir())
        for candidate in candidates
    )


def relative_path_parent_is_unsafe(root: Path, relative_path: str) -> bool:
    current = root
    for part in Path(relative_path).parts[:-1]:
        current = current / part
        if current.is_symlink() or (current.exists() and not current.is_dir()):
            return True
    return False


def relative_path_parent_has_non_directory(root: Path, relative_path: str) -> bool:
    current = root
    for part in Path(relative_path).parts[:-1]:
        current = current / part
        if current.exists() and not current.is_symlink() and not current.is_dir():
            return True
    return False


def ensure_stage_parent_directory(stage_path: Path, relative_path: str) -> None:
    current = stage_path
    for part in Path(relative_path).parts[:-1]:
        current = current / part
        if current.is_symlink():
            remove_path(current)
        elif current.exists() and not current.is_dir():
            raise InstallConflict(f"Refusing to replace non-directory install path: {current}")
        current.mkdir(exist_ok=True)


def copy_destination_to_stage(target: InstallTarget, stage_path: Path) -> None:
    if target.kind == "tree":
        if target.destination.exists() or target.destination.is_symlink():
            if not target.destination.is_dir() or target.destination.is_symlink():
                raise InstallConflict(f"Install destination is not a directory: {target.destination}")
            shutil.copytree(target.destination, stage_path, symlinks=True)
        else:
            stage_path.mkdir(parents=True, exist_ok=True)
        return

    stage_path.parent.mkdir(parents=True, exist_ok=True)
    if target.destination.exists() or target.destination.is_symlink():
        shutil.copy2(target.destination, stage_path, follow_symlinks=False)


def stage_target(target: InstallTarget, stage_path: Path, manifest: dict) -> dict[str, str]:
    copy_destination_to_stage(target, stage_path)
    previous_files = target_files_from_manifest(manifest, target)
    files = iter_source_files(target)
    next_files: dict[str, str] = {}

    for relative_path in sorted(set(previous_files) - set(files)):
        staged_destination = stage_file_path(target, stage_path, relative_path)
        if target.kind == "tree" and relative_path_parent_is_unsafe(stage_path, relative_path):
            continue
        if staged_destination.exists() or staged_destination.is_symlink():
            staged_destination.unlink()
            if target.kind == "tree":
                prune_empty_parents(staged_destination, stage_path)

    for relative_path, source_file in files.items():
        staged_destination = stage_file_path(target, stage_path, relative_path)
        if target.kind == "tree":
            ensure_stage_parent_directory(stage_path, relative_path)
        else:
            staged_destination.parent.mkdir(parents=True, exist_ok=True)
        if staged_destination.is_symlink():
            staged_destination.unlink()
        shutil.copy2(source_file, staged_destination)
        next_files[relative_path] = hash_file(staged_destination)

    return next_files


def unique_sibling_path(destination: Path, label: str) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(1000):
        candidate = destination.with_name(
            f".{destination.name}.dotagents-{label}-{os.getpid()}-{attempt}"
        )
        if not candidate.exists() and not candidate.is_symlink():
            return candidate
    raise RuntimeError(f"Could not allocate temporary {label} path next to {destination}")


def swap_target_into_place(stage_path: Path, target: InstallTarget) -> Path | None:
    backup_path = None
    # Writers are serialized by the install lock, but readers may briefly see no
    # destination between these two renames.
    if target.destination.exists() or target.destination.is_symlink():
        backup_path = unique_sibling_path(target.destination, "backup")
        target.destination.rename(backup_path)

    target.destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        stage_path.rename(target.destination)
    except Exception:
        if backup_path is not None and backup_path.exists():
            backup_path.rename(target.destination)
        raise
    return backup_path


def rollback_swaps(swapped: list[SwappedTarget]) -> None:
    for swapped_target in reversed(swapped):
        remove_path(swapped_target.target.destination)
        if swapped_target.backup_path is not None and swapped_target.backup_path.exists():
            swapped_target.backup_path.rename(swapped_target.target.destination)


def cleanup_backups(swapped: list[SwappedTarget]) -> None:
    for swapped_target in swapped:
        if swapped_target.backup_path is not None:
            remove_path(swapped_target.backup_path)


def generated_temp_siblings(destination: Path, label: str) -> list[Path]:
    parent = destination.parent
    if not parent.exists() or not parent.is_dir():
        return []

    prefix = f".{destination.name}.dotagents-{label}-"
    paths: list[Path] = []
    for candidate in parent.iterdir():
        suffix = candidate.name.removeprefix(prefix)
        parts = suffix.split("-")
        if (
            candidate.name.startswith(prefix)
            and len(parts) == 2
            and all(part.isdigit() for part in parts)
        ):
            paths.append(candidate)
    return sorted(paths)


def cleanup_stale_install_temp_paths(targets: list[InstallTarget], *, force: bool) -> None:
    for target in targets:
        stale_stages = generated_temp_siblings(target.destination, "stage")
        stale_backups = generated_temp_siblings(target.destination, "backup")
        destination_exists = target.destination.exists() or target.destination.is_symlink()

        if not destination_exists and stale_backups:
            if len(stale_backups) > 1:
                raise InstallConflict(
                    f"Refusing to choose between multiple stale install backups for {target.destination}"
                )
            if not force:
                raise InstallConflict(
                    f"Stale install backup found for {target.destination}. Run with FORCE=1 to restore it."
                )
            for stale_stage in stale_stages:
                remove_path(stale_stage)
            stale_backups[0].rename(target.destination)
            continue

        for stale_path in stale_stages + stale_backups:
            remove_path(stale_path)


def validate_install_target_paths(targets: list[InstallTarget]) -> None:
    unsafe_targets = [
        target.destination
        for target in targets
        if path_has_unsafe_existing_ancestor(
            target.destination, include_self=target.kind == "tree"
        )
    ]
    if unsafe_targets:
        paths = ", ".join(str(path) for path in unsafe_targets)
        raise InstallConflict(f"Refusing unsafe install target path(s): {paths}")


def validate_source_targets(targets: list[InstallTarget]) -> None:
    empty_targets = [target.name for target in targets if not iter_source_files(target)]
    if empty_targets:
        names = ", ".join(empty_targets)
        raise InstallConflict(f"No source files found for install target(s): {names}")


def collect_hard_install_conflicts(targets: list[InstallTarget], manifest: dict) -> list[str]:
    conflicts: list[str] = []
    for target in targets:
        relative_paths = set(iter_source_files(target)) | set(target_files_from_manifest(manifest, target))
        for relative_path in relative_paths:
            destination = destination_file(target, relative_path)
            if target.kind == "tree" and relative_path_parent_has_non_directory(
                target.destination, relative_path
            ):
                conflicts.append(f"{destination} has a non-directory install path")
                continue
            if destination.exists() and not destination.is_symlink() and not destination.is_file():
                conflicts.append(f"{destination} has a non-regular install path")
    return conflicts


def collect_install_conflicts(targets: list[InstallTarget], manifest: dict) -> list[str]:
    conflicts: list[str] = []

    for target in targets:
        previous_files = target_files_from_manifest(manifest, target)
        desired_files = desired_hashes(target)

        for relative_path, previous_hash in previous_files.items():
            destination = destination_file(target, relative_path)
            if target.kind == "tree" and relative_path_parent_is_unsafe(target.destination, relative_path):
                conflicts.append(f"{destination} has an unsafe parent path")
                continue
            if not destination.exists() and not destination.is_symlink():
                if relative_path in desired_files:
                    conflicts.append(f"{destination} was locally deleted")
                continue
            if destination.is_symlink() or not destination.is_file():
                conflicts.append(f"{destination} is not a regular file")
                continue
            if hash_file(destination) != previous_hash:
                conflicts.append(f"{destination} was locally modified")

        for relative_path, desired_hash in desired_files.items():
            destination = destination_file(target, relative_path)
            if relative_path in previous_files:
                continue
            if target.kind == "tree" and relative_path_parent_is_unsafe(target.destination, relative_path):
                conflicts.append(f"{destination} has an unsafe parent path")
                continue
            if destination.is_symlink() or (destination.exists() and not destination.is_file()):
                conflicts.append(f"{destination} already exists and is not a regular file")
                continue
            if destination.exists() and hash_file(destination) != desired_hash:
                conflicts.append(f"{destination} already exists and is not managed")

    return conflicts


def preflight_install_targets(targets: list[InstallTarget], manifest: dict, force: bool) -> None:
    hard_conflicts = collect_hard_install_conflicts(targets, manifest)
    if hard_conflicts:
        details = "\n".join(f"  - {conflict}" for conflict in hard_conflicts)
        raise InstallConflict(f"Refusing structural install conflicts:\n{details}")

    conflicts = collect_install_conflicts(targets, manifest)
    if force:
        if conflicts:
            print(f"  FORCE=1: ignoring {len(conflicts)} install conflict(s)")
        return

    if conflicts:
        details = "\n".join(f"  - {conflict}" for conflict in conflicts)
        raise InstallConflict(f"Refusing to overwrite locally modified install files:\n{details}")


def destination_is_empty(target: InstallTarget) -> bool:
    if not target.destination.exists() and not target.destination.is_symlink():
        return True
    if target.kind == "file":
        return False
    if not target.destination.is_dir() or target.destination.is_symlink():
        return False
    return next(target.destination.iterdir(), None) is None


def manifest_for_install(manifest_path: Path, force: bool, targets: list[InstallTarget]) -> dict:
    try:
        manifest = load_install_manifest(manifest_path)
    except InstallConflict:
        if not force:
            raise
        return empty_manifest()

    if manifest is not None:
        return manifest

    if force or all(destination_is_empty(target) for target in targets):
        return empty_manifest()

    raise InstallConflict(
        "No dotagents install manifest found and at least one install destination is not empty. "
        "Run `make install FORCE=1` to bootstrap managed install state."
    )


def cleanup_staged_paths(
    staged_targets: list[StagedTarget], staged_manifest: Path | None = None
) -> None:
    for staged_target in staged_targets:
        remove_path(staged_target.stage_path)
    if staged_manifest is not None:
        remove_path(staged_manifest)


def stage_install_targets(
    targets: list[InstallTarget],
    manifest: dict,
) -> tuple[list[StagedTarget], dict, InstallResult]:
    next_manifest = deepcopy(manifest)
    files_written = 0
    files_removed = 0
    staged_targets: list[StagedTarget] = []

    try:
        for target in targets:
            stage_path = unique_sibling_path(target.destination, "stage")
            try:
                previous_files = target_files_from_manifest(next_manifest, target)
                next_files = stage_target(target, stage_path, next_manifest)
            except Exception:
                remove_path(stage_path)
                raise

            files_removed += len(set(previous_files) - set(next_files))
            files_written += len(next_files)
            next_manifest["targets"][target.name] = {
                "path": str(target.destination),
                "kind": target.kind,
                "files": next_files,
            }
            staged_targets.append(StagedTarget(target, stage_path, previous_files, next_files))
    except Exception:
        cleanup_staged_paths(staged_targets)
        raise

    result = InstallResult(files_written=files_written, files_removed=files_removed)
    return staged_targets, next_manifest, result


def write_staged_manifest(manifest: dict, manifest_path: Path) -> Path:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    staged_manifest = unique_sibling_path(manifest_path, "stage")
    try:
        staged_manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    except Exception:
        remove_path(staged_manifest)
        raise
    return staged_manifest


def commit_staged_install(
    staged_targets: list[StagedTarget],
    staged_manifest: Path,
    manifest_path: Path,
) -> None:
    swapped: list[SwappedTarget] = []
    try:
        for staged_target in staged_targets:
            backup_path = swap_target_into_place(staged_target.stage_path, staged_target.target)
            swapped.append(SwappedTarget(staged_target.target, backup_path))
        os.replace(staged_manifest, manifest_path)
    except Exception:
        rollback_swaps(swapped)
        raise
    else:
        cleanup_backups(swapped)


def safe_install_targets(
    targets: Iterable[InstallTarget],
    *,
    manifest_path: Path | None = None,
    force: bool = False,
) -> InstallResult:
    if manifest_path is None:
        manifest_path = MANIFEST_PATH
    targets = list(targets)
    validate_install_target_paths(targets)
    validate_source_targets(targets)
    cleanup_stale_install_temp_paths(targets, force=force)
    manifest = manifest_for_install(manifest_path, force, targets)
    preflight_install_targets(targets, manifest, force)

    staged_targets: list[StagedTarget] = []
    staged_manifest: Path | None = None
    try:
        staged_targets, next_manifest, result = stage_install_targets(targets, manifest)
        staged_manifest = write_staged_manifest(next_manifest, manifest_path)
        commit_staged_install(staged_targets, staged_manifest, manifest_path)
    finally:
        cleanup_staged_paths(staged_targets, staged_manifest)

    return result


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


def build_skill(name: str, source: Path) -> bool:
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


def build_extension(name: str, source: Path) -> bool:
    """Build a single Pi extension from a source directory."""
    entrypoint = source / "index.ts"
    if not entrypoint.exists():
        print(f"    Warning: {source} has no index.ts, skipping")
        return False

    dest = BUILD_DIR / "extensions" / name
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(source, dest)
    return True


def extension_dirs() -> list[Path]:
    """Return custom Pi extension directories under ./pi-extensions."""
    if not PI_EXTENSIONS_DIR.exists():
        return []

    return [
        path
        for path in sorted(PI_EXTENSIONS_DIR.iterdir())
        if path.is_dir() and (path / "index.ts").exists()
    ]


def build_skills() -> None:
    """Build all custom skills from ./skills."""
    print("Building skills...")

    skills_build = BUILD_DIR / "skills"
    if skills_build.exists():
        shutil.rmtree(skills_build)
    skills_build.mkdir(parents=True)

    built = 0
    if SKILLS_DIR.exists():
        for skill_dir in sorted(SKILLS_DIR.iterdir()):
            if not skill_dir.is_dir():
                continue
            if build_skill(skill_dir.name, skill_dir):
                print(f"  {skill_dir.name}")
                built += 1

    print(f"  Built {built} skills")


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


def build_extensions() -> None:
    """Build all custom Pi extensions from ./pi-extensions."""
    print("Building extensions...")

    extensions_build = BUILD_DIR / "extensions"
    if extensions_build.exists():
        shutil.rmtree(extensions_build)
    extensions_build.mkdir(parents=True)

    built = 0
    for ext_dir in extension_dirs():
        if build_extension(ext_dir.name, ext_dir):
            print(f"  {ext_dir.name}")
            built += 1

    print(f"  Built {built} extensions")


@contextmanager
def install_lock():
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with LOCK_PATH.open("w") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        yield


def skill_install_targets() -> list[InstallTarget]:
    source = BUILD_DIR / "skills"
    return [
        InstallTarget(f"{name}-skills", source, destination, "tree")
        for name, destination in INSTALL_PATHS.items()
    ]


def agent_install_targets() -> list[InstallTarget]:
    return [InstallTarget("pi-agents", BUILD_DIR / "agents", PI_AGENTS_PATH, "tree")]


def extension_install_targets() -> list[InstallTarget]:
    return [InstallTarget("pi-extensions", BUILD_DIR / "extensions", PI_EXTENSIONS_PATH, "tree")]


def global_agents_md_target() -> InstallTarget | None:
    if not GLOBAL_AGENTS_MD.exists():
        return None
    return InstallTarget("global-agents-md", GLOBAL_AGENTS_MD, HOME / ".agents" / "AGENTS.md", "file")


def full_install_targets() -> list[InstallTarget]:
    targets = skill_install_targets() + agent_install_targets() + extension_install_targets()
    global_target = global_agents_md_target()
    if global_target is not None:
        targets.append(global_target)
    return targets


def install_skills(force: bool = False) -> None:
    """Install built skills to configured agent directories."""
    print("Installing skills...")

    source = BUILD_DIR / "skills"
    if not source.exists():
        print("  No skills built, run 'make build' first")
        return

    result = safe_install_targets(skill_install_targets(), force=force)

    count = len([path for path in source.iterdir() if path.is_dir()])
    for name, dest in INSTALL_PATHS.items():
        print(f"  {name}: {count} skills -> {dest}")
    print(f"  Synced {result.files_written} files, removed {result.files_removed} managed files")


def install_agents(force: bool = False) -> None:
    """Install built agents to the Pi subagents directory."""
    print("Installing agents...")

    source = BUILD_DIR / "agents"
    if not source.exists():
        print("  No agents built, run 'make build' first")
        return

    result = safe_install_targets(agent_install_targets(), force=force)
    count = len([path for path in source.iterdir() if path.is_file() and path.suffix == ".md"])
    print(f"  pi-subagents: {count} agents -> {PI_AGENTS_PATH}")
    print(f"  Synced {result.files_written} files, removed {result.files_removed} managed files")


def install_extensions(force: bool = False) -> None:
    """Install built Pi extensions to the Pi extensions directory."""
    print("Installing extensions...")

    source = BUILD_DIR / "extensions"
    if not source.exists():
        print("  No extensions built, run 'make build' first")
        return

    result = safe_install_targets(extension_install_targets(), force=force)
    count = len([path for path in source.iterdir() if path.is_dir()])
    print(f"  pi: {count} extensions -> {PI_EXTENSIONS_PATH}")
    print(f"  Synced {result.files_written} files, removed {result.files_removed} managed files")


def install_global_agents_md(force: bool = False) -> None:
    """Install global AGENTS.md for unified agents path."""
    print("Installing global AGENTS.md...")

    target = global_agents_md_target()
    if target is None:
        print("  No AGENTS.md found in configs/, skipping")
        return

    result = safe_install_targets([target], force=force)
    print(f"  Installed to {target.destination}")
    print(f"  Synced {result.files_written} files, removed {result.files_removed} managed files")


def install_all(force: bool = False) -> None:
    """Install all built artifacts as one manifest transaction."""
    print("Installing skills, agents, extensions, and global AGENTS.md...")

    skills_source = BUILD_DIR / "skills"
    agents_source = BUILD_DIR / "agents"
    extensions_source = BUILD_DIR / "extensions"
    if not skills_source.exists():
        print("  No skills built, run 'make build' first")
        return
    if not agents_source.exists():
        print("  No agents built, run 'make build' first")
        return
    if not extensions_source.exists():
        print("  No extensions built, run 'make build' first")
        return

    result = safe_install_targets(full_install_targets(), force=force)

    skill_count = len([path for path in skills_source.iterdir() if path.is_dir()])
    agent_count = len([path for path in agents_source.iterdir() if path.is_file() and path.suffix == ".md"])
    extension_count = len([path for path in extensions_source.iterdir() if path.is_dir()])
    print(f"  claude: {skill_count} skills -> {INSTALL_PATHS['claude']}")
    print(f"  unified: {skill_count} skills -> {INSTALL_PATHS['unified']}")
    print(f"  pi-subagents: {agent_count} agents -> {PI_AGENTS_PATH}")
    print(f"  pi: {extension_count} extensions -> {PI_EXTENSIONS_PATH}")
    global_target = global_agents_md_target()
    if global_target is not None:
        print(f"  global AGENTS.md -> {global_target.destination}")
    print(f"  Synced {result.files_written} files, removed {result.files_removed} managed files")


def load_manifest(manifest: Path) -> set[str]:
    if not manifest.exists():
        return set()
    return {line.strip() for line in manifest.read_text().splitlines() if line.strip()}


def managed_skills_manifest_path(dest: Path) -> Path:
    return dest / SKILLS_MANIFEST


def load_managed_skills(dest: Path) -> set[str]:
    return load_manifest(managed_skills_manifest_path(dest))


def managed_extensions_manifest_path() -> Path:
    return PI_EXTENSIONS_PATH / PI_EXTENSIONS_MANIFEST


def load_managed_extensions() -> set[str]:
    return load_manifest(managed_extensions_manifest_path())


def known_install_targets() -> dict[str, InstallTarget]:
    targets = skill_install_targets() + agent_install_targets() + extension_install_targets()
    targets.append(
        InstallTarget("global-agents-md", GLOBAL_AGENTS_MD, HOME / ".agents" / "AGENTS.md", "file")
    )
    return {target.name: target for target in targets}


def is_safe_relative_manifest_path(relative_path: str) -> bool:
    path = Path(relative_path)
    return bool(path.parts) and not path.is_absolute() and ".." not in path.parts


def manifest_clean_entries(manifest: dict) -> list[tuple[InstallTarget, list[str]]]:
    known_targets = known_install_targets()
    entries: list[tuple[InstallTarget, list[str]]] = []

    for target_name, target_data in manifest.get("targets", {}).items():
        expected_target = known_targets.get(target_name)
        if expected_target is None:
            raise InstallConflict(f"Refusing to clean unknown install target: {target_name}")

        destination = Path(target_data.get("path", ""))
        kind = target_data.get("kind")
        if kind != expected_target.kind or resolved_path(destination) != resolved_path(
            expected_target.destination
        ):
            raise InstallConflict(
                f"Refusing to clean {destination}: outside known install target {expected_target.destination}"
            )
        if path_has_unsafe_existing_ancestor(
            expected_target.destination, include_self=expected_target.kind == "tree"
        ):
            raise InstallConflict(f"Refusing unsafe install target path: {expected_target.destination}")

        files = target_data.get("files", {})
        if not isinstance(files, dict):
            raise InstallConflict(f"Invalid install manifest files for target: {target_name}")

        relative_paths = sorted(files)
        for relative_path in relative_paths:
            if not is_safe_relative_manifest_path(relative_path):
                raise InstallConflict(f"Refusing unsafe manifest path: {relative_path}")
            if expected_target.kind == "file" and relative_path != expected_target.destination.name:
                raise InstallConflict(f"Refusing unsafe manifest path: {relative_path}")
            if expected_target.kind == "tree" and (
                expected_target.destination.is_symlink()
                or relative_path_parent_is_unsafe(expected_target.destination, relative_path)
            ):
                raise InstallConflict(f"Refusing unsafe manifest path: {relative_path}")
            installed = (
                expected_target.destination
                if expected_target.kind == "file"
                else expected_target.destination / relative_path
            )
            if installed.exists() and not installed.is_symlink() and not installed.is_file():
                raise InstallConflict(f"Refusing unsafe manifest path: {relative_path}")

        entries.append((expected_target, relative_paths))

    return entries


def clean_manifest_install(manifest_path: Path | None = None) -> None:
    if manifest_path is None:
        manifest_path = MANIFEST_PATH
    manifest = load_install_manifest(manifest_path)
    if manifest is None:
        return

    for target, relative_paths in manifest_clean_entries(manifest):
        for relative_path in relative_paths:
            installed = target.destination if target.kind == "file" else target.destination / relative_path
            remove_path(installed)
            if target.kind == "tree":
                prune_empty_parents(installed, target.destination)
            print(f"  Removed {installed}")

    manifest_path.unlink()
    print(f"  Removed {manifest_path}")


def validate_legacy_manifest_entries(root: Path, entries: Iterable[str]) -> list[str]:
    if path_has_unsafe_existing_ancestor(root, include_self=True):
        raise InstallConflict(f"Refusing unsafe legacy manifest entry under {root}")

    safe_entries: list[str] = []
    for entry in entries:
        path = Path(entry)
        if not is_safe_relative_manifest_path(entry) or len(path.parts) != 1:
            raise InstallConflict(f"Refusing unsafe legacy manifest entry: {entry}")
        safe_entries.append(entry)
    return safe_entries


def remove_legacy_file_if_matches_source(installed: Path, source: Path) -> None:
    if not source.exists() or (not installed.exists() and not installed.is_symlink()):
        return
    if installed.is_symlink() or not installed.is_file() or hash_file(installed) != hash_file(source):
        raise InstallConflict(f"Refusing to remove locally modified legacy install file: {installed}")
    installed.unlink()
    print(f"  Removed {installed}")


def legacy_directory_files(root: Path) -> dict[str, Path]:
    if root.is_symlink() or not root.is_dir():
        raise InstallConflict(f"Refusing locally modified legacy install directory: {root}")

    files: dict[str, Path] = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or (path.exists() and not path.is_dir() and not path.is_file()):
            raise InstallConflict(f"Refusing locally modified legacy install directory: {root}")
        if path.is_file():
            files[path.relative_to(root).as_posix()] = path
    return files


def remove_legacy_directory_if_matches_source(installed: Path, source: Path) -> None:
    if not installed.exists() and not installed.is_symlink():
        return
    if not source.is_dir():
        raise InstallConflict(f"Refusing locally modified legacy install directory: {installed}")

    installed_files = legacy_directory_files(installed)
    source_files = legacy_directory_files(source)
    if set(installed_files) != set(source_files):
        raise InstallConflict(f"Refusing locally modified legacy install directory: {installed}")
    for relative_path, installed_file in installed_files.items():
        if hash_file(installed_file) != hash_file(source_files[relative_path]):
            raise InstallConflict(f"Refusing locally modified legacy install directory: {installed}")

    remove_path(installed)
    print(f"  Removed {installed}")


def clean_legacy_installs() -> None:
    for path in INSTALL_PATHS.values():
        if not path.exists():
            continue

        for skill_name in validate_legacy_manifest_entries(path, sorted(load_managed_skills(path))):
            remove_legacy_directory_if_matches_source(
                path / skill_name, BUILD_DIR / "skills" / skill_name
            )

        manifest = managed_skills_manifest_path(path)
        if manifest.exists():
            manifest.unlink()
            print(f"  Removed {manifest}")

    if PI_AGENTS_PATH.exists() and AGENTS_DIR.exists():
        if path_has_unsafe_existing_ancestor(PI_AGENTS_PATH, include_self=True):
            raise InstallConflict(f"Refusing unsafe legacy install path: {PI_AGENTS_PATH}")
        for agent_file in AGENTS_DIR.iterdir():
            if not agent_file.is_file() or agent_file.suffix != ".md":
                continue
            remove_legacy_file_if_matches_source(PI_AGENTS_PATH / agent_file.name, agent_file)

    if PI_EXTENSIONS_PATH.exists():
        for extension_name in validate_legacy_manifest_entries(
            PI_EXTENSIONS_PATH, sorted(load_managed_extensions())
        ):
            remove_legacy_directory_if_matches_source(
                PI_EXTENSIONS_PATH / extension_name, BUILD_DIR / "extensions" / extension_name
            )

        manifest = managed_extensions_manifest_path()
        if manifest.exists():
            manifest.unlink()
            print(f"  Removed {manifest}")

    agents_md_path = HOME / ".agents" / "AGENTS.md"
    if agents_md_path.exists() or agents_md_path.is_symlink():
        if path_has_unsafe_existing_ancestor(agents_md_path):
            raise InstallConflict(f"Refusing unsafe legacy install path: {agents_md_path}")
        remove_legacy_file_if_matches_source(agents_md_path, GLOBAL_AGENTS_MD)


def clean() -> None:
    """Remove installed artifacts managed by this repo."""
    print("Cleaning installed artifacts...")

    clean_manifest_install()
    clean_legacy_installs()

    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
        print("  Removed build directory")

    print("  Done")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build and install AI agent skills, agents, and Pi extensions"
    )
    parser.add_argument(
        "command",
        choices=["build", "install", "install-skills", "install-extensions", "clean"],
        help="Command to run",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip install conflict checks and initialize the install manifest when bootstrapping",
    )
    args = parser.parse_args()

    try:
        if args.command == "build":
            build_skills()
            build_agents()
            build_extensions()
        elif args.command == "install":
            with install_lock():
                build_skills()
                build_agents()
                build_extensions()
                install_all(force=args.force)
            print("\nAll done!")
        elif args.command == "install-skills":
            with install_lock():
                build_skills()
                install_skills(force=args.force)
        elif args.command == "install-extensions":
            with install_lock():
                build_extensions()
                install_extensions(force=args.force)
        elif args.command == "clean":
            with install_lock():
                clean()
    except InstallConflict as error:
        sys.exit(f"Error: {error}")


if __name__ == "__main__":
    main()
