from collections.abc import Iterator, Sequence
from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication, QStandardPaths, QTranslator
from PySide6.QtSql import QSqlDatabase, QSqlQuery

from kondor.core.database import sql
from kondor.core.database.database import Database
from kondor.core.database.defaultbookmarks import CONTEXT, DEFAULT_BOOKMARKS, DefaultBookmark

OLD_CONNECTION = "old"
VERSION_ONE_STATEMENTS = (
    "CREATE TABLE history (id INTEGER PRIMARY KEY AUTOINCREMENT,"
    " url TEXT NOT NULL, title TEXT NOT NULL DEFAULT '', visited_at INTEGER NOT NULL)",
    "INSERT INTO history (url, title, visited_at) VALUES ('https://kde.org/', 'KDE', 1)",
    "PRAGMA user_version = 1",
)
CHILDREN = "SELECT id, title, url, position FROM bookmarks WHERE parent_id = ? ORDER BY position"
TOOLBAR = "SELECT id FROM bookmarks WHERE special IS NOT NULL"
ROOT_FOLDERS = "SELECT COUNT(*) FROM bookmarks WHERE special IS NOT NULL"
SCHEMA_VERSION = 6
ROOT_FOLDER_COUNT = 1
BookmarkRow = tuple[int, str, str | None, int]


@pytest.fixture
def database_file(qapp: object) -> Iterator[Path]:
    Database.reset_instance()
    folder = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation))
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "kondor.sqlite"
    path.unlink(missing_ok=True)
    yield path
    Database.reset_instance()
    path.unlink(missing_ok=True)


def execute_on_old_connection(path: Path, statements: Sequence[str]) -> None:
    old = QSqlDatabase.addDatabase("QSQLITE", OLD_CONNECTION)
    old.setDatabaseName(str(path))
    assert old.open()
    query = QSqlQuery(old)
    for statement in statements:
        assert query.exec(statement)
    old.close()


def write_version_one_file(path: Path) -> None:
    execute_on_old_connection(path, VERSION_ONE_STATEMENTS)
    QSqlDatabase.removeDatabase(OLD_CONNECTION)


def scalar(statement: str) -> int:
    query = sql.run(statement)
    return int(query.value(0)) if query is not None and query.next() else -1


def url_of(query: QSqlQuery) -> str | None:
    return None if query.isNull(2) else str(query.value(2))


def fetch_children(parent_id: int) -> list[BookmarkRow]:
    query = sql.run(CHILDREN, (parent_id,))
    rows = []
    while query is not None and query.next():
        rows.append((query.value(0), query.value(1), url_of(query), query.value(3)))
    return rows


def read_tree(parent_id: int) -> tuple[DefaultBookmark, ...]:
    rows = fetch_children(parent_id)
    assert [position for *_, position in rows] == list(range(len(rows)))
    return tuple(DefaultBookmark(title, url, read_tree(row_id)) for row_id, title, url, _ in rows)


def test_upgrades_version_one_file_keeping_history(database_file: Path) -> None:
    write_version_one_file(database_file)
    assert Database.instance().is_valid()
    assert scalar("SELECT COUNT(*) FROM history") == 1
    assert scalar("PRAGMA user_version") == SCHEMA_VERSION
    assert scalar("SELECT COUNT(*) FROM favicons") == 0
    assert scalar("SELECT COUNT(*) FROM extension_storage") == 0
    assert scalar(ROOT_FOLDERS) == ROOT_FOLDER_COUNT


def test_fresh_file_gets_the_default_bookmarks(database_file: Path) -> None:
    assert Database.instance().is_valid()
    assert read_tree(sql.ids(TOOLBAR)[0]) == DEFAULT_BOOKMARKS


def test_unusable_file_leaves_the_database_invalid(database_file: Path) -> None:
    database_file.write_bytes(b"this is not an SQLite database\n" * 64)
    assert not Database.instance().is_valid()
    assert sql.run("SELECT 1") is None


class PortugueseFolders(QTranslator):
    TITLES = {"News": "Notícias", "Development": "Desenvolvimento", "Linux": "Linux"}

    def translate(self, context: str, source_text: str, *_: object) -> str:
        return self.TITLES.get(source_text, "") if context == CONTEXT else ""


def test_default_folders_are_translated_when_a_translator_is_installed(
    database_file: Path,
) -> None:
    translator = PortugueseFolders()
    QCoreApplication.installTranslator(translator)
    try:
        assert Database.instance().is_valid()
        titles = [title for _, title, *_ in fetch_children(sql.ids(TOOLBAR)[0]) if title]
    finally:
        QCoreApplication.removeTranslator(translator)
    assert {"Notícias", "Desenvolvimento"} <= set(titles)
