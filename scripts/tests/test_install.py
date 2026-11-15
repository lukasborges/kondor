import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from staging.install import install

REPOSITORY = Path(__file__).resolve().parents[2]


def write(path: Path, text: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class InstallLayoutTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        root = Path(self.directory.name)
        staged = root / "staged"
        for name in ("kondor.rcc", "kondor.qrc", "i18n/kondor_de.qm", "qml/Kondor/qmldir"):
            write(staged / name)
        self.prefix = root / "usr"
        install(REPOSITORY, staged, self.prefix)
        self.share = self.prefix / "share" / "kondor"

    def tearDown(self):
        self.directory.cleanup()

    def test_installs_the_staged_files_without_the_qrc_and_translations(self):
        self.assertTrue((self.share / "kondor.rcc").exists())
        self.assertTrue((self.share / "qml" / "Kondor" / "qmldir").exists())
        self.assertFalse((self.share / "kondor.qrc").exists())
        self.assertFalse((self.share / "i18n").exists())

    def test_installs_the_python_package_without_the_page_scripts(self):
        self.assertTrue((self.share / "kondor" / "__main__.py").exists())
        self.assertEqual(list((self.share / "kondor").rglob("*.js")), [])

    def test_installs_an_executable_launcher(self):
        self.assertTrue(os.access(self.prefix / "bin" / "kondor", os.X_OK))

    def test_installs_the_desktop_integration_files(self):
        self.assertTrue((self.prefix / "share" / "applications" / "kondor.desktop").exists())
        self.assertTrue(
            (
                self.prefix / "share" / "icons" / "hicolor" / "scalable" / "apps" / "kondor.svg"
            ).exists()
        )


if __name__ == "__main__":
    unittest.main()
