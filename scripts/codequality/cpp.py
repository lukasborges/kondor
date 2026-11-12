import re
from typing import Iterator, List, NamedTuple

from .blocks import count_parameters, match_braces, matching_parenthesis
from .metrics import Body, Function, measure, unique_keys

MACRO = re.compile(r"\b[A-Z][A-Z0-9_]{2,}\b(?:\((?:[^()]|\([^()]*\))*\))?")
TEMPLATE_PREFIX = re.compile(r"template\s*<[^>]*>")
ACCESS_LABEL = re.compile(r"^\s*(?:public|private|protected|signals)\b[^:;]*:(?!:)")
PREPROCESSOR = re.compile(r"^[ \t]*#.*$", re.M)
SCOPE_KEYWORD = re.compile(r"\b(class|struct|union)\s+(\w+)")
FUNCTION_END = re.compile(r"\)\s*(?:const|override|noexcept|final|volatile|&|->[^;]*|\s)*$")
INIT_LIST = re.compile(r"\)\s*:(?!:)[^;]*\)\s*$")
OPERATOR_NAME = re.compile(r"(operator\s*[^\s\w(]+|operator\s*\w+)\s*$")
PLAIN_NAME = re.compile(r"([~\w:]+)\s*$")


class Block(NamedTuple):
    header: str
    span: tuple


class Context(NamedTuple):
    path: str
    text: str
    pairs: dict


def clean_header(header: str) -> str:
    header = PREPROCESSOR.sub("", header)
    header = TEMPLATE_PREFIX.sub("", header)
    header = MACRO.sub("", header)
    while ACCESS_LABEL.search(header):
        header = ACCESS_LABEL.sub("", header, count=1)
    return header.strip()


def header_before(text: str, cursor: int, brace: int) -> str:
    start = max(cursor, text.rfind(";", cursor, brace) + 1)
    return clean_header(text[start:brace])


def scope_name(header: str):
    if header.startswith(("namespace", "extern")):
        return ""
    match = SCOPE_KEYWORD.search(header)
    if match and not header.startswith("enum"):
        return match.group(2)
    return None


def is_assignment(header: str) -> bool:
    before_parameters = header.split("(", 1)[0]
    return "=" in re.sub(r"operator\s*\S+", "", before_parameters)


def is_function_header(header: str) -> bool:
    if "(" not in header or is_assignment(header):
        return False
    return bool(FUNCTION_END.search(header) or INIT_LIST.search(header))


def function_name(before_parameters: str) -> str:
    match = OPERATOR_NAME.search(before_parameters) or PLAIN_NAME.search(before_parameters)
    return re.sub(r"\s+", "", match.group(1)) if match else "anonymous"


def split_signature(header: str):
    open_index = header.index("(")
    close_index = matching_parenthesis(header, open_index)
    return function_name(header[:open_index]), header[open_index + 1:close_index]


def make_function(ctx: Context, block: Block, scope: List[str]) -> Function:
    name, parameters = split_signature(block.header)
    key = "::".join([ctx.path] + scope + [name])
    return measure(key, Body(ctx.text, block.span), count_parameters(parameters))


def scan_scope(ctx: Context, bounds: tuple, scope: List[str]) -> Iterator[Function]:
    cursor, end = bounds
    while True:
        brace = ctx.text.find("{", cursor, end)
        if brace < 0:
            return
        close = ctx.pairs[brace]
        yield from handle_block(ctx, Block(header_before(ctx.text, cursor, brace), (brace, close)), scope)
        cursor = close + 1


def handle_block(ctx: Context, block: Block, scope: List[str]) -> Iterator[Function]:
    name = scope_name(block.header)
    if name is not None:
        yield from scan_scope(ctx, (block.span[0] + 1, block.span[1]), scope + ([name] if name else []))
    elif is_function_header(block.header):
        yield make_function(ctx, block, scope)


def find_cpp_functions(path: str, text: str) -> List[Function]:
    ctx = Context(path, text, match_braces(text))
    return unique_keys(list(scan_scope(ctx, (0, len(text)), [])))
