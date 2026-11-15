from PySide6.QtSql import QSqlQuery


def text_at(query: QSqlQuery, column: int) -> str:
    return "" if query.isNull(column) else str(query.value(column))


def integer_at(query: QSqlQuery, column: int) -> int:
    return 0 if query.isNull(column) else int(query.value(column))


def flag_at(query: QSqlQuery, column: int) -> bool:
    return integer_at(query, column) != 0
