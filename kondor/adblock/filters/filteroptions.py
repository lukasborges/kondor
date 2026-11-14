from typing import Protocol

from kondor.adblock.filters.filterkinds import ResourceKind, ThirdParty
from kondor.adblock.filters.filterpattern import host_matches
from kondor.adblock.filters.filterrequest import FilterRequest

DOMAIN_OPTION = "domain="
EXCLUDED_PREFIX = "~"
PARTY_OPTIONS = {
    "third-party": ThirdParty.ONLY_THIRD_PARTY,
    "~third-party": ThirdParty.ONLY_FIRST_PARTY,
}
TYPE_OPTIONS = {
    "script": ResourceKind.SCRIPT,
    "image": ResourceKind.IMAGE,
    "stylesheet": ResourceKind.STYLESHEET,
    "xmlhttprequest": ResourceKind.XML_HTTP_REQUEST,
    "subdocument": ResourceKind.SUB_FRAME,
}


class OptionRule(Protocol):
    third_party: ThirdParty
    type_mask: int
    domains_include: list[str]
    domains_exclude: list[str]


def add_domain(domain: str, rule: OptionRule) -> None:
    if domain.startswith(EXCLUDED_PREFIX):
        rule.domains_exclude.append(domain[1:])
    elif domain:
        rule.domains_include.append(domain)


def add_domains(domains: str, rule: OptionRule) -> None:
    for domain in domains.lower().split("|"):
        add_domain(domain, rule)


def apply_party_option(option: str, rule: OptionRule) -> bool:
    if option not in PARTY_OPTIONS:
        return False
    rule.third_party = PARTY_OPTIONS[option]
    return True


def apply_domain_option(option: str, rule: OptionRule) -> bool:
    if not option.startswith(DOMAIN_OPTION):
        return False
    add_domains(option[len(DOMAIN_OPTION) :], rule)
    return True


def apply_type_option(option: str, rule: OptionRule) -> bool:
    kind = int(TYPE_OPTIONS.get(option, 0))
    rule.type_mask |= kind
    return kind != 0


def apply_filter_option(option: str, rule: OptionRule) -> bool:
    return (
        apply_party_option(option, rule)
        or apply_domain_option(option, rule)
        or apply_type_option(option, rule)
    )


def apply_filter_options(options: str, rule: OptionRule) -> bool:
    return all(apply_filter_option(option, rule) for option in options.split(","))


def matches_any_domain(domains: list[str], host: str) -> bool:
    return any(host_matches(host, domain) for domain in domains)


def party_matches(rule: OptionRule, request: FilterRequest) -> bool:
    if rule.third_party is ThirdParty.ONLY_THIRD_PARTY:
        return request.third_party
    if rule.third_party is ThirdParty.ONLY_FIRST_PARTY:
        return not request.third_party
    return True


def domains_match(rule: OptionRule, request: FilterRequest) -> bool:
    if matches_any_domain(rule.domains_exclude, request.first_party_host):
        return False
    return not rule.domains_include or matches_any_domain(
        rule.domains_include, request.first_party_host
    )


def options_match(rule: OptionRule, request: FilterRequest) -> bool:
    return (
        bool(rule.type_mask & request.kind)
        and party_matches(rule, request)
        and domains_match(rule, request)
    )
