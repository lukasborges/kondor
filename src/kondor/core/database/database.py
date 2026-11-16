from collections.abc import Callable
from pathlib import Path
from typing import NamedTuple

from PySide6.QtCore import QStandardPaths, qWarning
from PySide6.QtSql import QSqlDatabase, QSqlQuery

from kondor.core.database import bookmarkrootmerge, databasemigrations, sql

SCHEMA_VERSION = 6
DRIVER = "QSQLITE"
CONNECTION_NAME = "kondor"
FILE_NAME = "kondor.sqlite"


class MigrationStep(NamedTuple):
    version: int
    apply: Callable[[], bool]


MIGRATION_STEPS = (
    MigrationStep(1, databasemigrations.create_history_table),
    MigrationStep(2, databasemigrations.create_bookmarks_table),
    MigrationStep(2, databasemigrations.create_root_folders),
    MigrationStep(3, databasemigrations.create_favicons_table),
    MigrationStep(4, databasemigrations.seed_default_bookmarks),
    MigrationStep(5, databasemigrations.create_extension_storage_table),
    MigrationStep(6, bookmarkrootmerge.merge_other_into_toolbar),
)


def database_path() -> str:
    folder = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    Path(folder).mkdir(parents=True, exist_ok=True)
    return f"{folder}/{FILE_NAME}"


def apply_migrations(current_version: int) -> bool:
    for step in MIGRATION_STEPS:
        if step.version > current_version and not step.apply():
            return False
    return sql.run(f"PRAGMA user_version = {SCHEMA_VERSION}") is not None


def schema_version() -> int:
    query = sql.run("PRAGMA user_version")
    return int(query.value(0)) if query is not None and query.next() else 0


class Database:
    _instance: "Database | None" = None

    def __init__(self) -> None:
        self._path = database_path()
        self._database = QSqlDatabase.addDatabase(DRIVER, CONNECTION_NAME)
        self._database.setDatabaseName(self._path)
        self._is_valid = False

    @classmethod
    def instance(cls) -> "Database":
        if cls._instance is None:
            cls._instance = cls()
            cls._instance.open()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        if cls._instance is not None:
            cls._instance.close()
        cls._instance = None
        QSqlDatabase.removeDatabase(CONNECTION_NAME)

    def is_valid(self) -> bool:
        return self._is_valid and self._database.isOpen()

    def handle(self) -> QSqlDatabase:
        return self._database

    def open(self) -> None:
        if not self._database.open():
            qWarning(f"Database: failed to open {self._path}: {self.last_error()}")
            return
        self._is_valid = self.is_usable_file()
        if self._is_valid:
            self.migrate()
        else:
            self._database.close()

    def close(self) -> None:
        self._database.close()
        self._database = QSqlDatabase()
        self._is_valid = False

    def last_error(self) -> str:
        return str(self._database.lastError().text())

    def is_usable_file(self) -> bool:
        if QSqlQuery(self._database).exec("PRAGMA user_version"):
            return True
        qWarning(f"Database: {self._path} is not a usable SQLite database: {self.last_error()}")
        return False

    def migrate(self) -> None:
        current = schema_version()
        if current >= SCHEMA_VERSION:
            return
        if not sql.in_transaction(lambda: apply_migrations(current)):
            qWarning(f"Database: migration failed: {self.last_error()}")
