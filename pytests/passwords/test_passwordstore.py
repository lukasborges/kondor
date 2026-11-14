import pytest
from PySide6.QtCore import QUrl

from kondor.passwords.passwordstore import PasswordStore

EXAMPLE = "https://example.com"

ORIGIN_OF_ROWS = {
    "https": ("https://Example.com/login?x=1", EXAMPLE),
    "default port dropped": ("https://example.com:443/", EXAMPLE),
    "custom port kept": ("http://localhost:8080/a", "http://localhost:8080"),
    "idn": ("https://bücher.example/login", "https://xn--bcher-kva.example"),
    "file": ("file:///tmp/a.html", ""),
    "about": ("about:blank", ""),
}
CAN_SAVE_FOR_ROWS = {
    "https": (EXAMPLE, True),
    "http": ("http://example.com", False),
    "localhost": ("http://localhost:3000", True),
    "subdomain of localhost": ("http://app.localhost", True),
    "empty": ("", False),
}
ORIGIN_FROM_INPUT_ROWS = {
    "bare host": ("example.com", EXAMPLE),
    "with path": ("https://example.com/login", EXAMPLE),
    "upper case, default port": ("https://EXAMPLE.com:443", EXAMPLE),
    "trimmed": ("  example.com \n", EXAMPLE),
    "host with path": ("invent.kde.org/foo", "https://invent.kde.org"),
    "http refused": ("http://example.com", ""),
    "ftp refused": ("ftp://example.com", ""),
    "localhost accepted": ("http://localhost:8080", "http://localhost:8080"),
    "empty": ("", ""),
    "blank": ("   ", ""),
}


@pytest.mark.parametrize(("url", "origin"), ORIGIN_OF_ROWS.values(), ids=ORIGIN_OF_ROWS.keys())
def test_origin_of(qapp: object, url: str, origin: str) -> None:
    assert PasswordStore.instance().originOf(QUrl(url)) == origin


@pytest.mark.parametrize(
    ("origin", "is_allowed"), CAN_SAVE_FOR_ROWS.values(), ids=CAN_SAVE_FOR_ROWS.keys()
)
def test_can_save_for(qapp: object, origin: str, is_allowed: bool) -> None:
    assert PasswordStore.instance().canSaveFor(origin) is is_allowed


@pytest.mark.parametrize(
    ("text", "origin"), ORIGIN_FROM_INPUT_ROWS.values(), ids=ORIGIN_FROM_INPUT_ROWS.keys()
)
def test_origin_from_input(qapp: object, text: str, origin: str) -> None:
    assert PasswordStore.instance().originFromInput(text) == origin


def test_contains_when_closed(qapp: object) -> None:
    assert not PasswordStore.instance().contains(EXAMPLE, "student")


def test_starts_closed(qapp: object) -> None:
    store = PasswordStore.instance()
    assert store.state == "closed"
    assert store.entries == []
    assert store.usernames(EXAMPLE) == []
