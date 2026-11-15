from dataclasses import dataclass, field
from enum import Enum


class Format(Enum):
    BITWARDEN = "Bitwarden"
    ONE_PASSWORD = "1Password"
    FIREFOX = "Firefox"
    CHROME = "Chrome"
    KEEPASSXC = "KeePassXC"
    CSV = "CSV"


class Error(Enum):
    NONE = "none"
    NOT_PASSWORD_EXPORT = "notPasswordExport"
    EMPTY = "empty"


@dataclass
class Login:
    origin: str
    username: str
    password: str


@dataclass
class Result:
    format: Format = Format.CSV
    logins: list[Login] = field(default_factory=list)
    skipped_no_site: int = 0
    skipped_no_credentials: int = 0
    skipped_not_login: int = 0
    error: Error = Error.NONE
