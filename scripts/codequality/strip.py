import re
from typing import List, NamedTuple, Tuple

TOKEN = re.compile(
    r"""
    (?P<line>//[^\n]*)
    |(?P<block>/\*.*?\*/)
    |(?P<raw>R"(?P<delimiter>[^()\s]*)\(.*?\)(?P=delimiter)")
    |(?P<string>"(?:\\.|[^"\\\n])*")
    |(?P<char>'(?:\\.|[^'\\\n])*')
    |(?P<template>`(?:\\.|[^`\\])*`)
    """,
    re.S | re.X,
)

ALLOWED_COMMENT = re.compile(
    r"^//[:~]|SPDX-|bugreports\.qt\.io|bugs\.kde\.org|invent\.kde\.org/\S*/issues|github\.com/\S*/issues"
)


class Comment(NamedTuple):
    line: int
    end_line: int
    text: str


def blank(text: str) -> str:
    return re.sub(r"[^\n]", " ", text)


def is_comment(match) -> bool:
    return match.group("line") is not None or match.group("block") is not None


def line_number(source: str, index: int) -> int:
    return source.count("\n", 0, index) + 1


def make_comment(source: str, match) -> Comment:
    text = match.group(0)
    first = line_number(source, match.start())
    return Comment(first, first + text.count("\n"), text)


def strip_source(source: str) -> Tuple[str, List[Comment]]:
    comments: List[Comment] = []

    def replace(match) -> str:
        if is_comment(match):
            comments.append(make_comment(source, match))
        return blank(match.group(0))

    return TOKEN.sub(replace, source), comments


def is_translator_note(comment: Comment) -> bool:
    return comment.text.startswith(("//:", "//~"))


def continues_group(previous: Comment, comment: Comment) -> bool:
    adjacent = comment.line == previous.end_line + 1
    return adjacent and comment.text.startswith("//") and previous.text.startswith("//")


def group_comments(comments: List[Comment]) -> List[List[Comment]]:
    groups: List[List[Comment]] = []
    for comment in comments:
        if groups and not is_translator_note(comment) and continues_group(groups[-1][-1], comment):
            groups[-1].append(comment)
        else:
            groups.append([comment])
    return groups


def is_allowed_group(group: List[Comment]) -> bool:
    return any(ALLOWED_COMMENT.search(comment.text) for comment in group)


def count_lines(group: List[Comment]) -> int:
    return sum(comment.end_line - comment.line + 1 for comment in group)


def forbidden_comment_lines(comments: List[Comment]) -> int:
    groups = group_comments(comments)
    return sum(count_lines(group) for group in groups if not is_allowed_group(group))
