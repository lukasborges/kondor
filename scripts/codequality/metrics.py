import re
from typing import Dict, NamedTuple

from .blocks import line_of


class Function(NamedTuple):
    key: str
    line: int
    body_lines: int
    parameters: int
    nesting: int


def body_line_count(text: str, open_index: int, close_index: int) -> int:
    first = line_of(text, open_index)
    last = line_of(text, close_index)
    return 1 if first == last else last - first - 1


BLOCK_OPENER = re.compile(
    r"(?:[)\]{};:]|=>|\b(?:else|do|try|mutable|noexcept|const)|->\s*[\w:<>*&\s]+)\s*$"
)
OPENER_WINDOW = 80


def opens_block(text: str, index: int) -> bool:
    return bool(BLOCK_OPENER.search(text[max(0, index - OPENER_WINDOW):index]))


def update_block_flags(flags: list, text: str, index: int) -> None:
    if text[index] == "{":
        flags.append(all(flags) and opens_block(text, index))
    elif text[index] == "}" and flags:
        flags.pop()


def max_nesting(text: str, open_index: int, close_index: int) -> int:
    flags: list = []
    deepest = 0
    for index in range(open_index + 1, close_index):
        update_block_flags(flags, text, index)
        deepest = max(deepest, sum(flags))
    return deepest


class Body(NamedTuple):
    text: str
    span: tuple


def measure(key: str, body: Body, parameters: int) -> Function:
    text = body.text
    open_index, close_index = body.span
    return Function(
        key,
        line_of(text, open_index),
        body_line_count(text, open_index, close_index),
        parameters,
        max_nesting(text, open_index, close_index),
    )


def unique_keys(functions: list) -> list:
    seen: Dict[str, int] = {}
    result = []
    for function in functions:
        seen[function.key] = seen.get(function.key, 0) + 1
        suffix = "" if seen[function.key] == 1 else "#%d" % seen[function.key]
        result.append(function._replace(key=function.key + suffix))
    return result
