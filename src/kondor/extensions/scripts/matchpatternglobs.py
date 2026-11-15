SCHEME_SEPARATOR = "://"
ALL_URLS = "<all_urls>"


def schemes_of(scheme: str) -> list[str]:
    if scheme == "*":
        return ["http", "https"]
    return [scheme]


def hosts_of(host: str) -> list[str]:
    if host == "*":
        return [host]
    hosts = [host]
    if host.startswith("*."):
        hosts.append(host[2:])
    return hosts + [name + ":*" for name in hosts]


def combine(schemes: list[str], hosts: list[str], path: str) -> list[str]:
    return [scheme + SCHEME_SEPARATOR + host + path for scheme in schemes for host in hosts]


def match_pattern_as_globs(match_pattern: str) -> list[str]:
    if match_pattern == ALL_URLS:
        return ["*"]
    scheme_end = match_pattern.find(SCHEME_SEPARATOR)
    host_end = match_pattern.find("/", scheme_end + 3)
    if scheme_end < 0 or host_end < 0:
        return [match_pattern]
    host = match_pattern[scheme_end + 3 : host_end]
    path = match_pattern[host_end:]
    return combine(schemes_of(match_pattern[:scheme_end]), hosts_of(host), path)
