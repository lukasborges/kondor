import pytest
from PySide6.QtCore import QUrl

from kondor.site.httpsonly.upgrade import is_upgradable, secure_version_of


def upgradable(url: str, allowed: set[str] | None = None) -> bool:
    return is_upgradable(QUrl(url), allowed or set())


def test_public_http_site_is_upgraded() -> None:
    assert upgradable("http://example.com/a?b=1")


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost:8000",
        "http://app.localhost/",
        "http://127.0.0.1/",
        "http://[::1]/",
        "http://192.168.1.1",
        "http://10.0.0.5/",
        "http://172.16.3.4/",
        "http://router/",
        "https://example.com/",
        "ftp://example.com/",
    ],
)
def test_local_and_non_http_addresses_are_left_alone(url: str) -> None:
    assert not upgradable(url)


def test_allowed_host_is_left_alone() -> None:
    assert not upgradable("http://neverssl.com/", {"neverssl.com"})


def test_public_ip_is_upgraded() -> None:
    assert upgradable("http://8.8.8.8/")


def test_secure_version_keeps_path_and_query_and_drops_port_80() -> None:
    assert secure_version_of(QUrl("http://example.com:80/a?b=1")).toString() == (
        "https://example.com/a?b=1"
    )


def test_secure_version_keeps_other_ports() -> None:
    assert secure_version_of(QUrl("http://example.com:8080/")).toString() == (
        "https://example.com:8080/"
    )
