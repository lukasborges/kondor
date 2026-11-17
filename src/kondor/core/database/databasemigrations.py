from collections.abc import Sequence

from PySide6.QtCore import QCoreApplication, QDateTime

from kondor.core.database import sql
from kondor.core.database.defaultbookmarks import CONTEXT, DEFAULT_BOOKMARKS, DefaultBookmark

BOOKMARKS_TABLE = (
    "CREATE TABLE IF NOT EXISTS bookmarks ("
    "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
    "  parent_id INTEGER REFERENCES bookmarks(id) ON DELETE CASCADE,"
    "  is_folder INTEGER NOT NULL DEFAULT 0,"
    "  title TEXT NOT NULL DEFAULT '',"
    "  url TEXT,"
    "  position INTEGER NOT NULL DEFAULT 0,"
    "  created_at INTEGER NOT NULL,"
    "  special TEXT)"
)
BOOKMARKS_INDEX = "CREATE INDEX IF NOT EXISTS bookmarks_parent ON bookmarks(parent_id, position)"
HISTORY_STATEMENTS = (
    "CREATE TABLE IF NOT EXISTS history ("
    "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
    "  url TEXT NOT NULL,"
    "  title TEXT NOT NULL DEFAULT '',"
    "  visited_at INTEGER NOT NULL)",
    "CREATE INDEX IF NOT EXISTS history_visited_at ON history(visited_at DESC)",
    "CREATE INDEX IF NOT EXISTS history_url ON history(url)",
)
FAVICONS_TABLE = (
    "CREATE TABLE IF NOT EXISTS favicons ("
    "  host TEXT PRIMARY KEY,"
    "  image BLOB NOT NULL,"
    "  updated_at INTEGER NOT NULL)"
)
EXTENSION_STORAGE_TABLE = (
    "CREATE TABLE IF NOT EXISTS extension_storage ("
    "  extension_id TEXT NOT NULL,"
    "  key TEXT NOT NULL,"
    "  value TEXT NOT NULL,"
    "  PRIMARY KEY (extension_id, key))"
)
SITE_SETTINGS_TABLE = (
    "CREATE TABLE IF NOT EXISTS site_settings ("
    "  host TEXT PRIMARY KEY,"
    "  allow_popups INTEGER NOT NULL DEFAULT 0,"
    "  user_agent TEXT)"
)
INSERT_ROOT_FOLDER = (
    "INSERT INTO bookmarks (parent_id, is_folder, title, url, position,"
    " created_at, special) "
    "SELECT NULL, 1, ?, NULL, 0, ?, ? "
    "WHERE NOT EXISTS (SELECT 1 FROM bookmarks WHERE special = ?)"
)
INSERT_DEFAULT_BOOKMARK = (
    "INSERT INTO bookmarks (parent_id, is_folder, title, url, position,"
    " created_at, special) VALUES (?, ?, ?, ?, ?, ?, NULL)"
)
HAS_USER_BOOKMARKS = "SELECT 1 FROM bookmarks WHERE special IS NULL LIMIT 1"
TOOLBAR_FOLDER = "SELECT id FROM bookmarks WHERE special = 'toolbar' LIMIT 1"


def run_all(statements: Sequence[str]) -> bool:
    return all(sql.run(statement) is not None for statement in statements)


def insert_root_folder(title: str, special: str) -> bool:
    values = (title, QDateTime.currentMSecsSinceEpoch(), special, special)
    return sql.run(INSERT_ROOT_FOLDER, values) is not None


def has_user_bookmarks() -> bool:
    query = sql.run(HAS_USER_BOOKMARKS)
    return query is not None and query.next()


def display_title(row: DefaultBookmark) -> str:
    if row.is_folder():
        return str(QCoreApplication.translate(CONTEXT, row.title))
    return row.title


def insert_default_bookmark(row: DefaultBookmark, parent_id: object, position: int) -> object:
    is_folder = 1 if row.is_folder() else 0
    values = (parent_id, is_folder, display_title(row), row.url, position)
    insert = sql.run(INSERT_DEFAULT_BOOKMARK, (*values, QDateTime.currentMSecsSinceEpoch()))
    return None if insert is None else insert.lastInsertId()


def insert_default_rows(rows: Sequence[DefaultBookmark], parent_id: object) -> bool:
    for position, row in enumerate(rows):
        row_id = insert_default_bookmark(row, parent_id, position)
        if row_id is None or not insert_default_rows(row.children, row_id):
            return False
    return True


def create_history_table() -> bool:
    return run_all(HISTORY_STATEMENTS)


def create_bookmarks_table() -> bool:
    return run_all((BOOKMARKS_TABLE, BOOKMARKS_INDEX))


def create_root_folders() -> bool:
    return insert_root_folder("Bookmarks Toolbar", "toolbar")


def create_favicons_table() -> bool:
    return sql.run(FAVICONS_TABLE) is not None


def seed_default_bookmarks() -> bool:
    if has_user_bookmarks():
        return True
    toolbar = sql.ids(TOOLBAR_FOLDER)
    return bool(toolbar) and insert_default_rows(DEFAULT_BOOKMARKS, toolbar[0])


def create_extension_storage_table() -> bool:
    return sql.run(EXTENSION_STORAGE_TABLE) is not None


def create_site_settings_table() -> bool:
    return sql.run(SITE_SETTINGS_TABLE) is not None
