from PySide6.QtCore import QDateTime

from kondor.core.database import sql
from kondor.core.settings.settings import Settings

INSERT_VISIT = "INSERT INTO history (url, title, visited_at) VALUES (?, ?, ?)"
TITLES = "SELECT title FROM history ORDER BY visited_at, id"
ID_OF_TITLE = "SELECT id FROM history WHERE title = ?"


def now_ms() -> int:
    return int(QDateTime.currentMSecsSinceEpoch())


def reset_history() -> None:
    assert sql.run("DELETE FROM history") is not None
    Settings.instance().setProperty("hiddenTopSites", [])


def add_visit(url: str, title: str, visited_at: int) -> None:
    assert sql.run(INSERT_VISIT, (url, title, visited_at)) is not None


def add_grouped_visits() -> None:
    now = now_ms()
    add_visit("https://kde.org/a", "A", now - 4000)
    add_visit("https://kde.org/b", "B", now - 3000)
    add_visit("https://kde.org/a", "A latest", now - 2000)
    add_visit("https://wikipedia.org/", "Wiki", now - 5000)
    add_visit("https://fedoraproject.org/", "Fedora", now - 6000)


def titles() -> list[str]:
    query = sql.run(TITLES)
    result = []
    while query is not None and query.next():
        result.append(str(query.value(0)))
    return result


def id_of_title(title: str) -> int:
    found = sql.ids(ID_OF_TITLE, (title,))
    return found[0] if found else -1
