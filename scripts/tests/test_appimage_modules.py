import re
import unittest
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[2]
IMPORT = re.compile(r"^\s*(?:from|import) PySide6\.(Qt\w+)", re.M)


def listed_modules() -> set[str]:
    text = (REPOSITORY / "packaging" / "appimage" / "pyside-modules.txt").read_text()
    return {"Qt" + line for line in text.split()}


def imported_modules() -> set[str]:
    sources = (REPOSITORY / "kondor").rglob("*.py")
    return {name for path in sources for name in IMPORT.findall(path.read_text(encoding="utf-8"))}


class PysideModulesTest(unittest.TestCase):
    def test_lists_every_pyside_module_the_package_imports(self):
        self.assertEqual(imported_modules() - listed_modules(), set())


if __name__ == "__main__":
    unittest.main()
