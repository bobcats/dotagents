import importlib
import tempfile
import unittest
from pathlib import Path


class BuildExtensionsTests(unittest.TestCase):
    def setUp(self):
        self.build = importlib.import_module("scripts.build")
        self.original_pi_extensions_dir = getattr(self.build, "PI_EXTENSIONS_DIR", None)
        self.original_build_dir = self.build.BUILD_DIR
        self.original_pi_extensions_path = getattr(self.build, "PI_EXTENSIONS_PATH", None)

    def tearDown(self):
        if self.original_pi_extensions_dir is not None:
            self.build.PI_EXTENSIONS_DIR = self.original_pi_extensions_dir
        if self.original_pi_extensions_path is not None:
            self.build.PI_EXTENSIONS_PATH = self.original_pi_extensions_path
        self.build.BUILD_DIR = self.original_build_dir

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

    def test_install_extensions_copies_built_extensions_into_pi_extensions_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            built = root / "build" / "extensions" / "session-query"
            built.mkdir(parents=True)
            (built / "index.ts").write_text("export default function () {}\n")

            self.build.BUILD_DIR = root / "build"
            self.build.PI_EXTENSIONS_PATH = root / "installed-extensions"

            self.build.install_extensions()

            self.assertTrue((self.build.PI_EXTENSIONS_PATH / "session-query" / "index.ts").exists())

    def test_install_extensions_removes_stale_managed_extensions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            built = root / "build" / "extensions" / "session-query"
            built.mkdir(parents=True)
            (built / "index.ts").write_text("export default function () {}\n")

            installed = root / "installed-extensions"
            stale = installed / "old-ext"
            stale.mkdir(parents=True)
            (stale / "index.ts").write_text("export default function () {}\n")

            unmanaged = installed / "third-party"
            unmanaged.mkdir(parents=True)
            (unmanaged / "index.ts").write_text("export default function () {}\n")

            manifest = installed / ".dotagents-managed-extensions"
            manifest.write_text("old-ext\nsession-query\n")

            self.build.BUILD_DIR = root / "build"
            self.build.PI_EXTENSIONS_PATH = installed

            self.build.install_extensions()

            self.assertFalse((installed / "old-ext").exists())
            self.assertTrue((installed / "session-query" / "index.ts").exists())
            self.assertTrue((installed / "third-party" / "index.ts").exists())
            self.assertEqual(manifest.read_text(), "session-query\n")


if __name__ == "__main__":
    unittest.main()
