import re

from kondor.passwords import passwordorigin
from kondor.passwords.csvimport.csvreader import read_csv_rows
from kondor.passwords.csvimport.importtypes import Error, Format, Login, Result
from kondor.passwords.csvimport.passwordimportcolumns import (
    Columns,
    detect_format,
    find_columns,
    normalized_header,
)

__all__ = ["Error", "Format", "Login", "Result", "format_name", "parse"]

SITE_SEPARATORS = re.compile(r"[,\r\n]")
LOGIN_TYPE = "login"
MINIMUM_ROWS = 2


def cell(row: list[str], column: int) -> str:
    return row[column] if 0 <= column < len(row) else ""


def origins_in(sites: str) -> list[str]:
    origins: list[str] = []
    for part in SITE_SEPARATORS.split(sites):
        origin = passwordorigin.origin_from_input(part)
        if origin and origin not in origins:
            origins.append(origin)
    return origins


class RowReader:
    def __init__(self, format_: Format, columns: Columns) -> None:
        self._columns = columns
        self._result = Result(format=format_)
        self._seen: dict[tuple[str, str], int] = {}

    def add_row(self, row: list[str]) -> None:
        if self._is_not_login(row):
            self._result.skipped_not_login += 1
        else:
            self._add_login_row(row)

    def result(self) -> Result:
        return self._result

    def _is_not_login(self, row: list[str]) -> bool:
        type_column = self._columns.type
        return type_column >= 0 and cell(row, type_column).strip().lower() != LOGIN_TYPE

    def _add_login_row(self, row: list[str]) -> None:
        origins = origins_in(cell(row, self._columns.site))
        if not origins:
            self._result.skipped_no_site += 1
            return
        username, password = cell(row, self._columns.user), cell(row, self._columns.password)
        if not username or not password:
            self._result.skipped_no_credentials += 1
            return
        for origin in origins:
            self._add_login(Login(origin, username, password))

    def _add_login(self, login: Login) -> None:
        key = (login.origin, login.username)
        if key in self._seen:
            self._result.logins[self._seen[key]].password = login.password
            return
        self._seen[key] = len(self._result.logins)
        self._result.logins.append(login)


def read_rows(rows: list[list[str]], header: list[str], columns: Columns) -> Result:
    reader = RowReader(detect_format(header), columns)
    for row in rows[1:]:
        reader.add_row(row)
    return reader.result()


def format_name(format_: Format) -> str:
    return format_.value


def parse(csv: bytes | bytearray) -> Result:
    rows = read_csv_rows(csv)
    if not rows:
        return Result(error=Error.EMPTY)
    header = normalized_header(rows[0])
    columns = find_columns(header)
    if not columns.is_complete():
        return Result(error=Error.NOT_PASSWORD_EXPORT)
    if len(rows) < MINIMUM_ROWS:
        return Result(error=Error.EMPTY)
    return read_rows(rows, header, columns)
