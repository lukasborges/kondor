import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from codequality.rules import check_source


def body(lines: int) -> str:
    return "".join("    work();\n" for _ in range(lines))


def cpp_function(lines: int, signature: str = "void Foo::run()") -> str:
    return "%s\n{\n%s}\n" % (signature, body(lines))


def rules_of(path: str, source: str) -> set:
    return {violation.rule for violation in check_source(path, source)}


class FunctionLengthTest(unittest.TestCase):
    def test_ten_lines_pass(self):
        self.assertEqual(rules_of("src/a.cpp", cpp_function(10)), set())

    def test_eleven_lines_fail(self):
        self.assertEqual(rules_of("src/a.cpp", cpp_function(11)), {"function-length"})

    def test_tests_may_use_twenty_lines(self):
        self.assertEqual(rules_of("tests/a/tst_a.cpp", cpp_function(20)), set())
        self.assertEqual(rules_of("tests/a/tst_a.cpp", cpp_function(21)), {"function-length"})

    def test_inline_method_in_class_is_found(self):
        source = "class Foo {\npublic:\n    void run() {\n%s    }\n};\n" % body(11)
        violation = check_source("src/a.h", source)[0]
        self.assertEqual(violation.key, "src/a.h::Foo::run")

    def test_constructor_with_initializer_list_is_found(self):
        source = "Foo::Foo() : m_a(1), m_b(2)\n{\n%s}\n" % body(11)
        self.assertEqual(check_source("src/a.cpp", source)[0].key, "src/a.cpp::Foo::Foo")

    def test_braces_in_strings_and_comments_are_ignored(self):
        source = 'void run()\n{\n    s = "}}";\n    // {\n}\n'
        self.assertEqual(rules_of("src/a.cpp", source), {"comments"})

    def test_raw_string_is_ignored(self):
        source = 'const char *kText = R"x(\n{ { {\n)x";\n' + cpp_function(1)
        self.assertEqual(rules_of("src/a.cpp", source), set())

    def test_if_blocks_are_not_functions(self):
        source = "void run()\n{\n    if (a) {\n        b();\n    }\n}\n"
        self.assertEqual(rules_of("src/a.cpp", source), set())

    def test_overloads_get_distinct_keys(self):
        source = cpp_function(11) + cpp_function(11)
        keys = [violation.key for violation in check_source("src/a.cpp", source)]
        self.assertEqual(keys, ["src/a.cpp::Foo::run", "src/a.cpp::Foo::run#2"])


class ParametersAndNestingTest(unittest.TestCase):
    def test_three_parameters_pass(self):
        self.assertEqual(rules_of("src/a.cpp", cpp_function(1, "void f(int a, int b, int c)")), set())

    def test_four_parameters_fail(self):
        self.assertEqual(rules_of("src/a.cpp", cpp_function(1, "void f(int a, int b, int c, int d)")),
                         {"parameters"})

    def test_template_commas_do_not_count(self):
        signature = "void f(QMap<int, int> a, QPair<int, int> b)"
        self.assertEqual(rules_of("src/a.cpp", cpp_function(1, signature)), set())

    def test_nesting_of_two_passes(self):
        source = "void f()\n{\n    if (a) {\n        if (b) {\n            c();\n        }\n    }\n}\n"
        self.assertEqual(rules_of("src/a.cpp", source), set())

    def test_nesting_of_three_fails(self):
        source = "void f()\n{\n    if (a) {\n        if (b) {\n            if (c) {\n                d();\n"
        source += "            }\n        }\n    }\n}\n"
        self.assertIn("nesting", rules_of("src/a.cpp", source))

    def test_lambda_counts_as_a_level(self):
        source = "void f()\n{\n    auto g = [] {\n        if (a) {\n            if (b) {\n                c();\n"
        source += "            }\n        }\n    };\n}\n"
        self.assertIn("nesting", rules_of("src/a.cpp", source))


class QmlTest(unittest.TestCase):
    def test_long_function_fails(self):
        source = "Item {\n    function go() {\n%s    }\n}\n" % body(11)
        self.assertEqual(check_source("qml/a/A.qml", source)[0].key, "qml/a/A.qml::go")

    def test_short_handler_passes(self):
        source = "Item {\n    onClicked: {\n        go()\n    }\n}\n"
        self.assertEqual(rules_of("qml/a/A.qml", source), set())

    def test_long_handler_is_keyed_by_position(self):
        source = "Item {\n    onClicked: {\n%s    }\n    onClicked: {\n%s    }\n}\n" % (body(11), body(11))
        keys = [violation.key for violation in check_source("qml/a/A.qml", source)]
        self.assertEqual(keys, ["qml/a/A.qml::onClicked#1", "qml/a/A.qml::onClicked#2"])

    def test_function_inside_handler_belongs_to_the_handler(self):
        source = "Item {\n    onClicked: {\n        function f() {}\n    }\n}\n"
        self.assertEqual(rules_of("qml/a/A.qml", source), set())

    def test_javascript_function_parameters_are_counted(self):
        source = "function f(a, b, c, d) {\n    return a;\n}\n"
        self.assertEqual(rules_of("src/a.js", source), {"parameters"})


class FileAndCommentTest(unittest.TestCase):
    def test_two_hundred_lines_pass(self):
        self.assertEqual(rules_of("src/a.cpp", "int x;\n" * 200), set())

    def test_two_hundred_and_one_lines_fail(self):
        self.assertEqual(rules_of("src/a.cpp", "int x;\n" * 201), {"file-length"})

    def test_plain_comment_fails(self):
        self.assertEqual(rules_of("src/a.cpp", "// explains what\nint x;\n"), {"comments"})

    def test_block_comment_fails(self):
        self.assertEqual(rules_of("qml/a/A.qml", "/* what */\nItem {}\n"), {"comments"})

    def test_translator_notes_are_allowed(self):
        self.assertEqual(rules_of("src/a.cpp", "//: Menu item\n//~ Context here\nint x;\n"), set())

    def test_spdx_line_is_allowed(self):
        self.assertEqual(rules_of("src/a.cpp", "// SPDX-License-Identifier: MIT\nint x;\n"), set())

    def test_bug_link_makes_the_workaround_comment_allowed(self):
        source = "// Why: the view crashes\n// https://bugreports.qt.io/browse/QTBUG-1\nint x;\n"
        self.assertEqual(rules_of("src/a.cpp", source), set())

    def test_comment_marker_inside_string_is_not_a_comment(self):
        self.assertEqual(rules_of("src/a.cpp", 'const char *u = "http://kde.org";\n'), set())


if __name__ == "__main__":
    unittest.main()
