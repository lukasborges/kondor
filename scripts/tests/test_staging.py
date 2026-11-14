import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from staging.bundle import qrc_text
from staging.cmakeresources import cmake_resource_entries
from staging.qmlmodule import DuplicateBaseNameError, stage_qml_module
from staging.resources import ResourceEntry, static_resource_entries
from staging.stage import stage
from staging.tools import MissingToolError

REPOSITORY = Path(__file__).resolve().parents[2]


def write(root: Path, relative: str, text: str = "") -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class ResourceTableTest(unittest.TestCase):
    def test_matches_the_cmake_resource_blocks(self):
        cmake = (REPOSITORY / "CMakeLists.txt").read_text(encoding="utf-8")
        self.assertEqual(static_resource_entries(), cmake_resource_entries(cmake))

    def test_keeps_the_cpp_resource_paths(self):
        paths = {entry.resource_path for entry in static_resource_entries()}
        self.assertLessEqual(
            {"/packaging/kondor.png", "/reader/Readability.js", "/scripts/passwords.js",
             "/scripts/usergm.js", "/LICENSE"}, paths)

    def test_qrc_lists_every_entry_with_its_alias(self):
        text = qrc_text([ResourceEntry("/i18n/kondor_de.qm", "/tmp/kondor_de.qm")], Path("/repo"))
        self.assertIn('<file alias="i18n/kondor_de.qm">/tmp/kondor_de.qm</file>', text)


class QmlModuleTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.qml = self.root / "qml"
        self.out = self.root / "out"

    def tearDown(self):
        self.directory.cleanup()

    def test_qmldir_has_one_sorted_line_per_qml_file(self):
        write(self.qml, "common/InlineBar.qml")
        write(self.qml, "Main.qml")
        write(self.qml, "common/helper.js")
        module = stage_qml_module(self.qml, self.out)
        lines = (module / "qmldir").read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines, ["module Kondor", "Main 1.0 Main.qml", "InlineBar 1.0 common/InlineBar.qml"])

    def test_copies_qml_and_js_keeping_the_tree(self):
        write(self.qml, "common/InlineBar.qml")
        write(self.qml, "common/helper.js")
        module = stage_qml_module(self.qml, self.out)
        self.assertTrue((module / "common" / "InlineBar.qml").exists())
        self.assertTrue((module / "common" / "helper.js").exists())

    def test_duplicate_base_names_fail_naming_both_files(self):
        write(self.qml, "a/Same.qml")
        write(self.qml, "b/Same.qml")
        with self.assertRaises(DuplicateBaseNameError) as raised:
            stage_qml_module(self.qml, self.out)
        self.assertIn("a/Same.qml", str(raised.exception))
        self.assertIn("b/Same.qml", str(raised.exception))


class MissingToolTest(unittest.TestCase):
    def test_names_the_fedora_package(self):
        with mock.patch.dict(os.environ, {"PATH": ""}), self.assertRaises(MissingToolError) as raised:
            stage(REPOSITORY, Path(tempfile.gettempdir()) / "unused-stage")
        self.assertIn("pyside6-tools", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
