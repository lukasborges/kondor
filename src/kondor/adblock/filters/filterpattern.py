import re
from typing import Protocol

MIN_TOKEN_LENGTH = 3
MIN_LABELS_WITH_SECOND_LEVEL = 3
COUNTRY_CODE_LENGTH = 2
MAX_SHORT_SECOND_LEVEL_LENGTH = 3
WILDCARD = "*"
SEPARATOR = "^"
NOT_FOUND = -1
ALPHANUMERIC_RUN = re.compile(r"[a-z0-9]+")
TOKEN_RUN = re.compile(r"[a-z0-9]{3,}")
NON_SEPARATORS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_-.%")


class PatternRule(Protocol):
    @property
    def pattern(self) -> str: ...
    @property
    def segments(self) -> list[str]: ...
    @property
    def anchor_start(self) -> bool: ...
    @property
    def anchor_end(self) -> bool: ...


def is_separator(character: str) -> bool:
    return character not in NON_SEPARATORS


def advance_over_separator(text: str, position: int) -> int:
    if position == len(text):
        return position
    return position + 1 if is_separator(text[position]) else NOT_FOUND


def advance(expected: str, text: str, position: int) -> int:
    if expected == SEPARATOR:
        return advance_over_separator(text, position)
    if position >= len(text) or text[position] != expected:
        return NOT_FOUND
    return position + 1


def match_segment_at(segment: str, text: str, position: int) -> int:
    if SEPARATOR not in segment:
        return position + len(segment) if text.startswith(segment, position) else NOT_FOUND
    for expected in segment:
        position = advance(expected, text, position)
        if position < 0:
            return NOT_FOUND
    return position


def search_literal(segment: str, text: str, start: int) -> int:
    found = text.find(segment, start)
    return NOT_FOUND if found < 0 else found + len(segment)


def search_segment(segment: str, text: str, start: int) -> int:
    if SEPARATOR not in segment:
        return search_literal(segment, text, start)
    for candidate in range(start, len(text) + 1):
        end = match_segment_at(segment, text, candidate)
        if end >= 0:
            return end
    return NOT_FOUND


def ends_where_required(rule: PatternRule, text: str, position: int) -> bool:
    must_end_at_end = rule.anchor_end and not rule.pattern.endswith(WILDCARD)
    return not must_end_at_end or position == len(text)


def matches_pattern(rule: PatternRule, text: str, is_unanchored_search: bool) -> bool:
    is_first_anchored = rule.anchor_start or not is_unanchored_search
    position = 0
    for index, segment in enumerate(rule.segments):
        if index == 0 and is_first_anchored:
            position = match_segment_at(segment, text, 0)
        elif segment:
            position = search_segment(segment, text, position)
        if position < 0:
            return False
    return ends_where_required(rule, text, position)


def is_left_bound(pattern: str, run: re.Match[str], anchor_start: bool) -> bool:
    return pattern[run.start() - 1] != WILDCARD if run.start() > 0 else anchor_start


def is_right_bound(pattern: str, run: re.Match[str], anchor_end: bool) -> bool:
    return pattern[run.end()] != WILDCARD if run.end() < len(pattern) else anchor_end


def token_of(pattern: str, anchor_start: bool, anchor_end: bool) -> str:
    best = ""
    for run in ALPHANUMERIC_RUN.finditer(pattern):
        if len(run.group()) < MIN_TOKEN_LENGTH or len(run.group()) <= len(best):
            continue
        if is_left_bound(pattern, run, anchor_start) and is_right_bound(pattern, run, anchor_end):
            best = run.group()
    return best


def url_tokens(url: str) -> set[str]:
    return set(TOKEN_RUN.findall(url))


def has_short_second_level_under_country_code(labels: list[str]) -> bool:
    return (
        len(labels) >= MIN_LABELS_WITH_SECOND_LEVEL
        and len(labels[-1]) == COUNTRY_CODE_LENGTH
        and len(labels[-2]) <= MAX_SHORT_SECOND_LEVEL_LENGTH
    )


def registrable_domain(host: str) -> str:
    labels = host.split(".")
    keep = 3 if has_short_second_level_under_country_code(labels) else 2
    if len(labels) <= keep:
        return host
    return ".".join(labels[-keep:])


def host_matches(host: str, domain: str) -> bool:
    return host == domain or host.endswith("." + domain)
