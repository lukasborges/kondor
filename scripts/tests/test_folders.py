import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from codequality.folders import all_folders, folder_problems


def make_file(root: str, path: str, content: str = "") -> None:
    os.makedirs(os.path.dirname(os.path.join(root, path)), exist_ok=True)
    with open(os.path.join(root, path), "w") as handle:
        handle.write(content)


def make_folder(root: str, folder: str, files: int) -> None:
    os.makedirs(os.path.join(root, folder), exist_ok=True)
    for number in range(files):
        open(os.path.join(root, folder, "f%d.cpp" % number), "w").close()


class FolderRulesTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = self.directory.name

    def tearDown(self):
        self.directory.cleanup()

    def problems(self) -> list:
        return folder_problems(self.root, all_folders(self.root))

    def test_ten_files_pass(self):
        make_folder(self.root, "src/history", 10)
        self.assertEqual(self.problems(), [])

    def test_eleven_files_fail(self):
        make_folder(self.root, "src/history", 11)
        self.assertEqual(self.problems(), ["src/history/: folder files: 11 > 10"])

    def test_test_data_is_ignored(self):
        make_folder(self.root, "tests/data/extensions", 30)
        self.assertEqual(self.problems(), [])

    def test_pytests_data_is_ignored(self):
        make_folder(self.root, "pytests/data/extensions", 30)
        self.assertEqual(self.problems(), [])

    def test_pycache_is_never_in_scope(self):
        make_folder(self.root, "kondor/core/__pycache__", 30)
        self.assertEqual(self.problems(), [])

    def test_empty_init_does_not_count(self):
        make_folder(self.root, "kondor/core", 10)
        make_file(self.root, "kondor/core/__init__.py")
        self.assertEqual(self.problems(), [])

    def test_non_empty_init_counts(self):
        make_folder(self.root, "kondor/core", 10)
        make_file(self.root, "kondor/core/__init__.py", "VALUE = 1\n")
        self.assertEqual(self.problems(), ["kondor/core/: folder files: 11 > 10"])

    def test_two_levels_pass(self):
        make_folder(self.root, "src/browser/tabs/features", 1)
        self.assertEqual(self.problems(), [])

    def test_three_levels_fail(self):
        make_folder(self.root, "src/browser/tabs/features/deep", 1)
        self.assertEqual(self.problems(), ["src/browser/tabs/features/deep/: folder depth: 3 > 2"])


if __name__ == "__main__":
    unittest.main()
