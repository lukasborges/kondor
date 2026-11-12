import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from codequality import baseline as bl
from codequality.cli import run
from test_check_code_quality import cpp_function


class BaselineTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.root, "src"))
        self.baseline_file = os.path.join(self.root, "baseline.json")

    def write_source(self, name: str, content: str) -> None:
        with open(os.path.join(self.root, "src", name), "w", encoding="utf-8") as handle:
            handle.write(content)

    def run_checker(self, *arguments: str):
        output = io.StringIO()
        with redirect_stdout(output):
            code = run(["--root", self.root, "--baseline", self.baseline_file] + list(arguments))
        return code, output.getvalue()

    def read_baseline(self) -> dict:
        with open(self.baseline_file, encoding="utf-8") as handle:
            return json.load(handle)

    def test_existing_offender_passes(self):
        self.write_source("a.cpp", cpp_function(12))
        self.run_checker("--init-baseline")
        self.assertEqual(self.run_checker()[0], 0)

    def test_offender_that_grows_fails(self):
        self.write_source("a.cpp", cpp_function(12))
        self.run_checker("--init-baseline")
        self.write_source("a.cpp", cpp_function(13))
        code, output = self.run_checker()
        self.assertEqual(code, 1)
        self.assertIn("grew from baseline 12", output)

    def test_fixed_offender_must_leave_the_baseline(self):
        self.write_source("a.cpp", cpp_function(12))
        self.run_checker("--init-baseline")
        self.write_source("a.cpp", cpp_function(3))
        code, output = self.run_checker()
        self.assertEqual(code, 1)
        self.assertIn("fixed: remove it from the baseline", output)

    def test_new_offender_fails(self):
        self.write_source("a.cpp", cpp_function(3))
        self.run_checker("--init-baseline")
        self.write_source("b.cpp", cpp_function(12))
        code, output = self.run_checker()
        self.assertEqual(code, 1)
        self.assertIn("src/b.cpp:2: function-length: 12 > 10", output)

    def test_update_removes_fixed_and_lowers_values(self):
        self.write_source("a.cpp", cpp_function(12) + cpp_function(12, "void Foo::two()"))
        self.run_checker("--init-baseline")
        self.write_source("a.cpp", cpp_function(11) + cpp_function(3, "void Foo::two()"))
        self.assertEqual(self.run_checker("--update-baseline")[0], 0)
        self.assertEqual(self.read_baseline()["function-length"], {"src/a.cpp::Foo::run": 11})

    def test_update_refuses_to_add_entries(self):
        self.write_source("a.cpp", cpp_function(3))
        self.run_checker("--init-baseline")
        self.write_source("a.cpp", cpp_function(12))
        before = self.read_baseline()
        self.assertEqual(self.run_checker("--update-baseline")[0], 1)
        self.assertEqual(self.read_baseline(), before)

    def test_init_refuses_to_overwrite(self):
        self.write_source("a.cpp", cpp_function(3))
        self.run_checker("--init-baseline")
        self.assertEqual(self.run_checker("--init-baseline")[0], 1)

    def test_path_of_key(self):
        self.assertEqual(bl.path_of("src/a.cpp::Foo::run"), "src/a.cpp")


if __name__ == "__main__":
    unittest.main()
