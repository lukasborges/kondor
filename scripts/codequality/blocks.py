from typing import Dict


def match_braces(text: str) -> Dict[int, int]:
    pairs: Dict[int, int] = {}
    stack = []
    for index, char in enumerate(text):
        if char == "{":
            stack.append(index)
        elif char == "}" and stack:
            pairs[stack.pop()] = index
    return pairs


def line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def matching_parenthesis(text: str, open_index: int) -> int:
    depth = 0
    for index in range(open_index, len(text)):
        depth += {"(": 1, ")": -1}.get(text[index], 0)
        if depth == 0:
            return index
    return -1


def count_parameters(parameters: str) -> int:
    cleaned = parameters.strip()
    if cleaned in ("", "void"):
        return 0
    return count_top_level_items(cleaned)


def count_top_level_items(text: str) -> int:
    depth = 0
    count = 1
    for char in text:
        depth += {"(": 1, "[": 1, "<": 1, ")": -1, "]": -1, ">": -1}.get(char, 0)
        count += char == "," and depth <= 0
    return count
