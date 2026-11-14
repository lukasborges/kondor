import re
from dataclasses import dataclass, field

from kondor.adblock.filters.filterkinds import ResourceKind, ThirdParty
from kondor.adblock.filters.filteroptions import apply_filter_options

__all__ = ["FilterRule", "ThirdParty", "parse_filter_rule"]

DEFAULT_TYPE_MASK = int(
    ResourceKind.SUB_FRAME
    | ResourceKind.STYLESHEET
    | ResourceKind.SCRIPT
    | ResourceKind.IMAGE
    | ResourceKind.XML_HTTP_REQUEST
    | ResourceKind.OTHER
)
COSMETIC_MARKERS = ("##", "#@#", "#?#", "#$#")
SKIPPED_PREFIXES = ("!", "[")
EXCEPTION_PREFIX = "@@"
DOMAIN_ANCHOR = "||"
ANCHOR = "|"
OPTIONS_SEPARATOR = "$"
REGEX_DELIMITER = "/"
HOST_TERMINATOR = re.compile(r"[\^/*:?|]")
PATTERN_SPECIAL = re.compile(r"[*^]")


@dataclass(slots=True)
class FilterRule:
    pattern: str = ""
    host: str = ""
    anchor_start: bool = False
    anchor_end: bool = False
    exception: bool = False
    type_mask: int = 0
    third_party: ThirdParty = ThirdParty.ANY
    domains_include: list[str] = field(default_factory=list)
    domains_exclude: list[str] = field(default_factory=list)
    segments: list[str] = field(default_factory=list)
    literal: str = ""


def is_cosmetic_rule(line: str) -> bool:
    return any(marker in line for marker in COSMETIC_MARKERS)


def is_skipped_line(line: str) -> bool:
    return not line or line.startswith(SKIPPED_PREFIXES) or is_cosmetic_rule(line)


def is_regex_rule(line: str) -> bool:
    return len(line) > 1 and line.startswith(REGEX_DELIMITER) and line.endswith(REGEX_DELIMITER)


def has_valid_options(line: str, rule: FilterRule) -> bool:
    dollar = line.rfind(OPTIONS_SEPARATOR)
    return dollar < 0 or apply_filter_options(line[dollar + 1 :], rule)


def without_options(line: str) -> str:
    dollar = line.rfind(OPTIONS_SEPARATOR)
    return line if dollar < 0 else line[:dollar]


def without_start_anchor(line: str, rule: FilterRule) -> str:
    if line.startswith(DOMAIN_ANCHOR):
        return line[len(DOMAIN_ANCHOR) :]
    rule.anchor_start = line.startswith(ANCHOR)
    return line[1:] if rule.anchor_start else line


def without_end_anchor(line: str, rule: FilterRule) -> str:
    rule.anchor_end = line.endswith(ANCHOR)
    return line[:-1] if rule.anchor_end else line


def longest_literal(pattern: str) -> str:
    return max(PATTERN_SPECIAL.split(pattern), key=len)


def with_pattern(rule: FilterRule, pattern: str) -> FilterRule:
    rule.pattern = pattern
    rule.segments = pattern.split("*")
    rule.literal = longest_literal(pattern)
    return rule


def host_end(line: str) -> int:
    terminator = HOST_TERMINATOR.search(line)
    return len(line) if terminator is None else terminator.start()


def split_host(line: str, rule: FilterRule) -> FilterRule | None:
    end = host_end(line)
    rule.host = line[:end]
    if "." not in rule.host:
        return None
    rule.anchor_start = True
    return with_pattern(rule, line[end:])


def finish_pattern(line: str, rule: FilterRule) -> FilterRule | None:
    is_domain_anchor = line.startswith(DOMAIN_ANCHOR)
    line = without_end_anchor(without_start_anchor(line, rule), rule)
    if not line:
        return None
    if is_domain_anchor:
        return split_host(line, rule)
    return with_pattern(rule, line)


def parse_filter_rule(text: str) -> FilterRule | None:
    line = text.strip()
    if is_skipped_line(line):
        return None
    rule = FilterRule(exception=line.startswith(EXCEPTION_PREFIX))
    line = line[len(EXCEPTION_PREFIX) :] if rule.exception else line
    if not has_valid_options(line, rule) or is_regex_rule(without_options(line)):
        return None
    rule.type_mask = rule.type_mask or DEFAULT_TYPE_MASK
    return finish_pattern(without_options(line).lower(), rule)
