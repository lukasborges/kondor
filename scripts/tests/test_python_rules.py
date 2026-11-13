import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from codequality.python import find_python_functions
from codequality.rules import check_source

PATH = "kondor/a.py"


def statements(count: int, indent: str = "    ") -> str:
    return "".join("%swork()\n" % indent for _ in range(count))


def rules_of(source: str, path: str = PATH) -> set:
    return {violation.rule for violation in check_source(path, source)}


def only_function(source: str):
    return find_python_functions(PATH, source)[0]


class FunctionLengthTest(unittest.TestCase):
    def test_ten_lines_pass(self):
        self.assertEqual(rules_of("def run():\n" + statements(10)), set())

    def test_eleven_lines_fail(self):
        self.assertEqual(rules_of("def run():\n" + statements(11)), {"function-length"})

    def test_blank_lines_are_not_counted(self):
        self.assertEqual(only_function("def run():\n    work()\n\n    work()\n").body_lines, 2)

    def test_docstring_counts_as_a_body_line(self):
        source = 'def run():\n    """Text."""\n    work()\n'
        self.assertEqual(only_function(source).body_lines, 2)

    def test_pytests_may_use_twenty_lines(self):
        source = "def test_run():\n" + statements(20)
        self.assertEqual(rules_of(source, "pytests/test_a.py"), set())
        self.assertEqual(rules_of(source + statements(1), "pytests/test_a.py"), {"function-length"})

    def test_method_key_is_qualified(self):
        function = only_function("class Foo:\n    def run(self):\n        work()\n")
        self.assertEqual(function.key, "kondor/a.py::Foo.run")


class ParametersTest(unittest.TestCase):
    def test_self_is_not_counted(self):
        source = "class Foo:\n    def run(self, a, b, c):\n        work()\n"
        self.assertEqual(only_function(source).parameters, 3)

    def test_cls_is_not_counted(self):
        source = "class Foo:\n    @classmethod\n    def run(cls, a):\n        work()\n"
        self.assertEqual(only_function(source).parameters, 1)

    def test_every_parameter_kind_is_counted(self):
        source = "def run(a, /, b, *args, c, **kwargs):\n    work()\n"
        self.assertEqual(only_function(source).parameters, 5)
        self.assertEqual(rules_of(source), {"parameters"})


class NestingTest(unittest.TestCase):
    def test_two_levels_pass(self):
        source = "def run():\n    if a:\n        for b in c:\n            work()\n"
        self.assertEqual(only_function(source).nesting, 2)
        self.assertEqual(rules_of(source), set())

    def test_three_levels_fail(self):
        source = "def run():\n    if a:\n        for b in c:\n            with d:\n                work()\n"
        self.assertEqual(rules_of(source), {"nesting"})

    def test_elif_stays_at_the_depth_of_its_if(self):
        source = "def run():\n    if a:\n        work()\n    elif b:\n        work()\n    elif c:\n        work()\n"
        self.assertEqual(only_function(source).nesting, 1)

    def test_try_handler_and_match_case_count(self):
        source = "def run():\n    try:\n        match a:\n            case 1:\n                work()\n    except E:\n        pass\n"
        self.assertEqual(only_function(source).nesting, 2)

    def test_nested_def_is_measured_on_its_own(self):
        source = "def run():\n    if a:\n        def inner():\n            if b:\n                work()\n"
        functions = find_python_functions(PATH, source)
        self.assertEqual([f.nesting for f in functions], [1, 1])
        self.assertEqual(functions[1].key, "kondor/a.py::run.inner")


class CommentsTest(unittest.TestCase):
    def test_hash_comment_fails(self):
        self.assertEqual(rules_of("# note\nVALUE = 1\n"), {"comments"})

    def test_docstring_fails(self):
        self.assertEqual(rules_of('def run():\n    """Text."""\n'), {"comments"})

    def test_module_docstring_fails(self):
        self.assertEqual(rules_of('"""Text."""\n'), {"comments"})

    def test_shebang_on_first_line_passes(self):
        self.assertEqual(rules_of("#!/usr/bin/env python3\nVALUE = 1\n"), set())

    def test_spdx_passes(self):
        self.assertEqual(rules_of("# SPDX-License-Identifier: GPL-3.0-or-later\nVALUE = 1\n"), set())

    def test_workaround_link_passes(self):
        source = "# why\n# https://bugreports.qt.io/browse/QTBUG-1\nVALUE = 1\n"
        self.assertEqual(rules_of(source), set())

    def test_type_ignore_with_code_passes(self):
        self.assertEqual(rules_of("VALUE = f()  # type: ignore[misc]\n"), set())

    def test_noqa_with_code_passes(self):
        self.assertEqual(rules_of("VALUE = f()  # noqa: E501\n"), set())

    def test_bare_noqa_fails(self):
        self.assertEqual(rules_of("VALUE = f()  # noqa\n"), {"comments"})

    def test_bare_type_ignore_fails(self):
        self.assertEqual(rules_of("VALUE = f()  # type: ignore\n"), {"comments"})

    def test_hash_inside_a_string_is_not_a_comment(self):
        self.assertEqual(rules_of('VALUE = "# note"\n'), set())


class FileLengthTest(unittest.TestCase):
    def test_file_over_two_hundred_lines_fails(self):
        self.assertEqual(rules_of("VALUE = 1\n" * 201), {"file-length"})


if __name__ == "__main__":
    unittest.main()
