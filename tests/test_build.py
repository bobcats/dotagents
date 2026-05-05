import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD_SCRIPT = ROOT / "scripts" / "build.py"


def load_build_module():
    spec = importlib.util.spec_from_file_location("dotagents_build_test_build", BUILD_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["dotagents_build_test_build"] = module
    spec.loader.exec_module(module)
    return module


class BuildSkillsTests(unittest.TestCase):
    def setUp(self):
        self.build = load_build_module()
        self.original_build_dir = self.build.BUILD_DIR
        self.original_install_paths = dict(self.build.INSTALL_PATHS)
        self.original_home = self.build.HOME
        self.original_agents_dir = self.build.AGENTS_DIR
        self.original_pi_agents_path = self.build.PI_AGENTS_PATH
        self.original_pi_extensions_path = self.build.PI_EXTENSIONS_PATH
        self.original_manifest_path = getattr(self.build, "MANIFEST_PATH", None)
        self.original_state_dir = getattr(self.build, "STATE_DIR", None)
        self.original_lock_path = getattr(self.build, "LOCK_PATH", None)

    def tearDown(self):
        self.build.BUILD_DIR = self.original_build_dir
        self.build.INSTALL_PATHS = self.original_install_paths
        self.build.HOME = self.original_home
        self.build.AGENTS_DIR = self.original_agents_dir
        self.build.PI_AGENTS_PATH = self.original_pi_agents_path
        self.build.PI_EXTENSIONS_PATH = self.original_pi_extensions_path
        if self.original_manifest_path is not None:
            self.build.MANIFEST_PATH = self.original_manifest_path
        if self.original_state_dir is not None:
            self.build.STATE_DIR = self.original_state_dir
        if self.original_lock_path is not None:
            self.build.LOCK_PATH = self.original_lock_path

    def configure_install_state(self, root: Path) -> None:
        self.build.STATE_DIR = root / "state" / "dotagents"
        self.build.MANIFEST_PATH = self.build.STATE_DIR / "install-manifest.json"
        self.build.LOCK_PATH = self.build.STATE_DIR / "install.lock"

    def test_install_skills_preserves_unmanaged_skills_after_manifest_bootstrap(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            built = root / "build" / "skills" / "new-skill"
            built.mkdir(parents=True)
            (built / "SKILL.md").write_text("---\nname: new-skill\n---\nv1\n")

            installed = root / "installed-skills"
            self.build.BUILD_DIR = root / "build"
            self.build.INSTALL_PATHS = {"unified": installed}
            self.configure_install_state(root)

            self.build.install_skills(force=True)

            unmanaged = installed / "third-party"
            unmanaged.mkdir(parents=True)
            (unmanaged / "SKILL.md").write_text("---\nname: third-party\n---\n")
            (built / "SKILL.md").write_text("---\nname: new-skill\n---\nv2\n")

            self.build.install_skills()

            self.assertEqual((installed / "new-skill" / "SKILL.md").read_text(), "---\nname: new-skill\n---\nv2\n")
            self.assertTrue((installed / "third-party" / "SKILL.md").exists())

    def test_install_skills_removes_stale_managed_skills(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fresh = root / "build" / "skills" / "fresh-skill"
            fresh.mkdir(parents=True)
            (fresh / "SKILL.md").write_text("---\nname: fresh-skill\n---\n")
            stale_source = root / "build" / "skills" / "old-skill"
            stale_source.mkdir(parents=True)
            (stale_source / "SKILL.md").write_text("---\nname: old-skill\n---\n")

            installed = root / "installed-skills"
            self.build.BUILD_DIR = root / "build"
            self.build.INSTALL_PATHS = {"unified": installed}
            self.configure_install_state(root)
            self.build.install_skills(force=True)

            shutil.rmtree(stale_source)
            unmanaged = installed / "third-party"
            unmanaged.mkdir(parents=True)
            (unmanaged / "SKILL.md").write_text("---\nname: third-party\n---\n")

            self.build.install_skills()

            self.assertFalse((installed / "old-skill").exists())
            self.assertTrue((installed / "fresh-skill" / "SKILL.md").exists())
            self.assertTrue((installed / "third-party" / "SKILL.md").exists())

    def test_clean_removes_only_manifest_managed_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            installed = root / "installed-skills"

            managed = installed / "managed-skill"
            managed.mkdir(parents=True)
            (managed / "SKILL.md").write_text("---\nname: managed-skill\n---\n")

            unmanaged = installed / "third-party"
            unmanaged.mkdir(parents=True)
            (unmanaged / "SKILL.md").write_text("---\nname: third-party\n---\n")

            self.build.INSTALL_PATHS = {"unified": installed}
            self.build.BUILD_DIR = root / "build"
            self.build.HOME = root / "home"
            self.build.AGENTS_DIR = root / "agents-source"
            self.build.PI_AGENTS_PATH = root / "pi-agents"
            self.build.PI_EXTENSIONS_PATH = root / "pi-extensions"
            self.configure_install_state(root)
            self.build.MANIFEST_PATH.parent.mkdir(parents=True)
            self.build.MANIFEST_PATH.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "targets": {
                            "unified-skills": {
                                "path": str(installed),
                                "kind": "tree",
                                "files": {"managed-skill/SKILL.md": "unused"},
                            }
                        },
                    }
                )
            )

            self.build.clean()

            self.assertFalse((installed / "managed-skill").exists())
            self.assertTrue((installed / "third-party" / "SKILL.md").exists())
            self.assertFalse(self.build.MANIFEST_PATH.exists())


class BuildExtensionsTests(unittest.TestCase):
    def setUp(self):
        self.build = load_build_module()
        self.original_pi_extensions_dir = getattr(self.build, "PI_EXTENSIONS_DIR", None)
        self.original_build_dir = self.build.BUILD_DIR
        self.original_pi_extensions_path = getattr(self.build, "PI_EXTENSIONS_PATH", None)
        self.original_manifest_path = getattr(self.build, "MANIFEST_PATH", None)
        self.original_state_dir = getattr(self.build, "STATE_DIR", None)
        self.original_lock_path = getattr(self.build, "LOCK_PATH", None)

    def tearDown(self):
        if self.original_pi_extensions_dir is not None:
            self.build.PI_EXTENSIONS_DIR = self.original_pi_extensions_dir
        if self.original_pi_extensions_path is not None:
            self.build.PI_EXTENSIONS_PATH = self.original_pi_extensions_path
        self.build.BUILD_DIR = self.original_build_dir
        if self.original_manifest_path is not None:
            self.build.MANIFEST_PATH = self.original_manifest_path
        if self.original_state_dir is not None:
            self.build.STATE_DIR = self.original_state_dir
        if self.original_lock_path is not None:
            self.build.LOCK_PATH = self.original_lock_path

    def configure_install_state(self, root: Path) -> None:
        self.build.STATE_DIR = root / "state" / "dotagents"
        self.build.MANIFEST_PATH = self.build.STATE_DIR / "install-manifest.json"
        self.build.LOCK_PATH = self.build.STATE_DIR / "install.lock"

    def test_build_extensions_copies_extension_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "pi-extensions"
            ext_dir = source / "handoff"
            ext_dir.mkdir(parents=True)
            (ext_dir / "index.ts").write_text("export default function () {}\n")
            (ext_dir / "events.ts").write_text("export const value = 1\n")

            self.build.PI_EXTENSIONS_DIR = source
            self.build.BUILD_DIR = root / "build"

            self.build.build_extensions()

            self.assertTrue((self.build.BUILD_DIR / "extensions" / "handoff" / "index.ts").exists())
            self.assertTrue((self.build.BUILD_DIR / "extensions" / "handoff" / "events.ts").exists())

    def test_install_extensions_preserves_unmanaged_and_removes_stale_after_bootstrap(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fresh = root / "build" / "extensions" / "session-query"
            fresh.mkdir(parents=True)
            (fresh / "index.ts").write_text("export default function () {}\n")
            stale_source = root / "build" / "extensions" / "old-ext"
            stale_source.mkdir(parents=True)
            (stale_source / "index.ts").write_text("export default function () {}\n")

            installed = root / "installed-extensions"
            self.build.BUILD_DIR = root / "build"
            self.build.PI_EXTENSIONS_PATH = installed
            self.configure_install_state(root)
            self.build.install_extensions(force=True)

            shutil.rmtree(stale_source)
            unmanaged = installed / "third-party"
            unmanaged.mkdir(parents=True)
            (unmanaged / "index.ts").write_text("export default function () {}\n")

            self.build.install_extensions()

            self.assertFalse((installed / "old-ext").exists())
            self.assertTrue((installed / "session-query" / "index.ts").exists())
            self.assertTrue((installed / "third-party" / "index.ts").exists())


if __name__ == "__main__":
    unittest.main()
