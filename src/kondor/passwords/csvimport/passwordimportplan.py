from dataclasses import dataclass, replace

from kondor.passwords.csvimport.importtypes import Login

SavedLogins = dict[str, dict[str, str]]


@dataclass
class ImportSummary:
    new_count: int = 0
    identical_count: int = 0
    conflict_count: int = 0
    conflict_sites: int = 0


class ImportCounter:
    def __init__(self) -> None:
        self._summary = ImportSummary()
        self._conflict_origins: set[str] = set()

    def add(self, login: Login, saved: dict[str, str]) -> None:
        if login.username not in saved:
            self._summary.new_count += 1
        elif saved[login.username] == login.password:
            self._summary.identical_count += 1
        else:
            self._add_conflict(login.origin)

    def summary(self) -> ImportSummary:
        return replace(self._summary, conflict_sites=len(self._conflict_origins))

    def _add_conflict(self, origin: str) -> None:
        self._summary.conflict_count += 1
        self._conflict_origins.add(origin)


def should_write(saved: dict[str, str], login: Login, replace_conflicts: bool) -> bool:
    if login.username not in saved:
        return True
    return replace_conflicts and saved[login.username] != login.password


def summarize_import(logins: list[Login], saved: SavedLogins) -> ImportSummary:
    counter = ImportCounter()
    for login in logins:
        counter.add(login, saved.get(login.origin, {}))
    return counter.summary()


def merge_logins(saved: dict[str, str], logins: list[Login], replace_conflicts: bool) -> int:
    changes = 0
    for login in logins:
        if should_write(saved, login, replace_conflicts):
            saved[login.username] = login.password
            changes += 1
    return changes
