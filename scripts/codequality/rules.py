from typing import List, NamedTuple

from .cpp import find_cpp_functions
from .metrics import Function
from .qml import find_qml_functions
from .strip import forbidden_comment_lines, strip_source

MAX_FUNCTION_LINES = 10
MAX_TEST_FUNCTION_LINES = 20
MAX_PARAMETERS = 3
MAX_NESTING = 2
MAX_FILE_LINES = 200
MAX_COMMENT_LINES = 0

FUNCTION_RULES = ("function-length", "parameters", "nesting")
FILE_RULES = ("file-length", "comments")


class Violation(NamedTuple):
    rule: str
    key: str
    line: int
    value: int
    limit: int


def is_qml_family(path: str) -> bool:
    return path.endswith((".qml", ".js"))


def length_limit(path: str) -> int:
    return MAX_TEST_FUNCTION_LINES if path.startswith("tests/") else MAX_FUNCTION_LINES


def function_violations(function: Function, path: str) -> List[Violation]:
    checks = (
        ("function-length", function.body_lines, length_limit(path)),
        ("parameters", function.parameters, MAX_PARAMETERS),
        ("nesting", function.nesting, MAX_NESTING),
    )
    return [Violation(rule, function.key, function.line, value, limit)
            for rule, value, limit in checks if value > limit]


def find_functions(path: str, text: str) -> List[Function]:
    return find_qml_functions(path, text) if is_qml_family(path) else find_cpp_functions(path, text)


def file_violations(path: str, source: str, comment_lines: int) -> List[Violation]:
    checks = (
        ("file-length", len(source.splitlines()), MAX_FILE_LINES),
        ("comments", comment_lines, MAX_COMMENT_LINES),
    )
    return [Violation(rule, path, 1, value, limit) for rule, value, limit in checks if value > limit]


def check_source(path: str, source: str) -> List[Violation]:
    text, comments = strip_source(source)
    violations = file_violations(path, source, forbidden_comment_lines(comments))
    for function in find_functions(path, text):
        violations += function_violations(function, path)
    return violations
