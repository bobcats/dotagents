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


def test_install_without_manifest_requires_force_and_does_not_write(tmp_path):
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


def test_force_bootstrap_replaces_tree_and_writes_manifest(tmp_path):
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
    assert not (destination / "stale" / "SKILL.md").exists()

    manifest = json.loads(manifest_path.read_text())
    assert manifest["version"] == 1
    assert set(manifest["targets"]) == {"unified-skills"}
    assert set(manifest["targets"]["unified-skills"]["files"]) == {"demo/SKILL.md"}


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


def test_install_command_without_manifest_fails_before_installing(tmp_path):
    env = {
        "HOME": str(tmp_path / "home"),
        "XDG_STATE_HOME": str(tmp_path / "state"),
    }

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
    assert not (tmp_path / "home" / ".agents" / "skills").exists()
