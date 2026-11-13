import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from codequality.folders import all_folders, folder_problems


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

    def test_two_levels_pass(self):
        make_folder(self.root, "src/browser/tabs/features", 1)
        self.assertEqual(self.problems(), [])

    def test_three_levels_fail(self):
        make_folder(self.root, "src/browser/tabs/features/deep", 1)
        self.assertEqual(self.problems(), ["src/browser/tabs/features/deep/: folder depth: 3 > 2"])


if __name__ == "__main__":
    unittest.main()
