from typing import NamedTuple

NORMALIZED_PARTS = 3


class VersionPart(NamedTuple):
    number: int
    rest: str


def leading_digits(part: str) -> str:
    length = 0
    while length < len(part) and part[length].isdecimal():
        length += 1
    return part[:length]


def part_of(parts: list[str], index: int) -> VersionPart:
    if index >= len(parts):
        return VersionPart(0, "")
    digits = leading_digits(parts[index])
    return VersionPart(int(digits) if digits else 0, parts[index][len(digits) :])


def compare_part(candidate: VersionPart, installed: VersionPart) -> int:
    if candidate.number != installed.number:
        return -1 if candidate.number < installed.number else 1
    return (candidate.rest > installed.rest) - (candidate.rest < installed.rest)


def normalized_user_script_version(raw: str) -> str:
    parts = raw.split(".")
    return ".".join(str(part_of(parts, index).number) for index in range(NORMALIZED_PARTS))


def is_newer_user_script_version(candidate: str, installed: str) -> bool:
    candidate_parts, installed_parts = candidate.split("."), installed.split(".")
    for index in range(max(len(candidate_parts), len(installed_parts))):
        order = compare_part(part_of(candidate_parts, index), part_of(installed_parts, index))
        if order != 0:
            return order > 0
    return False
