from collections.abc import Callable, Sequence

from PySide6.QtSql import QSqlDatabase, QSqlQuery

from kondor.core.database import database


def bind_and_execute(query: QSqlQuery, values: Sequence[object]) -> bool:
    for value in values:
        query.addBindValue(value)
    return bool(query.exec())


def opened_handle() -> QSqlDatabase:
    return database.Database.instance().handle()


def run(statement: str, values: Sequence[object] = ()) -> QSqlQuery | None:
    if not database.Database.instance().is_valid():
        return None
    query = QSqlQuery(opened_handle())
    if not query.prepare(statement) or not bind_and_execute(query, values):
        return None
    return query


def ids(statement: str, values: Sequence[object] = ()) -> list[int]:
    result: list[int] = []
    query = run(statement, values)
    while query is not None and query.next():
        result.append(int(query.value(0)))
    return result


def in_transaction(work: Callable[[], bool]) -> bool:
    handle = opened_handle()
    if not handle.transaction():
        return False
    if work() and handle.commit():
        return True
    handle.rollback()
    return False


def id_or_null(row_id: int) -> int | None:
    return row_id if row_id > 0 else None
