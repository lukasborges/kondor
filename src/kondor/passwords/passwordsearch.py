def _matches_text(entry: dict[str, str], text: str) -> bool:
    return text in entry["host"].casefold() or text in entry["username"].casefold()


def _site_key(entry: dict[str, str]) -> tuple[str, str]:
    return entry["host"].casefold(), entry["username"].casefold()


def _is_this_site(entry: dict[str, str], site_origin: str) -> bool:
    return entry["origin"] == site_origin


def _candidates(entries: list[dict[str, str]], text: str, site_origin: str) -> list[dict[str, str]]:
    if not text:
        return [entry for entry in entries if _is_this_site(entry, site_origin)]
    return [entry for entry in entries if _matches_text(entry, text)]


def _ranking(entry: dict[str, str], site_origin: str) -> tuple[bool, str, str]:
    return (not _is_this_site(entry, site_origin), *_site_key(entry))


def _result(entry: dict[str, str], site_origin: str) -> dict[str, object]:
    return {
        "origin": entry["origin"],
        "host": entry["host"],
        "username": entry["username"],
        "isThisSite": _is_this_site(entry, site_origin),
    }


def matching_logins(
    entries: list[dict[str, str]], text: str, site_origin: str
) -> list[dict[str, object]]:
    found = _candidates(entries, text.strip().casefold(), site_origin)
    found.sort(key=lambda entry: _ranking(entry, site_origin))
    return [_result(entry, site_origin) for entry in found]
