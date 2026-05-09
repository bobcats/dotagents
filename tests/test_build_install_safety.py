from contextlib import contextmanager
import importlib.util
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
BUILD_SCRIPT = ROOT / "scripts" / "build.py"


def load_build_module():
    spec = importlib.util.spec_from_file_location("dotagents_build", BUILD_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["dotagents_build"] = module
    spec.loader.exec_module(module)
    return module


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def tree_target(build, name: str, source: Path, destination: Path):
    return build.InstallTarget(name, source, destination, "tree")


def bootstrap_install(build, target, manifest_path: Path) -> str:
    build.safe_install_targets([target], manifest_path=manifest_path, force=True)
    return manifest_path.read_text()


def test_install_without_manifest_requires_force_for_non_empty_destination_and_does_not_write(tmp_path):
    build = load_build_module()
    source = tmp_path / "build" / "skills"
    destination = tmp_path / "home" / ".agents" / "skills"
    manifest_path = tmp_path / "state" / "install-manifest.json"

    write_file(source / "demo" / "SKILL.md", "repo version\n")
    write_file(destination / "demo" / "SKILL.md", "local version\n")

    target = tree_target(build, "unified-skills", source, destination)

    with pytest.raises(build.InstallConflict, match="FORCE=1"):
        build.safe_install_targets([target], manifest_path=manifest_path, force=False)

    assert (destination / "demo" / "SKILL.md").read_text() == "local version\n"
    assert not manifest_path.exists()


def test_install_without_manifest_bootstraps_empty_tree_destination_without_force(tmp_path):
    build = load_build_module()
    source = tmp_path / "build" / "skills"
    destination = tmp_path / "home" / ".agents" / "skills"
    manifest_path = tmp_path / "state" / "install-manifest.json"

    write_file(source / "demo" / "SKILL.md", "repo version\n")
    destination.mkdir(parents=True)

    target = tree_target(build, "unified-skills", source, destination)

    result = build.safe_install_targets([target], manifest_path=manifest_path, force=False)

    assert result == build.InstallResult(files_written=1, files_removed=0)
    assert (destination / "demo" / "SKILL.md").read_text() == "repo version\n"
    assert json.loads(manifest_path.read_text())["targets"]["unified-skills"]["files"]


def test_file_target_without_manifest_bootstraps_missing_destination_without_force(tmp_path):
    build = load_build_module()
    source = tmp_path / "configs" / "AGENTS.md"
    destination = tmp_path / "home" / ".agents" / "AGENTS.md"
    manifest_path = tmp_path / "state" / "install-manifest.json"

    write_file(source, "agents guidance\n")

    target = build.InstallTarget("global-agents-md", source, destination, "file")

    build.safe_install_targets([target], manifest_path=manifest_path, force=False)

    assert destination.read_text() == "agents guidance\n"
    assert json.loads(manifest_path.read_text())["targets"]["global-agents-md"]["files"] == {
        "AGENTS.md": build.hash_file(destination)
    }


def test_file_target_without_manifest_requires_force_for_existing_destination(tmp_path):
    build = load_build_module()
    source = tmp_path / "configs" / "AGENTS.md"
    destination = tmp_path / "home" / ".agents" / "AGENTS.md"
    manifest_path = tmp_path / "state" / "install-manifest.json"

    write_file(source, "repo guidance\n")
    write_file(destination, "local guidance\n")

    target = build.InstallTarget("global-agents-md", source, destination, "file")

    with pytest.raises(build.InstallConflict, match="FORCE=1"):
        build.safe_install_targets([target], manifest_path=manifest_path, force=False)

    assert destination.read_text() == "local guidance\n"
    assert not manifest_path.exists()


def test_force_bootstrap_overwrites_collisions_preserves_unmanaged_and_writes_manifest(tmp_path):
    build = load_build_module()
    source = tmp_path / "build" / "skills"
    destination = tmp_path / "home" / ".agents" / "skills"
    manifest_path = tmp_path / "state" / "install-manifest.json"

    write_file(source / "demo" / "SKILL.md", "repo version\n")
    write_file(destination / "demo" / "SKILL.md", "local version\n")
    write_file(destination / "stale" / "SKILL.md", "old install\n")

    target = tree_target(build, "unified-skills", source, destination)

    build.safe_install_targets([target], manifest_path=manifest_path, force=True)

    assert (destination / "demo" / "SKILL.md").read_text() == "repo version\n"
    assert (destination / "stale" / "SKILL.md").read_text() == "old install\n"

    manifest = json.loads(manifest_path.read_text())
    assert manifest["version"] == 1
    assert set(manifest["targets"]) == {"unified-skills"}
    assert set(manifest["targets"]["unified-skills"]["files"]) == {"demo/SKILL.md"}


def test_force_removes_stale_managed_files_while_preserving_unmanaged_files(tmp_path):
    build = load_build_module()
    source = tmp_path / "build" / "skills"
    destination = tmp_path / "home" / ".agents" / "skills"
    manifest_path = tmp_path / "state" / "install-manifest.json"

    write_file(source / "demo" / "SKILL.md", "repo v1\n")
    write_file(source / "stale" / "SKILL.md", "repo stale\n")
    target = tree_target(build, "unified-skills", source, destination)
    bootstrap_install(build, target, manifest_path)

    shutil_source = source / "stale"
    for child in shutil_source.iterdir():
        child.unlink()
    shutil_source.rmdir()
    write_file(source / "demo" / "SKILL.md", "repo v2\n")
    write_file(destination / "custom" / "SKILL.md", "manual skill\n")
    write_file(destination / "demo" / "local.txt", "manual note\n")

    build.safe_install_targets([target], manifest_path=manifest_path, force=True)

    assert (destination / "demo" / "SKILL.md").read_text() == "repo v2\n"
    assert not (destination / "stale" / "SKILL.md").exists()
    assert (destination / "custom" / "SKILL.md").read_text() == "manual skill\n"
    assert (destination / "demo" / "local.txt").read_text() == "manual note\n"


def test_install_removes_stale_dotagents_stage_and_backup_siblings(tmp_path):
    build = load_build_module()
    source = tmp_path / "build" / "skills"
    destination = tmp_path / "home" / ".agents" / "skills"
    manifest_path = tmp_path / "state" / "install-manifest.json"

    write_file(source / "demo" / "SKILL.md", "repo version\n")
    destination.mkdir(parents=True)
    stale_stage = destination.with_name(f".{destination.name}.dotagents-stage-123-0")
    stale_backup = destination.with_name(f".{destination.name}.dotagents-backup-123-0")
    nonmatching = destination.with_name(f".{destination.name}.dotagents-stage-manual")
    write_file(stale_stage / "leftover.txt", "stale stage\n")
    write_file(stale_backup / "leftover.txt", "stale backup\n")
    write_file(nonmatching / "leftover.txt", "manual\n")

    target = tree_target(build, "unified-skills", source, destination)

    build.safe_install_targets([target], manifest_path=manifest_path, force=False)

    assert not stale_stage.exists()
    assert not stale_backup.exists()
    assert (nonmatching / "leftover.txt").read_text() == "manual\n"
    assert (destination / "demo" / "SKILL.md").read_text() == "repo version\n"


def test_install_restores_single_stale_backup_when_destination_is_missing(tmp_path):
    build = load_build_module()
    source = tmp_path / "build" / "skills"
    destination = tmp_path / "home" / ".agents" / "skills"
    manifest_path = tmp_path / "state" / "install-manifest.json"

    write_file(source / "demo" / "SKILL.md", "repo version\n")
    stale_backup = destination.with_name(f".{destination.name}.dotagents-backup-123-0")
    write_file(stale_backup / "custom" / "SKILL.md", "manual skill\n")

    target = tree_target(build, "unified-skills", source, destination)

    build.safe_install_targets([target], manifest_path=manifest_path, force=True)

    assert not stale_backup.exists()
    assert (destination / "custom" / "SKILL.md").read_text() == "manual skill\n"
    assert (destination / "demo" / "SKILL.md").read_text() == "repo version\n"


def test_empty_source_target_with_stale_backup_is_refused_without_restoring(tmp_path):
    build = load_build_module()
    source = tmp_path / "build" / "skills"
    destination = tmp_path / "home" / ".agents" / "skills"
    manifest_path = tmp_path / "state" / "install-manifest.json"

    source.mkdir(parents=True)
    stale_backup = destination.with_name(f".{destination.name}.dotagents-backup-123-0")
    write_file(stale_backup / "custom" / "SKILL.md", "manual skill\n")

    target = tree_target(build, "unified-skills", source, destination)

    with pytest.raises(build.InstallConflict, match="No source files"):
        build.safe_install_targets([target], manifest_path=manifest_path, force=True)

    assert not destination.exists()
    assert (stale_backup / "custom" / "SKILL.md").read_text() == "manual skill\n"
    assert not manifest_path.exists()


def test_empty_source_target_is_refused_without_changing_destination(tmp_path):
    build = load_build_module()
    source = tmp_path / "build" / "skills"
    destination = tmp_path / "home" / ".agents" / "skills"
    manifest_path = tmp_path / "state" / "install-manifest.json"

    source.mkdir(parents=True)
    write_file(destination / "custom" / "SKILL.md", "manual skill\n")
    target = tree_target(build, "unified-skills", source, destination)

    with pytest.raises(build.InstallConflict, match="No source files"):
        build.safe_install_targets([target], manifest_path=manifest_path, force=True)

    assert (destination / "custom" / "SKILL.md").read_text() == "manual skill\n"
    assert not manifest_path.exists()


def test_force_install_refuses_unmanaged_file_blocking_source_directory(tmp_path):
    build = load_build_module()
    source = tmp_path / "build" / "skills"
    destination = tmp_path / "home" / ".agents" / "skills"
    manifest_path = tmp_path / "state" / "install-manifest.json"

    write_file(source / "demo" / "SKILL.md", "repo version\n")
    write_file(destination / "demo", "manual file\n")

    target = tree_target(build, "unified-skills", source, destination)

    with pytest.raises(build.InstallConflict, match="non-directory install path"):
        build.safe_install_targets([target], manifest_path=manifest_path, force=True)

    assert (destination / "demo").read_text() == "manual file\n"
    assert not manifest_path.exists()


def test_force_install_refuses_directory_blocking_source_file(tmp_path):
    build = load_build_module()
    source = tmp_path / "build" / "skills"
    destination = tmp_path / "home" / ".agents" / "skills"
    manifest_path = tmp_path / "state" / "install-manifest.json"

    write_file(source / "demo" / "SKILL.md", "repo version\n")
    write_file(destination / "demo" / "SKILL.md" / "local.txt", "manual file\n")

    target = tree_target(build, "unified-skills", source, destination)

    with pytest.raises(build.InstallConflict, match="non-regular install path"):
        build.safe_install_targets([target], manifest_path=manifest_path, force=True)

    assert (destination / "demo" / "SKILL.md" / "local.txt").read_text() == "manual file\n"
    assert not manifest_path.exists()


def test_force_file_target_refuses_directory_destination(tmp_path):
    build = load_build_module()
    source = tmp_path / "configs" / "AGENTS.md"
    destination = tmp_path / "home" / ".agents" / "AGENTS.md"
    manifest_path = tmp_path / "state" / "install-manifest.json"

    write_file(source, "repo guidance\n")
    write_file(destination / "local.txt", "manual file\n")

    target = build.InstallTarget("global-agents-md", source, destination, "file")

    with pytest.raises(build.InstallConflict, match="non-regular install path"):
        build.safe_install_targets([target], manifest_path=manifest_path, force=True)

    assert (destination / "local.txt").read_text() == "manual file\n"
    assert not manifest_path.exists()


def test_install_overwrites_destination_symlink_without_following_it(tmp_path):
    build = load_build_module()
    source = tmp_path / "build" / "skills"
    destination = tmp_path / "home" / ".agents" / "skills"
    manifest_path = tmp_path / "state" / "install-manifest.json"
    outside = tmp_path / "outside.txt"

    write_file(source / "demo" / "SKILL.md", "repo version\n")
    write_file(outside, "outside\n")
    (destination / "demo").mkdir(parents=True)
    (destination / "demo" / "SKILL.md").symlink_to(outside)

    target = tree_target(build, "unified-skills", source, destination)

    build.safe_install_targets([target], manifest_path=manifest_path, force=True)

    installed = destination / "demo" / "SKILL.md"
    assert installed.read_text() == "repo version\n"
    assert not installed.is_symlink()
    assert outside.read_text() == "outside\n"


def test_force_install_replaces_symlinked_parent_without_touching_target(tmp_path):
    build = load_build_module()
    source = tmp_path / "build" / "skills"
    destination = tmp_path / "home" / ".agents" / "skills"
    manifest_path = tmp_path / "state" / "install-manifest.json"
    outside = tmp_path / "outside"

    write_file(source / "demo" / "SKILL.md", "repo version\n")
    write_file(outside / "SKILL.md", "outside\n")
    destination.mkdir(parents=True)
    (destination / "demo").symlink_to(outside, target_is_directory=True)

    target = tree_target(build, "unified-skills", source, destination)

    build.safe_install_targets([target], manifest_path=manifest_path, force=True)

    assert (outside / "SKILL.md").read_text() == "outside\n"
    assert not (destination / "demo").is_symlink()
    assert (destination / "demo" / "SKILL.md").read_text() == "repo version\n"


def test_install_rejects_symlinked_destination_parent(tmp_path):
    build = load_build_module()
    source = tmp_path / "build" / "skills"
    home = tmp_path / "home"
    outside = tmp_path / "outside"
    destination = home / ".agents" / "skills"
    manifest_path = tmp_path / "state" / "install-manifest.json"

    write_file(source / "demo" / "SKILL.md", "repo version\n")
    home.mkdir()
    outside.mkdir()
    (home / ".agents").symlink_to(outside, target_is_directory=True)

    target = tree_target(build, "unified-skills", source, destination)

    with pytest.raises(build.InstallConflict, match="unsafe install target path"):
        build.safe_install_targets([target], manifest_path=manifest_path, force=True)

    assert not (outside / "skills").exists()
    assert not manifest_path.exists()


def test_force_install_refuses_directory_replacing_stale_managed_file(tmp_path):
    build = load_build_module()
    source = tmp_path / "build" / "skills"
    destination = tmp_path / "home" / ".agents" / "skills"
    manifest_path = tmp_path / "state" / "install-manifest.json"

    write_file(source / "demo" / "old.txt", "repo v1\n")
    target = tree_target(build, "unified-skills", source, destination)
    bootstrap_install(build, target, manifest_path)

    (source / "demo" / "old.txt").unlink()
    write_file(source / "demo" / "new.txt", "repo v2\n")
    (destination / "demo" / "old.txt").unlink()
    write_file(destination / "demo" / "old.txt" / "local.txt", "manual file\n")

    with pytest.raises(build.InstallConflict, match="non-regular install path"):
        build.safe_install_targets([target], manifest_path=manifest_path, force=True)

    assert (destination / "demo" / "old.txt" / "local.txt").read_text() == "manual file\n"


def test_force_reinitializes_unsupported_manifest(tmp_path):
    build = load_build_module()
    source = tmp_path / "build" / "skills"
    destination = tmp_path / "home" / ".agents" / "skills"
    manifest_path = tmp_path / "state" / "install-manifest.json"

    write_file(source / "demo" / "SKILL.md", "repo version\n")
    write_file(manifest_path, json.dumps({"version": 999, "targets": {}}))

    target = tree_target(build, "unified-skills", source, destination)

    build.safe_install_targets([target], manifest_path=manifest_path, force=True)

    assert (destination / "demo" / "SKILL.md").read_text() == "repo version\n"
    manifest = json.loads(manifest_path.read_text())
    assert manifest["version"] == 1
    assert set(manifest["targets"]) == {"unified-skills"}


def test_file_target_installs_exact_destination_and_manifest_entry(tmp_path):
    build = load_build_module()
    source = tmp_path / "configs" / "AGENTS.md"
    destination = tmp_path / "home" / ".agents" / "AGENTS.md"
    manifest_path = tmp_path / "state" / "install-manifest.json"

    write_file(source, "agents guidance\n")

    target = build.InstallTarget("global-agents-md", source, destination, "file")

    result = build.safe_install_targets([target], manifest_path=manifest_path, force=True)

    assert destination.read_text() == "agents guidance\n"
    assert result == build.InstallResult(files_written=1, files_removed=0)

    manifest = json.loads(manifest_path.read_text())
    assert manifest["targets"]["global-agents-md"]["path"] == str(destination)
    assert manifest["targets"]["global-agents-md"]["kind"] == "file"
    assert set(manifest["targets"]["global-agents-md"]["files"]) == {"AGENTS.md"}


def test_install_result_counts_desired_and_removed_managed_files(tmp_path):
    build = load_build_module()
    source = tmp_path / "build" / "skills"
    destination = tmp_path / "home" / ".agents" / "skills"
    manifest_path = tmp_path / "state" / "install-manifest.json"

    write_file(source / "demo" / "SKILL.md", "repo v1\n")
    write_file(source / "demo" / "script.py", "print('v1')\n")
    target = tree_target(build, "unified-skills", source, destination)
    bootstrap_install(build, target, manifest_path)

    (source / "demo" / "script.py").unlink()
    (destination / "demo" / "script.py").unlink()

    result = build.safe_install_targets([target], manifest_path=manifest_path, force=False)

    assert result == build.InstallResult(files_written=1, files_removed=1)
    manifest = json.loads(manifest_path.read_text())
    assert set(manifest["targets"]["unified-skills"]["files"]) == {"demo/SKILL.md"}


def test_locally_modified_managed_file_aborts_without_partial_writes(tmp_path):
    build = load_build_module()
    source = tmp_path / "build" / "skills"
    destination = tmp_path / "home" / ".agents" / "skills"
    manifest_path = tmp_path / "state" / "install-manifest.json"

    write_file(source / "demo" / "SKILL.md", "repo v1\n")
    write_file(source / "demo" / "script.py", "print('v1')\n")

    target = tree_target(build, "unified-skills", source, destination)
    original_manifest = bootstrap_install(build, target, manifest_path)

    write_file(destination / "demo" / "SKILL.md", "local edit\n")
    write_file(source / "demo" / "script.py", "print('v2')\n")

    with pytest.raises(build.InstallConflict, match="locally modified"):
        build.safe_install_targets([target], manifest_path=manifest_path, force=False)

    assert (destination / "demo" / "SKILL.md").read_text() == "local edit\n"
    assert (destination / "demo" / "script.py").read_text() == "print('v1')\n"
    assert manifest_path.read_text() == original_manifest


def test_locally_deleted_managed_file_aborts_without_recreating(tmp_path):
    build = load_build_module()
    source = tmp_path / "build" / "skills"
    destination = tmp_path / "home" / ".agents" / "skills"
    manifest_path = tmp_path / "state" / "install-manifest.json"

    write_file(source / "demo" / "SKILL.md", "repo v1\n")
    target = tree_target(build, "unified-skills", source, destination)
    original_manifest = bootstrap_install(build, target, manifest_path)

    (destination / "demo" / "SKILL.md").unlink()

    with pytest.raises(build.InstallConflict, match="locally deleted"):
        build.safe_install_targets([target], manifest_path=manifest_path, force=False)

    assert not (destination / "demo" / "SKILL.md").exists()
    assert manifest_path.read_text() == original_manifest


def test_unchanged_managed_files_update_and_unmanaged_files_are_preserved(tmp_path):
    build = load_build_module()
    source = tmp_path / "build" / "skills"
    destination = tmp_path / "home" / ".agents" / "skills"
    manifest_path = tmp_path / "state" / "install-manifest.json"

    write_file(source / "demo" / "SKILL.md", "repo v1\n")
    target = tree_target(build, "unified-skills", source, destination)
    bootstrap_install(build, target, manifest_path)

    write_file(destination / "custom" / "SKILL.md", "manual skill\n")
    write_file(source / "demo" / "SKILL.md", "repo v2\n")

    build.safe_install_targets([target], manifest_path=manifest_path, force=False)

    assert (destination / "demo" / "SKILL.md").read_text() == "repo v2\n"
    assert (destination / "custom" / "SKILL.md").read_text() == "manual skill\n"


def test_removed_managed_file_is_deleted_when_unchanged(tmp_path):
    build = load_build_module()
    source = tmp_path / "build" / "skills"
    destination = tmp_path / "home" / ".agents" / "skills"
    manifest_path = tmp_path / "state" / "install-manifest.json"

    write_file(source / "demo" / "SKILL.md", "repo v1\n")
    write_file(source / "demo" / "script.py", "print('v1')\n")
    target = tree_target(build, "unified-skills", source, destination)
    bootstrap_install(build, target, manifest_path)

    (source / "demo" / "script.py").unlink()

    build.safe_install_targets([target], manifest_path=manifest_path, force=False)

    assert (destination / "demo" / "SKILL.md").exists()
    assert not (destination / "demo" / "script.py").exists()


def test_install_rolls_back_all_targets_when_later_target_swap_fails(tmp_path, monkeypatch):
    build = load_build_module()
    skills_source = tmp_path / "build" / "skills"
    agents_source = tmp_path / "build" / "agents"
    skills_destination = tmp_path / "home" / ".agents" / "skills"
    agents_destination = tmp_path / "home" / ".pi" / "agent" / "agents"
    manifest_path = tmp_path / "state" / "install-manifest.json"

    write_file(skills_source / "demo" / "SKILL.md", "skill v1\n")
    write_file(agents_source / "reviewer.md", "agent v1\n")

    skills_target = tree_target(build, "unified-skills", skills_source, skills_destination)
    agents_target = tree_target(build, "pi-agents", agents_source, agents_destination)
    build.safe_install_targets([skills_target, agents_target], manifest_path=manifest_path, force=True)
    original_manifest = manifest_path.read_text()

    write_file(skills_source / "demo" / "SKILL.md", "skill v2\n")
    write_file(agents_source / "reviewer.md", "agent v2\n")

    original_swap_target = build.swap_target_into_place

    def fail_on_agents(stage_path, target):
        if target.name == "pi-agents":
            raise OSError("simulated swap failure")
        return original_swap_target(stage_path, target)

    monkeypatch.setattr(build, "swap_target_into_place", fail_on_agents)

    with pytest.raises(OSError, match="simulated swap failure"):
        build.safe_install_targets([skills_target, agents_target], manifest_path=manifest_path, force=False)

    assert (skills_destination / "demo" / "SKILL.md").read_text() == "skill v1\n"
    assert (agents_destination / "reviewer.md").read_text() == "agent v1\n"
    assert manifest_path.read_text() == original_manifest


def test_install_all_syncs_all_targets_in_one_safe_install_call(tmp_path, monkeypatch):
    build = load_build_module()
    build_dir = tmp_path / "build"
    home = tmp_path / "home"
    global_agents_md = tmp_path / "configs" / "AGENTS.md"

    write_file(build_dir / "skills" / "demo" / "SKILL.md", "skill\n")
    write_file(build_dir / "agents" / "reviewer.md", "agent\n")
    write_file(build_dir / "extensions" / "session-query" / "index.ts", "extension\n")
    write_file(global_agents_md, "agents guidance\n")

    monkeypatch.setattr(build, "BUILD_DIR", build_dir)
    monkeypatch.setattr(
        build,
        "INSTALL_PATHS",
        {
            "claude": home / ".claude" / "skills",
            "unified": home / ".agents" / "skills",
        },
    )
    monkeypatch.setattr(build, "PI_AGENTS_PATH", home / ".pi" / "agent" / "agents")
    monkeypatch.setattr(build, "PI_EXTENSIONS_PATH", home / ".pi" / "agent" / "extensions")
    monkeypatch.setattr(build, "GLOBAL_AGENTS_MD", global_agents_md)
    monkeypatch.setattr(build, "HOME", home)

    calls = []

    def fake_safe_install_targets(targets, *, force=False, manifest_path=build.MANIFEST_PATH):
        calls.append(([target.name for target in targets], force, manifest_path))
        return build.InstallResult(files_written=5, files_removed=0)

    monkeypatch.setattr(build, "safe_install_targets", fake_safe_install_targets)

    build.install_all(force=True)

    assert calls == [
        (
            [
                "claude-skills",
                "unified-skills",
                "pi-agents",
                "pi-extensions",
                "global-agents-md",
            ],
            True,
            build.MANIFEST_PATH,
        )
    ]


def test_install_extensions_syncs_extension_target_in_safe_install_call(tmp_path, monkeypatch):
    build = load_build_module()
    build_dir = tmp_path / "build"
    extensions_path = tmp_path / "home" / ".pi" / "agent" / "extensions"

    write_file(build_dir / "extensions" / "session-query" / "index.ts", "extension\n")

    monkeypatch.setattr(build, "BUILD_DIR", build_dir)
    monkeypatch.setattr(build, "PI_EXTENSIONS_PATH", extensions_path)

    calls = []

    def fake_safe_install_targets(targets, *, force=False, manifest_path=build.MANIFEST_PATH):
        calls.append(([target.name for target in targets], force, manifest_path))
        return build.InstallResult(files_written=1, files_removed=0)

    monkeypatch.setattr(build, "safe_install_targets", fake_safe_install_targets)

    build.install_extensions(force=True)

    assert calls == [(["pi-extensions"], True, build.MANIFEST_PATH)]


def test_clean_manifest_rejects_symlinked_destination_ancestor(tmp_path, monkeypatch):
    build = load_build_module()
    home = tmp_path / "home"
    outside = tmp_path / "outside"
    destination = home / ".agents" / "skills"
    manifest_path = tmp_path / "state" / "install-manifest.json"

    home.mkdir()
    write_file(outside / "skills" / "managed" / "SKILL.md", "do not delete\n")
    (home / ".agents").symlink_to(outside, target_is_directory=True)
    write_file(
        manifest_path,
        json.dumps(
            {
                "version": 1,
                "targets": {
                    "unified-skills": {
                        "path": str(destination),
                        "kind": "tree",
                        "files": {"managed/SKILL.md": "unused"},
                    }
                },
            }
        ),
    )
    monkeypatch.setattr(build, "INSTALL_PATHS", {"unified": destination})
    monkeypatch.setattr(build, "PI_AGENTS_PATH", home / ".pi" / "agent" / "agents")
    monkeypatch.setattr(build, "PI_EXTENSIONS_PATH", home / ".pi" / "agent" / "extensions")
    monkeypatch.setattr(build, "HOME", home)

    with pytest.raises(build.InstallConflict, match="unsafe install target path"):
        build.clean_manifest_install(manifest_path)

    assert (outside / "skills" / "managed" / "SKILL.md").read_text() == "do not delete\n"
    assert manifest_path.exists()


def test_clean_manifest_rejects_targets_outside_known_install_roots(tmp_path, monkeypatch):
    build = load_build_module()
    install_root = tmp_path / "home" / ".agents" / "skills"
    victim = tmp_path / "victim"
    manifest_path = tmp_path / "state" / "install-manifest.json"

    write_file(victim / "data.txt", "do not delete\n")
    write_file(
        manifest_path,
        json.dumps(
            {
                "version": 1,
                "targets": {
                    "unified-skills": {
                        "path": str(victim),
                        "kind": "tree",
                        "files": {"data.txt": "unused"},
                    }
                },
            }
        ),
    )
    monkeypatch.setattr(build, "INSTALL_PATHS", {"unified": install_root})
    monkeypatch.setattr(build, "PI_AGENTS_PATH", tmp_path / "home" / ".pi" / "agent" / "agents")
    monkeypatch.setattr(build, "PI_EXTENSIONS_PATH", tmp_path / "home" / ".pi" / "agent" / "extensions")
    monkeypatch.setattr(build, "HOME", tmp_path / "home")

    with pytest.raises(build.InstallConflict, match="outside known install target"):
        build.clean_manifest_install(manifest_path)

    assert (victim / "data.txt").read_text() == "do not delete\n"
    assert manifest_path.exists()


def test_clean_manifest_rejects_directory_file_entries(tmp_path, monkeypatch):
    build = load_build_module()
    destination = tmp_path / "home" / ".agents" / "skills"
    manifest_path = tmp_path / "state" / "install-manifest.json"

    write_file(destination / "managed" / "local.txt", "do not delete\n")
    write_file(
        manifest_path,
        json.dumps(
            {
                "version": 1,
                "targets": {
                    "unified-skills": {
                        "path": str(destination),
                        "kind": "tree",
                        "files": {"managed": "unused"},
                    }
                },
            }
        ),
    )
    monkeypatch.setattr(build, "INSTALL_PATHS", {"unified": destination})
    monkeypatch.setattr(build, "PI_AGENTS_PATH", tmp_path / "home" / ".pi" / "agent" / "agents")
    monkeypatch.setattr(build, "PI_EXTENSIONS_PATH", tmp_path / "home" / ".pi" / "agent" / "extensions")
    monkeypatch.setattr(build, "HOME", tmp_path / "home")

    with pytest.raises(build.InstallConflict, match="unsafe manifest path"):
        build.clean_manifest_install(manifest_path)

    assert (destination / "managed" / "local.txt").read_text() == "do not delete\n"
    assert manifest_path.exists()


def test_clean_manifest_rejects_symlinked_parent_paths(tmp_path, monkeypatch):
    build = load_build_module()
    destination = tmp_path / "home" / ".agents" / "skills"
    outside = tmp_path / "outside"
    manifest_path = tmp_path / "state" / "install-manifest.json"

    write_file(outside / "SKILL.md", "do not delete\n")
    destination.mkdir(parents=True)
    (destination / "managed").symlink_to(outside, target_is_directory=True)
    write_file(
        manifest_path,
        json.dumps(
            {
                "version": 1,
                "targets": {
                    "unified-skills": {
                        "path": str(destination),
                        "kind": "tree",
                        "files": {"managed/SKILL.md": "unused"},
                    }
                },
            }
        ),
    )
    monkeypatch.setattr(build, "INSTALL_PATHS", {"unified": destination})
    monkeypatch.setattr(build, "PI_AGENTS_PATH", tmp_path / "home" / ".pi" / "agent" / "agents")
    monkeypatch.setattr(build, "PI_EXTENSIONS_PATH", tmp_path / "home" / ".pi" / "agent" / "extensions")
    monkeypatch.setattr(build, "HOME", tmp_path / "home")

    with pytest.raises(build.InstallConflict, match="unsafe manifest path"):
        build.clean_manifest_install(manifest_path)

    assert (outside / "SKILL.md").read_text() == "do not delete\n"
    assert manifest_path.exists()


def test_clean_manifest_rejects_unsafe_relative_paths(tmp_path, monkeypatch):
    build = load_build_module()
    destination = tmp_path / "home" / ".agents" / "skills"
    victim = tmp_path / "home" / ".agents" / "victim.txt"
    manifest_path = tmp_path / "state" / "install-manifest.json"

    write_file(destination / "managed" / "SKILL.md", "managed\n")
    write_file(victim, "do not delete\n")
    write_file(
        manifest_path,
        json.dumps(
            {
                "version": 1,
                "targets": {
                    "unified-skills": {
                        "path": str(destination),
                        "kind": "tree",
                        "files": {"../victim.txt": "unused"},
                    }
                },
            }
        ),
    )
    monkeypatch.setattr(build, "INSTALL_PATHS", {"unified": destination})
    monkeypatch.setattr(build, "PI_AGENTS_PATH", tmp_path / "home" / ".pi" / "agent" / "agents")
    monkeypatch.setattr(build, "PI_EXTENSIONS_PATH", tmp_path / "home" / ".pi" / "agent" / "extensions")
    monkeypatch.setattr(build, "HOME", tmp_path / "home")

    with pytest.raises(build.InstallConflict, match="unsafe manifest path"):
        build.clean_manifest_install(manifest_path)

    assert victim.read_text() == "do not delete\n"
    assert manifest_path.exists()


def test_clean_legacy_skills_rejects_unsafe_manifest_entry(tmp_path, monkeypatch):
    build = load_build_module()
    install_root = tmp_path / "home" / ".agents" / "skills"
    victim = tmp_path / "home" / ".agents" / "victim"

    write_file(install_root / build.SKILLS_MANIFEST, "../victim\n")
    write_file(victim / "SKILL.md", "do not delete\n")
    monkeypatch.setattr(build, "INSTALL_PATHS", {"unified": install_root})
    monkeypatch.setattr(build, "PI_AGENTS_PATH", tmp_path / "home" / ".pi" / "agent" / "agents")
    monkeypatch.setattr(build, "PI_EXTENSIONS_PATH", tmp_path / "home" / ".pi" / "agent" / "extensions")
    monkeypatch.setattr(build, "HOME", tmp_path / "home")

    with pytest.raises(build.InstallConflict, match="unsafe legacy manifest entry"):
        build.clean_legacy_installs()

    assert (victim / "SKILL.md").read_text() == "do not delete\n"
    assert (install_root / build.SKILLS_MANIFEST).exists()


def test_clean_legacy_extensions_rejects_unsafe_manifest_entry(tmp_path, monkeypatch):
    build = load_build_module()
    install_root = tmp_path / "home" / ".pi" / "agent" / "extensions"
    victim = tmp_path / "home" / ".pi" / "agent" / "victim"

    write_file(install_root / build.PI_EXTENSIONS_MANIFEST, "../victim\n")
    write_file(victim / "index.ts", "do not delete\n")
    monkeypatch.setattr(build, "INSTALL_PATHS", {})
    monkeypatch.setattr(build, "PI_AGENTS_PATH", tmp_path / "home" / ".pi" / "agent" / "agents")
    monkeypatch.setattr(build, "PI_EXTENSIONS_PATH", install_root)
    monkeypatch.setattr(build, "HOME", tmp_path / "home")

    with pytest.raises(build.InstallConflict, match="unsafe legacy manifest entry"):
        build.clean_legacy_installs()

    assert (victim / "index.ts").read_text() == "do not delete\n"
    assert (install_root / build.PI_EXTENSIONS_MANIFEST).exists()


def test_clean_legacy_skills_refuses_modified_managed_directory(tmp_path, monkeypatch):
    build = load_build_module()
    install_root = tmp_path / "home" / ".agents" / "skills"
    build_dir = tmp_path / "build"

    write_file(install_root / build.SKILLS_MANIFEST, "demo\n")
    write_file(install_root / "demo" / "SKILL.md", "local skill\n")
    write_file(build_dir / "skills" / "demo" / "SKILL.md", "repo skill\n")
    monkeypatch.setattr(build, "INSTALL_PATHS", {"unified": install_root})
    monkeypatch.setattr(build, "BUILD_DIR", build_dir)
    monkeypatch.setattr(build, "PI_AGENTS_PATH", tmp_path / "home" / ".pi" / "agent" / "agents")
    monkeypatch.setattr(build, "PI_EXTENSIONS_PATH", tmp_path / "home" / ".pi" / "agent" / "extensions")
    monkeypatch.setattr(build, "HOME", tmp_path / "home")

    with pytest.raises(build.InstallConflict, match="locally modified legacy install directory"):
        build.clean_legacy_installs()

    assert (install_root / "demo" / "SKILL.md").read_text() == "local skill\n"
    assert (install_root / build.SKILLS_MANIFEST).exists()


def test_clean_legacy_extensions_refuses_modified_managed_directory(tmp_path, monkeypatch):
    build = load_build_module()
    install_root = tmp_path / "home" / ".pi" / "agent" / "extensions"
    build_dir = tmp_path / "build"

    write_file(install_root / build.PI_EXTENSIONS_MANIFEST, "demo\n")
    write_file(install_root / "demo" / "index.ts", "local extension\n")
    write_file(build_dir / "extensions" / "demo" / "index.ts", "repo extension\n")
    monkeypatch.setattr(build, "INSTALL_PATHS", {})
    monkeypatch.setattr(build, "BUILD_DIR", build_dir)
    monkeypatch.setattr(build, "PI_AGENTS_PATH", tmp_path / "home" / ".pi" / "agent" / "agents")
    monkeypatch.setattr(build, "PI_EXTENSIONS_PATH", install_root)
    monkeypatch.setattr(build, "HOME", tmp_path / "home")

    with pytest.raises(build.InstallConflict, match="locally modified legacy install directory"):
        build.clean_legacy_installs()

    assert (install_root / "demo" / "index.ts").read_text() == "local extension\n"
    assert (install_root / build.PI_EXTENSIONS_MANIFEST).exists()


def test_clean_legacy_agents_refuses_modified_file_without_manifest(tmp_path, monkeypatch):
    build = load_build_module()
    source = tmp_path / "agents-source"
    installed = tmp_path / "home" / ".pi" / "agent" / "agents"

    write_file(source / "code-reviewer.md", "repo agent\n")
    write_file(installed / "code-reviewer.md", "local agent\n")
    monkeypatch.setattr(build, "INSTALL_PATHS", {})
    monkeypatch.setattr(build, "AGENTS_DIR", source)
    monkeypatch.setattr(build, "PI_AGENTS_PATH", installed)
    monkeypatch.setattr(build, "PI_EXTENSIONS_PATH", tmp_path / "home" / ".pi" / "agent" / "extensions")
    monkeypatch.setattr(build, "HOME", tmp_path / "home")

    with pytest.raises(build.InstallConflict, match="locally modified legacy install file"):
        build.clean_legacy_installs()

    assert (installed / "code-reviewer.md").read_text() == "local agent\n"


def test_clean_legacy_global_agents_refuses_modified_file_without_manifest(tmp_path, monkeypatch):
    build = load_build_module()
    source = tmp_path / "configs" / "AGENTS.md"
    installed = tmp_path / "home" / ".agents" / "AGENTS.md"

    write_file(source, "repo guidance\n")
    write_file(installed, "local guidance\n")
    monkeypatch.setattr(build, "INSTALL_PATHS", {})
    monkeypatch.setattr(build, "AGENTS_DIR", tmp_path / "agents-source")
    monkeypatch.setattr(build, "PI_AGENTS_PATH", tmp_path / "home" / ".pi" / "agent" / "agents")
    monkeypatch.setattr(build, "PI_EXTENSIONS_PATH", tmp_path / "home" / ".pi" / "agent" / "extensions")
    monkeypatch.setattr(build, "GLOBAL_AGENTS_MD", source)
    monkeypatch.setattr(build, "HOME", tmp_path / "home")

    with pytest.raises(build.InstallConflict, match="locally modified legacy install file"):
        build.clean_legacy_installs()

    assert installed.read_text() == "local guidance\n"


def test_clean_command_runs_under_install_lock(monkeypatch):
    build = load_build_module()
    events = []

    @contextmanager
    def fake_install_lock():
        events.append("lock-enter")
        yield
        events.append("lock-exit")

    monkeypatch.setattr(build, "install_lock", fake_install_lock)
    monkeypatch.setattr(build, "clean", lambda: events.append("clean"))
    monkeypatch.setattr(sys, "argv", ["build.py", "clean"])

    build.main()

    assert events == ["lock-enter", "clean", "lock-exit"]


def test_empty_xdg_state_home_uses_default_state_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("XDG_STATE_HOME", "")

    build = load_build_module()

    assert build.STATE_DIR == tmp_path / "home" / ".local" / "state" / "dotagents"


def test_install_command_without_manifest_fails_for_non_empty_destination(tmp_path):
    env = {
        "HOME": str(tmp_path / "home"),
        "XDG_STATE_HOME": str(tmp_path / "state"),
    }
    write_file(tmp_path / "home" / ".agents" / "skills" / "custom" / "SKILL.md", "manual\n")

    import os
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, str(BUILD_SCRIPT), "install-skills"],
        cwd=ROOT,
        env={**os.environ, **env},
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "FORCE=1" in result.stderr or "FORCE=1" in result.stdout
    assert "Traceback" not in result.stderr
    assert (tmp_path / "home" / ".agents" / "skills" / "custom" / "SKILL.md").read_text() == "manual\n"
