from pathlib import Path
from typing import NamedTuple

import pytest

from kondor.passwords.csvimport.passwordimport import Error, Format, parse

TWO_LOGINS = 2
THREE_SKIPPED = 3
TWO_SKIPPED = 2
DATA = Path(__file__).resolve().parents[2] / "data" / "passwords"


class FixtureRow(NamedTuple):
    file: str
    format: Format
    count: int
    first_user: str
    first_password: str


FIXTURE_ROWS = {
    "chrome": FixtureRow("chrome.csv", Format.CHROME, 2, "alice", "pw-chrome-1"),
    "firefox": FixtureRow("firefox.csv", Format.FIREFOX, 2, "alice", "pw-fx-1"),
    "bitwarden": FixtureRow("bitwarden.csv", Format.BITWARDEN, 2, "alice", "pw-bw-1"),
    "1password": FixtureRow("1password.csv", Format.ONE_PASSWORD, 2, "alice", "pw-op-1"),
    "keepassxc": FixtureRow("keepassxc.csv", Format.KEEPASSXC, 1, "alice", "pw-kp-1"),
    "lastpass": FixtureRow("lastpass.csv", Format.CSV, 1, "alice", "pw-lp-1"),
}


def fixture(name: str) -> bytes:
    return (DATA / name).read_bytes()


@pytest.mark.parametrize("row", FIXTURE_ROWS.values(), ids=FIXTURE_ROWS.keys())
def test_fixtures(row: FixtureRow) -> None:
    result = parse(fixture(row.file))
    assert result.error is Error.NONE
    assert result.format is row.format
    assert len(result.logins) == row.count
    assert result.logins[0].origin == "https://example.com"
    assert result.logins[0].username == row.first_user
    assert result.logins[0].password == row.first_password


def test_quoted_fields() -> None:
    result = parse(b'url,username,password\nhttps://example.com,"a,b","pa""ss\nword"\n')
    assert len(result.logins) == 1
    assert result.logins[0].username == "a,b"
    assert result.logins[0].password == 'pa"ss\nword'


def test_crlf_and_bom() -> None:
    result = parse(
        b"\xef\xbb\xbfurl,username,password\r\n"
        b"\r\n"
        b"https://example.com,alice,one\r\n"
        b"https://example.org,bob,two\r\n"
    )
    assert result.error is Error.NONE
    assert len(result.logins) == TWO_LOGINS
    assert result.logins[-1].password == "two"


def test_short_rows() -> None:
    result = parse(
        b"url,username,password,extra\nhttps://example.com,alice\nhttps://example.org,bob,secret\n"
    )
    assert len(result.logins) == 1
    assert result.skipped_no_credentials == 1


def test_bitwarden_two_uris() -> None:
    result = parse(fixture("bitwarden.csv"))
    assert len(result.logins) == TWO_LOGINS
    assert result.logins[0].origin == "https://example.com"
    assert result.logins[1].origin == "https://www.example.com"
    assert result.logins[1].username == "alice"


def test_website_column() -> None:
    result = parse(
        b"url,username,password\n"
        b"http://localhost:8080,a,1\n"
        b"http://example.com,b,2\n"
        b"android://abc@com.example.app,c,3\n"
        b"example.com,d,4\n"
        b",e,5\n"
    )
    assert [login.origin for login in result.logins] == [
        "http://localhost:8080",
        "https://example.com",
    ]
    assert result.skipped_no_site == THREE_SKIPPED


def test_skips_and_duplicates() -> None:
    bitwarden = parse(fixture("bitwarden.csv"))
    assert bitwarden.skipped_not_login == 1
    assert bitwarden.skipped_no_site == TWO_SKIPPED
    assert bitwarden.skipped_no_credentials == 1
    duplicate = parse(
        b"url,username,password\nhttps://example.com,alice,old\nhttps://example.com,alice,new\n"
    )
    assert len(duplicate.logins) == 1
    assert duplicate.logins[0].password == "new"


def test_not_a_password_export() -> None:
    assert parse(b"name,notes\nfoo,bar\n").error is Error.NOT_PASSWORD_EXPORT


def test_empty_file() -> None:
    assert parse(b"url,username,password\n").error is Error.EMPTY
    assert parse(b"").error is Error.EMPTY
