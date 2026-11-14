import re

COMMENT = re.compile(r"//[^\n]*|/\*.*?\*/", re.S)
CLASS_HEAD = re.compile(r"\b(?:class|struct)\s+(?:[A-Z_]+\s+)?(\w+)\s*(?:final\s*)?(?::[^{;]*)?\{")


def strip_comments(text: str) -> str:
    return COMMENT.sub(lambda match: re.sub(r"[^\n]", " ", match.group(0)), text)


def matching_close(text: str, open_index: int) -> int:
    depth = 0
    for index in range(open_index, len(text)):
        depth += {"{": 1, "}": -1}.get(text[index], 0)
        if depth == 0:
            return index
    return len(text)


def class_bodies(text: str) -> dict[str, str]:
    bodies = {}
    for match in CLASS_HEAD.finditer(text):
        close = matching_close(text, match.end() - 1)
        body = text[match.end():close]
        if "Q_OBJECT" in body:
            bodies[match.group(1)] = body
    return bodies


def collapse_bodies(body: str) -> str:
    result = []
    parentheses = braces = 0
    for char in body:
        parentheses += {"(": 1, ")": -1}.get(char, 0)
        if parentheses == 0 and char in "{}":
            braces += 1 if char == "{" else -1
            result.append(";" if braces == 0 else "")
        elif braces == 0:
            result.append(char)
    return "".join(result)


def balanced_arguments(text: str, open_index: int) -> str:
    depth = 0
    for index in range(open_index, len(text)):
        depth += {"(": 1, ")": -1, "<": 0}.get(text[index], 0)
        if depth == 0:
            return text[open_index + 1:index]
    return text[open_index + 1:]


def split_top_level(arguments: str) -> list[str]:
    parts: list[str] = []
    depth = 0
    current = ""
    for char in arguments:
        depth += {"(": 1, "<": 1, "{": 1, "[": 1, ")": -1, ">": -1, "}": -1, "]": -1}.get(char, 0)
        if char == "," and depth == 0:
            parts.append(current)
            current = ""
        else:
            current += char
    return [*parts, current] if current.strip() else parts


def argument_counts(arguments: str) -> set[int]:
    parts = [part for part in split_top_level(arguments) if part.strip() not in ("", "void")]
    required = sum(1 for part in parts if "=" not in part)
    return set(range(required, len(parts) + 1))
