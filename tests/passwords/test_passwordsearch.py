from kondor.passwords.passwordsearch import matching_logins

SITE = "https://a.example"


def entry(host: str, username: str) -> dict[str, str]:
    return {"origin": f"https://{host}", "host": host, "username": username}


ENTRIES = [
    entry("z.example", "ann"),
    entry("b.example", "Bob"),
    entry("a.example", "zed"),
    entry("a.example", "amy"),
]


def usernames(found: list[dict[str, object]]) -> list[object]:
    return [item["username"] for item in found]


def test_empty_text_returns_this_site_only() -> None:
    assert usernames(matching_logins(ENTRIES, "  ", SITE)) == ["amy", "zed"]


def test_matches_host_ignoring_case() -> None:
    assert usernames(matching_logins(ENTRIES, "B.EXA", SITE)) == ["Bob"]


def test_matches_username() -> None:
    assert usernames(matching_logins(ENTRIES, "bob", SITE)) == ["Bob"]


def test_this_site_comes_first() -> None:
    found = matching_logins(ENTRIES, "example", SITE)
    assert [item["isThisSite"] for item in found] == [True, True, False, False]


def test_other_sites_sorted_by_host() -> None:
    found = matching_logins(ENTRIES, "example", SITE)
    assert [item["host"] for item in found[2:]] == ["b.example", "z.example"]
