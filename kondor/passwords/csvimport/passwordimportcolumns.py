from dataclasses import dataclass

from kondor.passwords.csvimport.importtypes import Format

NOT_FOUND = -1
FORMAT_SIGNATURES = (
    (Format.BITWARDEN, ("login_password",)),
    (Format.ONE_PASSWORD, ("otpauth", "title")),
    (Format.FIREFOX, ("formactionorigin",)),
    (Format.FIREFOX, ("httprealm",)),
    (Format.KEEPASSXC, ("group", "title")),
)
CHROME_HEADER = ["name", "url", "username", "password"]
CHROME_NOTE_COLUMN = "note"
SITE_NAMES = ("url", "login_uri", "website", "uri", "web site", "login url")
USER_NAMES = ("username", "login_username", "user name", "login", "login name")
PASSWORD_NAMES = ("password", "login_password")
TYPE_NAME = "type"


@dataclass
class Columns:
    site: int = NOT_FOUND
    user: int = NOT_FOUND
    password: int = NOT_FOUND
    type: int = NOT_FOUND

    def is_complete(self) -> bool:
        return min(self.site, self.user, self.password) >= 0


def is_chrome_header(header: list[str]) -> bool:
    return header in (CHROME_HEADER, [*CHROME_HEADER, CHROME_NOTE_COLUMN])


def detect_format(header: list[str]) -> Format:
    for format_, required_columns in FORMAT_SIGNATURES:
        if all(name in header for name in required_columns):
            return format_
    return Format.CHROME if is_chrome_header(header) else Format.CSV


def find_column(header: list[str], names: tuple[str, ...]) -> int:
    return next((index for index, name in enumerate(header) if name in names), NOT_FOUND)


def find_columns(header: list[str]) -> Columns:
    return Columns(
        site=find_column(header, SITE_NAMES),
        user=find_column(header, USER_NAMES),
        password=find_column(header, PASSWORD_NAMES),
        type=find_column(header, (TYPE_NAME,)),
    )


def normalized_header(row: list[str]) -> list[str]:
    return [name.strip().lower() for name in row]
