import ast
import io
import re
import tokenize
from typing import Iterator, List, NamedTuple, Optional, Union

from .metrics import Function, unique_keys
from .strip import ALLOWED_COMMENT

FunctionNode = Union[ast.FunctionDef, ast.AsyncFunctionDef]
FUNCTION_TYPES = (ast.FunctionDef, ast.AsyncFunctionDef)
NESTING_TYPES = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.With, ast.AsyncWith,
                 ast.Try, ast.TryStar, ast.Match)
PRAGMA = re.compile(r"#\s*(?:type:\s*ignore\[[^\]]+\]|noqa:\s*[A-Z]+\d+)")
SPDX = re.compile(r"SPDX-")
IMPLICIT_FIRST_PARAMETERS = ("self", "cls")


class PythonComment(NamedTuple):
    line: int
    text: str


def child_blocks(statement: ast.stmt) -> List[List[ast.stmt]]:
    blocks = [getattr(statement, name, []) for name in ("body", "orelse", "finalbody")]
    blocks += [handler.body for handler in getattr(statement, "handlers", [])]
    blocks += [case.body for case in getattr(statement, "cases", [])]
    return [block for block in blocks if block and isinstance(block[0], ast.stmt)]


def is_elif(statement: ast.stmt, block: List[ast.stmt]) -> bool:
    is_else_block = isinstance(statement, ast.If) and block is statement.orelse
    return is_else_block and len(block) == 1 and isinstance(block[0], ast.If)


def statement_depth(statement: ast.stmt, depth: int) -> int:
    if not isinstance(statement, NESTING_TYPES):
        return depth
    inner = depth + 1
    deepest = inner
    for block in child_blocks(statement):
        block_base = depth if is_elif(statement, block) else inner
        deepest = max(deepest, block_depth(block, block_base))
    return deepest


def block_depth(block: List[ast.stmt], depth: int) -> int:
    return max([depth] + [statement_depth(statement, depth) for statement in block])


def count_parameters(node: FunctionNode) -> int:
    arguments = node.args
    positional = arguments.posonlyargs + arguments.args
    count = len(positional) + len(arguments.kwonlyargs)
    count += (arguments.vararg is not None) + (arguments.kwarg is not None)
    implicit = bool(positional) and positional[0].arg in IMPLICIT_FIRST_PARAMETERS
    return count - implicit


def count_body_lines(node: FunctionNode, lines: List[str]) -> int:
    first = node.body[0].lineno
    last = node.end_lineno or first
    return sum(1 for line in lines[first - 1:last] if line.strip())


def measure_function(node: FunctionNode, key: str, lines: List[str]) -> Function:
    return Function(key, node.lineno, count_body_lines(node, lines), count_parameters(node),
                    block_depth(node.body, 0))


def walk_functions(node: ast.AST, scope: List[str], path: str, lines: List[str]) -> Iterator[Function]:
    for child in ast.iter_child_nodes(node):
        inner_scope = scope
        if isinstance(child, FUNCTION_TYPES):
            inner_scope = scope + [child.name]
            yield measure_function(child, "::".join([path] + [".".join(inner_scope)]), lines)
        elif isinstance(child, ast.ClassDef):
            inner_scope = scope + [child.name]
        yield from walk_functions(child, inner_scope, path, lines)


def find_python_functions(path: str, source: str) -> List[Function]:
    tree = ast.parse(source)
    return unique_keys(list(walk_functions(tree, [], path, source.splitlines())))


def has_allowed_pragma(comment: PythonComment) -> bool:
    shebang = comment.line == 1 and comment.text.startswith("#!")
    return shebang or bool(PRAGMA.search(comment.text) or SPDX.search(comment.text))


def read_comments(source: str) -> List[PythonComment]:
    tokens = tokenize.generate_tokens(io.StringIO(source).readline)
    return [PythonComment(token.start[0], token.string) for token in tokens
            if token.type == tokenize.COMMENT]


def group_by_adjacency(comments: List[PythonComment]) -> List[List[PythonComment]]:
    groups: List[List[PythonComment]] = []
    for comment in comments:
        if groups and groups[-1][-1].line + 1 == comment.line:
            groups[-1].append(comment)
        else:
            groups.append([comment])
    return groups


def is_allowed_group(group: List[PythonComment]) -> bool:
    return any(ALLOWED_COMMENT.search(comment.text) for comment in group)


def count_comment_lines(source: str) -> int:
    comments = [c for c in read_comments(source) if not has_allowed_pragma(c)]
    groups = group_by_adjacency(comments)
    return sum(len(group) for group in groups if not is_allowed_group(group))


def has_docstring(node: ast.AST) -> bool:
    body: Optional[List[ast.stmt]] = getattr(node, "body", None)
    if not body or not isinstance(body[0], ast.Expr):
        return False
    return isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str)


def count_docstrings(source: str) -> int:
    documented = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
    return sum(1 for node in ast.walk(ast.parse(source))
               if isinstance(node, documented) and has_docstring(node))


def python_comment_lines(source: str) -> int:
    return count_comment_lines(source) + count_docstrings(source)
