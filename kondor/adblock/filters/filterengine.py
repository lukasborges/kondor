from collections.abc import Iterator

from PySide6.QtCore import QUrl

from kondor.adblock.filters.filterkinds import ResourceKind
from kondor.adblock.filters.filteroptions import options_match
from kondor.adblock.filters.filterpattern import matches_pattern, token_of, url_tokens
from kondor.adblock.filters.filterrequest import FilterRequest, make_filter_request
from kondor.adblock.filters.filterrule import FilterRule, parse_filter_rule

__all__ = ["FilterEngine", "ResourceKind"]

FILTERABLE_SCHEMES = frozenset(("http", "https", "ws", "wss"))


def parent_domains(host: str) -> Iterator[str]:
    while host:
        yield host
        dot = host.find(".")
        host = "" if dot < 0 else host[dot + 1 :]


def domain_rule_matches(rule: FilterRule, request: FilterRequest, exceptions: bool) -> bool:
    return (
        rule.exception == exceptions
        and rule.literal in request.rest
        and options_match(rule, request)
        and (not rule.pattern or matches_pattern(rule, request.rest, False))
    )


def search_rule_matches(rule: FilterRule, request: FilterRequest, exceptions: bool) -> bool:
    return (
        rule.exception == exceptions
        and rule.literal in request.url
        and options_match(rule, request)
        and matches_pattern(rule, request.url, True)
    )


def any_search_rule_matches(
    rules: list[FilterRule], request: FilterRequest, exceptions: bool
) -> bool:
    return any(search_rule_matches(rule, request, exceptions) for rule in rules)


class FilterEngine:
    def __init__(self) -> None:
        self._domain_rules: dict[str, list[FilterRule]] = {}
        self._token_rules: dict[str, list[FilterRule]] = {}
        self._other_rules: list[FilterRule] = []
        self._rule_count = 0

    def add_list(self, text: bytes) -> None:
        for line in text.split(b"\n"):
            self.add_rule(line.decode("utf-8", errors="replace"))

    def add_rule(self, line: str) -> bool:
        rule = parse_filter_rule(line)
        if rule is None:
            return False
        self._index_rule(rule)
        self._rule_count += 1
        return True

    def rule_count(self) -> int:
        return self._rule_count

    def should_block(self, url: QUrl, first_party_host: str, kind: ResourceKind) -> bool:
        if kind == ResourceKind.MAIN_FRAME or not self._is_filterable(url):
            return False
        request = make_filter_request(url, first_party_host, kind)
        return self._matches_any(request, False) and not self._matches_any(request, True)

    def _is_filterable(self, url: QUrl) -> bool:
        return self._rule_count > 0 and url.scheme() in FILTERABLE_SCHEMES

    def _index_rule(self, rule: FilterRule) -> None:
        if rule.host:
            self._domain_rules.setdefault(rule.host, []).append(rule)
            return
        token = token_of(rule.pattern, rule.anchor_start, rule.anchor_end)
        if token:
            self._token_rules.setdefault(token, []).append(rule)
        else:
            self._other_rules.append(rule)

    def _matches_host_rules(self, host: str, request: FilterRequest, exceptions: bool) -> bool:
        rules = self._domain_rules.get(host, [])
        return any(domain_rule_matches(rule, request, exceptions) for rule in rules)

    def _matches_domain_rules(self, request: FilterRequest, exceptions: bool) -> bool:
        hosts = parent_domains(request.host)
        return any(self._matches_host_rules(host, request, exceptions) for host in hosts)

    def _matches_token_rules(self, request: FilterRequest, exceptions: bool) -> bool:
        rules = self._token_rules
        tokens = url_tokens(request.url)
        return any(
            any_search_rule_matches(rules.get(token, []), request, exceptions) for token in tokens
        )

    def _matches_any(self, request: FilterRequest, exceptions: bool) -> bool:
        return (
            self._matches_domain_rules(request, exceptions)
            or self._matches_token_rules(request, exceptions)
            or any_search_rule_matches(self._other_rules, request, exceptions)
        )
